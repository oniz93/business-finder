import os
import multiprocessing as mp
import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor
from collections import defaultdict
import time

# --- Configuration ---
# Database
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "reddit_threads"
DB_USER = "reddit_user"
DB_PASS = "reddit_password"

# Processing
N_PROCESSES = 20
CHUNK_SIZE = 100
OUTPUT_DIR = "processed_data"

# --- Database Functions ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)

def reconstruct_thread(start_id, id_to_message_map, link_id_to_messages_map):
    """
    Reconstructs a message thread from a starting comment up to its root.
    Returns the concatenated body and vote statistics if a valid root is found.
    """
    if start_id not in id_to_message_map:
        return None

    start_message = id_to_message_map[start_id]
    thread_link_id = start_message['trunc_link_id']
    
    if thread_link_id not in link_id_to_messages_map:
        return None

    # All messages in the same original post
    thread_messages = link_id_to_messages_map[thread_link_id]
    
    # Create a quick lookup for messages in this specific thread by their truncated ID
    thread_id_lookup = {msg['id'].split('_')[-1]: msg for msg in thread_messages}

    path = []
    current_id = start_id.split('_')[-1]
    root_found = False

    # Walk up the tree from the starting comment
    for _ in range(100): # Safety break
        if current_id not in thread_id_lookup:
            break # Broken chain

        message = thread_id_lookup[current_id]
        path.append(message)
        
        current_parent_id = message.get('trunc_parent_id')
        
        # A message is a root if its parent_id is null/empty.
        if not current_parent_id:
            root_found = True
            break
        
        # If not the root, move up to the parent.
        current_id = current_parent_id

    if not root_found:
        return None

    # Thread is valid, now calculate stats and concatenate bodies
    path.reverse() # Order from root to comment
    
    full_body = "\n\n---\n\n".join([p['body'] for p in path])
    
    total_ups = sum(p['ups'] for p in path if p['ups'] is not None)
    avg_ups = total_ups / len(path) if path else 0
    
    total_downs = sum(p['downs'] for p in path if p['downs'] is not None)
    avg_downs = total_downs / len(path) if path else 0

    return {
        "start_id": start_id,
        "full_thread_body": full_body,
        "total_ups": total_ups,
        "avg_ups": avg_ups,
        "total_downs": total_downs,
        "avg_downs": avg_downs
    }

def process_chunk(prefix, subreddit, id_chunk):
    """
    Worker function to process a chunk of IDs for a given subreddit prefix.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    print(f"[Worker-{os.getpid()}] Processing {len(id_chunk)} IDs for prefix '{prefix}' in r/{subreddit}")

    try:
        # 1. Get the link_ids for the chunk of message IDs
        cur.execute(
            "SELECT DISTINCT trunc_link_id FROM all_messages WHERE subreddit_prefix = %s AND id = ANY(%s)",
            (prefix, id_chunk)
        )
        link_ids = [row['trunc_link_id'] for row in cur.fetchall()]

        if not link_ids:
            print(f"[Worker-{os.getpid()}] No link_ids found for chunk in r/{subreddit}. Skipping.")
            return 0

        # 2. Fetch all messages related to those link_ids
        cur.execute(
            "SELECT * FROM all_messages WHERE subreddit_prefix = %s AND trunc_link_id = ANY(%s)",
            (prefix, link_ids)
        )
        all_thread_messages = cur.fetchall()

        # 3. Group messages by link_id and create an id->message map for quick lookups
        link_id_to_messages_map = defaultdict(list)
        id_to_message_map = {}
        for msg in all_thread_messages:
            link_id_to_messages_map[msg['trunc_link_id']].append(msg)
            id_to_message_map[msg['id']] = msg

        # 4. Reconstruct each thread
        results = []
        for start_id in id_chunk:
            result = reconstruct_thread(start_id, id_to_message_map, link_id_to_messages_map)
            if result:
                results.append(result)
        
        # 5. Save results to Parquet
        if results:
            df = pd.DataFrame(results)
            subreddit_dir = os.path.join(OUTPUT_DIR, subreddit)
            os.makedirs(subreddit_dir, exist_ok=True)
            
            # Generate a unique filename for the chunk
            file_name = f"{id_chunk[0]}_{len(id_chunk)}.parquet"
            output_path = os.path.join(subreddit_dir, file_name)
            
            df.to_parquet(output_path)
            print(f"[Worker-{os.getpid()}] Saved {len(df)} threads to {output_path}")
            return len(df)

    except Exception as e:
        print(f"[Worker-{os.getpid()}] Error processing chunk for r/{subreddit}: {e}")
    finally:
        cur.close()
        conn.close()
    
    return 0

def main():
    """Main orchestrator."""
    print("--- Starting Thread Reconstruction ---")
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    print("Fetching all IDs to keep from the database...")
    cur.execute("SELECT id, subreddit, subreddit_prefix FROM id_to_keep")
    
    ideas_df = pd.DataFrame(cur.fetchall(), columns=['id', 'subreddit', 'subreddit_prefix'])
    cur.close()
    conn.close()

    if ideas_df.empty:
        print("No ideas found in 'id_to_keep' for the test subreddits. Exiting.")
        return

    print(f"Found {len(ideas_df)} total ideas to process across {ideas_df['subreddit'].nunique()} subreddits.")

    # Group by prefix and subreddit, then create chunks
    tasks = []
    for (prefix, subreddit), group in ideas_df.groupby(['subreddit_prefix', 'subreddit']):
        ids = group['id'].tolist()
        for i in range(0, len(ids), CHUNK_SIZE):
            chunk = ids[i:i + CHUNK_SIZE]
            tasks.append((prefix, subreddit, chunk))

    print(f"Created {len(tasks)} chunks to be processed by {N_PROCESSES} workers.")

    # Run tasks in parallel
    start_time = time.time()
    with mp.Pool(N_PROCESSES) as pool:
        results = pool.starmap(process_chunk, tasks)
    
    total_processed = sum(results)
    end_time = time.time()

    print("\n--- Reconstruction Complete ---")
    print(f"Successfully processed and saved {total_processed} threads.")
    print(f"Total time: {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()