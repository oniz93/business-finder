# Phase 3 Chains: Visual Flow

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│  Phase 2 Output: /Volumes/2TBSSD/reddit/processed                   │
│  ├── 01/                                                             │
│  │   ├── AskReddit/                                                  │
│  │   │   ├── 2016_04.parquet  (all messages, is_idea flagged)       │
│  │   │   ├── 2016_05.parquet                                         │
│  │   │   └── ...                                                     │
│  │   └── ...                                                         │
│  ├── 02/                                                             │
│  └── ...                                                             │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Phase 3 Process: Chain Building                                    │
│                                                                       │
│  For each subreddit:                                                 │
│  1. Load all parquet files                                           │
│  2. Filter: is_idea = true                                           │
│  3. Build HashMap<id, MessageNode>                                   │
│  4. Validate chains:                                                 │
│     ┌─────────────────────────────────────────┐                     │
│     │  For each message:                       │                     │
│     │  • Check parent_id                       │                     │
│     │  • Recursively follow to root            │                     │
│     │  • Keep only if reaches parent_id=null   │                     │
│     └─────────────────────────────────────────┘                     │
│  5. Filter DataFrame to keep only valid chains                       │
│  6. Write to output                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Phase 3 Output: /Volumes/2TBSSD/reddit/chains                      │
│  ├── 01/                                                             │
│  │   ├── AskReddit/                                                  │
│  │   │   └── chains.parquet  (only complete chains)                 │
│  │   └── ...                                                         │
│  ├── 02/                                                             │
│  └── ...                                                             │
└─────────────────────────────────────────────────────────────────────┘
```

## Example Chain Validation

```
Input Messages (all marked is_idea=true):
┌───────────────────────────────────────────────────────┐
│ Message A: id="abc", parent_id=null                   │  ✅ ROOT
│ Message B: id="def", parent_id="t1_abc"               │  ✅ Valid chain
│ Message C: id="ghi", parent_id="t1_def"               │  ✅ Valid chain
│ Message D: id="jkl", parent_id="t1_xyz"               │  ❌ Broken (xyz not in dataset)
│ Message E: id="mno", parent_id="t1_jkl"               │  ❌ Broken (parent is broken)
└───────────────────────────────────────────────────────┘

Chain Validation Process:
• Message A: has_path_to_root() → TRUE (is root)
• Message B: has_path_to_root() → follows to A → TRUE
• Message C: has_path_to_root() → follows to B → follows to A → TRUE
• Message D: has_path_to_root() → parent "xyz" not found → FALSE
• Message E: has_path_to_root() → follows to D (broken) → FALSE

Output: Only Messages A, B, C are written to chains.parquet
```

## Performance Characteristics

- **Sequential Processing**: Processes one subreddit at a time to support checkpointing
- **Checkpoint/Resume**: Saves progress after each subreddit in `checkpoint/phase3_progress.json`
- **Memory Efficient**: Processes one subreddit at a time
- **Handles Corrupted Files**: Skips bad files with warnings
- **Progress Tracking**: Real-time progress bars with indicatif

**Checkpoint File Location**: `/Users/teomiscia/web/business-finder/rust/checkpoint/phase3_progress.json`

If interrupted, the program will automatically resume from the last completed subreddit when restarted.

## Usage

```bash
# Build
cd rust/phase3_chains
cargo build --release

# Run
cargo run --release

# Or use the build script
./build.sh
```

## Expected Output

```
╔══════════════════════════════════════════════════════════╗
║   Phase 3: Building Message Chains from Ideas           ║
╚══════════════════════════════════════════════════════════╝
INFO  📂 Scanning for subreddit directories...
INFO  ✓ Found 15432 subreddit directories
█▓▒░ [00:05:23] [████████████████████████] 15432/15432 (00:00:00) Processing r/AskReddit
INFO  ✓ Wrote 1234 chain messages to /Volumes/2TBSSD/reddit/chains/01/AskReddit/chains.parquet
...
╔══════════════════════════════════════════════════════════╗
║   Phase 3: Complete!                                     ║
╚══════════════════════════════════════════════════════════╝
```
