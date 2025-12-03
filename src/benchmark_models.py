#!/usr/bin/env python3
"""
Benchmark script for NLP classifier models.
Tests multiple models on 300 messages from Redis without consuming them.
Runs two phases: single classifier and dual classifiers.
Outputs sorted tables of performance metrics and comparisons.
"""

import os
import json
import redis
import logging
import time
import math
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import torch
from tabulate import tabulate
import multiprocessing
from queue import Empty

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "rediss://:zBORiqFgabxlB7VMDjXvNWC2VAP9JPDWqAzCaLXjUNk%3D@businessfinder.redis.cache.windows.net:6380/0")
REDIS_TODO_QUEUE = "nlp_todo_queue"
BENCHMARK_COUNT = 300
DEVICE = os.getenv("DEVICE", "mps")  # Can be "mps", "cpu", or "cuda"

# Models to benchmark
MODELS_TO_TEST = [
    "MoritzLaurer/xtremedistil-l6-h256-zeroshot-v1.1-all-33",
    "typeform/distilbert-base-uncased-mnli",
    "cross-encoder/nli-MiniLM2-L6-H768",
    "MoritzLaurer/xtremedistil-l6-h256-mnli-fever-anli-ling-binary",
]

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_device_id(device_type):
    """Convert device type to device ID for pipeline."""
    if device_type.lower() == "cpu":
        return -1
    elif device_type.lower() == "mps":
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        else:
            logging.warning("MPS requested but not available. Falling back to CPU.")
            return -1
    elif device_type.lower().startswith("cuda"):
        if torch.cuda.is_available():
            return 0
        else:
            logging.warning("CUDA requested but not available. Falling back to CPU.")
            return -1
    else:
        return -1

def load_classifier(model_name, device_type):
    """Load a classifier model with the specified configuration."""
    device_id = get_device_id(device_type)
    logging.info(f"Loading model: {model_name} on device: {device_id}")
    
    # For MPS or basic compatibility, skip ONNX
    use_onnx = False
    if device_id != "mps" and device_type.lower() != "cpu":
        try:
            import onnxruntime
            from optimum.onnxruntime import ORTModelForSequenceClassification
            
            available_providers = onnxruntime.get_available_providers()
            provider = "CPUExecutionProvider"
            provider_options = {}
            
            if isinstance(device_id, int) and device_id >= 0:
                if "CUDAExecutionProvider" in available_providers:
                    provider = "CUDAExecutionProvider"
                    provider_options = {"device_id": str(device_id)}
                    use_onnx = True
            
            if use_onnx:
                model = ORTModelForSequenceClassification.from_pretrained(
                    model_name,
                    export=True,
                    provider=provider,
                    provider_options=provider_options,
                )
                tokenizer = AutoTokenizer.from_pretrained(model_name, model_max_length=512)
                logging.info(f"Loaded with ONNX Runtime")
        except Exception as e:
            logging.info(f"Falling back to standard transformers: {e}")
            use_onnx = False
    
    if not use_onnx:
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name, model_max_length=512)
    
    classifier = pipeline(
        "zero-shot-classification",
        model=model,
        tokenizer=tokenizer,
        device=device_id
    )
    
    return classifier

def fetch_messages(r, count):
    """Fetch messages from Redis without acknowledging them."""
    logging.info(f"Fetching {count} messages from Redis (LRANGE)...")
    messages_raw = r.lrange(REDIS_TODO_QUEUE, 0, count - 1)
    
    if not messages_raw:
        logging.error("No messages found in Redis queue!")
        return []
    
    messages = []
    for msg_json in messages_raw:
        try:
            job = json.loads(msg_json)
            messages.append(job['text'])
        except Exception as e:
            logging.warning(f"Failed to parse message: {e}")
            continue
    
    logging.info(f"Fetched {len(messages)} valid messages")
    return messages

