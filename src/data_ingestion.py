import sys
import os
import time
import gc
import glob
import pandas as pd
import psycopg2
import binascii
import io
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fileStreams import getFileJsonStream
from transformers import pipeline
import multiprocessing as mp
import torch
import re

# --- Configuration ---
# Multiprocessing
N_GPUS = torch.cuda.device_count() if torch.cuda.is_available() else 0
N_WORKERS = N_GPUS * 2 if N_GPUS > 0 else 16 # Use GPUs if available, else CPUs
N_CPU_PRODUCERS = 16 # Keep this separate
RAW_QUEUE_SIZE = 200000
DB_QUEUE_SIZE = 10000

# NLP
NLP_BATCH_SIZE = 512 # Smaller batch for mixed processing

# Database
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "reddit_threads"
DB_USER = "reddit_user"
DB_PASS = "reddit_password"

# File Paths & Logging
LOG_INTERVAL = 50000

def get_files_to_process(base_dir, year="2025", excluded_month="07"):
    """
    Dynamically finds reddit data files for a given year, excluding a specific month.
    """
    all_files = []
    
    # Submissions
    submission_pattern = os.path.join(base_dir, "submissions", f"RS_{year}-*.zst")
    for f in glob.glob(submission_pattern):
        if f"_{year}-{excluded_month}" not in os.path.basename(f):
            all_files.append({"path": f, "type": "submission"})
            
    # Comments
    comment_pattern = os.path.join(base_dir, "comments", f"RC_{year}-*.zst")
    for f in glob.glob(comment_pattern):
        if f"_{year}-{excluded_month}" not in os.path.basename(f):
            all_files.append({"path": f, "type": "comment"})
            
    return all_files

files_to_process = get_files_to_process("/home/coinsafe/business-finder/reddit-dumps/reddit", "2025", "00")

# --- Globals for Models and Keywords ---
_candidate_labels = ["pain_point", "idea"]
_pain_point_keywords = ["frustrating", "problem", "difficult", "struggle", "annoying", "wish", "need", "can't", "should be", "hard to", "lack of", "missing", "broken"]
_idea_keywords = ["idea", "solution", "concept", "opportunity", "build", "create", "develop", "imagine", "what if", "improve", "new way", "innovate"]

# Red flags that indicate low-quality "ideas"
EXCLUDE_PATTERNS = [
    r"why doesn't someone",     # Pure speculation
    r"wouldn't it be cool if",  # Fantasy thinking
    r"in a perfect world",      # Unrealistic
    r"they should just",        # Passive complaining
    r"if I won the lottery",    # Not serious
    r"magical solution",
    r"cure for cancer",         # Too ambitious/vague
    r"world peace",
    r"free .* for everyone"     # Economically naive
]

# --- Database Functions ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)

def setup_database():
    """Sets up the necessary partitioned table and indexes in the database."""
    print("--- Setting up database tables ---")
    conn = get_db_connection()
    cur = conn.cursor()

    print("Dropping old tables for a clean slate...")
    cur.execute("DROP TABLE IF EXISTS all_messages CASCADE;")
    cur.execute("DROP TABLE IF EXISTS interesting_messages CASCADE;")
    cur.execute("DROP TABLE IF EXISTS flagged_threads CASCADE;")

    print("Creating new partitioned table 'all_messages'...")
    cur.execute("""
        CREATE TABLE all_messages (
            id VARCHAR(20) NOT NULL,
            link_id VARCHAR(20),
            parent_id VARCHAR(20),
            trunc_link_id VARCHAR(20),
            trunc_parent_id VARCHAR(20),
            subreddit VARCHAR(100) NOT NULL,
            subreddit_prefix VARCHAR(2) NOT NULL,
            author VARCHAR(100),
            body TEXT,
            permalink TEXT,
            created_utc TIMESTAMP,
            ups INT,
            downs INT,
            is_idea BOOLEAN DEFAULT FALSE,
            nlp_top_score REAL,
            PRIMARY KEY (id, subreddit_prefix)
        ) PARTITION BY LIST (subreddit_prefix);
    """)

    print("Creating indexes on 'all_messages'...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_all_link_id ON all_messages USING HASH (link_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_all_trunc_link_id ON all_messages USING HASH (trunc_link_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_all_author ON all_messages (author);")

    conn.commit()
    cur.close()
    conn.close()
    print("Database setup complete. Partitions will be created automatically.")

