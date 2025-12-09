import os
import shutil
import torch
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import polars as pl
import duckdb
import config
from typing import List
from src.utils import sanitize_for_filesystem
import uuid
import multiprocessing
import tqdm
import functools
import sys
import logging
from logging.handlers import RotatingFileHandler
import queue
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn



def setup_worker_logging(log_file: str):
    """
    Configures a rotating logger for a worker process and redirects all output.
    """
    # 1. Configure Python's logging to go to a file.
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=1, mode='a', encoding='utf-8')
    formatter = logging.Formatter(f'[%(asctime)s] [Worker %(process)d] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # 2. Capture warnings issued by libraries (like transformers) into the logger.
    logging.captureWarnings(True)

    # 3. Perform low-level redirection of stdout and stderr for this process.
    # This will capture output from C++ extensions (like ONNX Runtime).
    log_file_handle = open(log_file, 'a', encoding='utf-8')
    os.dup2(log_file_handle.fileno(), sys.stdout.fileno())
    os.dup2(log_file_handle.fileno(), sys.stderr.fileno())


def get_classifier():
    """
    Initializes a smaller, faster, and quantized zero-shot-classification pipeline
    using Optimum and ONNX Runtime.
    """
    logging.info(f"Initializing classifier on device: {'mps' if torch.backends.mps.is_available() else 'cpu'}")

    model_name = "typeform/mobilebert-uncased-mnli"
    
    try:
        from optimum.onnxruntime import ORTModelForSequenceClassification
        from transformers import AutoTokenizer

        model = ORTModelForSequenceClassification.from_pretrained(model_name, export=True)
        tokenizer = AutoTokenizer.from_pretrained(model_name, model_max_length=512)
        logging.info(f"Loaded and optimized model with ONNX Runtime: {model_name}")
    except ImportError:
        logging.warning("`optimum` or `onnxruntime` not found. Falling back to standard transformers.")
        logging.warning("For better performance, run: pip install optimum[onnxruntime]")
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name, model_max_length=512)

    return pipeline(
        "zero-shot-classification",
        model=model,
        tokenizer=tokenizer,
    )

def find_subreddits_to_process() -> List[str]:
    """
    Discovers subreddits by scanning the directory structure of the processed data folder.
    """
    # This runs in the main process, so print is fine.
    print("[NLP] Discovering subreddits by scanning directories...")
    subreddits = []
    processed_dir = config.PROCESSED_DATA_DIR
    if not os.path.exists(processed_dir):
        print(f"[NLP] Processed data directory not found: {processed_dir}")
        return []

    for prefix_dir in os.scandir(processed_dir):
        if prefix_dir.is_dir():
            for subreddit_dir in os.scandir(prefix_dir.path):
                if subreddit_dir.is_dir() and not subreddit_dir.name.endswith('.tmp'):
                    subreddits.append(subreddit_dir.name)
    
    print(f"[NLP] Found {len(subreddits)} subreddits from directory names.")
    return subreddits


def process_subreddit_for_nlp(subreddit: str, classifier, chunk_size=100_000):
    """
    Loads data for a given subreddit in smaller chunks, runs NLP on flagged ideas,
    and overwrites the partition with updated data to avoid duplication.
    """
    logging.info(f"Processing subreddit: {subreddit}")

    sanitized_subreddit_name = sanitize_for_filesystem(subreddit)
    prefix = subreddit[:2]
    prefix_dir = sanitize_for_filesystem(prefix)

    subreddit_dir = os.path.join(config.PROCESSED_DATA_DIR, prefix_dir, sanitized_subreddit_name)

    if not os.path.isdir(subreddit_dir):
        logging.warning(f"Subreddit directory not found: {subreddit_dir}. Skipping.")
        return

    temp_subreddit_dir = f"{subreddit_dir}.tmp"
    if os.path.exists(temp_subreddit_dir):
        shutil.rmtree(temp_subreddit_dir)
    os.makedirs(temp_subreddit_dir)

    parquet_files_glob = os.path.join(subreddit_dir, '**', '*.parquet')

    try:
        count_query = f"SELECT COUNT(*) FROM '{parquet_files_glob}'"
        with duckdb.connect(database=':memory:') as con:
            total_rows = con.execute(count_query).fetchone()[0]

        logging.info(f"Subreddit {subreddit} contains {total_rows} messages.")

        if total_rows == 0:
            logging.info(f"No data found for subreddit: {subreddit}. Skipping.")
            shutil.rmtree(temp_subreddit_dir)
            return

        for offset in range(0, total_rows, chunk_size):
            query = f"""
                SELECT * FROM '{parquet_files_glob}'
                ORDER BY created_utc
                LIMIT {chunk_size} OFFSET {offset}
            """
            with duckdb.connect(database=':memory:') as con:
                df_chunk = con.execute(query).pl()

            if df_chunk.height == 0:
                continue

            df_chunk = df_chunk.with_row_index("unique_id")
            df_ideas = df_chunk.filter(pl.col("cpu_filter_is_idea") == True)

            if df_ideas.height > 0:
                texts_for_nlp = df_ideas["body"].to_list()
                candidate_labels = ["pain_point", "idea"]

                nlp_results = []
                batch_size = 32
                for i in range(0, len(texts_for_nlp), batch_size):
                    batch_texts = texts_for_nlp[i:i+batch_size]
                    try:
                        results = classifier(batch_texts, candidate_labels=candidate_labels, truncation=True, max_length=512)
                        nlp_results.extend(results)
                    except Exception as e:
                        logging.error(f"Error during NLP batch for {subreddit}: {e}")
                        nlp_results.extend([{'labels': ['none'], 'scores': [0.0]} for _ in batch_texts])

                if nlp_results:
                    df_ideas_with_nlp = df_ideas.with_columns([
                        pl.Series("nlp_label", [r['labels'][0] for r in nlp_results]),
                        pl.Series("nlp_score", [r['scores'][0] for r in nlp_results])
                    ])
                    df_nlp_results = df_ideas_with_nlp.select(["unique_id", "nlp_label", "nlp_score"])
                    df_chunk = df_chunk.join(df_nlp_results, on="unique_id", how="left")

                    df_chunk = df_chunk.with_columns([
                        pl.when(pl.col("nlp_label") == "idea").then(True).otherwise(pl.col("is_idea")).alias("is_idea"),
                        pl.when(pl.col("nlp_score").is_not_null()).then(pl.col("nlp_score")).otherwise(pl.col("nlp_top_score")).alias("nlp_top_score")
                    ]).drop(["nlp_label", "nlp_score"])

            df_chunk = df_chunk.drop("unique_id")

            df_chunk = df_chunk.with_columns([
                pl.from_epoch("created_utc", time_unit="s").dt.strftime("%m%y").alias("mmyy")
            ])

            grouped = df_chunk.group_by("mmyy")
            for mmyy_tuple, data in grouped:
                mmyy_str = mmyy_tuple[0]
                output_dir = os.path.join(temp_subreddit_dir, mmyy_str)
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, f"{uuid.uuid4()}.parquet")
                data.write_parquet(output_file)

        shutil.rmtree(subreddit_dir)
        os.rename(temp_subreddit_dir, subreddit_dir)

    except Exception as e:
        logging.error(f"An error occurred while processing {subreddit}: {e}. Cleaning up temp directory.")
        if 'temp_subreddit_dir' in locals() and os.path.exists(temp_subreddit_dir):
            shutil.rmtree(temp_subreddit_dir)
        raise

