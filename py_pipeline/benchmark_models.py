#!/usr/bin/env python3
"""
Benchmark Models Script

This script benchmarks the `all-MiniLM-L6-v2` embedding model execution on 1000 rows 
from AskReddit using three different configurations:
1. PyTorch MPS (Metal Performance Shaders)
2. PyTorch CPU
3. ONNX CPU

Based on py_pipeline/phase4_analytics.py for data loading structure.
"""

import os
import sys
import time
import glob
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

import polars as pl
import numpy as np
from rich.console import Console
from rich.table import Table
import torch
from sentence_transformers import SentenceTransformer

# Configure logging to suppress verbose transformers output
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("optimum").setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO, format='%(message)s')

console = Console()

# Configuration
CHAINS_INPUT_DIR = "/Volumes/2TBSSD/reddit/chains"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 32

def find_askreddit_path(base_dir: str) -> str:
    """
    Search for AskReddit directory within the base directory.
    Supports both flat structure and hash-based subdirectories (00-ff).
    """
    base = Path(base_dir)
    if not base.exists():
        console.print(f"[red]Input directory does not exist: {base}[/red]")
        sys.exit(1)

    # Direct check
    direct = base / "AskReddit"
    if direct.exists() and direct.is_dir():
        return str(direct)
    
    # Recursive check (depth 1 for hash folders)
    console.print(f"[dim]Searching for AskReddit in {base}...[/dim]")
    for path in base.iterdir():
        if path.is_dir():
            # Check if this is a subreddit (case insensitive fallback)
            if path.name.lower() == "askreddit":
                return str(path)
            
            # Check inside if it looks like a hash dir (2 chars)
            if len(path.name) == 2 and path.name.isalnum():
                sub_path = path / "AskReddit"
                if sub_path.exists() and sub_path.is_dir():
                    return str(sub_path)
    
    console.print("[red]AskReddit subreddit not found in chains directory![/red]")
    sys.exit(1)

def load_data(subreddit_path: str, limit: int = 1000) -> List[str]:
    """Load texts from Parquet files."""
    parquet_files = glob.glob(os.path.join(subreddit_path, "*.parquet"))
    
    if not parquet_files:
        console.print(f"[red]No parquet files found in {subreddit_path}[/red]")
        sys.exit(1)
    
    console.print(f"[blue]Loading data from {len(parquet_files)} files...[/blue]")
    
    texts = []
    text_columns = ["body", "text", "selftext", "content", "message"]
    
    for file_path in parquet_files:
        try:
            df = pl.read_parquet(file_path)
            
            # Identify text column
            target_col = None
            for col in text_columns:
                if col in df.columns:
                    target_col = col
                    break
            
            if not target_col:
                continue
                
            # Filter valid texts
            valid_texts = df.filter(
                pl.col(target_col).is_not_null() & 
                (pl.col(target_col).str.len_chars() > 20)
            ).select(target_col).to_series().to_list()
            
            texts.extend(valid_texts)
            
            if len(texts) >= limit:
                break
                
        except Exception as e:
            console.print(f"[yellow]Error reading {file_path}: {e}[/yellow]")
            continue

    if len(texts) < limit:
        console.print(f"[yellow]Warning: Only found {len(texts)} rows (requested {limit})[/yellow]")
    
    return texts[:limit]

# -----------------------------------------------------------------------------
# Benchmark Implementations
# -----------------------------------------------------------------------------

def benchmark_pytorch_mps(texts: List[str]) -> Dict[str, Any]:
    """Benchmark using SentenceTransformer on MPS."""
    console.print("\n[bold cyan]Benchmarking PyTorch MPS...[/bold cyan]")
    
    if not torch.backends.mps.is_available():
        console.print("[red]MPS not available on this system![/red]")
        return {"time": 0, "fps": 0, "status": "Failed (No MPS)"}

    try:
        start_load = time.time()
        model = SentenceTransformer(MODEL_NAME, device="mps")
        load_time = time.time() - start_load
        console.print(f"[dim]Model load time: {load_time:.2f}s[/dim]")

        start_infer = time.time()
        _ = model.encode(
            texts, 
            batch_size=BATCH_SIZE,
            show_progress_bar=True,
            device="mps"
        )
        total_time = time.time() - start_infer
        
        fps = len(texts) / total_time
        return {"time": total_time, "fps": fps, "status": "Success"}
        
    except Exception as e:
        console.print(f"[red]MPS Benchmark Failed: {e}[/red]")
        return {"time": 0, "fps": 0, "status": f"Failed: {e}"}

