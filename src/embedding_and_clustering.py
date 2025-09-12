import os
import time
import pandas as pd
import uuid
import cuml
import numpy as np
from transformers import pipeline, AutoTokenizer
import torch
import csv
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
import multiprocessing as mp
import glob
import argparse

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
N_GPU_WORKERS = 8
N_GPUS = 8

DATA_QUEUE_SIZE = 10000
SUMMARY_QUEUE_SIZE = 1000

LOG_INTERVAL = 5000
EMBEDDING_BATCH_SIZE = 128
QDRANT_BATCH_SIZE = 64

# --- Paths ---
PROCESSED_DATA_DIR = "/home/coinsafe/business-finder/processed_data/filtered_comments"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION_NAME = "reddit_ideas_pain_points"
CLUSTER_DATA_DIR = "/home/coinsafe/business-finder/data/clusters"
CLUSTER_ASSIGNMENTS_PATH = os.path.join(CLUSTER_DATA_DIR, "cluster_assignments.csv")
SUMMARIES_CSV_PATH = "/home/coinsafe/business-finder/summaries.csv"

# --- Worker Globals ---
_embedding_model = None
_qdrant_client_worker = None
_summarization_pipeline = None
_tokenizer = None

# --- Embedding Worker Functions (Phase 1) ---
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
        if item is None:
            break

        for index, row in item.iterrows():
            record_batch.append(row.to_dict())

            if len(record_batch) >= EMBEDDING_BATCH_SIZE:
                texts_to_encode = [rec['body'] for rec in record_batch]
                embeddings = model.encode(texts_to_encode, convert_to_tensor=True, device=f'cuda:{gpu_id % N_GPUS}')
                
                points = [models.PointStruct(id=str(uuid.uuid4().hex), vector=embeddings[i].tolist(), payload=record) for i, record in enumerate(record_batch)]

                if points:
                    qdrant_client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points, wait=True)
                
                processed_count += len(record_batch)
                if processed_count % LOG_INTERVAL == 0:
                    print(f"[Embed-Worker-{gpu_id}] Processed {processed_count} items.")
                record_batch = []

    if record_batch:
        texts_to_encode = [rec['body'] for rec in record_batch]
        embeddings = model.encode(texts_to_encode, convert_to_tensor=True, device=f'cuda:{gpu_id % N_GPUS}')
        points = [models.PointStruct(id=str(uuid.uuid4().hex), vector=embeddings[i].tolist(), payload=record) for i, record in enumerate(record_batch)]
        if points:
            qdrant_client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points, wait=True)

    print(f"[Embed-Worker-{gpu_id}] Finished.")

def run_phase_1_embedding():
    print("--- Starting Phase 1: Parallel Embedding ---")
    qdrant_client_main = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    dummy_model = SentenceTransformer('all-MiniLM-L6-v2')
    vector_size = dummy_model.get_sentence_embedding_dimension()
    del dummy_model

    print(f"Recreating Qdrant collection '{QDRANT_COLLECTION_NAME}' with vector size {vector_size}...")
    qdrant_client_main.recreate_collection(
        collection_name=QDRANT_COLLECTION_NAME,
        vectors_count=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )

    data_queue = mp.Queue(maxsize=DATA_QUEUE_SIZE)
    embedding_procs = []
    for i in range(N_GPU_WORKERS):
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
    for _ in range(N_GPU_WORKERS):
        data_queue.put(None)

    for p in embedding_procs:
        p.join()
    print("--- Embedding Phase Complete ---")

# --- Clustering Function (Phase 2) ---
MAX_POINTS_FOR_CLUSTERING = 4_000_000

