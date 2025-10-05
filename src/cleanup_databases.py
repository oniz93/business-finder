import os
from qdrant_client import QdrantClient
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", 9200))
ELASTICSEARCH_INDEX = "business_plans"

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_BUSINESS_PLANS_COLLECTION = "business_plans_embeddings"

def cleanup_elasticsearch():
    """Deletes the specified Elasticsearch index."""
    print("--- Cleaning up Elasticsearch ---")
    try:
        es_client = Elasticsearch(f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}")
        if es_client.indices.exists(index=ELASTICSEARCH_INDEX):
            print(f"Deleting Elasticsearch index: '{ELASTICSEARCH_INDEX}'...")
            es_client.indices.delete(index=ELASTICSEARCH_INDEX)
            print("Index deleted successfully.")
        else:
            print(f"Elasticsearch index '{ELASTICSEARCH_INDEX}' does not exist. Nothing to do.")
    except Exception as e:
        print(f"An error occurred while cleaning up Elasticsearch: {e}")

def cleanup_qdrant():
    """Deletes the specified Qdrant collection."""
    print("\n--- Cleaning up Qdrant ---")
    try:
        qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        # This call returns True if the collection existed and was deleted, False otherwise.
        deleted = qdrant_client.delete_collection(collection_name=QDRANT_BUSINESS_PLANS_COLLECTION)
        if deleted:
            print(f"Qdrant collection '{QDRANT_BUSINESS_PLANS_COLLECTION}' deleted successfully.")
        else:
            print(f"Qdrant collection '{QDRANT_BUSINESS_PLANS_COLLECTION}' does not exist or could not be deleted. Nothing to do.")
    except Exception as e:
        print(f"An error occurred while cleaning up Qdrant: {e}")

if __name__ == "__main__":
    print("Starting database cleanup...")
    cleanup_elasticsearch()
    cleanup_qdrant()
    print("\nCleanup complete.")
