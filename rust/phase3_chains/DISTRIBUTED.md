# Phase 3 Chains - Distributed Architecture

This document describes the distributed architecture support added to the Phase 3 chains processor.

## Overview

The Phase 3 chains processor now supports three operating modes:

1. **Standalone Mode** (default) - Single machine processing with checkpoint/resume support
2. **Coordinator Mode** - Acts as a task server, distributing work to workers
3. **Worker Mode** - Connects to coordinator, requests and processes tasks

## Architecture

### Components

#### Protocol (`protocol.rs`)
Defines the network messages exchanged between coordinator and workers:
- `RequestTask` - Worker requests a task from coordinator
- `AssignTask` - Coordinator assigns a subreddit task to worker
- `TaskComplete` - Worker reports task completion status
- `Heartbeat` - Keep-alive message from worker
- `NoTasksAvailable` - All work is done

Messages are serialized using bincode for efficient binary communication.

#### Discovery (`discovery.rs`)
mDNS service announcement and discovery:
- Coordinator announces itself on LAN as `_phase3._tcp.local.`
- Workers can auto-discover coordinator or use manual address
- Based on the `mdns-sd` crate

#### Processing (`processing.rs`)
Core subreddit processing logic extracted from original code:
- Processes a single subreddit directory
- Uses DuckDB for in-memory message chain validation
- Processes ideas in chunks for memory efficiency
- Writes validated chains to parquet files

#### Coordinator (`coordinator.rs`)
Task distribution server:
- Maintains task queue from scanned subreddits
- Tracks task states (Pending, Assigned, Completed, Failed)
- Monitors worker heartbeats (60-second timeout)
- Reassigns tasks from stale workers
- Provides status/progress information every 30 seconds

#### Worker (`worker.rs`)
Task processing client with smart caching:
- Connects to coordinator (via mDNS or manual address)
- Requests tasks and processes them
- **Smart Caching**: 
  - Multi-chunk subreddits copied to local cache before processing
  - Single-chunk subreddits processed directly on Samba
  - Results copied back to Samba and local cache cleaned up
- Sends periodic heartbeats to coordinator
- Reports task completion status

#### Standalone (`standalone.rs`)
Original single-machine logic preserved:
- Checkpoint/resume functionality
- Cached subreddit list
- Progress bar with ETA
- Single subreddit mode support

## Usage

### Standalone Mode (Backward Compatible)

Process all subreddits on a single machine:
```bash
# Use default paths
./phase3_chains

# Custom paths
./phase3_chains --data-dir /path/to/processed --output-dir /path/to/chains

# Process single subreddit
./phase3_chains --subreddit AskReddit
```

### Coordinator Mode

Run on the machine with the data:
```bash
./phase3_chains --mode coordinator \
  --data-dir /Volumes/2TBSSD/reddit/processed \
  --output-dir /Volumes/2TBSSD/reddit/chains \
  --port 5000
```

The coordinator will:
1. Scan for all subreddit directories
2. Create a task queue
3. Listen for worker connections on port 5000
4. Announce itself via mDNS as `_phase3._tcp.local.`
5. Distribute tasks to connected workers
6. Monitor worker heartbeats
7. Reassign tasks from disconnected workers
8. Print status updates every 30 seconds

### Worker Mode

Run on client machines with access to data via Samba:

#### With mDNS Auto-Discovery
```bash
./phase3_chains --mode worker \
  --data-dir /mnt/reddit/processed \
  --output-dir /mnt/reddit/chains \
  --local-cache-dir /tmp/phase3_cache
```

#### With Manual Coordinator Address
```bash
./phase3_chains --mode worker \
  --coordinator-addr 192.168.1.100:5000 \
  --data-dir /mnt/reddit/processed \
  --output-dir /mnt/reddit/chains \
  --local-cache-dir /tmp/phase3_cache \
  --worker-id worker-1
```

The worker will:
1. Connect to coordinator (auto-discover via mDNS or use manual address)
2. Request tasks from coordinator
3. Process subreddits with smart caching:
   - **Multi-chunk subreddits** (>1 parquet file): Copy to local cache → process → copy results back → cleanup
   - **Single-chunk subreddits** (≤1 parquet file): Process directly on Samba
4. Send heartbeats every 30 seconds
5. Report completion status
6. Request next task

## Smart Caching Strategy

Workers implement intelligent caching to optimize performance:

### When to Cache Locally
- **Condition**: Subreddit has more than 1 parquet file (chunk)
- **Reason**: Large subreddits benefit from local processing speed
- **Process**:
  1. Copy all input parquet files to `/tmp/phase3_cache/input_{uuid}/`
  2. Process using local files
  3. Write output to `/tmp/phase3_cache/output_{uuid}/`
  4. Copy output files to Samba mount
  5. Delete local cache directories

