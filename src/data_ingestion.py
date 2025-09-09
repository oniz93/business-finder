import sys
version = sys.version_info
if version.major < 3 or (version.major == 3 and version.minor < 10):
    raise RuntimeError("This script requires Python 3.10 or higher")
import os
from typing import Iterable, Optional
import pandas as pd # Import pandas for to_parquet
import dask.dataframe as dd # Use dask.dataframe for to_parquet

from src.fileStreams import getFileJsonStream # Adjusted import path
# from src.utils import FileProgressLog # Commenting out as it's not compatible with Dask Bag's parallel processing
import dask.bag as db
from dask_cuda import LocalCUDACluster # Import LocalCUDACluster
from dask.distributed import Client # Keep Client for connecting to the cluster
from transformers import pipeline # Import pipeline for zero-shot classification

# Set environment variable for PyTorch memory allocation
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# Global variable for the file path, will be set in main
file_to_process = ""
output_parquet_dir = "/home/coinsafe/business-finder/processed_data/filtered_comments" # Define output directory

# Initialize the zero-shot classification pipeline globally, but it will be created per worker
# This is a common pattern for Dask + Transformers to avoid re-downloading models
# and to ensure the model is loaded on the correct device within each worker.
# The actual pipeline object will be created inside the classify_and_filter_comment function
# when it's executed on a Dask worker.
_classifier = None
_candidate_labels = ["pain_point", "idea"]
_pain_point_keywords = ["frustrating", "problem", "difficult", "struggle", "annoying", "wish", "need", "can't", "should be", "hard to", "lack of", "missing", "broken"]
_idea_keywords = ["idea", "solution", "concept", "opportunity", "build", "create", "develop", "imagine", "what if", "improve", "new way", "innovate"]


def get_classifier():
    global _classifier
    if _classifier is None:
        # Initialize the zero-shot classification pipeline
        # Using a smaller model: typeform/distilbert-base-uncased-mnli
        _classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli", device=0) # device=0 for the first GPU on each worker
    return _classifier

def classify_and_filter_comment(row):
    # Get the classifier instance for this worker
    classifier = get_classifier()
    
    body = row.get("body", "")
    
    # Apply initial rule-based filter
    is_rule_pain_point = any(keyword in body.lower() for keyword in _pain_point_keywords)
    is_rule_idea = any(keyword in body.lower() for keyword in _idea_keywords)

    if not (is_rule_pain_point or is_rule_idea):
        return None # Skip if not initially classified by rules

    # Perform zero-shot classification
    # Only classify if the body is not empty and has some reasonable length
    if body and len(body) > 50: # Minimum length for meaningful classification
        try:
            # The zero-shot classifier expects a list of sequences
            # and returns a list of dictionaries.
            classification_results = classifier(body, _candidate_labels)
            
            # Get the top label and its score
            top_label = classification_results['labels'][0]
            top_score = classification_results['scores'][0]

            # Threshold the score to ensure confidence
            if top_score > 0.7: # Example threshold, can be adjusted
                is_nlp_pain_point = (top_label == "pain_point")
                is_nlp_idea = (top_label == "idea")
            else:
                is_nlp_pain_point = False
                is_nlp_idea = False

            # Combine rule-based and NLP classification
            # A comment is a pain point if either rule-based or NLP says so
            # and similarly for idea. Prioritize NLP if confident.
            final_is_pain_point = is_rule_pain_point or is_nlp_pain_point
            final_is_idea = is_rule_idea or is_nlp_idea

            if final_is_pain_point or final_is_idea:
                return {
                    "id": row.get("id"),
                    "link_id": row.get("link_id"),
                    "author": row.get("author"),
                    "subreddit": row.get("subreddit"),
                    "created_utc": row.get("created_utc"),
                    "body": body,
                    "is_pain_point": final_is_pain_point,
                    "is_idea": final_is_idea,
                    "nlp_top_label": top_label,
                    "nlp_top_score": top_score
                }
        except Exception as e:
            print(f"Error during NLP classification for row: {row.get('id')}. Error: {e}")
            return None
    return None


def process_single_file_with_dask(path: str, limit: Optional[int] = None):
    print(f"Processing file {path} with Dask Bag...\n")

    # Initialize a LocalCUDACluster to utilize GPUs
    # n_workers will default to the number of available GPUs
    cluster = LocalCUDACluster()
    client = Client(cluster)
    print(f"Dask dashboard link: {client.dashboard_link}\n")

    try:
        # Open the file and get the generator, passing the limit directly
        with open(path, "rb") as f:
            json_stream_generator = getFileJsonStream(path, f, max_items=limit) # Pass max_items here
            if json_stream_generator is None:
                print(f"Skipping unknown file {path}")
                return

            # Create a Dask Bag from the generator.
            bag = db.from_sequence(json_stream_generator, npartitions=20) # npartitions can be adjusted based on data size and cluster

            # Apply classification and filter out non-classified comments
            classified_data_bag = bag.map(classify_and_filter_comment).filter(lambda x: x is not None)

            # Convert Dask Bag to Dask DataFrame for Parquet output
            # Define meta for the DataFrame to help Dask infer types
            meta = {
                "id": str,
                "link_id": str,
                "author": str,
                "subreddit": str,
                "created_utc": int,
                "body": str,
                "is_pain_point": bool,
                "is_idea": bool,
                "nlp_top_label": str,
                "nlp_top_score": float
            }
            classified_data_df = classified_data_bag.to_dataframe(meta=meta)

            # Create output directory if it doesn't exist
            os.makedirs(output_parquet_dir, exist_ok=True)

            print(f"Writing classified data to Parquet files in {output_parquet_dir}...\n")
            # Write to Parquet files
            classified_data_df.to_parquet(output_parquet_dir, engine='pyarrow', write_metadata_file=True)
            print("Finished writing classified data to Parquet.\n")

            # For verification, let's count the items written
            count = classified_data_df.shape[0].compute()
            print(f"\nSuccessfully processed, classified, and saved {count} items to Parquet.\n")

    finally:
        client.close()
        cluster.close()
        print("Dask cluster closed.\n")

def main():
    global file_to_process
    # Set the path to the specific .zst file
    file_to_process = "/home/coinsafe/business-finder/reddit-dumps/reddit/comments/RC_2025-07.zst"

    if not os.path.exists(file_to_process):
        print(f"Error: File not found at {file_to_process}. Please ensure the data is downloaded.")
        print("You can download the data using the torrent file: /home/coinsafe/business-finder/reddit-dumps/reddit-b6a7ccf72368a7d39c018c423e01bc15aa551122.torrent")
        return

    # For testing, limit to 10000 messages as requested by the user
    process_single_file_with_dask(file_to_process, limit=None)
    
    print("Data ingestion, filtering, and classification phase complete.\n")

if __name__ == "__main__":
    main()