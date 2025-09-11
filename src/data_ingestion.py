import sys
version = sys.version_info
if version.major < 3 or (version.major == 3 and version.minor < 10):
    raise RuntimeError("This script requires Python 3.10 or higher")
import os
import time
import gc
from typing import List, Dict, Any, Optional
import pandas as pd
from src.fileStreams import getFileJsonStream
from transformers import pipeline
import multiprocessing as mp
import numba.cuda as cuda

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# --- Configuration ---
N_CPU_FILTER_WORKERS = 16
N_GPU_WORKERS = 16
N_GPUS = 8

RAW_QUEUE_SIZE = 200000
GPU_QUEUE_SIZE = 10000

LOG_INTERVAL = 20000
NLP_BATCH_SIZE = 3000
GPU_SAVE_THRESHOLD = 50000

file_to_process = ""
output_parquet_dir = "/home/coinsafe/business-finder/processed_data/filtered_comments"

# --- Globals for Models and Keywords ---
_candidate_labels = ["pain_point", "idea"]
_pain_point_keywords = ["frustrating", "problem", "difficult", "struggle", "annoying", "wish", "need", "can't", "should be", "hard to", "lack of", "missing", "broken"]
_idea_keywords = ["idea", "solution", "concept", "opportunity", "build", "create", "develop", "imagine", "what if", "improve", "new way", "innovate"]

# --- GPU Worker Functions ---
_worker_classifier = None

def get_classifier(gpu_id: int):
    """Initializes a classifier pipeline on a specific GPU for a worker process."""
    global _worker_classifier
    physical_gpu_id = gpu_id % N_GPUS
    if _worker_classifier is None:
        print(f"[GPU-Worker-{gpu_id}] Initializing classifier on physical GPU: {physical_gpu_id}")
        cuda.select_device(physical_gpu_id)
        _worker_classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli", device=physical_gpu_id)
    return _worker_classifier

def nlp_classify_batch(batch: List[Dict[str, Any]], gpu_id: int) -> List[Dict[str, Any]]:
    """Performs NLP classification on a batch of texts."""
    classifier = get_classifier(gpu_id)
    final_results = []
    texts_to_classify = [row.get("body", "") for row in batch]

    def text_generator(texts):
        for text in texts:
            yield text

    dataset = text_generator(texts_to_classify)
    
    try:
        classification_results_generator = classifier(dataset, candidate_labels=_candidate_labels)
        for i, classification_results in enumerate(classification_results_generator):
            row = batch[i]
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
            
    return final_results

def gpu_worker(gpu_id: int, gpu_queue: mp.Queue):
    """Main loop for a single GPU worker process."""
    print(f"[GPU-Worker-{gpu_id}] Starting.")
    processed_count = 0
    part_number = 0
    results_buffer = []
    batch = []

    while True:
        item = gpu_queue.get()

        if item is None: # Sentinel value
            if batch:
                classified_results = nlp_classify_batch(batch, gpu_id)
                if classified_results:
                    results_buffer.extend(classified_results)
                processed_count += len(batch)
                print(f"[GPU-Worker-{gpu_id}] Processed final batch of {len(batch)}. Total processed: {processed_count}.")
            break

        batch.append(item)

        if len(batch) >= NLP_BATCH_SIZE:
            classified_results = nlp_classify_batch(batch, gpu_id)
            if classified_results:
                results_buffer.extend(classified_results)
            
            processed_count += len(batch)
            print(f"[GPU-Worker-{gpu_id}] Processed batch of {len(batch)}. Total processed: {processed_count}. Buffer size: {len(results_buffer)}")
            batch.clear()

            if len(results_buffer) >= GPU_SAVE_THRESHOLD:
                part_number += 1
                print(f"[GPU-Worker-{gpu_id}] Reached threshold. Saving {len(results_buffer)} results to parquet file part {part_number}...")
                df = pd.DataFrame(results_buffer)
                os.makedirs(output_parquet_dir, exist_ok=True)
                output_file = os.path.join(output_parquet_dir, f"filtered_data_gpu_{gpu_id}_part_{part_number}.parquet")
                df.to_parquet(output_file, engine='pyarrow')
                print(f"[GPU-Worker-{gpu_id}] Saved file. Clearing buffer and running GC.")
                results_buffer.clear()
                gc.collect()

    if results_buffer:
        part_number += 1
        print(f"[GPU-Worker-{gpu_id}] Saving remaining {len(results_buffer)} results to parquet file part {part_number}...")
        df = pd.DataFrame(results_buffer)
        os.makedirs(output_parquet_dir, exist_ok=True)
        output_file = os.path.join(output_parquet_dir, f"filtered_data_gpu_{gpu_id}_part_{part_number}.parquet")
        df.to_parquet(output_file, engine='pyarrow')

    print(f"[GPU-Worker-{gpu_id}] Finished.")

