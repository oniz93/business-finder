import os
import duckdb
import polars as pl
import config
import glob
import uuid
import multiprocessing
from src.utils import DirectoryLock, sanitize_for_filesystem
from src.log_utils import setup_timestamped_logging
from tqdm import tqdm

# Number of processes to use for parallel processing. User requested 8 or 16.
NUM_PROCESSES = 16

def find_subreddits_to_process() -> list[str]:
    """
    Uses DuckDB to find distinct subreddits from the intermediate Parquet files.
    """
    print("[Phase 1.5] Discovering subreddits from intermediate files...")
    
    # Ensure the intermediate directory exists to avoid errors
    if not os.path.exists(config.INTERMEDIATE_DATA_DIR):
        print("[Phase 1.5] Intermediate data directory not found. Skipping.")
        return []

    query = f"""
        SELECT DISTINCT subreddit
        FROM read_parquet('{config.INTERMEDIATE_DATA_DIR}/**/*.parquet')
    """
    try:
        with duckdb.connect(database=':memory:') as con:
            result = con.execute(query).fetchall()
        subreddits = [row[0] for row in result if row[0]]
        print(f"[Phase 1.5] Found {len(subreddits)} subreddits to partition.")
        return subreddits
    except duckdb.Error as e:
        print(f"[Phase 1.5] DuckDB error while finding subreddits: {e}")
        return []

def process_subreddit_for_partitioning(subreddit_name: str):
    """
    - Loads all data for a given subreddit from the intermediate files.
    - Partitions the data by month/year.
    - Writes the data to the final processed directory, consolidating with existing files.
    """
    # Deduce the prefix directory from the subreddit name
    if not subreddit_name:
        prefix_dir = "misc"
    else:
        prefix = subreddit_name[:2]
        prefix_dir = sanitize_for_filesystem(prefix)

    parquet_path = os.path.join(config.INTERMEDIATE_DATA_DIR, prefix_dir, '*.parquet')

    # 1. Load all data for the subreddit from intermediate files
    try:
        # Check if any files exist before trying to read, as duckdb might error on an empty glob
        if not glob.glob(parquet_path):
            return

        with duckdb.connect(database=':memory:') as con:
            query = f"""
                SELECT *
                FROM read_parquet('{parquet_path}')
                WHERE subreddit = ?
            """
            df_subreddit = con.execute(query, [subreddit_name]).pl()
    except duckdb.Error as e:
        print(f"[Phase 1.5] DuckDB error processing subreddit {subreddit_name}: {e}")
        return

    if df_subreddit.height == 0:
        return

    # 2. Group by the partitioning columns (already present from Phase 1)
    grouped = df_subreddit.group_by(["sanitized_prefix", "subreddit", "mmyy"])

    for (sanitized_prefix, subreddit, mmyy), data in grouped:
        output_dir = os.path.join(
            config.PROCESSED_DATA_DIR,
            sanitize_for_filesystem(sanitized_prefix),
            sanitize_for_filesystem(subreddit),
            sanitize_for_filesystem(mmyy)
        )
        os.makedirs(output_dir, exist_ok=True)

        try:
            with DirectoryLock(output_dir):
                # Consolidate with existing data in the partition
                existing_files = glob.glob(os.path.join(output_dir, "*.parquet"))
                
                if existing_files:
                    existing_df = pl.read_parquet(existing_files)
                    merged_df = pl.concat([existing_df, data])
                else:
                    merged_df = data

                # Write data to temporary files, splitting if it's too large
                ROW_LIMIT = 100_000
                if merged_df.height == 0:
                    continue

                temp_files = []
                if merged_df.height < ROW_LIMIT:
                    temp_file = os.path.join(output_dir, f"{uuid.uuid4()}.parquet.tmp")
                    merged_df.write_parquet(temp_file) # No brotli here, keep it fast
                    temp_files.append(temp_file)
                else:
                    for i in range(0, merged_df.height, ROW_LIMIT):
                        chunk_df = merged_df.slice(i, ROW_LIMIT)
                        temp_file = os.path.join(output_dir, f"{uuid.uuid4()}_part_{i//ROW_LIMIT}.parquet.tmp")
                        chunk_df.write_parquet(temp_file)
                        temp_files.append(temp_file)
                
                # Atomically replace old files with new ones
                for f in existing_files:
                    os.remove(f)
                
                for tmp_f in temp_files:
                    final_path = tmp_f.replace(".tmp", "")
                    os.rename(tmp_f, final_path)
                
        except Exception as e:
            print(f"[Phase 1.5] ERROR consolidating Parquet for group {sanitized_prefix}/{subreddit}/{mmyy}: {e}")

def main_phase_1_5():
    """
    Orchestrates the repartitioning phase.
    """
    setup_timestamped_logging()
    print("--- Starting Phase 1.5: Repartitioning Data ---")
    os.makedirs(config.PROCESSED_DATA_DIR, exist_ok=True)

    subreddits = find_subreddits_to_process()
    if not subreddits:
        print("[Phase 1.5] No subreddits found to process. Phase complete.")
        return

    # Process subreddits in parallel
    print(f"[Phase 1.5] Starting partitioning with {NUM_PROCESSES} processes.")
    with multiprocessing.Pool(processes=NUM_PROCESSES) as pool:
        list(tqdm(pool.imap_unordered(process_subreddit_for_partitioning, subreddits), total=len(subreddits), desc="Phase 1.5: Partitioning subreddits"))

    print("--- Phase 1.5 Complete ---")

if __name__ == "__main__":
    # This allows running the phase independently for debugging
    main_phase_1_5()
