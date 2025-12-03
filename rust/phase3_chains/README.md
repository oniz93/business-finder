# Phase 3: Message Chains Builder

## Overview

This Rust program processes the classified Reddit data from Phase 2 and builds complete message chains for ideas. It filters out incomplete chains and keeps only messages that form a complete thread ending with a root message (parent_id = null).

## Purpose

The Phase 3 program solves the problem of fragmented conversation threads by:

1. **Filtering for Ideas**: Reading only messages classified as `is_idea = true` by the NLP model
2. **Building Chains**: Reconstructing parent-child relationships using the `parent_id` field
3. **Validating Completeness**: Keeping only messages that have a complete chain to a root message
4. **Preserving Context**: Ensuring that every idea in the output has its full conversation context

This is similar to the SQL recursive function `get_message_thread_bodies` from the previous version, but optimized for the new Parquet-based architecture.

## Algorithm

For each subreddit:

1. **Scan** all Parquet files in the subreddit directory
2. **Filter** for messages where `is_idea = true`
3. **Build** a hashmap of message ID → MessageNode
4. **Validate** each message by recursively checking if it has a path to a root (parent_id = null)
5. **Filter** the DataFrame to keep only messages with valid chains
6. **Write** the results to `/Volumes/2TBSSD/reddit/chains/{prefix}/{subreddit}/chains.parquet`

## Checkpoint & Resume

The program automatically saves progress after processing each subreddit to:
```
/Users/teomiscia/web/business-finder/rust/checkpoint/phase3_progress.json
```

**If the program is interrupted**, simply restart it and it will resume from the last completed subreddit. This is crucial for processing large datasets that may take hours or days.

The checkpoint file contains:
```json
{
  "subreddit_index": 1234
}
```

To **start fresh**, delete the checkpoint file:
```bash
rm /Users/teomiscia/web/business-finder/rust/checkpoint/phase3_progress.json
```


## Directory Structure

**Input**: `/Volumes/2TBSSD/reddit/processed/{prefix}/{subreddit}/*.parquet`

**Output**: `/Volumes/2TBSSD/reddit/chains/{prefix}/{subreddit}/chains.parquet`

The output maintains the same prefix/subreddit directory structure as the input.

## Schema

The output Parquet files contain all the same columns as the input:
- `id`: Unique message ID
- `parent_id`: Parent message ID (null for root messages)
- `link_id`: The submission/post this comment belongs to
- `subreddit`: Subreddit name
- `author`: Reddit username
- `body`: Message text
- `permalink`: Reddit permalink URL
- `created_utc`: Timestamp
- `ups`, `downs`: Vote counts
- `sanitized_prefix`: Hash prefix
- `cpu_filter_is_idea`: Fast heuristic filter result
- `is_idea`: NLP classification result
- `nlp_top_score`: NLP confidence score

## Building and Running

```bash
cd rust/phase3_chains
cargo build --release
cargo run --release
```

## Performance

- **Sequential Processing**: Processes subreddits one at a time to enable checkpoint/resume functionality
- **Checkpoint Support**: Automatically saves progress after each subreddit, allowing safe interruption and resumption
- **Efficient DataFrame Operations**: Uses **Polars** for fast in-memory processing
- **Progress Tracking**: Real-time progress bars with indicatif showing current subreddit and ETA
- **Error Handling**: Gracefully handles corrupted files with warnings and continues processing

## Comparison to PostgreSQL Function

The original PostgreSQL function `get_message_thread_bodies` used a recursive CTE to:
1. Start from a specific message
2. Recursively find all parent messages
3. Concatenate the bodies
4. Return empty string if chain was broken

Phase 3 performs a similar operation but:
- Processes entire datasets instead of single messages
- Keeps all columns instead of just concatenated bodies
- Outputs structured Parquet files for further processing
- Validates chains upfront instead of at query time

## Next Steps

The output from Phase 3 can be used for:
- **Embedding Generation**: Creating vector embeddings of complete conversation chains
- **Clustering**: Grouping similar conversation threads
- **Business Plan Generation**: Using complete context for LLM prompts
