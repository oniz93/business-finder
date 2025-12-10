#!/usr/bin/env python3
"""
Phase 4 Status Checker

Utility script to check the status of the Phase 4 distributed infrastructure:
- Redis queue length
- Progress through subreddits
- Embedding completion stats

Usage:
    python scripts/phase4_status.py
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

from rich.console import Console
from rich.table import Table

console = Console()

# Configuration
REDIS_URL = "redis://:kRoGWJXNK75zMIcJz4RDDhNhz1hfKq6OLAzCaCFPVIw%3D@businessfinder.canadacentral.redis.azure.net:10000/"
REDIS_PHASE4_QUEUE = "phase4_todo_queue"

CHAINS_DIR = "/Volumes/2TBSSD/reddit/chains"
EMBEDDINGS_DIR = "/Volumes/2TBSSD/reddit/embeddings"
CLUSTERS_DIR = "/Volumes/2TBSSD/reddit/clusters"

CHECKPOINT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rust", "checkpoint")


def check_redis():
    """Check Redis queue status."""
    console.print("\n[bold blue]📡 Redis Status[/bold blue]")
    
    if not HAS_REDIS:
        console.print("[red]Redis library not installed[/red]")
        return
    
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        console.print("[green]✓ Connected to Redis[/green]")
        
        queue_len = r.llen(REDIS_PHASE4_QUEUE)
        console.print(f"  Queue length: [bold]{queue_len}[/bold] jobs")
        
        if queue_len > 0:
            # Peek at first and last job
            first = r.lindex(REDIS_PHASE4_QUEUE, 0)
            last = r.lindex(REDIS_PHASE4_QUEUE, -1)
            
            if first:
                try:
                    job = json.loads(first)
                    console.print(f"  Next job: {os.path.basename(job.get('input_path', 'unknown'))}")
                except:
                    pass
                    
    except Exception as e:
        console.print(f"[red]✗ Failed to connect to Redis: {e}[/red]")


def check_directories():
    """Check directory existence and file counts."""
    console.print("\n[bold blue]📁 Directory Status[/bold blue]")
    
    dirs = [
        ("Chains (Input)", CHAINS_DIR),
        ("Embeddings (Output)", EMBEDDINGS_DIR),
        ("Clusters (Final)", CLUSTERS_DIR),
    ]
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Directory")
    table.add_column("Exists")
    table.add_column("Subreddits")
    table.add_column("Parquet Files")
    
    for name, path in dirs:
        exists = os.path.exists(path)
        subreddit_count = 0
        parquet_count = 0
        
        if exists:
            # Count subreddits (2-level: suffix/subreddit)
            try:
                for suffix_dir in Path(path).iterdir():
                    if suffix_dir.is_dir():
                        for sub_dir in suffix_dir.iterdir():
                            if sub_dir.is_dir():
                                subreddit_count += 1
                                parquet_count += len(list(sub_dir.glob("*.parquet")))
            except:
                pass
        
        table.add_row(
            name,
            "[green]✓[/green]" if exists else "[red]✗[/red]",
            str(subreddit_count) if exists else "-",
            str(parquet_count) if exists else "-",
        )
    
    console.print(table)


def check_progress():
    """Check checkpoint files for progress."""
    console.print("\n[bold blue]📊 Progress Checkpoints[/bold blue]")
    
    checkpoints = [
        ("Manager", "phase4_manager_progress.json"),
        ("Manager Subreddits", "subreddits_list_phase4.json"),
        ("Clusterer", "phase4_clusterer_progress.json"),
    ]
    
    for name, filename in checkpoints:
        path = os.path.join(CHECKPOINT_DIR, filename)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                
                if "subreddit_index" in data:
                    console.print(f"  {name}: index [bold]{data['subreddit_index']}[/bold]")
                elif isinstance(data, list):
                    console.print(f"  {name}: [bold]{len(data)}[/bold] items cached")
                else:
                    console.print(f"  {name}: {path}")
            except Exception as e:
                console.print(f"  {name}: [yellow]Error reading: {e}[/yellow]")
        else:
            console.print(f"  {name}: [dim]not found[/dim]")


def calculate_completion():
    """Calculate completion percentage."""
    console.print("\n[bold blue]📈 Completion Stats[/bold blue]")
    
    if not os.path.exists(CHAINS_DIR):
        console.print(f"[red]Chains directory not found: {CHAINS_DIR}[/red]")
        return
    
    chains_files = set()
    embeddings_files = set()
    
    # Count chains files
    try:
        for root, dirs, files in os.walk(CHAINS_DIR):
            for f in files:
                if f.endswith('.parquet'):
                    rel_path = os.path.relpath(os.path.join(root, f), CHAINS_DIR)
                    chains_files.add(rel_path)
    except Exception as e:
        console.print(f"[red]Error scanning chains: {e}[/red]")
        return
    
    # Count embeddings files
    if os.path.exists(EMBEDDINGS_DIR):
        try:
            for root, dirs, files in os.walk(EMBEDDINGS_DIR):
                for f in files:
                    if f.endswith('.parquet') and not f.endswith('.tmp'):
                        rel_path = os.path.relpath(os.path.join(root, f), EMBEDDINGS_DIR)
                        embeddings_files.add(rel_path)
        except Exception as e:
            console.print(f"[yellow]Warning scanning embeddings: {e}[/yellow]")
    
    total = len(chains_files)
    completed = len(embeddings_files.intersection(chains_files))
    percentage = (completed / total * 100) if total > 0 else 0
    
    console.print(f"  Total chain files: [bold]{total}[/bold]")
    console.print(f"  Embeddings completed: [bold]{completed}[/bold]")
    console.print(f"  Completion: [bold green]{percentage:.1f}%[/bold green]")
    
    remaining = total - completed
    if remaining > 0:
        console.print(f"  Remaining: [bold yellow]{remaining}[/bold yellow] files")


def main():
    console.print("╔══════════════════════════════════════════════════════════╗")
    console.print("║   Phase 4 Infrastructure Status                          ║")
    console.print("╚══════════════════════════════════════════════════════════╝")
    
    check_redis()
    check_directories()
    check_progress()
    calculate_completion()
    
    console.print()


if __name__ == "__main__":
    main()
