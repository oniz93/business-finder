#!/usr/bin/env python3
"""
Phase 4: AI-Powered Aggregation (Clustering Only)

This module performs:
1. Data Loading (Polars) - Reads Parquet files from Phase 3 chains output.
2. Embedding (SentenceTransformers) - Generates vectors using MPS (Mac GPU).
3. Clustering (HDBSCAN) - Clusters vectors to identify common business themes.
4. Storage (Polars) - Saves clustered opportunities to Parquet.

It operates at the subreddit level and uses checkpointing to resume progress,
similar to the Rust Phase 3 implementation.
"""

import os
import sys
import glob
import json
import argparse
from typing import List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import polars as pl
import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

# Import project config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
# Local import for simple sanitization if config doesn't have it or to ensure standalone capability
def sanitize_for_filesystem(name: str) -> str:
    return "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()

# Initialize console for logging
console = Console()

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Input/Output Directories
# Based on Rust Phase 3 output
CHAINS_INPUT_DIR = "/Volumes/2TBSSD/reddit/chains"
CLUSTERS_OUTPUT_DIR = "/Volumes/2TBSSD/reddit/clusters"

# Checkpointing
CHECKPOINT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoint")
CHECKPOINT_FILE = "phase4_progress.json"
SUBREDDITS_LIST_FILE = "subreddits_list_phase4.json"

# Embedding model
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# HDBSCAN parameters
MIN_CLUSTER_SIZE = 5
MIN_SAMPLES = 3

# Batching
EMBEDDING_BATCH_SIZE = 32

# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------

@dataclass
class Opportunity:
    """Represents a clustered business opportunity."""
    cluster_id: int
    representative_texts: List[str]
    cluster_size: int
    avg_quality_score: float

# -----------------------------------------------------------------------------
# State Management
# -----------------------------------------------------------------------------

def load_progress() -> dict:
    """Load progress from checkpoint file."""
    path = os.path.join(CHECKPOINT_DIR, CHECKPOINT_FILE)
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Failed to load progress: {e}[/yellow]")
    return {"subreddit_index": 0}

def save_progress(index: int):
    """Save progress to checkpoint file."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    path = os.path.join(CHECKPOINT_DIR, CHECKPOINT_FILE)
    with open(path, 'w') as f:
        json.dump({"subreddit_index": index}, f, indent=2)

def load_subreddits_list() -> Optional[List[str]]:
    """Load cached list of subreddits."""
    path = os.path.join(CHECKPOINT_DIR, SUBREDDITS_LIST_FILE)
    if os.path.exists(path):
        console.print(f"[green]✓ Found cached subreddits list at {path}[/green]")
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Failed to parse subreddits list: {e}[/yellow]")
    return None

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

    # Remove duplicates
    subreddits = sorted(list(set(subreddits)))
    console.print(f"[green]✓ Found {len(subreddits)} subreddit directories[/green]")
    return subreddits

# -----------------------------------------------------------------------------
# Embedder Class
# -----------------------------------------------------------------------------

class Embedder:
    """
    Handles embedding text using SentenceTransformers.
    Uses MPS (Metal Performance Shaders) on Mac for GPU acceleration.
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.model = None
        self.device = None
    
    def load_model(self):
        """Load the embedding model with optimal device selection."""
        import torch
        from sentence_transformers import SentenceTransformer
        
        # Determine best available device
        if torch.backends.mps.is_available():
            self.device = "mps"
            console.print("[green]Using MPS (Metal) for GPU acceleration[/green]")
        elif torch.cuda.is_available():
            self.device = "cuda"
            console.print("[green]Using CUDA for GPU acceleration[/green]")
        else:
            self.device = "cpu"
            console.print("[yellow]Using CPU (no GPU detected)[/yellow]")
        
        console.print(f"[blue]Loading embedding model: {self.model_name}[/blue]")
        self.model = SentenceTransformer(self.model_name, device=self.device)
    
    def embed(self, texts: List[str], batch_size: int = EMBEDDING_BATCH_SIZE) -> np.ndarray:
        """Embed a list of texts into vectors."""
        if self.model is None:
            self.load_model()
        
        if not texts:
            return np.array([])
            
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embeddings

# -----------------------------------------------------------------------------
# Clusterer Class
# -----------------------------------------------------------------------------

