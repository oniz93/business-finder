import os
import json
import redis
import logging
import multiprocessing
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import torch
import time
import math

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "rediss://:zBORiqFgabxlB7VMDjXvNWC2VAP9JPDWqAzCaLXjUNk%3D@businessfinder.redis.cache.windows.net:6380/0")
REDIS_TODO_QUEUE = "nlp_todo_queue"
REDIS_RESULTS_QUEUE = "nlp_results_queue"
# NOTE: For large models on a local machine, it's crucial to limit the number of
# workers to avoid memory overload. Start with 1 and increase carefully if you have ample RAM.
NUM_CONSUMERS = int(os.getenv("NUM_CONSUMERS", "1"))
# Comma-separated list of devices to use (e.g., "mps,cpu"). Overrides NUM_CONSUMERS if set.
CONSUMER_DEVICES = os.getenv("CONSUMER_DEVICES", "mps")
REPORT_BATCH_SIZE = int(os.getenv("REPORT_BATCH_SIZE", "50"))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s')

def get_classifier(device_override=None):
    """
    Initializes a smaller, faster, and quantized zero-shot-classification pipeline
    using Optimum and ONNX Runtime.
    """
    device_id = -1 # Default to CPU
    
    if device_override:
        if device_override.lower() == "cpu":
            device_id = -1
            logging.info("Initializing classifier on CPU (forced).")
        elif device_override.lower() == "mps":
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device_id = "mps"
                logging.info("Initializing classifier on Apple MPS device (forced).")
            else:
                logging.warning("MPS requested but not available. Falling back to CPU.")
                device_id = -1
        elif device_override.lower() == "cuda":
             # If specific cuda device is needed, it should be handled, but for now just auto-select or default
             if torch.cuda.is_available():
                 device_id = 0 # Default to first GPU if forced "cuda" without index
                 logging.info("Initializing classifier on CUDA device 0 (forced).")
             else:
                 device_id = -1
    else:
        # Auto-detection logic
        if torch.cuda.is_available():
            # Handle NVIDIA CUDA devices
            try:
                num_gpus = torch.cuda.device_count()
                # _identity is a tuple, usually (1,) for the first child
                identity = multiprocessing.current_process()._identity
                process_idx = identity[0] - 1 if identity else 0
                device_id = process_idx % num_gpus
                logging.info(f"Initializing classifier on CUDA device: {device_id}")
            except Exception as e:
                logging.warning(f"Could not determine CUDA device for process: {e}. Falling back to device 0.")
                device_id = 0
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            # Handle Apple Metal Performance Shaders (MPS)
            device_id = "mps"
            logging.info(f"Initializing classifier on Apple MPS device.")
        else:
            # Fallback to CPU
            logging.info(f"Initializing classifier on CPU.")

    model_name = "tasksource/deberta-small-long-nli"
    
    # Check if we should use ONNX Runtime
    # We skip ONNX for MPS to prefer native PyTorch MPS backend which is often more reliable/visible
    use_onnx = True
    if device_id == "mps":
        use_onnx = False
        logging.info("Skipping ONNX Runtime for MPS to use native PyTorch MPS backend.")

    if use_onnx:
        try:
            import onnxruntime
            from optimum.onnxruntime import ORTModelForSequenceClassification

            provider = "CPUExecutionProvider"
            provider_options = {}
            
            available_providers = onnxruntime.get_available_providers()
            
            if isinstance(device_id, int) and device_id >= 0:
                # Handle CUDA
                if "CUDAExecutionProvider" in available_providers:
                    provider = "CUDAExecutionProvider"
                    provider_options = {"device_id": str(device_id)}
                    logging.info(f"Configuring ONNX Runtime with {provider} on device {device_id}.")
                else:
                    logging.warning(f"CUDA requested but 'CUDAExecutionProvider' not found in ONNX Runtime providers: {available_providers}. Falling back to standard PyTorch.")
                    use_onnx = False
            
            # Note: CoreMLExecutionProvider logic removed to favor native MPS

            if use_onnx:
                model = ORTModelForSequenceClassification.from_pretrained(
                    model_name,
                    export=True,
                    provider=provider,
                    provider_options=provider_options,
                )
                tokenizer = AutoTokenizer.from_pretrained(model_name, model_max_length=512)
                logging.info(f"Loaded and optimized model with ONNX Runtime: {model_name}")
        except ImportError:
            logging.warning("`optimum` or `onnxruntime` not found. Falling back to standard transformers.")
            use_onnx = False
        except Exception as e:
            logging.warning(f"Failed to initialize ONNX Runtime: {e}. Falling back to standard transformers.")
            use_onnx = False

    if not use_onnx:
        logging.info(f"Loading standard transformers model on device: {device_id}")
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name, model_max_length=512)

    return pipeline(
        "zero-shot-classification",
        model=model,
        tokenizer=tokenizer,
        device=device_id # Pass the correct device ('mps', 0, 1, or -1)
    )

