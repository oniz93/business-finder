# Phase 3 Chains - Major Refactoring

## Summary of Changes

I've completely rewritten `src/main.rs` with the following major improvements:

### 1. ✅ Skip Subreddit Scan if Checkpoint Exists

- **New checkpoint file**: `rust/checkpoint/subreddits_list.json`
- On first run, scans all subreddits and saves the list to this file
- On subsequent runs, loads from the cached list instead of rescanning
- Saves significant time on restart

### 2. ✅ Fixed Chain Logic

**Previous (WRONG) behavior:**
- Only looked at `is_idea=true` messages when building chains
- If a parent message was not an idea, the chain would be broken

**New (CORRECT) behavior:**
- Only `is_idea=true` messages are in the **final output**
- BUT when tracing parent chains, we look at **ALL messages** (both ideas and non-ideas)
- This ensures we can properly validate complete chains even if intermediate parents aren't ideas

### 3. ✅ DuckDB Integration for Memory Efficiency

**Previous approach:**
- Loaded all messages into memory as Polars DataFrames
- Built HashMap of all messages
- Memory intensive for large subreddits

**New approach:**
- Uses DuckDB in-memory database
- Loads all messages from parquet files into DuckDB table
- Performs efficient SQL lookups when tracing parent chains
- Much better for subreddits with hundreds of millions of messages

### 4. ✅ Chunked Processing of Ideas

**Previous approach:**
- Processed all ideas at once
- Kept all valid IDs in memory simultaneously

**New approach:**
- Processes `is_idea=true` messages in chunks of 10,000
- For each chunk:
  1. Read 10,000 idea IDs from DuckDB
  2. Validate their chains
  3. Add valid IDs to HashSet
  4. Move to next chunk
- After all chunks processed, write all valid chains to output parquet
- Frees memory between chunks

### 5. ✅ Single Subreddit Mode

**New CLI argument:**
```bash
# Process all subreddits (default)
cargo run --release

# Process ONLY a specific subreddit
cargo run --release -- --subreddit AskReddit
```

When using `--subreddit`:
- Skips checkpoint system
- Skips scanning all subreddits
- Directly finds and processes the specified subreddit
- Useful for testing or reprocessing specific subreddits

## Technical Details

### New Dependencies

Added to `Cargo.toml`:
- `duckdb = { version = "1.1", features = ["bundled"] }` - For efficient database operations
- `clap = { version = "4.4", features = ["derive"] }` - For CLI argument parsing

### Key Functions

1. **`has_complete_chain()`**
   - Traces parent chain recursively using DuckDB
   - Looks at ALL messages (not just ideas)
   - Returns true only if chain reaches root (parent_id = null)
   - Detects circular references

2. **`process_subreddit()`**
   - Creates in-memory DuckDB connection
   - Loads all parquet files into a single table
   - Counts total ideas
   - Processes ideas in chunks of 10,000
   - Writes valid chains to output

3. **`write_valid_chains()`**
   - Creates temporary table with valid IDs
   - Uses SQL JOIN to filter messages
   - Uses DuckDB's `COPY TO` for efficient parquet export
   - Only exports `is_idea=true` messages with valid chains

## Usage

```bash
cd rust/phase3_chains

# Build the project
cargo build --release

# Run on all subreddits (uses checkpoints)
cargo run --release

# Run on a specific subreddit
cargo run --release -- --subreddit technology

# Check progress
cat rust/checkpoint/phase3_progress.json

# Check cached subreddits list
cat rust/checkpoint/subreddits_list.json

# Reset everything
rm rust/checkpoint/phase3_progress.json
rm rust/checkpoint/subreddits_list.json
```

## Performance Benefits

1. **Subreddit scanning**: Only done once, cached for future runs
2. **Memory usage**: Constant per chunk (10,000 ideas) instead of all at once
3. **Database lookups**: DuckDB SQL much faster than HashMap for large datasets
4. **Single subreddit mode**: Can reprocess one subreddit without scanning all

## Migration Notes

- Delete old checkpoint if you want to regenerate the subreddits list
- The output format is unchanged - still writes to `/Volumes/2TBSSD/reddit/chains/`
- All schema columns preserved from Phase 2

## Testing

To test on a small subreddit:
```bash
cargo run --release -- --subreddit [small_subreddit_name]
```

## Next Steps

After this builds successfully, you can:
1. Test with a small subreddit using `--subreddit` flag
2. Run the full pipeline with checkpointing
3. Monitor memory usage during chunked processing
