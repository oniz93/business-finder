#!/usr/bin/env python3
"""
Phase 4 Clusterer Ingestor: Scans subreddits and pushes clustering jobs to Redis.

This script scans the embeddings directory to find subreddits that need clustering,
checks which ones are already done, and pushes pending jobs to a Redis queue.

Usage:
    python phase4_clusterer_ingestor.py [--rescan] [--force]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Set

import redis
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

# Add project root for config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

console = Console()

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Redis configuration (same as phase4_worker.py)
REDIS_URL = "redis://:kRoGWJXNK75zMIcJz4RDDhNhz1hfKq6OLAzCaCFPVIw%3D@businessfinder.canadacentral.redis.azure.net:10000/"
REDIS_CLUSTER_QUEUE = "phase4_cluster_queue"

EMBEDDINGS_INPUT_DIR = "/Volumes/2TBSSD/reddit/embeddings"
CLUSTERS_OUTPUT_DIR = "/Volumes/2TBSSD/reddit/clusters"

CHECKPOINT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoint")
SUBREDDITS_LIST_FILE = "subreddits_list_clusterer.json"


def load_subreddits_list() -> List[str]:
    """Load cached list of subreddits."""
    path = os.path.join(CHECKPOINT_DIR, SUBREDDITS_LIST_FILE)
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Failed to load subreddits list: {e}[/yellow]")
    return []


def save_subreddits_list(subreddits: List[str]):
    """Save list of subreddits to cache."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    path = os.path.join(CHECKPOINT_DIR, SUBREDDITS_LIST_FILE)
    with open(path, 'w') as f:
        json.dump(subreddits, f, indent=2)


def scan_subreddits(base_path: str) -> List[str]:
    """
    Scan for subreddit directories in the input directory.
    Handles both:
    1. Partitioned structure: prefix/subreddit (e.g., 'ap/apple', '00/AskReddit')
    2. Flat structure: /subreddit (e.g., '/AskReddit')
    """
    base = Path(base_path)
    if not base.exists():
        console.print(f"[red]Input directory does not exist: {base}[/red]")
        return []
    
    console.print("[blue]Scanning for subreddit directories...[/blue]")
    subreddits = []
    
    try:
        items = list(base.iterdir())
    except OSError as e:
        console.print(f"[red]Error reading directory: {e}[/red]")
        return []
    
    for item in items:
        if not item.is_dir():
            continue
            
        # Check if it's a partition directory (short name, usually 2 chars)
        # AND it does NOT contain parquet files directly (which would mean it's a subreddit)
        is_partition = False
        if len(item.name) <= 2:
            # Check content to be sure
            try:
                # If it has specific subdirectories, treat as partition
                # If it has parquet files, treat as subreddit
                has_parquet = any(x.name.endswith('.parquet') for x in item.iterdir())
                if not has_parquet:
                    is_partition = True
            except OSError:
                pass
        
        if is_partition:
            # Scan inside the partition
            try:
                subs = [str(x) for x in item.iterdir() if x.is_dir()]
                if subs:
                    subreddits.extend(subs)
            except OSError:
                continue
        else:
            # Treat as a subreddit directly
            subreddits.append(str(item))

    # Remove duplicates if any
    subreddits = sorted(list(set(subreddits)))
    console.print(f"[green]✓ Found {len(subreddits)} subreddit directories[/green]")
    return subreddits


def get_completed_subreddits() -> Set[str]:
    """Get set of subreddit paths that already have clusters."""
    completed = set()
    clusters_base = Path(CLUSTERS_OUTPUT_DIR)
    
    if not clusters_base.exists():
        return completed
    
    # Scan clusters directory for completed subreddits
    for item in clusters_base.rglob("clustered.parquet"):
        # Get the parent directory (subreddit path relative to clusters output)
        rel_path = item.parent.relative_to(clusters_base)
        # Reconstruct the original input path
        original_path = Path(EMBEDDINGS_INPUT_DIR) / rel_path
        completed.add(str(original_path))
    
    return completed


