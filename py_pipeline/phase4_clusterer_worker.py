#!/usr/bin/env python3
"""
Phase 4 Clusterer Worker: Consumes subreddits from Redis and runs HDBSCAN clustering.

This worker consumes clustering jobs from Redis, processes them by running HDBSCAN
clustering on embeddings, and saves the results. Workers restart after a configurable
number of jobs (default 500) to deep clean memory.

Usage:
    python phase4_clusterer_worker.py [--jobs-before-restart 500]

Multiple workers can be spawned to process jobs in parallel. Each worker
will automatically restart after processing a set number of jobs to manage memory.
"""

import os
import sys
import json
import glob
import signal
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import multiprocessing as mp

import polars as pl
import numpy as np
import redis
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

# Add project root for config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

console = Console()

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Redis configuration (same as phase4_worker.py)
REDIS_URL = "redis://:kRoGWJXNK75zMIcJz4RDDhNhz1hfKq6OLAzCaCFPVIw%3D@businessfinder.canadacentral.redis.azure.net:10000/"
REDIS_CLUSTER_QUEUE = "phase4_cluster_queue"
REDIS_TIMEOUT_SECS = 10

EMBEDDINGS_INPUT_DIR = "/Volumes/2TBSSD/reddit/embeddings"
CLUSTERS_OUTPUT_DIR = "/Volumes/2TBSSD/reddit/clusters"

# Clustering parameters
MIN_CLUSTER_SIZE = 5
MIN_SAMPLES = 3
EMBEDDING_DIM = 384

# Job limit before restart (to clean memory)
DEFAULT_JOBS_BEFORE_RESTART = 500

# Graceful shutdown flag
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    console.print("[yellow]⚠️  Shutdown signal received, finishing current job...[/yellow]")
    shutdown_requested = True


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def get_embedding_columns() -> List[str]:
    """Get list of embedding column names."""
    return [f"emb_{i:03d}" for i in range(EMBEDDING_DIM)]


def extract_embeddings(df: pl.DataFrame) -> np.ndarray:
    """Extract embedding vectors from dataframe."""
    emb_cols = get_embedding_columns()
    
    # Check which columns exist
    existing_cols = [c for c in emb_cols if c in df.columns]
    if len(existing_cols) != EMBEDDING_DIM:
        raise ValueError(f"Expected {EMBEDDING_DIM} embedding columns, found {len(existing_cols)}")
    
    # Extract as numpy array
    embeddings = df.select(existing_cols).to_numpy()
    return embeddings


def reduce_dimensions(embeddings: np.ndarray, n_components: int = 15) -> np.ndarray:
    """Reduce dimensionality using UMAP for better density clustering."""
    if embeddings.shape[0] < n_components + 2:
        return embeddings

    try:
        import umap
        # UMAP is very effective for collapsing high-dim semantic vectors
        reducer = umap.UMAP(
            n_components=n_components,
            n_neighbors=15,
            min_dist=0.0,
            metric='cosine',
            random_state=42,
            n_jobs=1 
        )
        # Suppress UMAP chatter
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return reducer.fit_transform(embeddings)
    except ImportError:
        console.print("[dim]  UMAP not installed. Install 'umap-learn' for better clustering.[/dim]")
        return embeddings


def cluster_embeddings(embeddings: np.ndarray) -> np.ndarray:
    """Run HDBSCAN clustering on embeddings."""
    if embeddings.shape[0] == 0:
        return np.array([])
    
    try:
        import hdbscan
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=MIN_CLUSTER_SIZE,
            min_samples=MIN_SAMPLES,
            metric="euclidean",
            cluster_selection_method="leaf",  # 'leaf' produces more granular clusters than 'eom'
            prediction_data=False
        )
    except ImportError:
        console.print("[yellow]HDBSCAN not installed, falling back to sklearn DBSCAN[/yellow]")
        from sklearn.cluster import DBSCAN
        clusterer = DBSCAN(eps=0.5, min_samples=MIN_SAMPLES)
    
    return clusterer.fit_predict(embeddings)


