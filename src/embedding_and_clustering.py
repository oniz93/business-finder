import os
import pandas as pd
import numpy as np
import glob
import asyncio
from tqdm import tqdm
from dotenv import load_dotenv
import torch
import multiprocessing
from multiprocessing import Manager
import numba.cuda as cuda
import shutil
import time
import curses
import io
from collections import deque

# --- Configuration ---
load_dotenv()

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
SUMMARIZATION_MODEL_NAME = "models/gemini-2.5-flash-lite"
PROCESSED_DATA_DIR = "/home/coinsafe/business-finder/processed_data"
EMBEDDINGS_DIR = "/home/coinsafe/business-finder/data/embeddings"
OUTPUT_DIR = "/home/coinsafe/business-finder/data/summaries"
MIN_SUBREDDIT_ITEMS = 30
LOG_WINDOW_SIZE = 15 # Number of log lines to show

# For embeddings
from sentence_transformers import SentenceTransformer

# For clustering on GPU
import cuml

# For summarization with Gemini
import google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Worker Functions (unchanged logic, but receive log_queue) ---

def process_embedding_chunk(args):
    subreddits_chunk, gpu_id, completed_counter, log_queue = args
    try:
        cuda.select_device(gpu_id)
        device = f"cuda:{gpu_id}"
        log_queue.put(f"[GPU-{gpu_id}] Loading embedding model...")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
        log_queue.put(f"[GPU-{gpu_id}] Embedding model loaded.")

        for subreddit_name in subreddits_chunk:
            log_queue.put(f"[GPU-{gpu_id}] Processing subreddit: {subreddit_name}")
            # ... (rest of the function logic is the same, using log_queue.put instead of print)
            subreddit_dir = os.path.join(PROCESSED_DATA_DIR, subreddit_name)
            parquet_files = glob.glob(f"{subreddit_dir}/**/*.parquet", recursive=True)
            if not parquet_files:
                completed_counter.value += 1
                continue
            df = pd.concat([pd.read_parquet(f) for f in parquet_files], ignore_index=True)
            if len(df) < MIN_SUBREDDIT_ITEMS:
                completed_counter.value += 1
                continue
            df.dropna(subset=['full_thread_body'], inplace=True)
            df['full_thread_body'] = df['full_thread_body'].astype(str)
            if df.empty:
                completed_counter.value += 1
                continue
            embeddings = embedding_model.encode(df['full_thread_body'].tolist(), show_progress_bar=False, batch_size=256)
            output_subdir = os.path.join(EMBEDDINGS_DIR, subreddit_name)
            os.makedirs(output_subdir, exist_ok=True)
            df.to_parquet(os.path.join(output_subdir, "data.parquet"))
            np.save(os.path.join(output_subdir, "embeddings.npy"), embeddings)
            log_queue.put(f"[GPU-{gpu_id}] Finished embeddings for {subreddit_name}.")
            completed_counter.value += 1
    except Exception as e:
        log_queue.put(f"[GPU-{gpu_id}] ERROR in embedding chunk: {e}")

async def summarize_cluster_texts(cluster_id, texts, model, log_queue):
    """Generates a summary for a given cluster of texts using Gemini."""
    # Truncate texts to stay within token limits
    texts = [t[:500] for t in texts]
    
    prompt = f"""
    The following are posts and comments from a subreddit cluster about a similar topic.
    Please synthesize them into a single, concise business idea, problem, or opportunity.
    Focus on the core theme. Ignore boilerplate/unrelated text.
    The summary should be a single, actionable sentence.

    ---
    {texts}
    ---

    Synthesized Summary:
    """
    try:
        response = await model.generate_content_async(prompt)
        return {
            'cluster_id': cluster_id,
            'summary': response.text.strip(),
            'representative_text': texts[0] # Keep the first text as representative
        }
    except Exception as e:
        log_queue.put(f"[Summarizer] Error generating summary for cluster {cluster_id}: {e}")
        return None

async def cluster_and_summarize_chunk_async(args):
    subreddits_chunk, gpu_id, log_queue = args
    try:
        cuda.select_device(gpu_id)
        device = f"cuda:{gpu_id}"
        log_queue.put(f"[GPU-{gpu_id}] Initializing for clustering...")

        model = genai.GenerativeModel(SUMMARIZATION_MODEL_NAME)

        for subreddit_name in subreddits_chunk:
            embedding_path = os.path.join(EMBEDDINGS_DIR, subreddit_name, "embeddings.npy")
            data_path = os.path.join(EMBEDDINGS_DIR, subreddit_name, "data.parquet")

            if not os.path.exists(embedding_path) or not os.path.exists(data_path):
                continue

            log_queue.put(f"[GPU-{gpu_id}] Clustering {subreddit_name}...")
            embeddings = np.load(embedding_path)
            if embeddings.shape[0] < 2:
                continue

            clusterer = cuml.HDBSCAN(min_cluster_size=5, gen_min_span_tree=True)
            labels = clusterer.fit_predict(embeddings)

            df = pd.read_parquet(data_path)
            df['cluster'] = labels

            clustered_df = df[df['cluster'] != -1]

            if clustered_df.empty:
                continue

            tasks = []
            cluster_data_map = {}
            for cluster_id in clustered_df['cluster'].unique():
                cluster_sub_df = clustered_df[clustered_df['cluster'] == cluster_id]
                
                texts = cluster_sub_df['full_thread_body'].tolist()
                ids_in_cluster = cluster_sub_df['start_id'].tolist()
                total_ups = cluster_sub_df['total_ups'].sum()
                total_downs = cluster_sub_df['total_downs'].sum()

                cluster_data_map[cluster_id] = {
                    "subreddit": subreddit_name,
                    "ids_in_cluster": ids_in_cluster,
                    "texts": texts,
                    "total_ups": total_ups,
                    "total_downs": total_downs
                }
                tasks.append(summarize_cluster_texts(cluster_id, texts, model, log_queue))

            if not tasks:
                continue

            summaries = await asyncio.gather(*tasks)

            final_clusters = []
            for summary_result in summaries:
                if summary_result is not None:
                    cluster_id = summary_result['cluster_id']
                    data = cluster_data_map[cluster_id]
                    data['summary'] = summary_result['summary']
                    # Add cluster_id for reference, as it was in the previous version from business_plan_generation.py
                    data['cluster_id'] = cluster_id 
                    final_clusters.append(data)

            if not final_clusters:
                log_queue.put(f"[GPU-{gpu_id}] No successful summaries for {subreddit_name}.")
                continue

            final_df = pd.DataFrame(final_clusters)

            output_path = os.path.join(OUTPUT_DIR, f"{subreddit_name}_clusters.parquet")
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            final_df.to_parquet(output_path)
            log_queue.put(f"[GPU-{gpu_id}] Saved summaries for {subreddit_name} to {output_path}")

    except Exception as e:
        log_queue.put(f"[GPU-{gpu_id}] ERROR in clustering/summarizing chunk: {e}")