def benchmark_model(model_name, messages, device_type):
    """Benchmark a single model on the given messages."""
    logging.info(f"\n{'='*60}")
    logging.info(f"Benchmarking: {model_name}")
    logging.info(f"{'='*60}")
    
    try:
        # Load the model
        start_load = time.time()
        classifier = load_classifier(model_name, device_type)
        load_time = time.time() - start_load
        logging.info(f"Model loaded in {load_time:.2f}s")
        
        # Warm-up run
        logging.info("Warming up model...")
        _ = classifier([messages[0]], candidate_labels=["pain_point", "idea"], truncation=True, max_length=512)
        
        # Benchmark run
        logging.info(f"Processing {len(messages)} messages...")
        candidate_labels = ["pain_point", "idea"]
        start_time = time.time()
        
        for idx, text in enumerate(messages):
            try:
                results = classifier([text], candidate_labels=candidate_labels, truncation=True, max_length=512)
                
                # Validate result (same logic as consumer)
                if not results:
                    continue
                    
                result = results[0]
                score = float(result['scores'][0])
                if math.isnan(score):
                    score = 0.0
                    
            except Exception as e:
                logging.warning(f"Error processing message {idx}: {e}")
                continue
            
            # Progress indicator every 50 messages
            if (idx + 1) % 50 == 0:
                elapsed = time.time() - start_time
                rate = (idx + 1) / elapsed
                logging.info(f"  Processed {idx + 1}/{len(messages)} ({rate:.2f} msg/s)")
        
        total_time = time.time() - start_time
        messages_per_second = len(messages) / total_time
        
        logging.info(f"Completed in {total_time:.2f}s ({messages_per_second:.2f} msg/s)")
        
        # Clean up
        del classifier
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        return {
            'model': model_name,
            'time': total_time,
            'msg_per_sec': messages_per_second,
            'load_time': load_time,
            'success': True
        }
        
    except Exception as e:
        logging.error(f"Failed to benchmark {model_name}: {e}", exc_info=True)
        return {
            'model': model_name,
            'time': float('inf'),
            'msg_per_sec': 0.0,
            'load_time': 0.0,
            'success': False,
            'error': str(e)
        }

def worker_process(worker_id, model_name, device_type, message_queue, result_queue):
    """Worker process for dual-classifier benchmark."""
    try:
        # Load classifier in this process
        classifier = load_classifier(model_name, device_type)
        candidate_labels = ["pain_point", "idea"]
        
        # Warm-up
        if not message_queue.empty():
            try:
                first_msg = message_queue.get(timeout=1)
                _ = classifier([first_msg], candidate_labels=candidate_labels, truncation=True, max_length=512)
                message_queue.put(first_msg)  # Put it back
            except:
                pass
        
        processed = 0
        while True:
            try:
                text = message_queue.get(timeout=0.1)
                results = classifier([text], candidate_labels=candidate_labels, truncation=True, max_length=512)
                
                if results:
                    result = results[0]
                    score = float(result['scores'][0])
                    if math.isnan(score):
                        score = 0.0
                
                processed += 1
            except Empty:
                break
            except Exception as e:
                logging.warning(f"Worker {worker_id} error: {e}")
                continue
        
        result_queue.put({'worker_id': worker_id, 'processed': processed})
        
    except Exception as e:
        logging.error(f"Worker {worker_id} failed: {e}")
        result_queue.put({'worker_id': worker_id, 'processed': 0, 'error': str(e)})

def benchmark_model_dual(model_name, messages, device_type):
    """Benchmark a model with 2 parallel classifiers."""
    logging.info(f"\n{'='*60}")
    logging.info(f"Benchmarking (2x Classifiers): {model_name}")
    logging.info(f"{'='*60}")
    
    try:
        # Load time - we'll load in the workers, so measure that
        start_load = time.time()
        
        # Create queues
        message_queue = multiprocessing.Queue()
        result_queue = multiprocessing.Queue()
        
        # Fill message queue
        for msg in messages:
            message_queue.put(msg)
        
        # Start workers
        workers = []
        for i in range(2):
            p = multiprocessing.Process(
                target=worker_process,
                args=(i, model_name, device_type, message_queue, result_queue)
            )
            p.start()
            workers.append(p)
        
        load_time = time.time() - start_load
        logging.info(f"Workers started in {load_time:.2f}s")
        
        # Start timing
        start_time = time.time()
        
        # Wait for workers
        for p in workers:
            p.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        total_processed = 0
        for _ in range(2):
            try:
                res = result_queue.get(timeout=1)
                total_processed += res['processed']
            except:
                pass
        
        messages_per_second = total_processed / total_time if total_time > 0 else 0
        
        logging.info(f"Completed {total_processed} messages in {total_time:.2f}s ({messages_per_second:.2f} msg/s)")
        
        # Clean up
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        return {
            'model': model_name,
            'time': total_time,
            'msg_per_sec': messages_per_second,
            'load_time': load_time,
            'success': True,
            'processed': total_processed
        }
        
    except Exception as e:
        logging.error(f"Failed to benchmark {model_name} with dual classifiers: {e}", exc_info=True)
        return {
            'model': model_name,
            'time': float('inf'),
            'msg_per_sec': 0.0,
            'load_time': 0.0,
            'success': False,
            'error': str(e)
        }

