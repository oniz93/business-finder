# In file: src/phase1_ingestion.py

import gc
import os
import json
import polars as pl
import zstandard as zstd
import config
import sys
from io import BytesIO
from src.utils import sanitize_for_filesystem
from src.log_utils import setup_timestamped_logging
from typing import Dict, Any, Iterator

# --- Main Streaming Function (Optimized Version) ---

def stream_processed_chunks(file_info: Dict[str, str]) -> Iterator[pl.DataFrame]:
    """
    Reads a raw data file, processes it in chunks by offloading JSON parsing
    to Polars for high performance, applies filters, and yields each processed
    chunk as a Polars DataFrame. This approach is both fast and memory-safe.
    """
    file_path = file_info['path']
    item_type = file_info['type']
    print(f"[Phase 1] Streaming from {item_type} file: {os.path.basename(file_path)}")

    # Choose the correct streamer generator
    if file_path.endswith('.zst'):
        line_stream = stream_zst_lines(file_path)
    elif file_path.endswith('.jsonl'):
        line_stream = stream_jsonl_lines(file_path)
    else:
        print(f"[Phase 1] Skipping unsupported file type: {file_path}")
        return

    # Define the schema to ensure consistency and speed up parsing
    schema = {
        'id': pl.Utf8, 'name': pl.Utf8, 'link_id': pl.Utf8, 'parent_id': pl.Utf8,
        'subreddit': pl.Utf8, 'author': pl.Utf8, 'title': pl.Utf8, 'selftext': pl.Utf8,
        'body': pl.Utf8, 'permalink': pl.Utf8, 'created_utc': pl.Float64,
        'ups': pl.Float64, 'downs': pl.Float64, 'distinguished': pl.Utf8
    }

    while True:
        # 1. Read raw JSON strings into a chunk
        chunk_lines = [line for _, line in zip(range(config.CHUNK_SIZE), line_stream)]
        if not chunk_lines:
            break

        # 2. Create a Polars Series from the lines. This is memory efficient.
        json_series = pl.Series("json_str", chunk_lines, dtype=pl.Utf8)

        # 3. Use `json_decode` with a predefined schema. This is a fast, vectorized operation.
        # It robustly handles parsing errors by producing `null` for invalid JSON strings.
        # By providing a `dtype`, we instruct Polars to only parse the fields we care about
        # and ignore any extra fields (like 'poll_data'), preventing schema inference errors.
        struct_series = json_series.str.json_decode(dtype=pl.Struct(schema))

        # 4. Filter out the nulls from parsing errors and unnest the structs into a DataFrame.
        # The resulting DataFrame will already have the correct schema because we provided it.
        df_chunk = pl.DataFrame(struct_series.drop_nulls()).unnest("json_str")

        if df_chunk.height == 0:
            print(f"[Phase 1] Chunk processed. No valid JSON objects found.")
            continue

        # 3. Normalize & Filter Data (This logic remains unchanged)
        if item_type == 'submission':
            df_chunk = df_chunk.select([
                pl.col('id').fill_null('').alias('id'),
                pl.col('name').fill_null('').alias('link_id'),
                pl.lit(None, dtype=pl.Utf8).alias('parent_id'),
                pl.col('subreddit').fill_null('').alias('subreddit'),
                pl.col('author').fill_null('').alias('author'),
                (pl.col('title').fill_null('') + '\n' + pl.col('selftext').fill_null('')).alias('body'),
                pl.col('permalink').fill_null('').alias('permalink'),
                pl.col('created_utc').fill_null(0).alias('created_utc'),
                pl.col('ups').fill_null(0).alias('ups'),
                pl.col('downs').fill_null(0).alias('downs'),
                pl.col('distinguished').fill_null('').alias('distinguished')
            ])
        elif item_type == 'comment':
            # This selection is much simpler now as we don't have title/selftext
            df_chunk = df_chunk.select([
                pl.col('id').fill_null('').alias('id'),
                pl.col('link_id').fill_null('').alias('link_id'),
                pl.col('parent_id').fill_null('').alias('parent_id'),
                pl.col('subreddit').fill_null('').alias('subreddit'),
                pl.col('author').fill_null('').alias('author'),
                pl.col('body').fill_null('').alias('body'),
                pl.col('permalink').fill_null('').alias('permalink'),
                pl.col('created_utc').fill_null(0).alias('created_utc'),
                pl.col('ups').fill_null(0).alias('ups'),
                pl.col('downs').fill_null(0).alias('downs'),
                pl.col('distinguished').fill_null('').alias('distinguished')
            ])
        else:
            continue

        # All subsequent filtering logic is identical to your original code
        df_chunk = df_chunk.with_columns([
            pl.col("subreddit").str.slice(0, 2).alias("subreddit_prefix"),
            pl.from_epoch("created_utc", time_unit="s").dt.strftime("%m%y").alias("mmyy")
        ])
        df_chunk = df_chunk.with_columns(
            pl.col("subreddit_prefix").map_elements(sanitize_for_filesystem).alias("sanitized_prefix")
        )
        df_chunk = df_chunk.filter(~pl.col("author").str.contains("bot", literal=True))
        df_chunk = df_chunk.filter(~pl.col("distinguished").is_in(["moderator", "admin"]))
        df_chunk = df_chunk.filter(~pl.col("body").str.contains(config.EXCLUDE_PATTERN_STRING, literal=False))
        engagement_score = (pl.col("ups") * 0.8 + pl.col("body").str.len_chars() * 0.2)
        df_chunk = df_chunk.with_columns(engagement_score.alias("engagement_quality"))
        df_chunk = df_chunk.filter(pl.col("engagement_quality") > 5)
        df_chunk = df_chunk.with_columns([
            pl.col("body").str.contains(config.IDEA_KEYWORD_PATTERN_STRING, literal=False).alias("cpu_filter_is_idea"),
            pl.lit(False, dtype=pl.Boolean).alias("is_idea"),
            pl.lit(None, dtype=pl.Float32).alias("nlp_top_score")
        ])
        df_chunk = df_chunk.drop(['distinguished', 'engagement_quality'])

        print(f"[Phase 1] Chunk processed. {df_chunk.height} rows survived filtering.")
        if df_chunk.height > 0:
            yield df_chunk
        
        gc.collect()

# --- Helper Generators (to yield raw string lines) ---

def stream_zst_lines(file_path: str) -> Iterator[str]:
    """Creates a generator to stream raw string lines from a .zst file."""
    with open(file_path, 'rb') as f:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(f) as reader:
            buffer = ''
            while True:
                try:
                    chunk = reader.read(16384).decode('utf-8', errors='replace')
                except zstd.ZstdError as e:
                    print(f"[Worker] Error reading zst chunk from {os.path.basename(file_path)}: {e}")
                    break
                if not chunk:
                    break
                
                buffer += chunk
                lines = buffer.split('\n')
                buffer = lines.pop()
                for line in lines:
                    yield line
            if buffer:
                yield buffer

def stream_jsonl_lines(file_path: str) -> Iterator[str]:
    """Creates a generator to stream raw string lines from a .jsonl file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            yield line.strip()