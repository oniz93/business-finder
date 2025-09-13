

import os
import time
import pandas as pd
import uuid
import numpy as np
import hdbscan
import shutil
import asyncio

from pyspark.sql import SparkSession, Row
from pyspark.ml.clustering import KMeans
from pyspark.ml.linalg import Vectors
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.models import PointStruct, ScrollResult
from typing import List, Optional, Any

import multiprocessing as mp
import glob
import argparse

# For phase 1 and 3, we still need torch and transformers
import torch
from transformers import pipeline, AutoTokenizer
from sentence_transformers import SentenceTransformer

# --- Configuration ---
# General
N_GPUS = 8
N_GPU_WORKERS = 8

# Phase 1: Embedding
DATA_QUEUE_SIZE = 10000
EMBEDDING_BATCH_SIZE = 128
LOG_INTERVAL = 5000

# Phase 2: Spark & Clustering
SPARK_MASTER = "local[*"
SPARK_APP_NAME = "HybridClustering"
SPARK_EXECUTOR_MEMORY = "8g"
SPARK_DRIVER_MEMORY = "8g"
KMEANS_N_CLUSTERS = 100_000
HDB_SCAN_MIN_CLUSTER_SIZE = 15
TEMP_PARQUET_DIR = "/tmp/qdrant_export"

# Phase 3: Summarization
SUMMARY_QUEUE_SIZE = 1000

# Qdrant config
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION_NAME = "reddit_ideas_pain_points"

# --- Paths ---
PROCESSED_DATA_DIR = "/home/coinsafe/business-finder/processed_data/filtered_comments"
CLUSTER_DATA_DIR = "/home/coinsafe/business-finder/data/clusters"
CLUSTER_ASSIGNMENTS_PATH = "/home/coinsafe/business-finder/data/clusters/cluster_assignments.csv"
SUMMARIES_CSV_PATH = "/home/coinsafe/business-finder/summaries.csv"


# --- Embedding Worker Functions (Phase 1) ---
_embedding_model = None
_qdrant_client_worker = None

def get_embedding_model(gpu_id):
    global _embedding_model
    if _embedding_model is None:
        physical_gpu_id = gpu_id % N_GPUS
        print(f"[Embed-Worker-{gpu_id}] Initializing embedding model on GPU: {physical_gpu_id}")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=f'cuda:{physical_gpu_id}')
    return _embedding_model

def get_qdrant_client_worker():
    global _qdrant_client_worker
    if _qdrant_client_worker is None:
        from qdrant_client import QdrantClient
        _qdrant_client_worker = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    return _qdrant_client_worker

def embedding_worker(gpu_id: int, data_queue: mp.Queue):
    print(f"[Embed-Worker-{gpu_id}] Starting.")
    model = get_embedding_model(gpu_id)
    qdrant_client = get_qdrant_client_worker()
    processed_count = 0
    record_batch = []
    while True:
        item = data_queue.get()
        if item is None: break
        for index, row in item.iterrows():
            record_batch.append(row.to_dict())
            if len(record_batch) >= EMBEDDING_BATCH_SIZE:
                texts_to_encode = [rec['body'] for rec in record_batch]
                embeddings = model.encode(texts_to_encode, convert_to_tensor=True, device=f'cuda:{gpu_id % N_GPUS}')
                points = [models.PointStruct(id=str(uuid.uuid4().hex), vector=embeddings[i].tolist(), payload=record) for i, record in enumerate(record_batch)]
                if points: qdrant_client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points, wait=True)
                processed_count += len(record_batch)
                if processed_count % LOG_INTERVAL == 0: print(f"[Embed-Worker-{gpu_id}] Processed {processed_count} items.")
                record_batch = []
    if record_batch:
        texts_to_encode = [rec['body'] for rec in record_batch]
        embeddings = model.encode(texts_to_encode, convert_to_tensor=True, device=f'cuda:{gpu_id % N_GPUS}')
        points = [models.PointStruct(id=str(uuid.uuid4().hex), vector=embeddings[i].tolist(), payload=record) for i, record in enumerate(record_batch)]
        if points: qdrant_client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points, wait=True)
    print(f"[Embed-Worker-{gpu_id}] Finished.")

