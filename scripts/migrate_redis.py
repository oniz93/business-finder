import os
import redis
import logging
import time
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
# Source: Your Cloud Redis
#SOURCE_URL = os.getenv("SOURCE_REDIS_URL", "rediss://:zBORiqFgabxlB7VMDjXvNWC2VAP9JPDWqAzCaLXjUNk%3D@businessfinder.redis.cache.windows.net:6380/0")
SOURCE_URL = os.getenv("SOURCE_REDIS_URL", "redis://127.0.0.1:6379/0")

# Destination: Local Redis (Default)
DEST_URL = os.getenv("DEST_REDIS_URL", "rediss://:kRoGWJXNK75zMIcJz4RDDhNhz1hfKq6OLAzCaCFPVIw%3D@businessfinder.canadacentral.redis.azure.net:10000/0")

BATCH_SIZE = 1000

def migrate():
    logging.info("--- Starting Redis Migration ---")
    logging.info(f"Source: {SOURCE_URL.split('@')[-1]}") # Log only host part for security
    logging.info(f"Destination: {DEST_URL}")

    try:
        src = redis.Redis.from_url(SOURCE_URL)
        dest = redis.Redis.from_url(DEST_URL)

        # Test connections
        logging.info(f"Source DB Size: {src.dbsize()} keys")
        try:
            dest.ping()
            logging.info("Connected to Destination.")
        except Exception as e:
            logging.error(f"Could not connect to destination: {e}")
            return

        cursor = '0'
        total_migrated = 0
        start_time = time.time()

        while cursor != 0:
            cursor, keys = src.scan(cursor=cursor, count=BATCH_SIZE)
            
            if not keys:
                continue

            pipe = dest.pipeline()
            
            # We need to fetch dumps and ttls for all keys
            # To speed this up, we can use a pipeline on source too
            src_pipe = src.pipeline()
            for key in keys:
                src_pipe.dump(key)
                src_pipe.pttl(key)
            
            src_results = src_pipe.execute()
            
            # src_results is [dump1, pttl1, dump2, pttl2, ...]
            # We iterate by 2
            for i, key in enumerate(keys):
                dump_data = src_results[i*2]
                pttl = src_results[i*2+1]

                if dump_data is None:
                    logging.warning(f"Key {key} disappeared during migration.")
                    continue

                # PTTL: -1 means no expire, -2 means expired (shouldn't happen with scan usually but possible)
                # RESTORE command expects ttl in ms. If ttl is 0, it means no expire.
                # But PTTL returns -1 for no expire.
                
                ttl = 0
                if pttl > 0:
                    ttl = pttl
                
                # If replace=True, it overwrites existing keys in dest
                pipe.restore(key, ttl, dump_data, replace=True)

            try:
                pipe.execute()
                total_migrated += len(keys)
                if total_migrated % 10000 == 0:
                    logging.info(f"Migrated {total_migrated} keys...")
            except Exception as e:
                logging.error(f"Error executing batch write: {e}")
                # Fallback: try one by one to identify the bad key
                for i, key in enumerate(keys):
                    try:
                        dump_data = src_results[i*2]
                        pttl = src_results[i*2+1]
                        if dump_data:
                            ttl = max(0, pttl) if pttl > 0 else 0
                            dest.restore(key, ttl, dump_data, replace=True)
                    except Exception as inner_e:
                        logging.error(f"Failed to migrate key {key}: {inner_e}")

    except Exception as e:
        logging.error(f"Migration failed: {e}")
        return

    elapsed = time.time() - start_time
    logging.info(f"--- Migration Complete ---")
    logging.info(f"Total Keys Migrated: {total_migrated}")
    logging.info(f"Time Elapsed: {elapsed:.2f}s")

if __name__ == "__main__":
    # Confirm before running
    print(f"Source: {SOURCE_URL}")
    print(f"Destination: {DEST_URL}")
    confirm = input("Are you sure you want to migrate data? (yes/no): ")
    if confirm.lower() == "yes":
        migrate()
    else:
        print("Migration cancelled.")