def print_results_table(results, title, mode="single"):
    """Print formatted results table."""
    logging.info(f"\n{'='*80}")
    logging.info(title)
    logging.info(f"{'='*80}\n")
    
    # Sort by messages per second (descending)
    results_sorted = sorted(results, key=lambda x: x['msg_per_sec'], reverse=True)
    
    # Format table data
    table_data = []
    for r in results_sorted:
        if r['success']:
            model_short = r['model'].split('/')[-1] if '/' in r['model'] else r['model']
            row = [
                model_short,
                f"{r['time']:.2f}s",
                f"{r['msg_per_sec']:.2f}",
                f"{r['load_time']:.2f}s"
            ]
            if mode == "dual":
                row.append(f"{r.get('processed', 0)}")
            table_data.append(row)
        else:
            model_short = r['model'].split('/')[-1] if '/' in r['model'] else r['model']
            row = [model_short, "FAILED", "N/A", "N/A"]
            if mode == "dual":
                row.append("N/A")
            table_data.append(row)
    
    # Print table
    headers = ["Model", "Time", "Msg/s", "Load Time"]
    if mode == "dual":
        headers.append("Processed")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Print full model names for reference
    print("\nFull Model Names:")
    for idx, r in enumerate(results_sorted, 1):
        status = "✓" if r['success'] else "✗"
        print(f"{idx}. [{status}] {r['model']}")

def main():
    logging.info(f"Starting NLP Model Benchmark")
    logging.info(f"Device: {DEVICE}")
    logging.info(f"Messages to process per model: {BENCHMARK_COUNT}")
    logging.info(f"Models to test: {len(MODELS_TO_TEST)}")
    
    # Connect to Redis
    logging.info(f"Connecting to Redis...")
    r = redis.Redis.from_url(REDIS_URL)
    
    # Fetch messages
    messages = fetch_messages(r, BENCHMARK_COUNT)
    
    if not messages:
        logging.error("No messages to benchmark. Exiting.")
        return
    
    # === PHASE 1: Single Classifier Benchmarks ===
    logging.info(f"\n{'#'*80}")
    logging.info("PHASE 1: Single Classifier Benchmarks")
    logging.info(f"{'#'*80}")
    
    results_single = []
    for model_name in MODELS_TO_TEST:
        result = benchmark_model(model_name, messages, DEVICE)
        results_single.append(result)
        time.sleep(2)
    
    print_results_table(results_single, "PHASE 1 RESULTS: Single Classifier", mode="single")
    
    # === PHASE 2: Dual Classifier Benchmarks ===
    logging.info(f"\n{'#'*80}")
    logging.info("PHASE 2: Dual Classifier Benchmarks (2x Parallel Instances)")
    logging.info(f"{'#'*80}")
    
    results_dual = []
    for model_name in MODELS_TO_TEST:
        result = benchmark_model_dual(model_name, messages, DEVICE)
        results_dual.append(result)
        time.sleep(2)
    
    print_results_table(results_dual, "PHASE 2 RESULTS: Dual Classifiers", mode="dual")
    
    # === COMPARISON TABLE ===
    logging.info(f"\n{'#'*80}")
    logging.info("COMPARISON: Single vs Dual Classifier")
    logging.info(f"{'#'*80}\n")
    
    comparison_data = []
    for single, dual in zip(results_single, results_dual):
        if single['success'] and dual['success']:
            model_short = single['model'].split('/')[-1] if '/' in single['model'] else single['model']
            speedup = dual['msg_per_sec'] / single['msg_per_sec'] if single['msg_per_sec'] > 0 else 0
            comparison_data.append([
                model_short,
                f"{single['msg_per_sec']:.2f}",
                f"{dual['msg_per_sec']:.2f}",
                f"{speedup:.2f}x"
            ])
    
    # Sort by speedup
    comparison_data.sort(key=lambda x: float(x[3].replace('x', '')), reverse=True)
    
    print(tabulate(comparison_data, 
                   headers=["Model", "1x Msg/s", "2x Msg/s", "Speedup"], 
                   tablefmt="grid"))
    
    logging.info("\nBenchmark complete!")

if __name__ == "__main__":
    main()
