#!/usr/bin/env python3
"""
Phase 4 Worker (MPS/CUDA): Embedding Generation

This worker consumes embedding jobs from Redis, generates embeddings using
sentence-transformers with PyTorch (MPS for Apple Silicon, CUDA for NVIDIA),
and writes the results to Parquet files.

Usage:
    python phase4_worker.py [--device mps|cuda|cpu]
"""

import os
import sys
import json
import signal
import argparse
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

import polars as pl
import numpy as np
import redis
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

# Import SentenceTransformers (lazy import to check availability)
try:
    import torch
    from sentence_transformers import SentenceTransformer
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Add project root to path for config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize console
console = Console()

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Redis configuration
REDIS_URL = "redis://:kRoGWJXNK75zMIcJz4RDDhNhz1hfKq6OLAzCaCFPVIw%3D@businessfinder.canadacentral.redis.azure.net:10000/"
REDIS_PHASE4_QUEUE = "phase4_todo_queue"
REDIS_TIMEOUT_SECS = 5

# Model configuration
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
BATCH_SIZE = 32

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


@dataclass
class EmbeddingJob:
    """Job struct received from Redis."""
    input_path: str
    output_path: str
    
    @classmethod
    def from_json(cls, json_str: str) -> 'EmbeddingJob':
        data = json.loads(json_str)
        return cls(
            input_path=data['input_path'],
            output_path=data['output_path']
        )


class EmbeddingWorker:
    """
    Worker that consumes embedding jobs from Redis and processes them.
    Uses PyTorch with MPS (Apple Silicon) or CUDA (NVIDIA) acceleration.
    """
    
    def __init__(self, device: Optional[str] = None):
        if not HAS_TORCH:
            raise ImportError("PyTorch and sentence-transformers are required. Install with: pip install torch sentence-transformers")
        
        self.model = None
        self.device = device
        self.redis_client = None
        self.redis_conn = None
        self.jobs_processed = 0
        
    def connect_redis(self):
        """Establish Redis connection."""
        console.print("[blue]Connecting to Redis...[/blue]")
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        # Test connection
        self.redis_client.ping()
        console.print("[green]✓ Connected to Redis[/green]")
        
    def load_model(self):
        """Load the embedding model with optimal device selection."""
        # Determine best available device
        if self.device:
            device = self.device
        elif torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
        
        self.device = device
        
        device_names = {
            "mps": "MPS (Apple Silicon GPU)",
            "cuda": "CUDA (NVIDIA GPU)",
            "cpu": "CPU"
        }
        console.print(f"[blue]Loading model: {EMBEDDING_MODEL_NAME}[/blue]")
        console.print(f"[blue]Device: {device_names.get(device, device)}[/blue]")
        
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
        console.print("[green]✓ Model loaded[/green]")
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        if not texts:
            return np.array([])
        
        embeddings = self.model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embeddings
    
    def process_job(self, job: EmbeddingJob) -> bool:
        """Process a single embedding job. Returns True on success."""
        input_path = Path(job.input_path)
        output_path = Path(job.output_path)
        
        # Idempotency check
        if output_path.exists():
            console.print(f"[dim]Output exists, skipping: {output_path.name}[/dim]")
            return True
        
        try:
            # Read input parquet
            df = pl.read_parquet(input_path)
            
            if df.height == 0:
                console.print(f"[dim]Empty file, skipping: {input_path.name}[/dim]")
                return True
            
            # Find text column
            text_columns = ["body", "text", "selftext", "content", "message"]
            text_col = None
            for col in text_columns:
                if col in df.columns:
                    text_col = col
                    break
            
            if text_col is None:
                console.print(f"[yellow]No text column found in: {input_path.name}[/yellow]")
                return False
            
            # Extract texts
            texts = df[text_col].fill_null("").to_list()
            
            # Generate embeddings
            embeddings = self.embed_texts(texts)
            
            if len(embeddings) == 0:
                console.print(f"[yellow]No embeddings generated for: {input_path.name}[/yellow]")
                return False
            
            # Create embedding columns
            embedding_columns = {}
            for dim in range(EMBEDDING_DIM):
                embedding_columns[f"emb_{dim:03d}"] = embeddings[:, dim].tolist()
            
            # Add embeddings to dataframe
            for col_name, values in embedding_columns.items():
                df = df.with_columns(pl.Series(col_name, values))
            
            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Atomic write: write to temp file first
            temp_path = output_path.with_suffix(".parquet.tmp")
            df.write_parquet(temp_path, compression="zstd")
            
            # Rename to final path
            temp_path.rename(output_path)
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error processing {input_path.name}: {e}[/red]")
            return False
    
    def run(self):
        """Main worker loop: consume and process jobs from Redis."""
        global shutdown_requested
        
        console.rule("[bold blue]Phase 4 Worker (PyTorch/MPS) Started[/bold blue]")
        
        # Initialize
        self.connect_redis()
        self.load_model()
        
        # Get initial queue length
        queue_len = self.redis_client.llen(REDIS_PHASE4_QUEUE)
        console.print(f"Current queue length: {queue_len}")
        
        console.print("\n[green]Starting worker loop...[/green]")
        console.print("[dim]Press Ctrl+C to gracefully shutdown[/dim]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("Jobs: {task.completed}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Waiting for jobs...", total=None)
            
            while not shutdown_requested:
                try:
                    # BLPOP with timeout
                    result = self.redis_client.blpop(
                        REDIS_PHASE4_QUEUE,
                        timeout=REDIS_TIMEOUT_SECS
                    )
                    
                    if result is None:
                        # Timeout, no jobs available
                        progress.update(task, description="Waiting for jobs...")
                        continue
                    
                    _, job_json = result
                    
                    try:
                        job = EmbeddingJob.from_json(job_json)
                    except Exception as e:
                        console.print(f"[yellow]Failed to parse job: {e}[/yellow]")
                        continue
                    
                    # Update progress display
                    file_name = Path(job.input_path).name
                    progress.update(task, description=f"Processing: {file_name}")
                    
                    # Process the job
                    if self.process_job(job):
                        self.jobs_processed += 1
                        progress.update(task, completed=self.jobs_processed)
                    
                except redis.ConnectionError as e:
                    console.print(f"[red]Redis connection error: {e}[/red]")
                    console.print("[yellow]Reconnecting in 5 seconds...[/yellow]")
                    import time
                    time.sleep(5)
                    try:
                        self.connect_redis()
                    except Exception:
                        pass
                    
                except Exception as e:
                    console.print(f"[red]Unexpected error: {e}[/red]")
                    import traceback
                    traceback.print_exc()
        
        # Shutdown
        console.rule("[bold green]Worker Shutdown[/bold green]")
        console.print(f"Total jobs processed: {self.jobs_processed}")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 4 Embedding Worker (PyTorch/MPS)"
    )
    parser.add_argument(
        "--device",
        type=str,
        choices=["mps", "cuda", "cpu"],
        help="Device to use for inference (default: auto-detect)"
    )
    args = parser.parse_args()
    
    console.print("╔══════════════════════════════════════════════════════════╗")
    console.print("║   Phase 4 Worker (PyTorch): Embedding Generation         ║")
    console.print("╚══════════════════════════════════════════════════════════╝")
    
    worker = EmbeddingWorker(device=args.device)
    worker.run()


if __name__ == "__main__":
    main()