def consumer_worker(worker_id, device_type=None):
    logging.info(f"Consumer worker {worker_id} starting... Device: {device_type if device_type else 'Auto'}")
    r = redis.Redis.from_url(REDIS_URL)
    classifier = get_classifier(device_override=device_type)
    candidate_labels = ["pain_point", "idea"]

    # Benchmark stats
    batch_count = 0
    batch_start_time = time.time()

    while True:
        try:
            # Backpressure: Check if results queue is too full
            # If the writer is slow, we don't want to keep pushing results and OOM Redis.
            if r.llen(REDIS_RESULTS_QUEUE) > 10000:
                logging.warning(f"Worker {worker_id}: Results queue is full (>10k). Pausing for 5s...")
                time.sleep(5)
                continue

            # Blocking pop from the todo queue
            # Use a longer timeout to avoid premature exits if orchestrator is slow
            _, job_json = r.blpop(REDIS_TODO_QUEUE, timeout=60) 
            if job_json is None:
                logging.info(f"Consumer worker {worker_id} timed out waiting for jobs. Exiting.")
                break # Exit if no jobs for a while
            
            job = json.loads(job_json)
            file_path = job['file_path']
            row_id = job['row_id']
            text = job['text']

            #logging.info(f"Worker {worker_id} processing job for file: {file_path}, row_id: {row_id}")

            # Run NLP classification
            # Always pass a list to the classifier to ensure it returns a list of results.
            results = classifier([text], candidate_labels=candidate_labels, truncation=True, max_length=512)

            # If the input text was empty or invalid, the classifier might return an empty list.
            if not results:
                logging.warning(f"NLP classifier returned no results for row_id: {row_id}. Text may have been empty or invalid.")
                continue

            result = results[0] # Now this is safe because we checked for an empty list

            score = float(result['scores'][0])
            # The JSON standard does not support NaN values. If the model outputs NaN,
            # we replace it with 0.0 to ensure the payload is valid JSON.
            if math.isnan(score):
                logging.warning(f"Classifier returned NaN score for row_id: {row_id}. Replacing with 0.0.")
                score = 0.0

            nlp_result = {
                "file_path": file_path,
                "row_id": row_id,
                "nlp_label": result['labels'][0],
                "nlp_score": score,
            }
            
            r.rpush(REDIS_RESULTS_QUEUE, json.dumps(nlp_result))
            logging.debug(f"Worker {worker_id} finished job for file: {file_path}, row_id: {row_id}. Pushed result.")

            # Benchmark reporting
            batch_count += 1
            if batch_count >= REPORT_BATCH_SIZE:
                elapsed = time.time() - batch_start_time
                logging.info(f"Worker {worker_id} ({device_type if device_type else 'Auto'}): Processed {batch_count} messages in {elapsed:.2f}s ({(batch_count / elapsed):.2f} msg/s)")
                batch_count = 0
                batch_start_time = time.time()

        except redis.exceptions.ConnectionError as e:
            logging.error(f"Consumer worker {worker_id} Redis connection error: {e}. Retrying in 5s.")
            time.sleep(5)
        except Exception as e:
            logging.error(f"Consumer worker {worker_id} encountered an error: {e}", exc_info=True)
            # Optionally push job back to queue or to an error queue
            # For now, just log and continue to avoid getting stuck

def main():
    processes = []
    
    if CONSUMER_DEVICES:
        devices = [d.strip() for d in CONSUMER_DEVICES.split(',')]
        logging.info(f"Starting {len(devices)} NLP consumer workers with specified devices: {devices}")
        for i, device in enumerate(devices):
            p = multiprocessing.Process(target=consumer_worker, args=(i, device))
            processes.append(p)
            p.start()
    else:
        logging.info(f"Starting {NUM_CONSUMERS} NLP consumer workers (Auto-detect devices).")
        for i in range(NUM_CONSUMERS):
            p = multiprocessing.Process(target=consumer_worker, args=(i, None))
            processes.append(p)
            p.start()

    for p in processes:
        p.join()
    logging.info("All NLP consumer workers finished.")

if __name__ == "__main__":
    main()