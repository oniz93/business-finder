#!/usr/bin/env python3
"""
Count total rows in all Parquet files within a directory using DuckDB.
"""

import argparse
import duckdb
import os
import sys

DEFAULT_DIR = "/Volumes/2TBSSD/reddit/processed"

def count_rows(directory: str):
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)

    print(f"Scanning directory: {directory}")
    
    # Use recursive glob pattern to find all parquet files
    pattern = os.path.join(directory, "**", "*.parquet")
    
    query = f"SELECT COUNT(*) FROM read_parquet('{pattern}')"
    
    try:
        print("Executing DuckDB query...")
        result = duckdb.sql(query).fetchone()
        count = result[0] if result else 0
        print(f"Total Rows: {count:,}")
    except duckdb.Error as e:
        print(f"DuckDB Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Count rows in Parquet files recursively.")
    parser.add_argument(
        "directory", 
        nargs="?", 
        default=DEFAULT_DIR, 
        help=f"Directory to scan (default: {DEFAULT_DIR})"
    )
    
    args = parser.parse_args()
    count_rows(args.directory)

if __name__ == "__main__":
    main()
