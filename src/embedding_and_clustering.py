import os
import dask.dataframe as dd
from dask_cuda import LocalCUDACluster
from dask.distributed import Client
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from typing import Optional
import pandas as pd
import uuid
import cuml # Import cuml for HDBSCAN
import numpy as np # For array manipulation
import google.generativeai as genai # Import Gemini API
import asyncio # For asynchronous API calls
import csv # For writing summaries to CSV
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define paths
processed_data_dir = "/home/coinsafe/business-finder/processed_data/filtered_comments"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION_NAME = "reddit_ideas_pain_points"
SUMMARIES_CSV_PATH = "/home/coinsafe/business-finder/summaries.csv" # Output for summaries

# Global variables for model and client to be initialized once per worker
_embedding_model = None
_qdrant_client_worker = None

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')
    return _embedding_model

def get_qdrant_client_worker():
    global _qdrant_client_worker
    if _qdrant_client_worker is None:
        _qdrant_client_worker = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    return _qdrant_client_worker

def process_partition(partition_df: pd.DataFrame) -> int:
    model = get_embedding_model()
    qdrant_client = get_qdrant_client_worker()
    
    points = []
    for index, row in partition_df.iterrows():
        body = row['body']
        embedding = model.encode(body).tolist()
        
        payload = {
            "link_id": row['link_id'],
            "author": row['author'],
            "subreddit": row['subreddit'],
            "created_utc": row['created_utc'],
            "body": body,
            "is_pain_point": row['is_pain_point'],
            "is_idea": row['is_idea'],
            "nlp_top_label": row['nlp_top_label'],
            "nlp_top_score": row['nlp_top_score']
        }
        point_id = str(uuid.uuid4().hex)

        points.append(models.PointStruct(id=point_id, vector=embedding, payload=payload))

        if len(points) >= 100: # Batch size for Qdrant upload
            qdrant_client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points)
            points = []
    
    if len(points) > 0:
        qdrant_client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points)
    
    return len(partition_df)


async def generate_summary_for_cluster(cluster_id: int, sample_texts: list[str]) -> dict:
    """
    Generates a concise summary for a given cluster using Gemini 1.5 Flash.
    """
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite") # Changed model to gemini-2.5-flash-lite
    
    bullet_prefix = "- "
    newline_bullet_prefix = "\n- "
    
    prompt = f"""
    Below are several Reddit comments that belong to the same cluster.
    These comments discuss either a common pain point or a business idea.
    Your task is to synthesize these comments into a concise 1-2 sentence summary
    of the core business opportunity or the underlying problem that could lead to a business idea.

    Comments:
    {bullet_prefix + newline_bullet_prefix.join(sample_texts)}

    Concise Summary:
    """
    
    try:
        response = await model.generate_content_async(prompt)
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason = response.prompt_feedback.block_reason.name
            print(f"Prompt blocked for cluster {cluster_id} due to: {block_reason}")
            return {"cluster_id": cluster_id, "summary": f"Summary blocked: {block_reason}"}
        
        summary = response.text.strip()
        return {"cluster_id": cluster_id, "summary": summary}
    except Exception as e:
        print(f"Error generating summary for cluster {cluster_id}: {e}")
        return {"cluster_id": cluster_id, "summary": f"Error: {e}"}