def run_phase_1_embedding():
    print("--- Starting Phase 1: Parallel Embedding ---")
    number_workers = N_GPU_WORKERS * 2
    qdrant_client_main = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    dummy_model = SentenceTransformer('all-MiniLM-L6-v2')
    vector_size = dummy_model.get_sentence_embedding_dimension()
    del dummy_model
    print(f"Recreating Qdrant collection '{QDRANT_COLLECTION_NAME}' with vector size {vector_size}...")
    qdrant_client_main.recreate_collection(
        collection_name=QDRANT_COLLECTION_NAME,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )
    data_queue = mp.Queue(maxsize=DATA_QUEUE_SIZE)
    embedding_procs = []
    for i in range(number_workers):
        p = mp.Process(target=embedding_worker, args=(i, data_queue))
        embedding_procs.append(p)
        p.start()
    parquet_files = glob.glob(f"{PROCESSED_DATA_DIR}/**/*.parquet", recursive=True)
    print(f"Found {len(parquet_files)} parquet files to process.")
    for f in parquet_files:
        df = pd.read_parquet(f)
        for i in range(0, len(df), EMBEDDING_BATCH_SIZE):
            chunk = df.iloc[i:i+EMBEDDING_BATCH_SIZE]
            data_queue.put(chunk)
    print("Finished reading all files. Signaling end to embedding workers.")
    for _ in range(number_workers): data_queue.put(None)
    for p in embedding_procs: p.join()
    print("--- Embedding Phase Complete ---")


# --- Data Extraction Function (for Phase 2) ---
async def dump_qdrant_to_parquet():
    """Connects to Qdrant and dumps the entire collection to a directory of Parquet files."""
    print("--- Starting Data Extraction Phase ---")
    client = AsyncQdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=3600)
    
    if os.path.exists(TEMP_PARQUET_DIR):
        print(f"Removing existing temporary directory: {TEMP_PARQUET_DIR}")
        shutil.rmtree(TEMP_PARQUET_DIR)
    os.makedirs(TEMP_PARQUET_DIR, exist_ok=True)

    current_offset = None
    batch_num = 0
    total_points_saved = 0

    while True:
        print(f"Fetching batch {batch_num}...", end='\r')
        points, next_offset = await client.scroll(
            collection_name=QDRANT_COLLECTION_NAME,
            limit=2000,
            offset=current_offset,
            with_payload=True,
            with_vectors=True
        )

        if not points:
            break

        data = []
        for point in points:
            point_data = {
                "id": point.id,
                "vector": point.vector
            }
            data.append(point_data)
        df = pd.DataFrame(data)

        temp_file_path = os.path.join(TEMP_PARQUET_DIR, f"batch_{batch_num:05d}.parquet")
        df.to_parquet(temp_file_path, index=False)
        total_points_saved += len(df)

        current_offset = next_offset
        batch_num += 1

    print(f"\nData extraction complete. Saved {total_points_saved} points to {batch_num} Parquet files in {TEMP_PARQUET_DIR}")