### When to Process Directly
- **Condition**: Subreddit has 1 or fewer parquet files
- **Reason**: Small subreddits don't justify copy overhead
- **Process**: Read from Samba, write to Samba directly

### Benefits
- **Performance**: Fast local processing for large subreddits
- **Network**: Reduced network load during processing
- **Space**: Temporary files auto-cleaned after each task
- **Safety**: Only workers delete local cache, never the coordinator/master

## Network Protocol

### TCP Communication
- Binary protocol using bincode serialization
- Length-prefixed messages (4-byte BE header + message data)
- Maximum message size: 10MB
- Async I/O using Tokio

### Message Flow

1. **Task Request**:
   ```
   Worker → Coordinator: RequestTask { worker_id }
   Coordinator → Worker: AssignTask { task_id, relative_path }
   ```

2. **Task Completion**:
   ```
   Worker → Coordinator: TaskComplete { task_id, status }
   (No response - worker requests next task)
   ```

3. **Heartbeat**:
   ```
   Worker → Coordinator: Heartbeat { worker_id }
   (No response - fire and forget)
   ```

4. **No Tasks**:
   ```
   Worker → Coordinator: RequestTask { worker_id }
   Coordinator → Worker: NoTasksAvailable
   (Worker exits)
   ```

### Error Handling
- **Worker disconnection**: Coordinator detects via heartbeat timeout
- **Task failure**: Worker reports failure, coordinator re-queues task
- **Network errors**: Workers log error and exit, tasks are reassigned

## Configuration Options

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `--mode` | Operating mode | No | `standalone` |
| `--data-dir` | Input data directory | No | `/Volumes/2TBSSD/reddit/processed` |
| `--output-dir` | Output directory | No | `/Volumes/2TBSSD/reddit/chains` |
| `--subreddit` | Single subreddit mode | No | None (process all) |
| `--coordinator-addr` | Manual coordinator address | No | Auto-discover via mDNS |
| `--local-cache-dir` | Worker temp directory | No | None (no caching) |
| `--worker-id` | Worker identifier | No | Auto-generated UUID |
| `--port` | Coordinator listen port | No | `5000` |

## Example Deployment

### Scenario
- 1 coordinator (Mac with external SSD)
- 3 workers (Linux machines with Samba mounts)
- 15,432 subreddits to process

### Coordinator (Mac)
```bash
./phase3_chains --mode coordinator \
  --data-dir /Volumes/2TBSSD/reddit/processed \
  --output-dir /Volumes/2TBSSD/reddit/chains
```

### Workers (Linux machines)
```bash
# Worker 1
./phase3_chains --mode worker \
  --data-dir /mnt/reddit/processed \
  --output-dir /mnt/reddit/chains \
  --local-cache-dir /tmp/phase3_worker1 \
  --worker-id worker-1

# Worker 2
./phase3_chains --mode worker \
  --data-dir /mnt/reddit/processed \
  --output-dir /mnt/reddit/chains \
  --local-cache-dir /tmp/phase3_worker2 \
  --worker-id worker-2

# Worker 3
./phase3_chains --mode worker \
  --data-dir /mnt/reddit/processed \
  --output-dir /mnt/reddit/chains \
  --local-cache-dir /tmp/phase3_worker3 \
  --worker-id worker-3
```

### Result
- Tasks distributed evenly across 3 workers
- ~3x speedup compared to standalone mode
- Automatic load balancing and failover
- Progress visible on coordinator console

## Monitoring

### Coordinator Status
The coordinator prints status every 30 seconds:
```
📊 Tasks: 5000 pending, 3 assigned, 10432 completed, 0 failed. Workers: 3
```

### Worker Logs
Workers log all task processing:
```
📦 Received task abc-123: 01/AskReddit
  Subreddit has 5 parquet files
  Using local cache (multi-chunk processing)
  Copying input data to local cache...
  Processing from local cache...
  Copying results back to Samba...
  Cleaning up local cache...
  ✓ Task abc-123 completed successfully
```

## Troubleshooting

### Workers Can't Find Coordinator
- Verify mDNS is working on the network
- Use `--coordinator-addr` with explicit IP:port
- Check firewall rules (port 5000 TCP)

### Slow Performance on Workers
- Verify Samba mount is working correctly
- Use `--local-cache-dir` on fast local storage (SSD)
- Check network bandwidth between worker and coordinator

### Tasks Stuck in "Assigned" State
- Worker likely crashed or disconnected
- Coordinator will reassign after 60-second timeout
- Check worker logs for errors

