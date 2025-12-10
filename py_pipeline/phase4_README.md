# Phase 4: Distributed Embedding Infrastructure

This phase implements a distributed, polyglot system for generating embeddings from the chain data produced in Phase 3.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Phase 4 Data Flow                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   chains/             phase4_manager         Redis Queue                 │
│   ├── 00/             (Rust)                 [phase4_todo_queue]         │
│   │   ├── SubA/   ─────────────────────────► ┌───────────────────┐       │
│   │   └── SubB/                              │ {input, output}   │       │
│   └── 01/                                    │ {input, output}   │       │
│       └── SubC/                              └───────────────────┘       │
│                                                       │                  │
│                                                       ▼                  │
│                              ┌────────────────────────┴───────────────┐  │
│                              │                                        │  │
│                     ┌────────▼────────┐              ┌───────▼───────┐│  │
│                     │ phase4_worker   │              │ phase4_worker ││  │
│                     │ (Python/MPS)    │              │ (Rust/ONNX)   ││  │
│                     └────────┬────────┘              └───────┬───────┘│  │
│                              │                               │        │  │
│                              └───────────────┬───────────────┘        │  │
│                                              │                        │  │
│                                              ▼                        │  │
│   embeddings/                    Files with emb_000...emb_383         │  │
│   ├── 00/SubA/*.parquet                                               │  │
│   ├── 00/SubB/*.parquet                                               │  │
│   └── 01/SubC/*.parquet                                               │  │
│                                              │                        │  │
│                                              ▼                        │  │
│                              ┌───────────────────────────┐            │  │
│                              │    phase4_clusterer       │            │  │
│                              │    (Python/HDBSCAN)       │            │  │
│                              └───────────────────────────┘            │  │
│                                              │                        │  │
│                                              ▼                        │  │
│   clusters/                   Clustered parquet files                 │  │
│   ├── 00/SubA/clustered.parquet                                       │  │
│   └── ...                                                             │  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Phase 4 Manager (Rust)

**Path:** `rust/phase4_manager/`

Scans the chains directory, checks for missing embedding outputs, and queues jobs to Redis.

```bash
cd rust/phase4_manager
cargo build --release
./target/release/phase4_manager
```

**Features:**
- Fast filesystem scanning
- Idempotent: only queues missing outputs
- Checkpointing for resumability
- Graceful shutdown (Ctrl+C)

### 2. Phase 4 Worker - ONNX (Rust)

**Path:** `rust/phase4_worker/`

High-performance embedding worker using ONNX Runtime. Optimal for CPU nodes.

```bash
# First, export the model to ONNX format
python scripts/export_onnx.py --model all-MiniLM-L6-v2 --output models/onnx/minilm/

# Then build and run the worker
cd rust/phase4_worker
cargo build --release
./target/release/phase4_worker
```

**Requirements:**
- ONNX model exported to `models/onnx/minilm/`
- Includes: `model.onnx`, `tokenizer.json`

### 3. Phase 4 Worker - MPS/CUDA (Python)

**Path:** `py_pipeline/phase4_worker.py`

PyTorch-based worker optimized for GPU acceleration (MPS on Mac, CUDA on NVIDIA).

```bash
# Auto-detect device (MPS > CUDA > CPU)
python py_pipeline/phase4_worker.py

# Force specific device
python py_pipeline/phase4_worker.py --device mps
python py_pipeline/phase4_worker.py --device cuda
python py_pipeline/phase4_worker.py --device cpu
```

### 4. Phase 4 Clusterer (Python)

**Path:** `py_pipeline/phase4_clusterer.py`

Aggregates embeddings per subreddit and clusters using HDBSCAN.

```bash
# Process all subreddits
python py_pipeline/phase4_clusterer.py

# Process single subreddit
python py_pipeline/phase4_clusterer.py --subreddit AskReddit
```

## Setup

### 1. Export ONNX Model (for Rust worker)

```bash
python scripts/export_onnx.py --model all-MiniLM-L6-v2 --output models/onnx/minilm/
```

### 2. Build Rust Components

```bash
# Manager
cd rust/phase4_manager && cargo build --release

# ONNX Worker
cd rust/phase4_worker && cargo build --release
```

### 3. Verify Redis Connection

The system uses Azure Redis Cache. Ensure the URL in the code matches your Redis instance.

## Running the Pipeline

### Step 1: Queue Jobs

```bash
./rust/phase4_manager/target/release/phase4_manager
```

### Step 2: Start Workers

Run on multiple machines/terminals:

```bash
# On Mac (MPS)
python py_pipeline/phase4_worker.py --device mps

# On NVIDIA machine
python py_pipeline/phase4_worker.py --device cuda

# On CPU-only nodes (Rust ONNX is recommended for better CPU perf)
./rust/phase4_worker/target/release/phase4_worker
```

### Step 3: Cluster Embeddings

After all embedding jobs are complete:

```bash
python py_pipeline/phase4_clusterer.py
```

## Fault Tolerance

### Idempotency
- Manager checks for existing output files before queueing
- Workers check for existing outputs before processing
- Safe to restart the manager at any time

### Atomic Writes
- Workers write to `.parquet.tmp` first
- Rename to final `.parquet` on success
- Prevents partial/corrupt files

### Graceful Shutdown
- Ctrl+C sends shutdown signal
- Workers finish current job before exiting
- Progress is checkpointed

### Resumability
- Manager saves progress (subreddit index)
- Workers are stateless (jobs are in Redis)
- Clusterer saves progress (subreddit index)

## Directory Structure

```
/Volumes/2TBSSD/reddit/
├── chains/           # Input from Phase 3
│   ├── 00/
│   │   └── SubredditA/
│   │       └── chains_chunk_0.parquet
│   └── ...
├── embeddings/       # Output from Phase 4 Workers
│   ├── 00/
│   │   └── SubredditA/
│   │       └── chains_chunk_0.parquet  (+ emb_000...emb_383)
│   └── ...
└── clusters/         # Output from Phase 4 Clusterer
    ├── 00/
    │   └── SubredditA/
    │       └── clustered.parquet
    └── ...
```

## Monitoring

### Check Redis Queue Length

```bash
redis-cli -u "$REDIS_URL" LLEN phase4_todo_queue
```

### Check Worker Progress

Workers print progress to console. For distributed monitoring, consider adding metrics export.

## Performance Notes

- **MPS (Apple Silicon)**: Best for MacBooks/Mac Studio
- **CUDA (NVIDIA)**: Best throughput on GPU clusters
- **ONNX (Rust)**: Good CPU utilization, lower memory overhead
- **Batch Size**: Default 32, tune based on available VRAM/RAM

## Troubleshooting

### "Model file not found"
Run the ONNX export script first:
```bash
python scripts/export_onnx.py
```

### Redis Connection Failed
- Check network connectivity
- Verify Redis URL and credentials
- For local dev, use `redis://127.0.0.1:6379/`

### Worker Stuck
- Check for Redis connectivity
- Verify input files exist
- Check available disk space for output