def cluster_and_summarize_wrapper(args):
    asyncio.run(cluster_and_summarize_chunk_async(args))

# --- Curses Main UI Function ---

def main_ui(stdscr):
    # --- Curses Setup ---
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)
    log_window = deque(maxlen=LOG_WINDOW_SIZE)

    def redraw_ui(pbar_str=""):
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        # Draw logs
        for i, line in enumerate(log_window):
            if i < height - 2:
                stdscr.addstr(i, 0, str(line)[:width-1])
        # Draw progress bar at the bottom
        stdscr.addstr(height - 2, 0, "-" * (width - 1))
        stdscr.addstr(height - 1, 0, pbar_str[:width-1])
        stdscr.refresh()

    # --- Multiprocessing Setup ---
    manager = Manager()
    log_queue = manager.Queue()
    
    try:
        num_gpus = torch.cuda.device_count()
        if num_gpus == 0: raise SystemExit()
        num_processes = num_gpus * 5
        log_queue.put(f"Detected {num_gpus} GPUs. Creating {num_processes} worker processes.")
    except Exception as e:
        log_queue.put(f"Error detecting GPUs: {e}")
        return

    subreddits = [d for d in os.listdir(PROCESSED_DATA_DIR) if os.path.isdir(os.path.join(PROCESSED_DATA_DIR, d))]
    if not subreddits:
        log_queue.put(f"No subreddits found in {PROCESSED_DATA_DIR}.")
        return
    log_queue.put(f"Found {len(subreddits)} subreddits to process.")

    # --- Stage 1: Embedding Generation ---
    log_queue.put("--- Starting Stage 1: Embedding Generation ---")
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    completed_subreddits = manager.Value('i', 0)
    subreddit_chunks = np.array_split(subreddits, num_processes)
    tasks = [(chunk.tolist(), i % num_gpus, completed_subreddits, log_queue) for i, chunk in enumerate(subreddit_chunks)]

    pool = multiprocessing.Pool(processes=num_processes)
    result = pool.map_async(process_embedding_chunk, tasks)

    total_subreddit_count = len(subreddits)
    tqdm_out = io.StringIO()
    with tqdm(total=total_subreddit_count, desc="Embedding Subreddits", file=tqdm_out, ncols=80) as pbar:
        while not result.ready():
            pbar.n = completed_subreddits.value
            pbar.refresh()
            tqdm_out.seek(0)
            progress_string = tqdm_out.read().strip().replace("\n", "")
            tqdm_out.truncate(0)
            tqdm_out.seek(0)

            while not log_queue.empty():
                log_window.append(log_queue.get())
            
            redraw_ui(progress_string)
            time.sleep(0.2)

    pool.close()
    pool.join()
    log_queue.put("--- Finished Stage 1 ---")
    redraw_ui("Stage 1 Complete!")
    time.sleep(2)

    # --- Stage 2: Clustering and Summarization (Simplified for now) ---
    log_queue.put("--- Starting Stage 2: Clustering and Summarization ---")
    tasks_stage2 = [(chunk.tolist(), i % num_gpus, log_queue) for i, chunk in enumerate(subreddit_chunks)]
    with multiprocessing.Pool(processes=num_processes) as pool:
        list(tqdm(pool.imap_unordered(cluster_and_summarize_wrapper, tasks_stage2), total=len(tasks_stage2), desc="Clustering & Summarizing"))
    log_queue.put("--- Finished Stage 2 ---")

    # --- Exit ---
    log_queue.put("All processing complete. Press any key to exit.")
    redraw_ui()
    stdscr.nodelay(False)
    stdscr.getch()

if __name__ == "__main__":
    if os.path.exists(EMBEDDINGS_DIR):
        print(f"Cleaning up temporary directory: {EMBEDDINGS_DIR}")
        shutil.rmtree(EMBEDDINGS_DIR)

    if not os.getenv("GOOGLE_API_KEY"):
        raise SystemExit("Error: GOOGLE_API_KEY not found in .env file.")

    multiprocessing.set_start_method("spawn", force=True)
    curses.wrapper(main_ui)
