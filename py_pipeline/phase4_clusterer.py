#!/usr/bin/env python3
"""
Phase 4 Clusterer: Aggregates embeddings and runs HDBSCAN clustering.

This script reads the embedding parquet files produced by the Phase 4 workers,
aggregates them per subreddit, runs HDBSCAN clustering, and saves the cluster
assignments back to parquet files.

Usage:
    python phase4_clusterer.py [--subreddit SUBREDDIT_NAME]
"""

import os
import sys
import json
import glob
import argparse
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

import polars as pl
import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

# Add project root for config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

console = Console()

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

EMBEDDINGS_INPUT_DIR = "/Volumes/2TBSSD/reddit/embeddings"
CLUSTERS_OUTPUT_DIR = "/Volumes/2TBSSD/reddit/clusters"

CHECKPOINT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoint")
PROGRESS_FILE = "phase4_clusterer_progress.json"
SUBREDDITS_LIST_FILE = "subreddits_list_clusterer.json"

# HDBSCAN parameters
MIN_CLUSTER_SIZE = 5
MIN_SAMPLES = 3

# Embedding dimension (must match model output)
EMBEDDING_DIM = 384


@dataclass
class ClusterProgress:
    subreddit_index: int = 0
    
    def to_dict(self):
        return {"subreddit_index": self.subreddit_index}
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ClusterProgress':
        return cls(subreddit_index=data.get("subreddit_index", 0))


def save_progress(progress: ClusterProgress):
    """Save progress to checkpoint file."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    path = os.path.join(CHECKPOINT_DIR, PROGRESS_FILE)
    with open(path, 'w') as f:
        json.dump(progress.to_dict(), f, indent=2)


def load_progress() -> ClusterProgress:
    """Load progress from checkpoint file."""
    path = os.path.join(CHECKPOINT_DIR, PROGRESS_FILE)
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return ClusterProgress.from_dict(json.load(f))
        except Exception as e:
            console.print(f"[yellow]Failed to load progress: {e}[/yellow]")
    return ClusterProgress()


def save_subreddits_list(subreddits: List[str]):
    """Save list of subreddits to cache."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    path = os.path.join(CHECKPOINT_DIR, SUBREDDITS_LIST_FILE)
    with open(path, 'w') as f:
        json.dump(subreddits, f, indent=2)


def load_subreddits_list() -> Optional[List[str]]:
    """Load cached list of subreddits."""
    path = os.path.join(CHECKPOINT_DIR, SUBREDDITS_LIST_FILE)
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Failed to load subreddits list: {e}[/yellow]")
    return None


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
                    # console.print(f"[dim]  Found partition {item.name} with {len(subs)} subreddits[/dim]")
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


def process_subreddit(subreddit_path: str):
    """Process a single subreddit: load embeddings, cluster, save results."""
    subreddit_name = os.path.basename(subreddit_path)
    
    # Find all parquet files
    parquet_files = glob.glob(os.path.join(subreddit_path, "*.parquet"))
    
    if not parquet_files:
        return
    
    # Load and concatenate all files
    dfs = []
    for pf in parquet_files:
        try:
            df = pl.read_parquet(pf)
            dfs.append(df)
        except Exception as e:
            console.print(f"[yellow]Failed to read {pf}: {e}[/yellow]")
    
    if not dfs:
        return
    
    df = pl.concat(dfs)
    
    if df.height < MIN_CLUSTER_SIZE:
        console.print(f"[dim]  Not enough items ({df.height}) for clustering, skipping[/dim]")
        return
    
    console.print(f"  Processing [bold cyan]{subreddit_name}[/bold cyan] ({df.height} items)...")
    
    # Extract embeddings
    try:
        embeddings = extract_embeddings(df)
    except Exception as e:
        console.print(f"[red]  Failed to extract embeddings: {e}[/red]")
        return
    
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
        return
    
    # Create output directory
    try:
        rel_path = os.path.relpath(subreddit_path, EMBEDDINGS_INPUT_DIR)
    except ValueError:
        rel_path = os.path.basename(subreddit_path)
    
    output_dir = os.path.join(CLUSTERS_OUTPUT_DIR, rel_path)
    os.makedirs(output_dir, exist_ok=True)
    
    # Save clustered data
    output_path = os.path.join(output_dir, "clustered.parquet")
    df.write_parquet(output_path, compression="zstd")


def main():
    parser = argparse.ArgumentParser(description="Phase 4 Clusterer")
    parser.add_argument(
        "--subreddit",
        type=str,
        help="Process a specific subreddit only"
    )
    args = parser.parse_args()
    
    console.rule("[bold blue]Phase 4: Clustering (HDBSCAN)[/bold blue]")
    console.print(f"Input: {EMBEDDINGS_INPUT_DIR}")
    console.print(f"Output: {CLUSTERS_OUTPUT_DIR}")
    
    if args.subreddit:
        # Single subreddit mode
        console.print(f"[blue]Single subreddit mode: {args.subreddit}[/blue]")
        
        # Find the subreddit path
        target_path = None
        for root, dirs, files in os.walk(EMBEDDINGS_INPUT_DIR):
            if args.subreddit in dirs:
                target_path = os.path.join(root, args.subreddit)
                break
        
        if target_path:
            process_subreddit(target_path)
        else:
            console.print(f"[red]Subreddit {args.subreddit} not found[/red]")
        return
    
    # Load or scan subreddits
    subreddits = load_subreddits_list()
    if not subreddits:
        subreddits = scan_subreddits(EMBEDDINGS_INPUT_DIR)
        if subreddits:
            save_subreddits_list(subreddits)
    
    if not subreddits:
        console.print("[red]No subreddits found[/red]")
        return
    
    # Load progress
    progress = load_progress()
    console.print(f"Total subreddits: {len(subreddits)}")
    console.print(f"Resuming from index: {progress.subreddit_index}")
    
    # Process loop
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console
    ) as prog:
        task = prog.add_task("Clustering...", total=len(subreddits), completed=progress.subreddit_index)
        
        for i in range(progress.subreddit_index, len(subreddits)):
            subreddit_path = subreddits[i]
            prog.update(task, description=f"Processing {os.path.basename(subreddit_path)}")
            
            try:
                process_subreddit(subreddit_path)
            except Exception as e:
                console.print(f"[red]Error processing {subreddit_path}: {e}[/red]")
            
            progress.subreddit_index = i + 1
            save_progress(progress)
            prog.advance(task)
    
    console.rule("[bold green]Phase 4 Clustering Complete[/bold green]")


if __name__ == "__main__":
    main()