def enqueue_subreddits(subreddits: List[str], force: bool = False):
    """Enqueue subreddits to Redis for clustering."""
    console.print(f"[blue]Connecting to Redis...[/blue]")
    
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        console.print("[green]✓ Connected to Redis[/green]")
    except Exception as e:
        console.print(f"[red]Failed to connect to Redis: {e}[/red]")
        return
    
    # Check current queue length
    queue_len = r.llen(REDIS_CLUSTER_QUEUE)
    console.print(f"Current queue length: {queue_len}")
    
    if queue_len > 0 and not force:
        console.print("[yellow]Queue is not empty. Use --force to add more jobs.[/yellow]")
        return
    
    # Get completed subreddits
    completed = get_completed_subreddits()
    console.print(f"Already completed: {len(completed)} subreddits")
    
    # Filter out completed subreddits
    pending = [s for s in subreddits if s not in completed]
    console.print(f"Pending to cluster: {len(pending)} subreddits")
    
    if not pending:
        console.print("[green]All subreddits already clustered![/green]")
        return
    
    # Enqueue jobs
    console.print(f"[blue]Enqueueing {len(pending)} clustering jobs...[/blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Enqueueing...", total=len(pending))
        
        # Batch enqueue
        batch_size = 100
        for i in range(0, len(pending), batch_size):
            batch = pending[i:i + batch_size]
            jobs = [json.dumps({"subreddit_path": s}) for s in batch]
            r.rpush(REDIS_CLUSTER_QUEUE, *jobs)
            progress.advance(task, len(batch))
    
    # Get final queue length
    final_queue_len = r.llen(REDIS_CLUSTER_QUEUE)
    console.print(f"[green]✓ Enqueued {len(pending)} jobs. Queue length: {final_queue_len}[/green]")


def main():
    parser = argparse.ArgumentParser(description="Phase 4 Clusterer Ingestor")
    parser.add_argument(
        "--rescan",
        action="store_true",
        help="Force rescan of subreddit directories (ignore cache)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Add jobs even if queue is not empty"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the queue and exit"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show queue status and exit"
    )
    args = parser.parse_args()
    
    console.rule("[bold blue]Phase 4: Clusterer Ingestor[/bold blue]")
    console.print(f"Input: {EMBEDDINGS_INPUT_DIR}")
    console.print(f"Output: {CLUSTERS_OUTPUT_DIR}")
    console.print(f"Queue: {REDIS_CLUSTER_QUEUE}")
    
    # Status mode
    if args.status:
        try:
            r = redis.from_url(REDIS_URL, decode_responses=True)
            queue_len = r.llen(REDIS_CLUSTER_QUEUE)
            completed = get_completed_subreddits()
            console.print(f"\n[bold]Queue Status:[/bold]")
            console.print(f"  Jobs in queue: {queue_len}")
            console.print(f"  Completed: {len(completed)}")
        except Exception as e:
            console.print(f"[red]Failed to get status: {e}[/red]")
        return
    
    # Clear mode
    if args.clear:
        try:
            r = redis.from_url(REDIS_URL, decode_responses=True)
            r.delete(REDIS_CLUSTER_QUEUE)
            console.print("[green]✓ Queue cleared[/green]")
        except Exception as e:
            console.print(f"[red]Failed to clear queue: {e}[/red]")
        return
    
    # Load or scan subreddits
    subreddits = [] if args.rescan else load_subreddits_list()
    
    if not subreddits:
        subreddits = scan_subreddits(EMBEDDINGS_INPUT_DIR)
        if subreddits:
            save_subreddits_list(subreddits)
    else:
        console.print(f"[dim]Loaded {len(subreddits)} subreddits from cache[/dim]")
    
    if not subreddits:
        console.print("[red]No subreddits found[/red]")
        return
    
    # Enqueue jobs
    enqueue_subreddits(subreddits, force=args.force)
    
    console.rule("[bold green]Ingestor Complete[/bold green]")


if __name__ == "__main__":
    main()
