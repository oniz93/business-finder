#!/usr/bin/env python3
"""
Find and optionally fix/remove corrupted parquet files.
Also cleans up leftover temporary files from crashes.
"""

import os
import sys
from pathlib import Path
import pyarrow.parquet as pq

DATA_DIR = Path("/Volumes/2TBSSD/reddit/processed")

def check_parquet_file(file_path):
    """Check if a parquet file is valid."""
    try:
        # Try to read the metadata (doesn't load data, just checks header/footer)
        pq.read_metadata(file_path)
        return True, None
    except Exception as e:
        return False, str(e)

def find_issues(data_dir, fix=False):
    """Find corrupted parquet files and leftover temp files."""
    corrupted = []
    temp_files = []
    
    print(f"Scanning {data_dir} for issues...")
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            file_path = Path(root) / file
            
            # Check for temporary files
            if '.tmp.' in file:
                temp_files.append(file_path)
                continue
            
            # Check parquet files
            if file.endswith('.parquet'):
                is_valid, error = check_parquet_file(file_path)
                if not is_valid:
                    corrupted.append((file_path, error))
    
    # Report findings
    print(f"\n{'='*80}")
    print(f"SCAN RESULTS")
    print(f"{'='*80}")
    print(f"Corrupted parquet files: {len(corrupted)}")
    print(f"Leftover temp files: {len(temp_files)}")
    
    if corrupted:
        print(f"\n{'='*80}")
        print(f"CORRUPTED FILES:")
        print(f"{'='*80}")
        for file_path, error in corrupted:
            print(f"\n📛 {file_path}")
            print(f"   Error: {error[:100]}...")
            
            if fix:
                # Check if there's a temp file for this
                temp_pattern = f"{file_path}.tmp.*"
                temp_candidates = list(file_path.parent.glob(f"{file_path.name}.tmp.*"))
                
                if temp_candidates:
                    print(f"   ✓ Found temp file(s): {len(temp_candidates)}")
                    # Use the most recent temp file
                    temp_file = max(temp_candidates, key=lambda p: p.stat().st_mtime)
                    print(f"   → Checking temp file: {temp_file.name}")
                    
                    is_valid, _ = check_parquet_file(temp_file)
                    if is_valid:
                        print(f"   ✓ Temp file is valid! Restoring...")
                        os.replace(temp_file, file_path)
                        print(f"   ✅ Restored from temp file")
                    else:
                        print(f"   ✗ Temp file is also corrupted. Deleting both...")
                        file_path.unlink()
                        temp_file.unlink()
                        print(f"   ✅ Deleted corrupted files")
                else:
                    print(f"   ✗ No temp file found. Deleting corrupted file...")
                    file_path.unlink()
                    print(f"   ✅ Deleted")
    
    if temp_files:
        print(f"\n{'='*80}")
        print(f"LEFTOVER TEMP FILES:")
        print(f"{'='*80}")
        for temp_file in temp_files:
            print(f"\n🗑️  {temp_file}")
            
            # Check if the corresponding original file exists
            original_name = str(temp_file).split('.tmp.')[0]
            original_path = Path(original_name)
            
            if original_path.exists():
                print(f"   Original file exists")
                if fix:
                    print(f"   → Deleting redundant temp file...")
                    temp_file.unlink()
                    print(f"   ✅ Deleted")
            else:
                print(f"   ⚠️  Original file missing!")
                is_valid, _ = check_parquet_file(temp_file)
                if is_valid and fix:
                    print(f"   → Temp file is valid. Restoring as original...")
                    os.rename(temp_file, original_path)
                    print(f"   ✅ Restored")
                elif fix:
                    print(f"   → Temp file is corrupted. Deleting...")
                    temp_file.unlink()
                    print(f"   ✅ Deleted")
    
    print(f"\n{'='*80}")
    if fix:
        print(f"Cleanup complete!")
    else:
        print(f"Scan complete. Run with --fix to automatically repair/remove files.")
    print(f"{'='*80}\n")

def main():
    fix = '--fix' in sys.argv
    
    if not DATA_DIR.exists():
        print(f"Error: Data directory not found: {DATA_DIR}")
        sys.exit(1)
    
    if fix:
        response = input(f"\n⚠️  WARNING: This will DELETE corrupted files. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    find_issues(DATA_DIR, fix=fix)

if __name__ == "__main__":
    main()
