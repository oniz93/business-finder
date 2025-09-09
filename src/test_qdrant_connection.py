import os
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import uuid # Import uuid

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION_NAME = "test_collection"

def test_qdrant():
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

        # Recreate a test collection
        vector_size = SentenceTransformer('all-MiniLM-L6-v2').get_sentence_embedding_dimension()
        print(f"Creating test collection '{QDRANT_COLLECTION_NAME}' with vector size {vector_size}...")
        client.recreate_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )
        print("Test collection created/recreated.")

        # Create a dummy point
        dummy_text = "This is a test sentence."
        dummy_embedding = SentenceTransformer('all-MiniLM-L6-v2').encode(dummy_text).tolist()
        dummy_id = str(uuid.uuid4().hex) # Generate a UUID for the dummy ID
        dummy_payload = {"test_field": "test_value"}

        point = models.PointStruct(id=dummy_id, vector=dummy_embedding, payload=dummy_payload)

        # Try to upsert the point
        print(f"Upserting point with ID: {dummy_id}...")
        operation_info = client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=[point],
            wait=True # Wait for operation to complete
        )
        print(f"Upsert operation info: {operation_info}")
        print("Successfully upserted a test point.")

    except Exception as e:
        print(f"An error occurred: {e}")
        # If it's an UnexpectedResponse, try to print more details if available
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Qdrant response text: {e.response.text}")
        if hasattr(e, 'status_code'):
            print(f"HTTP Status Code: {e.status_code}")

if __name__ == "__main__":
    test_qdrant()