async def main_clustering_and_synthesis():
    print("Starting Phase 3: Embedding and Vector Storage...")

    cluster = LocalCUDACluster()
    client = Client(cluster)
    print(f"Dask dashboard link: {client.dashboard_link}")

    try:
        print(f"Loading data from {processed_data_dir}...")
        df = dd.read_parquet(processed_data_dir)
        print(f"Loaded {len(df)} items from Parquet.")

        qdrant_client_main = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

        dummy_model = SentenceTransformer('all-MiniLM-L6-v2')
        vector_size = dummy_model.get_sentence_embedding_dimension()
        del dummy_model

        print(f"Creating Qdrant collection '{QDRANT_COLLECTION_NAME}' with vector size {vector_size}...")
        qdrant_client_main.recreate_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )
        print("Qdrant collection created/recreated.")

        print("Generating embeddings and uploading to Qdrant...")
        processed_counts = df.map_partitions(process_partition, meta=(None, 'int')).compute()
        total_processed = sum(processed_counts)
        print(f"Finished generating embeddings and uploading to Qdrant. Total items processed: {total_processed}")

        # --- Clustering with HDBSCAN ---
        print("\nStarting Clustering with HDBSCAN...")

        print("Retrieving embeddings from Qdrant...")
        scroll_result = qdrant_client_main.scroll(
            collection_name=QDRANT_COLLECTION_NAME,
            limit=total_processed, # Retrieve all processed points
            with_payload=True,
            with_vectors=True
        )
        
        points_from_qdrant = scroll_result[0] # scroll_result is (list_of_points, next_page_offset)

        if not points_from_qdrant:
            print("No points retrieved from Qdrant for clustering. Exiting clustering phase.")
            return

        embeddings = []
        original_ids = []
        payloads = []
        for point in points_from_qdrant:
            embeddings.append(point.vector)
            original_ids.append(point.id)
            payloads.append(point.payload)

        embeddings_np = np.array(embeddings, dtype=np.float32)
        print(f"Retrieved {len(embeddings_np)} embeddings for clustering.")

        print("Applying HDBSCAN clustering...")
        hdbscan_model = cuml.HDBSCAN(min_cluster_size=5, min_samples=1) # Example parameters
        cluster_labels = hdbscan_model.fit_predict(embeddings_np)
        print("HDBSCAN clustering complete.")

        print("Updating Qdrant with cluster labels...")
        points_to_update = []
        for i, label in enumerate(cluster_labels):
            # Convert numpy.int64 to int for JSON serialization
            payloads[i]['cluster_label'] = int(label) 
            points_to_update.append(models.PointStruct(id=original_ids[i], vector=embeddings[i], payload=payloads[i]))

        # Batch update Qdrant with cluster labels
        # Qdrant upsert can update existing points by ID
        batch_size = 100
        for i in range(0, len(points_to_update), batch_size):
            batch = points_to_update[i:i+batch_size]
            qdrant_client_main.upsert(collection_name=QDRANT_COLLECTION_NAME, points=batch)
        print("Qdrant updated with cluster labels.")

        print("Clustering phase complete.")

        # --- LLM Synthesis ---
        print("\nStarting LLM Synthesis for Business Opportunities...")

        # Group comments by cluster label
        clusters_data = {}
        for i, label in enumerate(cluster_labels):
            if label != -1: # Exclude noise points (-1)
                if label not in clusters_data:
                    clusters_data[label] = []
                clusters_data[label].append(payloads[i]['body']) # Use original body text

        print(f"Found {len(clusters_data)} clusters (excluding noise).")

        summaries = []
        tasks = []
        for cluster_id, texts in clusters_data.items():
            # Sample representative texts (e.g., first 5 comments)
            sample_texts = texts[:5] 
            tasks.append(generate_summary_for_cluster(cluster_id, sample_texts))
        
        # Run all summary generation tasks concurrently
        print("Generating summaries using Gemini 1.5 Pro (asynchronously)...")
        summaries = await asyncio.gather(*tasks)
        print("Finished generating summaries.")

        # Store summaries in a CSV file
        print(f"Saving summaries to {SUMMARIES_CSV_PATH}...")
        with open(SUMMARIES_CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['cluster_id', 'summary']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for s in summaries:
                writer.writerow(s)
        print("Summaries saved to CSV.")

        print("LLM Synthesis phase complete.")

    finally:
        client.close()
        cluster.close()
        print("Dask cluster closed.")

if __name__ == "__main__":
    # Run the asynchronous main function
    asyncio.run(main_clustering_and_synthesis())