class Clusterer:
    """Wraps HDBSCAN clustering logic."""
    
    def __init__(self, min_cluster_size: int = MIN_CLUSTER_SIZE, min_samples: int = MIN_SAMPLES):
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
    
    def cluster(self, embeddings: np.ndarray) -> np.ndarray:
        """Cluster embeddings using HDBSCAN."""
        if embeddings.shape[0] == 0:
            return np.array([])
            
        try:
            import hdbscan
            # Suppress HDBSCAN joblib warnings if possible
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
                metric="euclidean",
                cluster_selection_method="eom"
            )
        except ImportError:
            console.print("[yellow]HDBSCAN not found, falling back to sklearn DBSCAN[/yellow]")
            from sklearn.cluster import DBSCAN
            clusterer = DBSCAN(eps=0.5, min_samples=self.min_samples)
        
        return clusterer.fit_predict(embeddings)

# -----------------------------------------------------------------------------
# Pipeline Class
# -----------------------------------------------------------------------------

class Pipeline:
    """
    Orchestrates the Phase 4 clustering pipeline per subreddit.
    """
    
    def __init__(self):
        self.embedder = Embedder()
        self.clusterer = Clusterer()
        
    def get_parquet_files(self, subreddit_path: str) -> List[str]:
        """Find all Parquet files in the subreddit directory."""
        return glob.glob(os.path.join(subreddit_path, "*.parquet"))
    
    def load_data(self, file_paths: List[str]) -> pl.DataFrame:
        """Load and combine data from multiple Parquet files."""
        dfs = []
        for path in file_paths:
            try:
                df = pl.read_parquet(path)
                dfs.append(df)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read {path}: {e}[/yellow]")
        
        if not dfs:
            return pl.DataFrame()
        
        return pl.concat(dfs)
    
    def extract_texts(self, df: pl.DataFrame) -> Tuple[List[str], pl.DataFrame]:
        """Extract text content from the DataFrame."""
        # Common column names for text in this pipeline
        text_columns = ["body", "text", "selftext", "content", "message"]
        text_col = None
        
        for col in text_columns:
            if col in df.columns:
                text_col = col
                break
        
        if text_col is None:
            return [], df.clear()
        
        # Filter out empty/null/short texts
        df_filtered = df.filter(
            pl.col(text_col).is_not_null() & 
            (pl.col(text_col).str.len_chars() > 10)
        )
        
        texts = df_filtered[text_col].to_list()
        return texts, df_filtered

    def build_opportunities(self, df: pl.DataFrame, texts: List[str], 
                           cluster_labels: np.ndarray) -> List[Opportunity]:
        """Build Opportunity objects from clustered data."""
        # Add cluster labels
        # Note: Polars requires Series length to match DataFrame
        # If filtering happened during extract_texts, df here is df_filtered
        
        df = df.with_columns(pl.Series("cluster_id", cluster_labels))
        
        # Filter noise (-1)
        df_clustered = df.filter(pl.col("cluster_id") >= 0)
        
        opportunities = []
        unique_clusters = df_clustered["cluster_id"].unique().to_list()
        
        for cluster_id in unique_clusters:
            # Reconstruct mask for texts list (which aligns with df rows)
            # Texts and df rows are 1:1 at this point
            
            # Get rows for this cluster
            cluster_rows = df_clustered.filter(pl.col("cluster_id") == cluster_id)
            
            # Simple average quality score
            avg_quality = 0.0
            # Check for score columns
            for col in ["quality_score", "score", "nlp_top_score", "ups"]:
                if col in cluster_rows.columns:
                    val = cluster_rows[col].mean()
                    if val is not None:
                        avg_quality = float(val)
                        break
            
            # Get texts for this cluster using the text column we found earlier
            # or just re-extract from the filtered rows
            # This is safer than boolean indexing on the list if we have the df
            text_columns = ["body", "text", "selftext", "content", "message"]
            cluster_texts = []
            for col in text_columns:
                if col in cluster_rows.columns:
                    cluster_texts = cluster_rows[col].to_list()
                    break
            
            # Representative texts (top 10 by length or quality? Just take first 10 for speed)
            representative = cluster_texts[:10]
            
            opportunities.append(Opportunity(
                cluster_id=int(cluster_id),
                representative_texts=representative,
                cluster_size=len(cluster_texts),
                avg_quality_score=avg_quality
            ))
        
        return opportunities

    def save_results(self, opportunities: List[Opportunity], subreddit_path: str):
        """Save clusters to Parquet."""
        # Calculate relative path to mirror structure
        # e.g. /Volumes/2TBSSD/reddit/chains/01/subreddit -> 01/subreddit
        try:
            rel_path = os.path.relpath(subreddit_path, CHAINS_INPUT_DIR)
        except ValueError:
            # Fallback if on different drives
            rel_path = os.path.basename(subreddit_path)
            
        output_dir = os.path.join(CLUSTERS_OUTPUT_DIR, rel_path)
        os.makedirs(output_dir, exist_ok=True)
        
        data = {
            "cluster_id": [o.cluster_id for o in opportunities],
            "cluster_size": [o.cluster_size for o in opportunities],
            "avg_quality_score": [o.avg_quality_score for o in opportunities],
            "representative_texts": [json.dumps(o.representative_texts) for o in opportunities],
        }
        
        df = pl.DataFrame(data)
        output_path = os.path.join(output_dir, "clusters.parquet")
        df.write_parquet(output_path)
        # console.print(f"[dim]    Saved -> {output_path}[/dim]")

    def process_subreddit(self, subreddit_path: str):
        """Process a single subreddit."""
        subreddit_name = os.path.basename(subreddit_path)
        
        files = self.get_parquet_files(subreddit_path)
        if not files:
            # console.print(f"[dim]  No parquet files in {subreddit_name}, skipping[/dim]")
            return

        df = self.load_data(files)
        if df.height == 0:
            return

        texts, df_filtered = self.extract_texts(df)
        if len(texts) < MIN_CLUSTER_SIZE:
            # console.print(f"[dim]  Not enough texts in {subreddit_name} ({len(texts)}), skipping[/dim]")
            return

        console.print(f"  Processing [bold cyan]{subreddit_name}[/bold cyan] ({len(texts)} items)...")
        
        embeddings = self.embedder.embed(texts)
        if len(embeddings) == 0:
            return

        cluster_labels = self.clusterer.cluster(embeddings)
        
        # Stats
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        
        if n_clusters > 0:
             opportunities = self.build_opportunities(df_filtered, texts, cluster_labels)
             self.save_results(opportunities, subreddit_path)
             console.print(f"    Found [green]{n_clusters} clusters[/green]")
        else:
             console.print(f"[dim]    No clusters found[/dim]")

    def run(self, subreddit_arg: Optional[str] = None):
        """Run the pipeline."""
        console.rule("[bold blue]Phase 4: Clustering[/bold blue]")
        console.print(f"Input: {CHAINS_INPUT_DIR}")
        console.print(f"Output: {CLUSTERS_OUTPUT_DIR}")

        # Ensure embedding model is loaded once
        self.embedder.load_model()

        if subreddit_arg:
             # Single subreddit mode logic
             target_path = None
             
             # Try to find it by scanning suffix dirs
             # This assumes standard 2-digit hex suffix (00-ff) or just 2-digit numeric if that was the scheme
             # Rust code uses suffix, let's just check standard range
             # Actually, scanning is safer than guessing if we don't know the exact hash
             
             # Check if input dir exists
             if not os.path.exists(CHAINS_INPUT_DIR):
                 console.print(f"[red]Input directory not found: {CHAINS_INPUT_DIR}[/red]")
                 return

             # 1. Check direct child
             potential = os.path.join(CHAINS_INPUT_DIR, subreddit_arg)
             if os.path.exists(potential):
                target_path = potential
             else:
                # 2. Search in subdirectories
                console.print(f"[dim]Searching for {subreddit_arg}...[/dim]")
                for root, dirs, files in os.walk(CHAINS_INPUT_DIR):
                    if subreddit_arg in dirs:
                        target_path = os.path.join(root, subreddit_arg)
                        break
            
             if target_path:
                 self.process_subreddit(target_path)
             else:
                 console.print(f"[red]Subreddit {subreddit_arg} not found in {CHAINS_INPUT_DIR}[/red]")
             return

        # Load or scan subreddits
        subreddits = load_subreddits_list()
        if not subreddits:
            subreddits = scan_subreddits(CHAINS_INPUT_DIR)
            if subreddits:
                save_subreddits_list(subreddits)

        if not subreddits:
            console.print("[red]No subreddits found to process.[/red]")
            return

        # Load progress
        progress_data = load_progress()
        start_index = progress_data.get("subreddit_index", 0)

        console.print(f"Total subreddits: {len(subreddits)}")
        console.print(f"Resuming from index: {start_index}")

        # Process loop
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.pos}/{task.total} ({task.percentage:.0f}%)"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Clustering...", total=len(subreddits), completed=start_index)
            
            for i in range(start_index, len(subreddits)):
                subreddit_path = subreddits[i]
                
                # Update progress display
                progress.update(task, description=f"Processing {os.path.basename(subreddit_path)}")
                
                try:
                    self.process_subreddit(subreddit_path)
                except Exception as e:
                    console.print(f"[red]Error processing {subreddit_path}: {e}[/red]")
                
                # Save progress
                save_progress(i + 1)
                progress.advance(task)
        
        console.rule("[bold green]Phase 4 Complete[/bold green]")

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Phase 4: Clustering")
    parser.add_argument("--subreddit", type=str, help="Process a specific subreddit only")
    args = parser.parse_args()
    
    pipeline = Pipeline()
    pipeline.run(subreddit_arg=args.subreddit)

if __name__ == "__main__":
    main()
