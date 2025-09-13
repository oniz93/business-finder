import os
import time
import pandas as pd
import uuid
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

# cuML and CUDA for GPU-specific tasks
import cudf
import cupy as cp
import numba.cuda as cuda
from cuml.cluster import KMeans, HDBSCAN

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
N_GPUS = 8
N_GPU_WORKERS = 8 # For summarization and embedding
KMEANS_N_CLUSTERS_PER_GPU = 12500
SUMMARY_QUEUE_SIZE = 1000
DATA_QUEUE_SIZE = 10000
EMBEDDING_BATCH_SIZE = 128
LOG_INTERVAL = 5000

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
    for _ in range(number_workers):
        data_queue.put(None)

    for p in embedding_procs:
        p.join()
    print("--- Embedding Phase Complete ---")

# --- Phase 2 Worker Function ---
def kmeans_worker(args):
    """Worker function to load its own data and run KMeans on a specific GPU."""
    gpu_id, offset, limit, vector_size = args
    try:
        cuda.select_device(gpu_id)
        print(f"[GPU-{gpu_id}] Worker started. Will load {limit} vectors starting from offset {offset}.")

        qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=120)
        worker_embeddings = np.empty((limit, vector_size), dtype=np.float32)
        worker_point_ids = []

        scroll_result, next_offset = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION_NAME, 
            limit=limit,
            offset=offset,
            with_payload=True, 
            with_vectors=True
        )

        if not scroll_result:
            print(f"[GPU-{gpu_id}] No data returned from Qdrant.")
            return None, None, None

        num_points_loaded = len(scroll_result)
        for i, point in enumerate(scroll_result):
            worker_embeddings[i] = point.vector
            worker_point_ids.append(point.id)
        
        if num_points_loaded < limit:
            print(f"[GPU-{gpu_id}] Loaded {num_points_loaded} which is less than limit {limit}. Slicing array.")
            worker_embeddings = worker_embeddings[:num_points_loaded]

        print(f"[GPU-{gpu_id}] Successfully loaded {len(worker_embeddings)} vectors.")

        cupy_array = cp.asarray(worker_embeddings)
        chunk_gdf = cudf.DataFrame(cupy_array)

        kmeans = KMeans(n_clusters=KMEANS_N_CLUSTERS_PER_GPU, random_state=gpu_id, n_init=1)
        kmeans.fit(chunk_gdf)

        print(f"[GPU-{gpu_id}] KMeans complete.")
        return kmeans.labels_.to_numpy(), kmeans.cluster_centers_.to_numpy(), worker_point_ids

    except Exception as e:
        print(f"[GPU-{gpu_id}] Error in worker: {e}")
        return None, None, None

N_MAX_POINTS = 16_000

# --- Clustering Function (Phase 2) ---
def run_phase_2_clustering():
    print("--- Starting Phase 2: Two-Phase Hybrid Clustering ---")

    try:
        qdrant_client_main = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        print("Getting total point count from Qdrant...")
        collection_info = qdrant_client_main.get_collection(collection_name=QDRANT_COLLECTION_NAME)
        total_points = collection_info.points_count
        dummy_model = SentenceTransformer('all-MiniLM-L6-v2')
        vector_size = dummy_model.get_sentence_embedding_dimension()
        del dummy_model

        if total_points == 0:
            print("No points in Qdrant to cluster. Exiting Phase 2.")
            return
        
        if total_points > N_MAX_POINTS:
            total_points = N_MAX_POINTS

        print(f"Total vectors to process: {total_points}")

        print("\n--- Starting Phase 1: Distributed K-Means Summarization ---")
        
        points_per_gpu = total_points // N_GPUS
        tasks = []
        for i in range(N_GPUS):
            offset = i * points_per_gpu
            limit = points_per_gpu
            if i == N_GPUS - 1:
                limit = total_points - offset
            tasks.append((i, offset, limit, vector_size))

        with mp.Pool(processes=N_GPUS) as pool:
            results = pool.map(kmeans_worker, tasks)

        valid_results = [res for res in results if res[0] is not None]
        if not valid_results:
            raise RuntimeError("All KMeans workers failed.")
            
        chunk_labels_list = [res[0] for res in valid_results]
        centroid_chunks_list = [res[1] for res in valid_results]
        point_id_chunks_list = [res[2] for res in valid_results]

        print("\n--- Starting Phase 2: Centralized HDBSCAN on Centroids ---")

        all_centroids = np.vstack(centroid_chunks_list)
        print(f"Total number of micro-cluster centroids to cluster: {len(all_centroids)}")

        cuda.select_device(0)
        print("Running HDBSCAN on GPU 0...")
        hdbscan = HDBSCAN(min_cluster_size=15, min_samples=10, metric='euclidean')
        meta_labels = hdbscan.fit_predict(all_centroids)
        print("HDBSCAN on centroids complete.")

        print("\n--- Mapping meta-clusters back to original data points ---")
        final_labels = []
        final_point_ids = []
        centroid_offset = 0
        for i in range(len(valid_results)):
            local_labels = chunk_labels_list[i]
            num_centroids_in_chunk = len(centroid_chunks_list[i])
            
            mapped_labels = [meta_labels[centroid_offset + label] if (centroid_offset + label) < len(meta_labels) else -1 for label in local_labels]
            final_labels.extend(mapped_labels)
            final_point_ids.extend(point_id_chunks_list[i])
            centroid_offset += num_centroids_in_chunk

        final_labels = np.array(final_labels)

        print("\n--- Saving final cluster assignments ---")
        os.makedirs(CLUSTER_DATA_DIR, exist_ok=True)
        assignments_df = pd.DataFrame({'point_id': final_point_ids, 'cluster_label': final_labels})
        assignments_df.to_csv(CLUSTER_ASSIGNMENTS_PATH, index=False)
        print(f"Final cluster assignments saved to {CLUSTER_ASSIGNMENTS_PATH}")

    except Exception as e:
        print(f"An error occurred during clustering: {e}")
    finally:
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
        prompt = f"""<s>[INST] <<SYS>>\nYour task is to synthesize the provided Reddit comments into a concise 1-2 sentence summary of the core business opportunity or underlying problem.\n<</SYS>>\n\nComments:\n- {formatted_comments}\n\nConcise Summary: [/INST]"""

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
    parser = argparse.ArgumentParser(description="Run the embedding and clustering pipeline in phases.")
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

    # run_phase_3_summarization()

    end_time = time.time()
    print(f"Pipeline finished in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