# --- Pipeline Stage 1: Decompression ---
def producer(raw_queue: mp.Queue, path: str, limit: Optional[int]):
    print(f"[Producer] Starting data ingestion...")
    count = 0
    start_time = time.time()
    back_pressure_threshold = int(RAW_QUEUE_SIZE * 0.8)

    try:
        with open(path, "rb") as f:
            json_stream_generator = getFileJsonStream(path, f, max_items=limit)
            if json_stream_generator:
                for item in json_stream_generator:
                    while raw_queue.qsize() >= back_pressure_threshold:
                        print(f"[Producer] Raw data queue is full ({raw_queue.qsize()}). Pausing...")
                        time.sleep(2)

                    raw_queue.put(item)
                    count += 1
                    if count % LOG_INTERVAL == 0:
                        elapsed = time.time() - start_time
                        rate = count / elapsed if elapsed > 0 else 0
                        print(f"[Producer] Ingested {count:,} items ({rate:,.0f} items/sec)")
    finally:
        print(f"[Producer] Finished ingesting {count:,} total items. Signaling end to CPU workers.")
        for _ in range(N_CPU_FILTER_WORKERS):
            raw_queue.put(None)

# --- Pipeline Stage 2: CPU Filtering (with Back-Pressure) ---
def cpu_filter_worker(worker_id: int, raw_queue: mp.Queue, gpu_queue: mp.Queue):
    print(f"[CPU-Filter-{worker_id}] Starting.")
    while True:
        if gpu_queue.qsize() >= GPU_QUEUE_SIZE:
            time.sleep(1)
            continue

        item = raw_queue.get()
        if item is None:
            break
        
        body = item.get("body", "")
        if body and len(body) > 50:
            if any(keyword in body.lower() for keyword in _pain_point_keywords) or \
               any(keyword in body.lower() for keyword in _idea_keywords):
                gpu_queue.put(item)

    print(f"[CPU-Filter-{worker_id}] Finished. Signaling end to GPU worker.")
    gpu_queue.put(None)

# --- Main Orchestrator ---
def process_single_file(path: str, limit: Optional[int] = None):
    print(f"Starting pipeline with new architecture for file: {path}...")
    print(f"CPU Filter Workers: {N_CPU_FILTER_WORKERS}, GPU Workers: {N_GPU_WORKERS} ({N_GPU_WORKERS // N_GPUS} per GPU)")

    raw_data_queue = mp.Queue(maxsize=RAW_QUEUE_SIZE)
    gpu_queues = [mp.Queue(maxsize=GPU_QUEUE_SIZE) for _ in range(N_GPU_WORKERS)]

    producer_proc = mp.Process(target=producer, args=(raw_data_queue, path, limit))
    producer_proc.start()

    cpu_procs = []
    for i in range(N_CPU_FILTER_WORKERS):
        p = mp.Process(target=cpu_filter_worker, args=(i, raw_data_queue, gpu_queues[i]))
        cpu_procs.append(p)
        p.start()

    gpu_procs = []
    for i in range(N_GPU_WORKERS):
        p = mp.Process(target=gpu_worker, args=(i, gpu_queues[i]))
        gpu_procs.append(p)
        p.start()

    print("[Orchestrator] All processes started. Waiting for completion...")
    producer_proc.join()
    print("[Orchestrator] Producer finished.")
    for p in cpu_procs:
        p.join()
    print("[Orchestrator] All CPU filters finished.")
    for p in gpu_procs:
        p.join()
    print("[Orchestrator] All GPU workers finished.")

def main():
    global file_to_process
    file_to_process = "/home/coinsafe/business-finder/reddit-dumps/reddit/comments/RC_2025-07.zst"

    if not os.path.exists(file_to_process):
        print(f"Error: File not found at {file_to_process}. Please ensure the data is downloaded.")
        return

    process_single_file(file_to_process, limit=None)
    
    print("Data ingestion and classification phase complete.")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()