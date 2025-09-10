import sys
version = sys.version_info
if version.major < 3 or (version.major == 3 and version.minor < 10):
    raise RuntimeError("This script requires Python 3.10 or higher")
import os
import time
from typing import List, Dict, Any, Optional
import pandas as pd
from src.fileStreams import getFileJsonStream
from transformers import pipeline
import multiprocessing as mp
import pprint
import numba.cuda as cuda
from itertools import cycle

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# --- Configuration ---
N_CPU_WORKERS = 40
N_GPU_WORKERS = 12 # One worker process per GPU
N_GPUS = 4
RAW_QUEUE_SIZE = 200000
FILTERED_QUEUE_SIZE = 200000
LOG_INTERVAL = 20000
NLP_BATCH_SIZE = 3000

file_to_process = ""
output_parquet_dir = "/home/coinsafe/business-finder/processed_data/filtered_comments"

# --- Globals for Models and Keywords ---
_candidate_labels = ["pain_point", "idea"]
_pain_point_keywords = ["frustrating", "problem", "difficult", "struggle", "annoying", "wish", "need", "can't", "should be", "hard to", "lack of", "missing", "broken"]
_idea_keywords = ["idea", "solution", "concept", "opportunity", "build", "create", "develop", "imagine", "what if", "improve", "new way", "innovate"]

# --- GPU Worker Functions ---

# Each worker process will have its own classifier instance
_worker_classifier = None

def get_classifier(gpu_id: int):
    gpu_id = gpu_id % N_GPUS
    """Initializes a classifier pipeline on a specific GPU for a worker process."""
    global _worker_classifier
    if _worker_classifier is None:
        print(f"[GPU-Worker-{gpu_id}] Initializing classifier on device: {gpu_id}")
        cuda.select_device(gpu_id)
        _worker_classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli", device=gpu_id)
    return _worker_classifier

def nlp_classify_batch_worker(batch: List[Dict[str, Any]], gpu_id: int) -> List[Dict[str, Any]]:
    """The target function for each GPU worker process."""
    classifier = get_classifier(gpu_id)
    final_results = []
    texts_to_classify = [row.get("body", "") for row in batch]

    # Create a simple generator dataset to follow Hugging Face recommendation
    def text_generator(texts):
        for text in texts:
            yield text

    dataset = text_generator(texts_to_classify)
    
    try:
        # The pipeline will now pull from the generator, which is more efficient.
        # It also returns a generator, so we must iterate over it.
        classification_results_generator = classifier(dataset, candidate_labels=_candidate_labels)

        for i, classification_results in enumerate(classification_results_generator):
            row = batch[i] # Get the original item by index
            top_label = classification_results['labels'][0]
            top_score = classification_results['scores'][0]

            if top_score > 0.7:
                final_results.append({
                    "id": row.get("id"), "link_id": row.get("link_id"),
                    "author": row.get("author"), "subreddit": row.get("subreddit"),
                    "created_utc": row.get("created_utc"), "body": row.get("body"),
                    "is_pain_point": (top_label == "pain_point"),
                    "is_idea": (top_label == "idea"),
                    "nlp_top_label": top_label, "nlp_top_score": top_score
                })

    except Exception as e:
        print(f"[GPU-Worker-{gpu_id}] Error during batch NLP classification: {e}")
        return []
    
    if len(batch) > 0:
        print(f"[GPU-Worker-{gpu_id}] Classified a batch of {len(batch):,} items, yielding {len(final_results):,} results.")
            
    return final_results

# --- Pipeline Stage 1: Decompression ---
def producer(queue: mp.Queue, path: str, limit: Optional[int], num_consumers: int):
    print(f"[Producer] Starting data ingestion for {num_consumers} consumer(s)...")
    count = 0
    start_time = time.time()
    try:
        with open(path, "rb") as f:
            json_stream_generator = getFileJsonStream(path, f, max_items=limit)
            if json_stream_generator:
                for item in json_stream_generator:
                    queue.put(item)
                    count += 1
                    if count % LOG_INTERVAL == 0:
                        elapsed = time.time() - start_time
                        rate = count / elapsed if elapsed > 0 else 0
                        print(f"[Producer] Ingested {count:,} items ({rate:,.0f} items/sec)")
    finally:
        print(f"[Producer] Finished ingesting {count:,} total items. Signaling end to CPU workers.")
        for _ in range(num_consumers):
            queue.put(None)