# --- Data Parsing ---
def parse_reddit_item(item: Dict[str, Any], item_type: str) -> Optional[List[Any]]:
    """Normalizes a submission or comment into a standard list format for insertion."""
    subreddit = item.get('subreddit')
    if not subreddit or len(subreddit) < 2:
        return None

    prefix = subreddit[:2].lower()
    body = ""
    link_id = None
    parent_id = None

    if item_type == 'submission':
        body = item.get('title', '') + '\n' + item.get('selftext', '')
        link_id = item.get('name')  # For a submission, its name is the link_id
        parent_id = None # Submissions have no parent
    elif item_type == 'comment':
        body = item.get('body')
        link_id = item.get('link_id')
        parent_id = item.get('parent_id')
    else:
        return None

    if not body or not item.get('id'):
        return None

    created_utc_val = item.get('created_utc')
    formatted_timestamp = None
    if created_utc_val:
        try:
            # Convert Unix timestamp to a format Postgres' COPY will understand
            formatted_timestamp = datetime.fromtimestamp(int(created_utc_val), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            formatted_timestamp = None # Handle cases where timestamp is invalid

    return [
        item.get('id'),
        link_id,
        parent_id,
        link_id.split('_')[-1] if link_id and '_' in link_id else link_id,
        parent_id.split('_')[-1] if parent_id and '_' in parent_id else parent_id,
        subreddit,
        prefix,
        item.get('author'),
        body.strip(),
        item.get('permalink'),
        formatted_timestamp, # Use the formatted timestamp
        item.get('ups'),
        item.get('downs'),
        False,  # is_idea placeholder
        None    # nlp_top_score placeholder
    ]

# --- Worker Functions ---

_worker_classifier = None
def get_classifier(gpu_id: int):
    global _worker_classifier
    if _worker_classifier is None:
        if N_GPUS == 0:
            print("[Classifier] Initializing classifier on CPU")
            _worker_classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")
        else:
            physical_gpu_id = gpu_id % N_GPUS
            print(f"[Classifier-{gpu_id}] Initializing classifier on physical GPU: {physical_gpu_id}")
            _worker_classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli", device=physical_gpu_id)
    return _worker_classifier

def producer(raw_queue: mp.Queue, path: str, item_type: str):
    """Reads a dump file and puts items into a queue for the CPU filters."""
    print(f"[Producer] Starting data ingestion for file: {path}")
    count = 0
    with open(path, "rb") as f:
        json_stream = getFileJsonStream(path, f)
        if json_stream:
            for item in json_stream:
                raw_queue.put((item, item_type))
                count += 1
                if count % LOG_INTERVAL == 0: print(f"[Producer] Ingested {count:,} items from {os.path.basename(path)}")
    print(f"[Producer] Finished ingesting {count:,} items from {os.path.basename(path)}. Signaling end.")
    for _ in range(N_CPU_PRODUCERS): raw_queue.put(None)

def calculate_engagement_quality(item, item_type):
    """Score based on discussion quality, not just volume"""
    
    # Get the full thread
    ups = item.get('ups', 0)
    if ups is None: ups = 0
    
    # Penalize pure rants (high emotion, low constructive value)
    text = ""
    if item_type == 'submission':
        text = item.get('title', '') + '\n' + item.get('selftext', '')
    elif item_type == 'comment':
        text = item.get('body', '')

    if not text: return 0

    exclamation_ratio = text.count('!') / max(len(text), 1)
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    
    # Reward thoughtful, detailed posts
    has_concrete_details = bool(re.search(r'\$\d+|[0-9]+%|\d+ (users|customers|months)', text))
    word_count = len(text.split())
    
    # Calculate composite score
    quality_score = ups
    if exclamation_ratio > 0.05 or caps_ratio > 0.3:
        quality_score *= 0.5  # Likely emotional venting
    if has_concrete_details and word_count > 100:
        quality_score *= 1.5  # Detailed, data-driven
        
    return quality_score

def cpu_filter_worker(raw_queue: mp.Queue, db_queue: mp.Queue):
    """CPU worker that does initial filtering before passing to the main worker."""
    while True:
        item_tuple = raw_queue.get()
        if item_tuple is None:
            db_queue.put(None) # Pass the signal along
            break
        
        item, item_type = item_tuple

        author = item.get("author", "")
        distinguished = item.get("distinguished")

        if "bot" in author.lower() or distinguished in ["moderator", "admin"]:
            continue

        # Context-aware filtering (Idea #2)
        body = ""
        if item_type == 'submission':
            body = item.get('title', '') + '\n' + item.get('selftext', '')
        elif item_type == 'comment':
            body = item.get('body', '')

        if body and any(re.search(p, body, re.IGNORECASE) for p in EXCLUDE_PATTERNS):
            continue

        # Engagement quality filter (Idea #3)
        if calculate_engagement_quality(item, item_type) < 1:
            continue
        
        db_queue.put(item)

def db_and_nlp_worker(worker_id: int, db_queue: mp.Queue, item_type: str):
    """Receives items, parses them, conditionally runs NLP, and bulk-loads them into the DB using COPY."""
    print(f"[DB-NLP-Worker-{worker_id}] Starting for item type: {item_type}")
    classifier = get_classifier(worker_id)
    conn = get_db_connection()
    cur = conn.cursor()
    batch = []
    created_partitions = set()

    def process_batch(current_batch):
        if not current_batch: return

        # 1. Parse all items and prepare for NLP
        parsed_records = []
        for item in current_batch:
            parsed = parse_reddit_item(item, item_type)
            if parsed:
                parsed_records.append({"data": parsed, "original_item": item})

        # 2. Run NLP on items that have idea-related keywords
        nlp_indices = [i for i, rec in enumerate(parsed_records) if any(kw in rec["data"][8].lower() for kw in _idea_keywords)]
        if nlp_indices:
            texts_for_nlp = [parsed_records[i]["data"][8] for i in nlp_indices]
            try:
                results = classifier(texts_for_nlp, candidate_labels=_candidate_labels)
                for i, result in enumerate(results):
                    if result['labels'][0] == 'idea' and result['scores'][0] > 0.7:
                        original_index = nlp_indices[i]
                        parsed_records[original_index]["data"][13] = True  # is_idea
                        parsed_records[original_index]["data"][14] = result['scores'][0] # nlp_top_score
            except Exception as e:
                print(f"[DB-NLP-Worker-{worker_id}] Error during NLP: {e}")

        # 3. Group final records by subreddit prefix
        records_by_prefix = {}
        for record in parsed_records:
            prefix = record["data"][6]
            if prefix not in records_by_prefix:
                records_by_prefix[prefix] = []
            records_by_prefix[prefix].append(record["data"])

        # 4. For each prefix, ensure partition exists and then COPY data
        for prefix, records in records_by_prefix.items():
            safe_suffix = binascii.hexlify(prefix.encode('utf-8')).decode('ascii')
            partition_name = f"all_messages_{safe_suffix}"

            if prefix not in created_partitions:
                try:
                    cur.execute(f"CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF all_messages FOR VALUES IN (%s);", (prefix,))
                    conn.commit()
                    created_partitions.add(prefix)
                except psycopg2.errors.DuplicateTable:
                    conn.rollback()
                    created_partitions.add(prefix)
                except Exception as e:
                    print(f"[DB-NLP-Worker-{worker_id}] Error creating partition {partition_name} for prefix '{prefix}': {e}")
                    conn.rollback()
                    continue

            if records:
                try:
                    temp_table_name = f"temp_batch_{worker_id}"
                    cur.execute(f"CREATE TEMPORARY TABLE {temp_table_name} (LIKE all_messages) ON COMMIT DROP;")
                    
                    buffer = io.StringIO()
                    for rec in records:
                        line = '\t'.join(map(lambda x: str(x).replace('\\', '\\\\').replace('\t', ' ').replace('\n', ' ').replace('\r', ' ') if x is not None else '\\N', rec))
                        buffer.write(line + '\n')
                    buffer.seek(0)

                    cur.copy_expert(f"COPY {temp_table_name} FROM STDIN WITH (FORMAT TEXT, DELIMITER E'\\t', NULL '\\N')", buffer)
                    
                    cur.execute(f"INSERT INTO {partition_name} SELECT * FROM {temp_table_name} ON CONFLICT (id, subreddit_prefix) DO NOTHING;")
                    conn.commit()
                except Exception as e:
                    print(f"[DB-NLP-Worker-{worker_id}] DB Error during COPY for {partition_name}: {e}")
                    conn.rollback()

    while True:
        item = db_queue.get()
        if item is None:
            process_batch(batch)
            break
        
        batch.append(item)
        if len(batch) >= NLP_BATCH_SIZE:
            process_batch(batch)
            batch.clear()
    
    cur.close()
    conn.close()
    print(f"[DB-NLP-Worker-{worker_id}] Finished for item type: {item_type}")

def run_ingestion_pass(file_path: str, item_type: str):
    """Orchestrates the single-pass ingestion for a given file type."""
    print(f"\n--- Starting Ingestion Pass for {item_type.upper()}s ---")
    raw_queue = mp.Queue(maxsize=RAW_QUEUE_SIZE)
    db_queue = mp.Queue(maxsize=DB_QUEUE_SIZE)

    producer_proc = mp.Process(target=producer, args=(raw_queue, file_path, item_type))
    cpu_procs = [mp.Process(target=cpu_filter_worker, args=(raw_queue, db_queue)) for _ in range(N_CPU_PRODUCERS)]
    db_nlp_procs = [mp.Process(target=db_and_nlp_worker, args=(i, db_queue, item_type)) for i in range(N_WORKERS)]

    producer_proc.start()
    for p in cpu_procs: p.start()
    for p in db_nlp_procs: p.start()

    producer_proc.join()
    for p in cpu_procs: p.join()
    for p in db_nlp_procs: p.join()
    print(f"--- Ingestion Pass for {item_type.upper()}s Complete ---")

# --- Main Orchestrator ---
def main():
    setup_database()

    imported_dir_base = "/home/coinsafe/business-finder/reddit-dumps/imported"
    source_dir_base = "/home/coinsafe/business-finder/reddit-dumps/reddit"

    # Ensure the base 'imported' directory exists
    os.makedirs(imported_dir_base, exist_ok=True)
    
    for file_info in files_to_process:
        path = file_info["path"]
        item_type = file_info["type"]
        if not os.path.exists(path):
            print(f"Warning: File not found at {path}. Skipping.")
            continue
        
        run_ingestion_pass(path, item_type)

        # Move the processed file
        try:
            relative_path = os.path.relpath(path, source_dir_base)
            destination_path = os.path.join(imported_dir_base, relative_path)
            
            # Ensure the destination subdirectory (e.g., 'imported/submissions') exists
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            print(f"--- Moving processed file to {destination_path} ---")
            os.rename(path, destination_path)
        except Exception as e:
            print(f"Error moving file {path}: {e}")
    
    print("\nFull data ingestion process complete.")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()