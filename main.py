import os
import shutil
import glob
from tqdm import tqdm
import config
import polars as pl
from src.utils import discover_files
from src.phase1_ingestion import stream_processed_chunks
from src.phase1_5_partitioning import main_phase_1_5
from src.phase2_nlp import main_nlp_phase
from src.log_utils import setup_timestamped_logging
from collections import defaultdict
import uuid

def main():
    """
    Main script to orchestrate the ingestion and filtering phase.
    """
    setup_timestamped_logging()
    # print("--- Starting Phase 1: Ingestion, Filtering & Parquet Creation ---")

    # os.makedirs(config.INTERMEDIATE_DATA_DIR, exist_ok=True)
    # os.makedirs(config.PROCESSED_DATA_DIR, exist_ok=True)

    # files_to_process = discover_files()
    # if not files_to_process:
    #     print("No data files found. Please place .zst or .jsonl files in the directory specified by RAW_DATA_DIR in config.py")
    #     return

    # print("Starting sequential processing for Phase 1...")
    
    # # --- New Partitioned Accumulation Logic ---
    # accumulator_by_prefix = defaultdict(list)
    # rows_by_prefix = defaultdict(int)
    # ROW_LIMIT = 5

    # # Loop through each raw file
    # for file_info in tqdm(files_to_process, desc="Phase 1: Processing raw files"):
    #     # Get a stream of processed chunks from the file
    #     for df_chunk in stream_processed_chunks(file_info):
            
    #         # Group chunk by sanitized_prefix
    #         grouped = df_chunk.group_by("sanitized_prefix")

    #         for prefix_tuple, data in grouped:
    #             prefix = prefix_tuple[0]
    #             if not prefix:
    #                 prefix = "misc" # Handle cases with no prefix

    #             accumulator_by_prefix[prefix].append(data)
    #             rows_by_prefix[prefix] += data.height
    #             print(f"[Phase 1] Accumulator for prefix '{prefix}' has {rows_by_prefix[prefix]} messages.")

    #             # If we have enough rows for this prefix, write a parquet file
    #             if rows_by_prefix[prefix] >= ROW_LIMIT:
    #                 combined_df = pl.concat(accumulator_by_prefix[prefix])
                    
    #                 output_dir = os.path.join(config.INTERMEDIATE_DATA_DIR, prefix)
    #                 os.makedirs(output_dir, exist_ok=True)
                    
    #                 output_file = os.path.join(output_dir, f"part-{uuid.uuid4()}.parquet")
                    
    #                 combined_df.write_parquet(output_file, compression='zstd')
    #                 print(f"[Phase 1] Wrote {combined_df.height} rows to {output_file}")

    #                 # Reset accumulator for this prefix
    #                 del accumulator_by_prefix[prefix]
    #                 del rows_by_prefix[prefix]

    # # Write any remaining data in the accumulator after all files are processed
    # for prefix, df_list in accumulator_by_prefix.items():
    #     if df_list:
    #         combined_df = pl.concat(df_list)
            
    #         output_dir = os.path.join(config.INTERMEDIATE_DATA_DIR, prefix)
    #         os.makedirs(output_dir, exist_ok=True)
            
    #         output_file = os.path.join(output_dir, f"part-{uuid.uuid4()}.parquet")
            
    #         combined_df.write_parquet(output_file, compression='zstd')
    #         print(f"[Phase 1] Wrote remaining {combined_df.height} rows for prefix '{prefix}' to {output_file}")


    # print("--- Phase 1 Complete ---")

    # --- New Compaction Step ---
    print("--- Starting Phase 1 Compaction ---")
    compaction_row_limit = 1_000_000
    
    # Find all prefix directories
    prefix_dirs = [d for d in os.listdir(config.INTERMEDIATE_DATA_DIR) if os.path.isdir(os.path.join(config.INTERMEDIATE_DATA_DIR, d))]
    prefix_dirs.sort()
    for prefix in tqdm(prefix_dirs, desc="Compacting prefixes"):
        prefix_path = os.path.join(config.INTERMEDIATE_DATA_DIR, prefix)
        
        # Get all small parquet files, the ones starting with "part-"
        original_files = glob.glob(os.path.join(prefix_path, 'inter-*.parquet'))
        if not original_files:
            continue

        print(f"[Compaction] Compacting {len(original_files)} files in {prefix_path}")

        valid_dfs = []
        files_to_compact = []
        for f in original_files:
            try:
                if os.path.getsize(f) == 0:
                    print(f"[Compaction] Skipping empty file: {f}")
                    continue
                df = pl.read_parquet(f)
                valid_dfs.append(df)
                files_to_compact.append(f)
            except Exception as e:
                print(f"[Compaction] Skipping invalid file {f} due to error: {e}")

        if not valid_dfs:
            print(f"[Compaction] No valid files to compact for prefix {prefix}.")
            continue
        
        try:
            combined_df = pl.concat(valid_dfs)
            
            if combined_df.height == 0:
                print(f"[Compaction] No data to write for prefix {prefix}.")
                print(f"[Compaction] Cleaning up {len(files_to_compact)} processed empty files.")
                for f in files_to_compact:
                    os.remove(f)
                continue

            # Write back in larger chunks
            if combined_df.height <= compaction_row_limit:
                # Write as a single new file
                output_file = os.path.join(prefix_path, f"compacted-{uuid.uuid4()}.parquet")
                combined_df.write_parquet(output_file, compression='zstd')
                print(f"[Compaction] Wrote {combined_df.height} rows to {output_file}")
            else:
                # Split into multiple files
                for i in range(0, combined_df.height, compaction_row_limit):
                    chunk_df = combined_df.slice(i, compaction_row_limit)
                    output_file = os.path.join(prefix_path, f"compacted-{uuid.uuid4()}_part_{i//compaction_row_limit}.parquet")
                    chunk_df.write_parquet(output_file, compression='zstd')
                    print(f"[Compaction] Wrote {chunk_df.height} rows to {output_file}")
            
            # If write is successful, remove the files that were compacted.
            print(f"[Compaction] Successfully compacted. Removing {len(files_to_compact)} original files.")
            for f in files_to_compact:
                os.remove(f)

        except Exception as e:
            print(f"[Compaction] Error during writing or cleanup for {prefix_path}: {e}. Original files are kept.")

    print("--- Phase 1 Compaction Complete ---")

    # print(f"Intermediate data is available in: {config.INTERMEDIATE_DATA_DIR}")

    # # --- Starting Phase 1.5: Repartitioning Data ---
    # main_phase_1_5()

    # --- Starting Phase 2: NLP Enrichment ---
    #main_nlp_phase()

if __name__ == "__main__":
    main()