# --- Pipeline Stage 2: CPU Filtering ---
def cpu_filter_worker(raw_q: mp.Queue, filtered_q: mp.Queue):
    pid = os.getpid()
    processed_count = 0
    forwarded_count = 0
    while True:
        item = raw_q.get()
        if item is None:
            break
        
        processed_count += 1
        body = item.get("body", "")
        if body and len(body) > 50:
            if any(keyword in body.lower() for keyword in _pain_point_keywords) or \
               any(keyword in body.lower() for keyword in _idea_keywords):
                filtered_q.put(item)
                forwarded_count += 1
        
        if processed_count % LOG_INTERVAL == 0:
            print(f"[CPU-Filter-{pid}] Processed: {processed_count:,}, Forwarded: {forwarded_count:,}")

    print(f"[CPU-Filter-{pid}] Shutting down. Processed {processed_count:,} total. Forwarded {forwarded_count:,} total.")
    filtered_q.put(None)


# --- Main Orchestrator (Refactored with Multiprocessing) ---
def process_single_file(path: str, limit: Optional[int] = None):
    print(f"Starting 3-stage pipeline for file: {path}...")
    print(f"CPU Filter Workers: {N_CPU_WORKERS}, GPU Workers: {N_GPU_WORKERS}, NLP Batch Size: {NLP_BATCH_SIZE}")

    raw_data_queue = mp.Queue(maxsize=RAW_QUEUE_SIZE)
    filtered_data_queue = mp.Queue(maxsize=FILTERED_QUEUE_SIZE)

    producer_proc = mp.Process(target=producer, args=(raw_data_queue, path, limit, N_CPU_WORKERS))
    
    cpu_workers = []
    for _ in range(N_CPU_WORKERS):
        p = mp.Process(target=cpu_filter_worker, args=(raw_data_queue, filtered_data_queue))
        cpu_workers.append(p)

    # --- Manual GPU Worker Pool Setup ---
    gpu_pool = mp.Pool(processes=N_GPU_WORKERS)
    gpu_ids = cycle(range(N_GPU_WORKERS)) # To round-robin tasks to GPUs

    try:
        producer_proc.start()
        for p in cpu_workers:
            p.start()

        async_results = []
        batch = []
        sentinels_received = 0
        
        print("[Orchestrator] Starting to listen for filtered data to submit to GPUs...")
        while sentinels_received < N_CPU_WORKERS:
            item = filtered_data_queue.get()
            if item is None:
                sentinels_received += 1
                continue
            
            batch.append(item)

            if len(batch) >= NLP_BATCH_SIZE:
                gpu_id = next(gpu_ids)
                print(f"[Orchestrator] Batch of {len(batch)} items ready. Submitting to GPU {gpu_id}...")
                res = gpu_pool.apply_async(nlp_classify_batch_worker, args=(batch, gpu_id))
                async_results.append(res)
                batch = [] # Reset batch

        if batch:
            gpu_id = next(gpu_ids)
            print(f"[Orchestrator] Submitting final batch of {len(batch)} items to GPU {gpu_id}...")
            res = gpu_pool.apply_async(nlp_classify_batch_worker, args=(batch, gpu_id))
            async_results.append(res)

        print(f"\n[Orchestrator] All data submitted. Total batches: {len(async_results):,}. Waiting for results...")
        
        all_results = []
        for res in async_results:
            result_batch = res.get()
            if result_batch:
                all_results.extend(result_batch)

        print(f"\n[Orchestrator] All {len(async_results):,} batches completed. Total results: {len(all_results):,}")

        if not all_results:
            print("[Orchestrator] No results to save. Exiting.")
            return

        df = pd.DataFrame(all_results)
        os.makedirs(output_parquet_dir, exist_ok=True)
        output_file = os.path.join(output_parquet_dir, "filtered_data.parquet")
        print(f"\n[Orchestrator] Writing {len(df):,} records to {output_file}...\n")
        df.to_parquet(output_file, engine='pyarrow')
        print("\n[Orchestrator] Finished writing classified data to Parquet.\n")

    finally:
        print("[Orchestrator] Cleaning up resources...")
        gpu_pool.close()
        gpu_pool.join()
        print("[Orchestrator] GPU worker pool closed.")
        producer_proc.join()
        print("[Orchestrator] Producer process joined.")
        for p in cpu_workers:
            p.join()
        print("[Orchestrator] All CPU filter workers joined.")

def main():
    global file_to_process
    file_to_process = "/home/coinsafe/business-finder/reddit-dumps/reddit/comments/RC_2025-07.zst"

    if not os.path.exists(file_to_process):
        print(f"Error: File not found at {file_to_process}. Please ensure the data is downloaded.")
        print("You can download the data using the torrent file: /home/coinsafe/business-finder/reddit-dumps/reddit-b6a7ccf72368a7d39c018c423e01bc15aa551122.torrent")
        return

    process_single_file(file_to_process, limit=None) # Renamed function
    
    print("Data ingestion, filtering, and classification phase complete.\n")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True) # Use spawn for CUDA safety
    main()
