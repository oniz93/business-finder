import os
import glob
from typing import List, Dict
import config
import re
import time
import errno

class DirectoryLock:
    """
    A simple file-based lock for a directory to prevent race conditions
    in a multiprocessing environment.
    """
    def __init__(self, dir_path, timeout=60):
        self.lock_file = os.path.join(dir_path, ".lock")
        self.dir_path = dir_path
        self.timeout = timeout
        self.fd = None

    def acquire(self):
        start_time = time.time()
        while True:
            try:
                os.makedirs(self.dir_path, exist_ok=True)
                self.fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                if time.time() - start_time >= self.timeout:
                    raise TimeoutError(f"Could not acquire lock for {self.dir_path} within {self.timeout}s")
                time.sleep(0.5)

    def release(self):
        if self.fd is not None:
            os.close(self.fd)
            os.remove(self.lock_file)
            self.fd = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

def sanitize_for_filesystem(text: str) -> str:
    """
    Sanitizes a string to be filesystem-compatible by keeping only
    alphanumeric characters, hyphens, and underscores.
    """
    if not text:
        return "_"
    return re.sub(r'[^A-Za-z0-9\-_]', '', text).lower()

def discover_files() -> List[Dict[str, str]]:
    """
    Dynamically finds all .zst and .jsonl files in the raw data directory.
    Returns a list of dictionaries, each containing the file path and its type.
    """
    all_files = []
    
    # Scan for .zst files (assumed to be comments or submissions)
    for zst_file in glob.glob(os.path.join(config.RAW_DATA_DIR, "**", "*.zst"), recursive=True):
        filename = os.path.basename(zst_file)
        if filename.startswith("RS"):
            item_type = "submission"
        elif filename.startswith("RC"):
            item_type = "comment"
        else:
            item_type = "unknown"
        all_files.append({"path": zst_file, "type": item_type})

    # Scan for .jsonl files
    for jsonl_file in glob.glob(os.path.join(config.RAW_DATA_DIR, "**", "*.jsonl"), recursive=True):
        # Simple assumption, could be refined if needed
        if "submission" in jsonl_file.lower():
             item_type = "submission"
        else:
            item_type = "comment"
        all_files.append({"path": jsonl_file, "type": item_type})
        
    print(f"Discovered {len(all_files)} files to process in {config.RAW_DATA_DIR}")
    return all_files