def benchmark_pytorch_cpu(texts: List[str]) -> Dict[str, Any]:
    """Benchmark using SentenceTransformer on CPU."""
    console.print("\n[bold cyan]Benchmarking PyTorch CPU...[/bold cyan]")
    
    try:
        start_load = time.time()
        model = SentenceTransformer(MODEL_NAME, device="cpu")
        load_time = time.time() - start_load
        console.print(f"[dim]Model load time: {load_time:.2f}s[/dim]")

        start_infer = time.time()
        _ = model.encode(
            texts, 
            batch_size=BATCH_SIZE,
            show_progress_bar=True,
            device="cpu"
        )
        total_time = time.time() - start_infer
        
        fps = len(texts) / total_time
        return {"time": total_time, "fps": fps, "status": "Success"}

    except Exception as e:
        console.print(f"[red]CPU Benchmark Failed: {e}[/red]")
        return {"time": 0, "fps": 0, "status": f"Failed: {e}"}

def benchmark_onnx_cpu(texts: List[str]) -> Dict[str, Any]:
    """Benchmark using ONNX Runtime CPU via Optimum."""
    console.print("\n[bold cyan]Benchmarking ONNX CPU...[/bold cyan]")
    
    try:
        from optimum.onnxruntime import ORTModelForFeatureExtraction
        from transformers import AutoTokenizer

        start_load = time.time()
        
        # Load ONNX model
        # Note: We use ORTModelForFeatureExtraction for embeddings
        model = ORTModelForFeatureExtraction.from_pretrained(
            MODEL_NAME,
            export=True,
            provider="CPUExecutionProvider"
        )
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        
        load_time = time.time() - start_load
        console.print(f"[dim]Model load time: {load_time:.2f}s[/dim]")

        start_infer = time.time()
        
        # Batch processing
        for i in range(0, len(texts), BATCH_SIZE):
            batch_texts = texts[i:i + BATCH_SIZE]
            inputs = tokenizer(batch_texts, padding=True, truncation=True, return_tensors="pt")
            with torch.no_grad():
                outputs = model(**inputs)
                # Perform mean pooling typically used for sentence embeddings
                # But for just benchmarking raw inference speed, just getting outputs is enough.
                # To be fair to SentenceTransformers, we should acknowledge they do pooling.
                # But optimum model forward pass is the main component.
                pass
                
        total_time = time.time() - start_infer
        
        fps = len(texts) / total_time
        return {"time": total_time, "fps": fps, "status": "Success"}

    except ImportError:
        console.print("[red]optimum or onnxruntime not installed![/red]")
        return {"time": 0, "fps": 0, "status": "Failed (Missing Deps)"}
    except Exception as e:
        console.print(f"[red]ONNX Benchmark Failed: {e}[/red]")
        return {"time": 0, "fps": 0, "status": f"Failed: {e}"}

def main():
    console.rule("[bold blue]Model Benchmark: AskReddit[/bold blue]")
    
    # 1. Locate Data
    askreddit_path = find_askreddit_path(CHAINS_INPUT_DIR)
    console.print(f"Subreddit Path: {askreddit_path}")
    
    # 2. Load Data
    texts = load_data(askreddit_path, limit=10000)
    console.print(f"Loaded {len(texts)} rows for benchmarking.")
    
    if len(texts) == 0:
        console.print("[red]No texts loaded. Exiting.[/red]")
        return

    # 3. Running Benchmarks
    results = []
    
    # PyTorch MPS
    res_mps = benchmark_pytorch_mps(texts)
    results.append(("PyTorch MPS", res_mps))
    
    # PyTorch CPU
    res_cpu = benchmark_pytorch_cpu(texts)
    results.append(("PyTorch CPU", res_cpu))
    
    # ONNX CPU
    res_onnx = benchmark_onnx_cpu(texts)
    results.append(("ONNX CPU", res_onnx))
    
    # 4. Display Results
    console.print("\n")
    table = Table(title=f"Benchmark Results (N={len(texts)})")
    table.add_column("Method", style="cyan")
    table.add_column("Total Time (s)", justify="right")
    table.add_column("Speed (msg/s)", justify="right", style="green")
    table.add_column("Status", style="magenta")
    
    for name, res in results:
        time_str = f"{res['time']:.2f}" if res['time'] > 0 else "-"
        fps_str = f"{res['fps']:.2f}" if res['fps'] > 0 else "-"
        table.add_row(name, time_str, fps_str, res['status'])
        
    console.print(table)

if __name__ == "__main__":
    main()