# --- Clustering Function (Phase 2) ---
def run_phase_2_clustering():
    asyncio.run(dump_qdrant_to_parquet())

    print("\n--- Starting Phase 2: Two-Phase Hybrid Clustering with Spark ---")
    spark = (
        SparkSession.builder.appName(SPARK_APP_NAME).master(SPARK_MASTER)
        .config("spark.executor.memory", SPARK_EXECUTOR_MEMORY).config("spark.driver.memory", SPARK_DRIVER_MEMORY)
        .getOrCreate()
    )
    try:
        print(f"Loading data from Parquet files at {TEMP_PARQUET_DIR} into Spark...")
        df = spark.read.parquet(TEMP_PARQUET_DIR)
        udf_to_vectors = spark.udf.register("to_vectors", lambda v: Vectors.dense(v), "vector")
        df = df.withColumn("features", udf_to_vectors(df['vector']))
        df.cache()
        print(f"Successfully loaded {df.count()} points into Spark.")

        print("\n--- Starting K-Means Summarization ---")
        kmeans = KMeans(k=KMEANS_N_CLUSTERS, seed=1, featuresCol="features")
        model = kmeans.fit(df)
        print("KMeans fitting complete. Collecting centroids.")
        centroids_np = np.array(model.clusterCenters())

        print("\n--- Starting Centralized HDBSCAN on Centroids ---")
        print(f"Clustering {len(centroids_np)} centroids with HDBSCAN...")
        hdbscan_clusterer = hdbscan.HDBSCAN(min_cluster_size=HDB_SCAN_MIN_CLUSTER_SIZE, metric='euclidean')
        meta_labels = hdbscan_clusterer.fit_predict(centroids_np)
        print("HDBSCAN on centroids complete.")

        print("\n--- Mapping meta-clusters back to original data points ---")
        centroid_map = {i: int(meta_labels[i]) for i in range(len(meta_labels))}
        b_centroid_map = spark.sparkContext.broadcast(centroid_map)
        predictions_df = model.transform(df)
        def get_meta_label(micro_cluster_id): return b_centroid_map.value.get(micro_cluster_id, -1)
        udf_get_meta_label = spark.udf.register("get_meta_label", get_meta_label)
        final_df = predictions_df.withColumn("cluster_label", udf_get_meta_label(predictions_df['prediction']))

        print("\n--- Saving final cluster assignments ---")
        output_df = final_df.select("id", "cluster_label")
        output_df.write.mode("overwrite").option("header", "true").csv(CLUSTER_ASSIGNMENTS_PATH + "_spark")
        print(f"Final cluster assignments saved to {CLUSTER_ASSIGNMENTS_PATH}_spark")

    except Exception as e:
        print(f"An error occurred during Spark clustering: {e}")
    finally:
        print("Stopping Spark session.")
        spark.stop()
        print(f"Cleaning up temporary directory: {TEMP_PARQUET_DIR}")
        shutil.rmtree(TEMP_PARQUET_DIR)
    print("--- Clustering Phase Complete ---")


# --- Summarization Worker Functions (Phase 3) ---
_summarization_pipeline = None
_tokenizer = None

def get_summarization_pipeline(gpu_id):
    global _summarization_pipeline, _tokenizer
    if _summarization_pipeline is None:
        physical_gpu_id = gpu_id % N_GPUS
        model_name = "meta-llama/Llama-2-13b-chat-hf"
        print(f"[Summary-Worker-{gpu_id}] Initializing model '{model_name}' on GPU: {physical_gpu_id}")
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _summarization_pipeline = pipeline(
            "text-generation", model=model_name, torch_dtype=torch.float16,
            device_map=f"cuda:{physical_gpu_id}", load_in_4bit=True,
        )
    return _summarization_pipeline, _tokenizer