def process_subreddit(subreddit_path: str) -> bool:
    """Process a single subreddit: load embeddings, cluster, save results.
    Returns True on success, False on failure.
    """
    subreddit_name = os.path.basename(subreddit_path)
    
    # Check if already completed (idempotency)
    try:
        rel_path = os.path.relpath(subreddit_path, EMBEDDINGS_INPUT_DIR)
    except ValueError:
        rel_path = os.path.basename(subreddit_path)
    
    output_dir = os.path.join(CLUSTERS_OUTPUT_DIR, rel_path)
    output_path = os.path.join(output_dir, "clustered.parquet")
    
    if os.path.exists(output_path):
        console.print(f"[dim]  Already completed, skipping: {subreddit_name}[/dim]")
        return True
    
    # Find all parquet files
    parquet_files = glob.glob(os.path.join(subreddit_path, "*.parquet"))
    
    if not parquet_files:
        console.print(f"[dim]  No parquet files found, skipping: {subreddit_name}[/dim]")
        return True  # Not an error, just nothing to process
    
    # Load and concatenate all files
    dfs = []
    for pf in parquet_files:
        try:
            df = pl.read_parquet(pf)
            dfs.append(df)
        except Exception as e:
            console.print(f"[yellow]Failed to read {pf}: {e}[/yellow]")
    
    if not dfs:
        return True  # Not an error, just nothing to process
    
    df = pl.concat(dfs)
    
    if df.height < MIN_CLUSTER_SIZE:
        console.print(f"[dim]  Not enough items ({df.height}) for clustering, skipping[/dim]")
        return True
    
    console.print(f"  Processing [bold cyan]{subreddit_name}[/bold cyan] ({df.height} items)...")
    
    # Extract embeddings
    try:
        embeddings = extract_embeddings(df)
    except Exception as e:
        console.print(f"[red]  Failed to extract embeddings: {e}[/red]")
        return False
    
    # Reduce dimensionality (critical for HDBSCAN performance)
    reduced_embeddings = reduce_dimensions(embeddings)

    # Cluster
    cluster_labels = cluster_embeddings(reduced_embeddings)
    
    # Add cluster labels to dataframe
    df = df.with_columns(pl.Series("cluster_id", cluster_labels))
    
    # Calculate stats
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    n_noise = np.sum(cluster_labels == -1)
    
    if n_clusters > 0:
        console.print(f"    Found [green]{n_clusters} clusters[/green], {n_noise} noise points")
    else:
        console.print(f"[dim]    No clusters found, all {n_noise} points are noise[/dim]")
        return True  # Not an error, just no clusters
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Atomic write: write to temp file first
    temp_path = output_path + ".tmp"
    df.write_parquet(temp_path, compression="zstd")
    
    # Rename to final path
    os.rename(temp_path, output_path)
    
    return True


def worker_process(worker_id: int, jobs_before_restart: int):
    """Worker process that consumes jobs from Redis."""
    global shutdown_requested
    
    console.print(f"[blue]Worker {worker_id}: Starting...[/blue]")
    
    # Connect to Redis
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        console.print(f"[green]Worker {worker_id}: Connected to Redis[/green]")
    except Exception as e:
        console.print(f"[red]Worker {worker_id}: Failed to connect to Redis: {e}[/red]")
        return 0
    
    jobs_processed = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn(f"[Worker {worker_id}] {{task.description}}"),
        TextColumn("Jobs: {task.completed}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Waiting for jobs...", total=None)
        
        while not shutdown_requested and jobs_processed < jobs_before_restart:
            try:
                # BLPOP with timeout
                result = r.blpop(REDIS_CLUSTER_QUEUE, timeout=REDIS_TIMEOUT_SECS)
                
                if result is None:
                    # Timeout, no jobs available
                    progress.update(task, description="Waiting for jobs...")
                    continue
                
                _, job_json = result
                
                try:
                    job = json.loads(job_json)
                    subreddit_path = job.get("subreddit_path")
                except Exception as e:
                    console.print(f"[yellow]Worker {worker_id}: Failed to parse job: {e}[/yellow]")
                    continue
                
                if not subreddit_path:
                    console.print(f"[yellow]Worker {worker_id}: Invalid job (no subreddit_path)[/yellow]")
                    continue
                
                # Update progress display
                subreddit_name = os.path.basename(subreddit_path)
                progress.update(task, description=f"Processing: {subreddit_name}")
                
                # Process the job
                try:
                    if process_subreddit(subreddit_path):
                        jobs_processed += 1
                        progress.update(task, completed=jobs_processed)
                except Exception as e:
                    console.print(f"[red]Worker {worker_id}: Error processing {subreddit_name}: {e}[/red]")
                
            except redis.ConnectionError as e:
                console.print(f"[red]Worker {worker_id}: Redis connection error: {e}[/red]")
                console.print("[yellow]Reconnecting in 5 seconds...[/yellow]")
                import time
                time.sleep(5)
                try:
                    r = redis.from_url(REDIS_URL, decode_responses=True)
                    r.ping()
                except Exception:
                    pass
                    
            except Exception as e:
                console.print(f"[red]Worker {worker_id}: Unexpected error: {e}[/red]")
                import traceback
                traceback.print_exc()
    
    reason = "shutdown requested" if shutdown_requested else f"reached {jobs_before_restart} jobs limit"
    console.print(f"[yellow]Worker {worker_id}: Stopping ({reason}). Processed {jobs_processed} jobs.[/yellow]")
    return jobs_processed