def run_phase_2_clustering():
    print("--- Starting Phase 2: Single-Process Clustering (Memory Optimized) ---")
    qdrant_client_main = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    print("Getting vector size from model...")
    dummy_model = SentenceTransformer('all-MiniLM-L6-v2')
    vector_size = dummy_model.get_sentence_embedding_dimension()
    del dummy_model

    print("Getting total point count from Qdrant...")
    collection_info = qdrant_client_main.get_collection(collection_name=QDRANT_COLLECTION_NAME)
    total_points = collection_info.points_count

    if total_points == 0:
        print("No points in Qdrant to cluster. Exiting Phase 2.")
        return

    points_to_process = total_points
    if total_points > MAX_POINTS_FOR_CLUSTERING:
        print(f"WARNING: Dataset size ({total_points}) is too large for GPU memory.")
        print(f"Clustering will be performed on the first {MAX_POINTS_FOR_CLUSTERING} points found.")
        points_to_process = MAX_POINTS_FOR_CLUSTERING

    print(f"Pre-allocating memory for {points_to_process} vectors...")
    embeddings_np = np.empty((points_to_process, vector_size), dtype=np.float32)
    point_ids = []
    
    print("Streaming vectors from Qdrant into pre-allocated array...")
    next_offset = None
    processed_points = 0
    while processed_points < points_to_process:
        limit = min(2000, points_to_process - processed_points)
        scroll_result, next_offset = qdrant_client_main.scroll(
            collection_name=QDRANT_COLLECTION_NAME,
            limit=limit,
            with_payload=False,
            with_vectors=True,
            offset=next_offset
        )
        
        if not scroll_result:
            break

        chunk_size = len(scroll_result)
        for i, point in enumerate(scroll_result):
            embeddings_np[processed_points + i] = point.vector
            point_ids.append(point.id)
        
        processed_points += chunk_size
        print(f"Loaded {processed_points}/{points_to_process} vectors...")

        if next_offset is None:
            break

    # If we didn't load as many points as we expected, we need to trim the numpy array
    if processed_points < points_to_process:
        embeddings_np = embeddings_np[:processed_points]

    print(f"Retrieved {processed_points} embeddings. Starting HDBSCAN clustering...")
    hdbscan_model = cuml.HDBSCAN(min_cluster_size=5, min_samples=10, alpha=2.0, verbose=True)
    cluster_labels = hdbscan_model.fit_predict(embeddings_np)
    print("HDBSCAN clustering complete.")

    os.makedirs(CLUSTER_DATA_DIR, exist_ok=True)
    print(f"Saving cluster assignments to {CLUSTER_ASSIGNMENTS_PATH}...")
    assignments_df = pd.DataFrame({
        'point_id': point_ids,
        'cluster_label': cluster_labels
    })
    assignments_df.to_csv(CLUSTER_ASSIGNMENTS_PATH, index=False)
    
    print("--- Clustering Phase Complete ---")

# --- Summarization Worker Functions (Phase 3) ---
def get_summarization_pipeline(gpu_id):
    global _summarization_pipeline, _tokenizer
    if _summarization_pipeline is None:
        physical_gpu_id = gpu_id % N_GPUS
        model_name = "meta-llama/Llama-2-13b-chat-hf"
        print(f"[Summary-Worker-{gpu_id}] Initializing model '{model_name}' on GPU: {physical_gpu_id}")
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _summarization_pipeline = pipeline(
            "text-generation",
            model=model_name,
            torch_dtype=torch.float16,
            device_map=f"cuda:{physical_gpu_id}",
            load_in_4bit=True,
        )
    return _summarization_pipeline, _tokenizer

def summarization_worker(gpu_id: int, summary_queue: mp.Queue, result_queue: mp.Queue):
    print(f"[Summary-Worker-{gpu_id}] Starting.")
    summarizer, tokenizer = get_summarization_pipeline(gpu_id)
    qdrant_client = get_qdrant_client_worker()

    while True:
        item = summary_queue.get()
        if item is None:
            break

        cluster_id, point_ids = item
        
        records = qdrant_client.retrieve(
            collection_name=QDRANT_COLLECTION_NAME,
            ids=point_ids,
            with_payload=True
        )
        texts = [rec.payload['body'] for rec in records]
        sample_texts = texts[:5]
        
        # Create the formatted string with backslashes before the f-string
        formatted_comments = '\n- '.join(sample_texts)

        prompt = f"""<s>[INST] <<SYS>>
Your task is to synthesize the provided Reddit comments into a concise 1-2 sentence summary of the core business opportunity or underlying problem.
<</SYS>>

Comments:
- {formatted_comments}

Concise Summary: [/INST]"""

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
    
    print(f"Reading cluster assignments from {CLUSTER_ASSIGNMENTS_PATH}...")
    if not os.path.exists(CLUSTER_ASSIGNMENTS_PATH):
        print(f"Error: Cluster assignments file not found. Please run Phase 2 first.")
        return
        
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
    parser = argparse.ArgumentParser(description="Run the embedding, clustering, and summarization pipeline in phases.")
    parser.add_argument('--skip-embedding', action='store_true', help="Skip Phase 1 (Embedding) and start from clustering.")
    parser.add_argument('--skip-clustering', action='store_true', help="Skip Phase 2 (Clustering) and start from summarization.")
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

    run_phase_3_summarization()

    end_time = time.time()
    print(f"Pipeline finished in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()