# --- Multiprocessing and UI Setup ---
def process_subreddit_chunk(subreddit_chunk: List[str], worker_id: int, progress_queue: multiprocessing.Queue):
    """
    Initializes a classifier once and processes a large chunk of subreddits,
    reporting progress back to the main process via a queue.
    """
    logging.info(f"Initializing classifier for a new chunk of {len(subreddit_chunk)} subreddits...")
    classifier = get_classifier()
    
    for subreddit in subreddit_chunk:
        try:
            process_subreddit_for_nlp(subreddit, classifier)
        except Exception as e:
            logging.error(f"FATAL ERROR processing subreddit {subreddit}: {e}")
        finally:
            # Report progress for this one subreddit
            progress_queue.put((worker_id, subreddit))
            
def worker_task_wrapper(args):
    """Helper to unpack arguments for the pool's map function and set up logging."""
    subreddit_chunk, worker_id, progress_queue, log_file = args
    
    # Setup logging to redirect all output for this worker to the specified file.
    setup_worker_logging(log_file)
    
    process_subreddit_chunk(subreddit_chunk, worker_id, progress_queue)

def chunked(iterable, n):
    """Yield successive n-sized chunks from iterable."""
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]
# ---

def main_nlp_phase():
    """
    Orchestrates the NLP enrichment phase with a rich multi-bar progress display.
    """
    print("--- Starting Phase 2: NLP Enrichment ---")
    
    subreddits = find_subreddits_to_process()

    if not subreddits:
        print("[NLP] No subreddits found to process. Phase 2 complete.")
        return

    num_processes = config.NLP_PROCESS_COUNT
    
    subreddit_chunks = list(chunked(subreddits, 100_000))
    
    if num_processes > 1:
        log_file = "phase2_nlp_workers.log"
        if os.path.exists(log_file):
            os.remove(log_file)
        
        print(f"\nWorker process logs will be written to: {log_file} (max 10MB, 1 backup)")
        print(f"In a separate terminal, run: tail -f {log_file}\n")

        # --- Rich Progress Bar Setup ---
        progress = Progress(
            TextColumn("{task.description}", justify="left"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
            "•",
            TimeElapsedColumn(),
            "•",
            SpinnerColumn(),
        )

        with progress:
            total_task = progress.add_task("[bold blue]Total Progress", total=len(subreddits))
            
            worker_tasks = [
                progress.add_task(f"  [green]Worker {i}", total=None, start=False) 
                for i in range(num_processes)
            ]

            with multiprocessing.Manager() as manager:
                progress_queue = manager.Queue()
                
                worker_args = []
                for i, chunk in enumerate(subreddit_chunks):
                    worker_id = i % num_processes
                    worker_args.append((chunk, worker_id, progress_queue, log_file))

                pool = multiprocessing.Pool(processes=num_processes)
                pool.map_async(worker_task_wrapper, worker_args)

                completed_subreddits = 0
                while completed_subreddits < len(subreddits):
                    try:
                        worker_id, subreddit_name = progress_queue.get(timeout=20)
                        
                        if not progress.tasks[worker_tasks[worker_id]].started:
                            progress.start_task(worker_tasks[worker_id])
                        
                        progress.update(worker_tasks[worker_id], description=f"  [green]Worker {worker_id}: Processing [cyan]{subreddit_name[:30]}[/cyan]")
                        progress.update(total_task, advance=1)
                        completed_subreddits += 1
                    except queue.Empty:
                        pass
                
                for task_id in worker_tasks:
                    progress.update(task_id, description="  [bold green]Done", visible=False)

                pool.close()
                pool.join()
    else:
        # Run sequentially for debugging
        print(f"[NLP] Starting NLP processing for {len(subreddits)} subreddits sequentially (in chunks).")
        for chunk in tqdm.tqdm(subreddit_chunks, desc="Processing Chunks (Sequential)"):
            process_subreddit_chunk(chunk, 0, None)

    print("--- Phase 2 Complete ---")

if __name__ == "__main__":
    main_nlp_phase()