def run_worker_with_restart(worker_id: int, jobs_before_restart: int):
    """Run a worker that restarts itself after processing jobs_before_restart jobs."""
    global shutdown_requested
    
    total_jobs = 0
    restart_count = 0
    
    while not shutdown_requested:
        restart_count += 1
        console.print(f"\n[bold blue]Worker {worker_id}: Starting session #{restart_count}[/bold blue]")
        
        # Run worker in this process (subprocess restart handled by parent)
        jobs = worker_process(worker_id, jobs_before_restart)
        total_jobs += jobs
        
        if shutdown_requested:
            break
        
        if jobs < jobs_before_restart:
            # Queue is likely empty or almost empty, wait a bit before restarting
            console.print(f"[dim]Worker {worker_id}: Processed {jobs} jobs (less than limit). Queue might be empty.[/dim]")
            import time
            time.sleep(5)
        
        console.print(f"[yellow]Worker {worker_id}: Restarting for memory cleanup...[/yellow]")
    
    console.print(f"\n[bold green]Worker {worker_id}: Total jobs processed: {total_jobs}[/bold green]")


def spawn_workers(num_workers: int, jobs_before_restart: int):
    """Spawn multiple worker processes."""
    global shutdown_requested
    
    console.print(f"[blue]Spawning {num_workers} worker processes...[/blue]")
    
    processes = []
    
    def spawn_worker(worker_id):
        """Spawn a single worker that restarts after job limit."""
        while not shutdown_requested:
            # Fork a new process for memory cleanup
            p = mp.Process(target=worker_process, args=(worker_id, jobs_before_restart))
            p.start()
            p.join()
            
            if shutdown_requested:
                break
            
            if p.exitcode != 0:
                console.print(f"[yellow]Worker {worker_id}: Process exited with code {p.exitcode}[/yellow]")
            
            console.print(f"[dim]Worker {worker_id}: Restarting for memory cleanup...[/dim]")
    
    # Spawn worker manager threads
    for i in range(num_workers):
        p = mp.Process(target=spawn_worker, args=(i,))
        processes.append(p)
        p.start()
    
    # Wait for all processes (they will run until shutdown)
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        console.print("[yellow]Shutdown requested, waiting for workers...[/yellow]")
        shutdown_requested = True
        for p in processes:
            p.terminate()
            p.join(timeout=10)


def main():
    parser = argparse.ArgumentParser(description="Phase 4 Clusterer Worker")
    parser.add_argument(
        "--jobs-before-restart",
        type=int,
        default=DEFAULT_JOBS_BEFORE_RESTART,
        help=f"Number of jobs to process before restarting (default: {DEFAULT_JOBS_BEFORE_RESTART})"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes to spawn (default: number of CPU cores)"
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Run a single worker without auto-restart (for debugging)"
    )
    args = parser.parse_args()
    
    num_workers = args.workers if args.workers else mp.cpu_count()
    
    console.print("╔══════════════════════════════════════════════════════════╗")
    console.print("║   Phase 4 Clusterer Worker: HDBSCAN Clustering           ║")
    console.print("╚══════════════════════════════════════════════════════════╝")
    console.print(f"Workers: {num_workers}")
    console.print(f"Jobs before restart: {args.jobs_before_restart}")
    console.print(f"Input: {EMBEDDINGS_INPUT_DIR}")
    console.print(f"Output: {CLUSTERS_OUTPUT_DIR}")
    console.print(f"Queue: {REDIS_CLUSTER_QUEUE}")
    
    if args.single:
        # Single worker mode (for debugging)
        console.print("\n[yellow]Running in single worker mode (no restart)[/yellow]")
        run_worker_with_restart(0, args.jobs_before_restart)
    else:
        # Multi-worker mode with auto-restart
        spawn_workers(num_workers, args.jobs_before_restart)
    
    console.rule("[bold green]Worker Shutdown Complete[/bold green]")


if __name__ == "__main__":
    main()
