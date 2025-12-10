# Phase 4 Distributed Infrastructure Plan (Polyglot)

## 1. Problem Statement

Benchmarking reveals that embedding generation is the primary bottleneck. To scale effectively, we need a distributed system that can leverage heterogeneous hardware ("several computers") including Macs (MPS), PCs (CUDA/CPU), and potentially pure CPU nodes.

## 2. Architecture: Hybrid Rust/Python

We will use a **Polyglot Microservices** approach to maximize performance and compatibility.

- **Rust**: For high-performance orchestration (file scanning) and CPU/ONNX inference.
- **Python**: For Apple Silicon (MPS) inference and complex Clustering (HDBSCAN).
- **Redis**: As the communication bus.
- **Shared Storage**: For heavy data access.

### Components

1.  **Manager (Rust)**: `phase4_manager`
    *   *Role*: Efficiently scans the filesystem, checks for existing output files, and queues missing work.
    *   *Why Rust?* Directory traversal and string manipulation on millions of files is significantly faster and safer in Rust. Resequencing logic matches the robust `phase2_orchestrator`.
    
2.  **Worker Type A (Python)**: `phase4_worker_mps`
    *   *Role*: Consumes tasks, runs inference using **PyTorch/MPS** (Apple Silicon) or PyTorch/CUDA.
    *   *Optimized for*: Mac Studio, MacBook Pro (M-series chips).

3.  **Worker Type B (Rust)**: `phase4_worker_onnx`
    *   *Role*: Consumes tasks, runs inference using **ONNX Runtime** (ORT).
    *   *Optimized for*: CPU nodes (Intel/AMD) or NVIDIA nodes (via CUDA provider validation).
    *   *Note*: Benchmarks showed ONNX CPU was slow in Python, but Rust `ort` often has lower overhead and better threading control.

4.  **Clusterer (Python)**: `phase4_clusterer`
    *   *Role*: Aggregates embeddings and runs HDBSCAN.
    *   *Why Python?* libraries like `hdbscan` or `rapids-cuml` are Python-native.

## 3. Data Flow

1.  **Input**: Parametrized by `chains/{suffix}/{subreddit}/*.parquet`.
2.  **Manager** puts Job: `{"input_path": "/Vol/.../in.parquet", "output_path": "/Vol/.../out.parquet"}`.
3.  **Worker** (Rust or Python):
    *   `BLPOP` Job.
    *   Reads `input_path` (Polars).
    *   Generates Embeddings (`all-MiniLM-L6-v2`).
    *   Writes `output_path` (Polars).
4.  **Clusterer**: Runs batch job at the end.

## 4. Implementation Details

### A. Phase 4 Manager (Rust)
*   **Path**: `rust/phase4_manager/src/main.rs`
*   **Logic**:
    *   Load `subreddits_list.json` (checkpoint).
    *   Iterate Subreddits.
    *   Iterate `chains` parquet files.
    *   Check if equivalent `embeddings` parquet file exists.
    *   If missing -> Push to `phase4_todo_queue`.

### B. Phase 4 Worker ONNX (Rust)
*   **Path**: `rust/phase4_worker/src/main.rs`
*   **Stack**: `ort`, `tokenizers`, `polars`, `redis`.
*   **Model**: Export `all-MiniLM-L6-v2` to ONNX format.
*   **Logic**:
    *   Initialize `ort::Session` (GraphOptimizationLevel::Level3).
    *   Loop `redis.blpop`.
    *   Read Parquet -> `Vec<String>`.
    *   Tokenize & Embed -> `Vec<Vec<f32>>` (Batched).
    *   Polars DataFrame -> Write Parquet.

### C. Phase 4 Worker MPS (Python)
*   **Path**: `py_pipeline/phase4_worker.py`
*   **Stack**: `sentence-transformers`, `redis`, `polars`.
*   **Logic**:
    *   Same loop, but uses `device='mps'`.

## 5. Fault Tolerance & Resumability

1.  **Idempotency**: The Manager checks `if output_file.exists()` before queuing. Restarting the manager "heals" the queue by re-adding only missing items.
2.  **Atomic Writes**:
    *   Workers write to `filename.parquet.tmp`.
    *   Rename to `filename.parquet` on success.
3.  **Graceful Shutdown**:
    *   Rust: `ctrlc` crate to set a flag, worker finishes current file then exits.
    *   Python: `signal` handler.

## 6. Model Export (Prerequisite)

We must export the embedding model to ONNX for the Rust worker:
```bash
python -m script.export_onnx --model sentence-transformers/all-MiniLM-L6-v2 --output models/onnx/minilm/
```

## 7. Estimate

*   **Rust Manager**: < 1s to scan checks.
*   **Rust Worker**: Parallelizes perfectly on CPUs.
*   **Python Worker**: Maxes out MPS.
*   **Total**: Scalable to any number of nodes.
