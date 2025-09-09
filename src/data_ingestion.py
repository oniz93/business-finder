import sys
version = sys.version_info
if version.major < 3 or (version.major == 3 and version.minor < 10):
    raise RuntimeError("This script requires Python 3.10 or higher")
import os
import time
from typing import List, Dict, Any, Optional
import pandas as pd
from src.fileStreams import getFileJsonStream
from dask_cuda import LocalCUDACluster
from dask.distributed import Client, as_completed
from dask.diagnostics import ProgressBar
from transformers import pipeline
import multiprocessing as mp
import pprint

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# --- Configuration ---
N_CPU_WORKERS = 20
RAW_QUEUE_SIZE = 200000
FILTERED_QUEUE_SIZE = 200000
LOG_INTERVAL = 20000
NLP_BATCH_SIZE = 1000

file_to_process = ""
output_parquet_dir = "/home/coinsafe/business-finder/processed_data/filtered_comments"

# --- Globals for Models and Keywords ---
_classifier = None
_candidate_labels = ["pain_point", "idea"]
_pain_point_keywords = ["frustrating", "problem", "difficult", "struggle", "annoying", "wish", "need", "can't", "should be", "hard to", "lack of", "missing", "broken"]
_idea_keywords = ["idea", "solution", "concept", "opportunity", "build", "create", "develop", "imagine", "what if", "improve", "new way", "innovate"]

def get_classifier():
    from dask.distributed import get_worker
    try:
        worker = get_worker()
        if not hasattr(worker, 'classifier'):
            # Dask-CUDA sets this environment variable for each worker
            cuda_device_index = os.environ.get("CUDA_VISIBLE_DEVICES", "0").split(",")[0]
            device = int(cuda_device_index)
            print(f"[GPU Worker {worker.name}] Initializing classifier on device: {device}")
            worker.classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli", device=device)
        return worker.classifier
    except (ValueError, ImportError):
        # This code runs on the main process (local fallback)
        print("[Local] Initializing classifier on device 0 (fallback)")
        global _classifier
        if '_classifier' not in globals() or _classifier is None:
            _classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli", device=0)
        return _classifier

# --- Pipeline Stage 1: Decompression ---
def producer(queue: mp.Queue, path: str, limit: Optional[int], num_consumers: int):
    print(f"[Producer] Starting data ingestion for {num_consumers} consumer(s)પૂર્ણ...")
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

# --- Pipeline Stage 3: GPU Classification ---
def nlp_classify_batch(batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    classifier = get_classifier()
    final_results = []
    texts_to_classify = [row.get("body", "") for row in batch]
    
    worker_name = "local"
    try:
        from dask.distributed import get_worker
        worker_name = get_worker().name
    except (ValueError, ImportError):
        pass

    try:
        classification_results_list = classifier(texts_to_classify, _candidate_labels)
    except Exception as e:
        print(f"[GPU Worker {worker_name}] Error during batch NLP classification: {e}")
        return []

    for i, row in enumerate(batch):
        classification_results = classification_results_list[i]
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
    
    if len(batch) > 0:
        print(f"[GPU Worker {worker_name}] Classified a batch of {len(batch):,} items, yielding {len(final_results):,} results.")
            
    return final_results

# --- Main Orchestrator ---
def process_single_file_with_dask(path: str, limit: Optional[int] = None):
    print(f"Starting 3-stage pipeline for file: {path}...")
    print(f"CPU Filter Workers: {N_CPU_WORKERS}, GPU Workers: 4, NLP Batch Size: {NLP_BATCH_SIZE}")

    raw_data_queue = mp.Queue(maxsize=RAW_QUEUE_SIZE)
    filtered_data_queue = mp.Queue(maxsize=FILTERED_QUEUE_SIZE)

    producer_proc = mp.Process(target=producer, args=(raw_data_queue, path, limit, N_CPU_WORKERS))
    
    cpu_workers = []
    for _ in range(N_CPU_WORKERS):
        p = mp.Process(target=cpu_filter_worker, args=(raw_data_queue, filtered_data_queue))
        cpu_workers.append(p)

    # Definitive cluster configuration
    cluster = LocalCUDACluster(n_workers=4, threads_per_worker=5, resources={"GPU": 1})
    client = Client(cluster)
    print(f"Dask dashboard link: {client.dashboard_link}\n")

    try:
        producer_proc.start()
        for p in cpu_workers:
            p.start()

        futures = []
        batch = []
        sentinels_received = 0
        
        print("[Orchestrator] Starting to listen for filtered data to submit to GPUs...")
        while sentinels_received < N_CPU_WORKERS:
            item = filtered_data_queue.get()
            if item is None:
                sentinels_received += 1
                print(f"[Orchestrator] Received sentinel {sentinels_received}/{N_CPU_WORKERS}.")
                continue
            
            batch.append(item)

            if len(batch) >= NLP_BATCH_SIZE:
                print(f"[Orchestrator] Batch of {len(batch)} items ready. Submitting as smaller chunks...")
                # Split the large batch into smaller chunks for better parallelism
                chunk_size = 100
                for i in range(0, len(batch), chunk_size):
                    chunk = batch[i:i + chunk_size]
                    if chunk:
                        future = client.submit(nlp_classify_batch, chunk, resources={'GPU': 1})
                        futures.append(future)
                
                batch = [] # Reset batch

        if batch:
            # Submit any remaining items as a final batch
            chunk_size = 100
            for i in range(0, len(batch), chunk_size):
                chunk = batch[i:i + chunk_size]
                if chunk:
                    future = client.submit(nlp_classify_batch, chunk, resources={'GPU': 1})
                    futures.append(future)

        print(f"\n[Orchestrator] All data submitted. Total futures: {len(futures):,}. Waiting for results...")
        
        all_results = []
        with ProgressBar(futures) as bar:
            for future in as_completed(futures):
                result_batch = future.result()
                if result_batch:
                    all_results.extend(result_batch)

        print(f"\n[Orchestrator] All {len(futures):,} futures completed. Total results: {len(all_results):,}")

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
        producer_proc.join()
        print("[Orchestrator] Producer process joined.")
        for p in cpu_workers:
            p.join()
        print("[Orchestrator] All CPU filter workers joined.")
        
        client.close()
        cluster.close()
        print("[Orchestrator] Dask cluster closed.\n")

def main():
    global file_to_process
    file_to_process = "/home/coinsafe/business-finder/reddit-dumps/reddit/comments/RC_2025-07.zst"

    if not os.path.exists(file_to_process):
        print(f"Error: File not found at {file_to_process}. Please ensure the data is downloaded.")
        print("You can download the data using the torrent file: /home/coinsafe/business-finder/reddit-dumps/reddit-b6a7ccf72368a7d39c018c423e01bc15aa551122.torrent")
        return

    process_single_file_with_dask(file_to_process, limit=None)
    
    print("Data ingestion, filtering, and classification phase complete.\n")

if __name__ == "__main__":
    mp.set_start_method("forkserver")
    main()