### Out of Disk Space on Worker
- Local cache fills up if not enough space
- Increase `--local-cache-dir` partition size
- Or process directly on Samba (remove `--local-cache-dir`)

## Technical Details

### Dependencies
- `tokio` - Async runtime for network I/O
- `mdns-sd` - mDNS service discovery
- `bincode` - Binary message serialization
- `uuid` - Task and worker identifiers
- `gethostname` - Hostname resolution for mDNS
- `duckdb` - In-memory database for chain validation
- `polars` - Parquet file I/O

### Performance Characteristics
- **Network overhead**: ~1KB per task assignment
- **Memory per task**: ~100MB-1GB (depends on subreddit size)
- **Heartbeat interval**: 30 seconds
- **Worker timeout**: 60 seconds
- **Task batch size**: 1 subreddit per task

### Scalability
- Tested with 3 workers, designed for up to 100
- Linear speedup with number of workers
- Coordinator handles 1000s of tasks efficiently
- Network bandwidth is typically not a bottleneck

## Persistent Task Queue

The coordinator now supports persistent checkpointing to survive restarts without losing progress.

### Checkpoint Files

All checkpoint files are stored in the `checkpoint/` directory:

1. **`coordinator_state.json`** - Full coordinator state including all tasks and their status
2. **`subreddits_list.json`** - Cached list of subreddit directories (avoids rescanning)
3. **`phase3_progress.json.migrated`** - Backup of migrated standalone checkpoint

### Checkpoint Format

The coordinator saves a JSON checkpoint every 30 seconds containing:

```json
{
  "version": 1,
  "tasks": [
    {
      "id": "uuid-here",
      "relative_path": "01/subreddit_name",
      "state": "Pending" | { "Assigned": { "worker_id": "..." }} | "Completed" | { "Failed": { "error": "..." }}
    }
  ]
}
```

### Migration from Standalone Mode

If you've been running in standalone mode and want to switch to distributed mode, the coordinator will automatically migrate your progress:

1. **Detection**: On startup, coordinator looks for `checkpoint/phase3_progress.json`
2. **Migration**: Reads the `subreddit_index` and marks all subreddits before that index as completed
3. **Conversion**: Creates coordinator tasks from the standalone checkpoint
4. **Backup**: Renames old checkpoint to `phase3_progress.json.migrated`
5. **Save**: Writes new coordinator checkpoint format

Example migration log:
```
📦 Found old standalone checkpoint, migrating...
   Standalone was at subreddit index 1234/5678
✓ Migrated 1234 completed and 4444 pending tasks from standalone checkpoint
   Backed up old checkpoint to "checkpoint/phase3_progress.json.migrated"
```

### Resume Behavior

When coordinator restarts:

1. **Load Checkpoint**: Reads `checkpoint/coordinator_state.json` if it exists
2. **Load Subreddits**: Uses cached `subreddits_list.json` to avoid rescanning
3. **Restore State**:
   - **Completed tasks**: Kept as completed, not re-queued
   - **Pending tasks**: Re-added to task queue
   - **Failed tasks**: Re-added to task queue for retry
   - **Assigned tasks**: Re-queued as pending (workers may have died during restart)
4. **Continue**: Starts accepting worker connections and distributing remaining tasks

### Important Notes

- **Periodic Saves**: Checkpoint is saved every 30 seconds during normal operation
- **No Data Loss**: Even if coordinator crashes, at most 30 seconds of progress is lost
- **Worker-Safe**: Workers are unaffected by coordinator restarts - they just reconnect
- **Disk Space**: Checkpoint file size is proportional to number of subreddits (~1KB per 10 subreddits)
- **Manual Recovery**: If needed, you can edit the checkpoint JSON manually to fix task states

### Example Restart Workflow

```bash
# Initial start - creates checkpoint
./phase3_chains --mode coordinator --data-dir /data --output-dir /output

# ... processing for a while ...
# Coordinator crashes or needs restart

# Restart - automatically resumes from checkpoint
./phase3_chains --mode coordinator --data-dir /data --output-dir /output

# Logs show:
# 📍 Found coordinator checkpoint at "checkpoint/coordinator_state.json"
# ✓ Loaded 5678 tasks from checkpoint (version 1)
# 📊 Restored state: 4000 pending, 1500 completed, 50 failed, 128 reassigned from assigned
```

## Future Improvements

Potential enhancements:
- [x] Persistent task queue (survive coordinator restarts) - **IMPLEMENTED**
- [ ] Web UI for monitoring progress
- [ ] Dynamic worker scaling based on load
- [ ] Task prioritization (process large subreddits first)
- [ ] Compression for network messages
- [ ] Authentication/encryption for worker connections
- [ ] Metrics export (Prometheus, Grafana)

## License

Same as the main project.