def summarization_worker(gpu_id: int, summary_queue: mp.Queue, result_queue: mp.Queue):
    print(f"[Summary-Worker-{gpu_id}] Starting.")
    summarizer, tokenizer = get_summarization_pipeline(gpu_id)
    qdrant_client = get_qdrant_client_worker()
    while True:
        item = summary_queue.get()
        if item is None: break
        cluster_id, point_ids = item
        records = qdrant_client.retrieve(collection_name=QDRANT_COLLECTION_NAME, ids=point_ids, with_payload=True)
        texts = [rec.payload['body'] for rec in records]
        sample_texts = texts[:5]
        formatted_comments = '\n- '.join(sample_texts)
        prompt = f"<s>[INST] <<SYS>>\nYour task is to synthesize the provided Reddit comments into a concise 1-2 sentence summary of the core business opportunity or underlying problem.\n<</SYS>>\n\nComments:\n- {formatted_comments}\n\nConcise Summary: [/INST]"
        try:
            sequences = summarizer(prompt, do_sample=True, top_k=10, num_return_sequences=1, eos_token_id=tokenizer.eos_token_id, max_length=200)
            summary = sequences[0]['generated_text'].split("[/INST]")[-1].strip()
            result_queue.put({"cluster_id": cluster_id, "summary": summary})
        except Exception as e:
            print(f"[Summary-Worker-{gpu_id}] Error for cluster {cluster_id}: {e}")
            result_queue.put({"cluster_id": cluster_id, "summary": f"Error: {e}"})
    print(f"[Summary-Worker-{gpu_id}] Finished.")

def run_phase_3_summarization():
    print("--- Starting Phase 3: Parallel Summarization ---")
    if not os.path.exists(CLUSTER_ASSIGNMENTS_PATH):
        if not os.path.exists(CLUSTER_ASSIGNMENTS_PATH + "_spark"):
            print(f"Error: Cluster assignments file not found. Please run Phase 2 first.")
            return
        print("Found Spark output, converting to single CSV for summarization...")
        spark = SparkSession.builder.appName("CsvConverter").master(SPARK_MASTER).getOrCreate()
        spark_df = spark.read.csv(CLUSTER_ASSIGNMENTS_PATH + "_spark", header=True)
        pandas_df = spark_df.toPandas()
        pandas_df['point_id'] = pandas_df['id']
        pandas_df[['point_id', 'cluster_label']].to_csv(CLUSTER_ASSIGNMENTS_PATH, index=False)
        spark.stop()
        print("Conversion complete.")

    assignments_df = pd.read_csv(CLUSTER_ASSIGNMENTS_PATH)
    clusters = assignments_df[assignments_df['cluster_label'] != -1].groupby('cluster_label')['point_id'].apply(list).to_dict()
    print(f"Found {len(clusters)} clusters to summarize.")
    summary_queue = mp.Queue(maxsize=SUMMARY_QUEUE_SIZE)
    result_queue = mp.Queue()
    summary_procs = []
    for i in range(N_GPU_WORKERS):
        p = mp.Process(target=summarization_worker, args=(i, summary_queue, result_queue))
        summary_procs.append(p)
        p.start()
    for cluster_id, point_ids in clusters.items():
        summary_queue.put((cluster_id, point_ids))
    print("Signaling end to summarization workers.")
    for _ in range(N_GPU_WORKERS):
        summary_queue.put(None)
    summaries = [result_queue.get() for _ in range(len(clusters))]
    for p in summary_procs:
        p.join()
    print(f"Saving {len(summaries)} summaries to {SUMMARIES_CSV_PATH}...")
    with open(SUMMARIES_CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['cluster_id', 'summary']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    print("--- Summarization Phase Complete ---")

# --- Main Orchestrator ---
def main():
    parser = argparse.ArgumentParser(description="Run the full pipeline.")
    parser.add_argument('--skip-embedding', action='store_true', help="Skip Phase 1 (Embedding).")
    parser.add_argument('--skip-clustering', action='store_true', help="Skip Phase 2 (Clustering).")
    parser.add_argument('--skip-summarization', action='store_true', help="Skip Phase 3 (Summarization).")
    args = parser.parse_args()

    start_time = time.time()

    if not args.skip_embedding:
        run_phase_1_embedding()
    else:
        print("--- Skipping Phase 1: Embedding ---")

    if not args.skip_clustering:
        run_phase_2_clustering()
    else:
        print("--- Skipping Phase 2: Clustering ---")

    if not args.skip_summarization:
        run_phase_3_summarization()
    else:
        print("--- Skipping Phase 3: Summarization ---")

    end_time = time.time()
    print(f"Pipeline finished in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
