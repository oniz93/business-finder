import os
import pandas as pd
import numpy as np
import glob
import argparse
import asyncio
from tqdm import tqdm
from dotenv import load_dotenv

# For embeddings
from sentence_transformers import SentenceTransformer

# For clustering on GPU
import cuml

# For summarization with Gemini
import google.generativeai as genai

# --- Configuration ---
load_dotenv()  # Load environment variables from .env file

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
SUMMARIZATION_MODEL_NAME = "models/gemini-2.5-flash-lite"
PROCESSED_DATA_DIR = "/home/coinsafe/business-finder/processed_data"
OUTPUT_DIR = "/home/coinsafe/business-finder/data/summaries"

# Configure the Gemini API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


async def summarize_cluster_texts(cluster_id, texts, model):
    """
    Generates a summary for a list of texts asynchronously using Gemini.
    """
    # Take a sample of texts to avoid making the prompt too long
    sample_texts = texts[:10]
    formatted_comments = '\n- '.join(sample_texts)

    prompt = f"""Your task is to synthesize the provided Reddit comments into a concise 1-2 sentence summary of the core business opportunity or underlying problem.
Focus on the recurring themes and ideas.

Comments:
- {formatted_comments}

Concise Summary:"""

    try:
        response = await model.generate_content_async(prompt)
        return cluster_id, response.text.strip()
    except Exception as e:
        print(f"Error summarizing cluster {cluster_id}: {e}")
        return cluster_id, "Error generating summary."


async def main(subreddit_name):
    """
    Main asynchronous function to process a subreddit.
    """
    print(f"--- Starting processing for subreddit: {subreddit_name} ---")

    # 1. Load data
    subreddit_dir = os.path.join(PROCESSED_DATA_DIR, subreddit_name)
    parquet_files = glob.glob(f"{subreddit_dir}/**/*.parquet", recursive=True)
    if not parquet_files:
        print(f"No parquet files found for subreddit '{subreddit_name}' in '{subreddit_dir}'")
        return

    print(f"Loading {len(parquet_files)} parquet files...")
    df = pd.concat([pd.read_parquet(f) for f in parquet_files], ignore_index=True)
    print(f"Loaded {len(df)} comments.")

    # Data cleaning
    df.dropna(subset=['full_thread_body'], inplace=True)
    df['full_thread_body'] = df['full_thread_body'].astype(str)
    df['total_ups'] = pd.to_numeric(df['total_ups'], errors='coerce').fillna(0)
    df['total_downs'] = pd.to_numeric(df['total_downs'], errors='coerce').fillna(0)

    # 2. Generate embeddings
    print("Generating embeddings... (This may take a while)")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device='cuda')
    embeddings = embedding_model.encode(
        df['full_thread_body'].tolist(),
        show_progress_bar=True,
        batch_size=256
    )

    # 3. Cluster embeddings with cuML HDBSCAN
    print("Clustering embeddings with GPU-accelerated HDBSCAN...")
    embeddings = embeddings.astype(np.float32)
    clusterer = cuml.HDBSCAN(min_cluster_size=15, metric='euclidean', gen_min_span_tree=True)
    cluster_labels = clusterer.fit_predict(embeddings)
    df['cluster'] = cluster_labels

    num_clusters = len(np.unique(cluster_labels)) - (1 if -1 in np.unique(cluster_labels) else 0)
    print(f"Found {num_clusters} clusters.")

    # 4. Process and summarize clusters
    clustered_df = df[df['cluster'] != -1].copy()

    if not clustered_df.empty:
        print(f"Summarizing {clustered_df['cluster'].nunique()} clusters asynchronously with Gemini...")

        # Configure Gemini model
        generation_config = {"temperature": 0.7, "top_p": 1, "top_k": 1, "max_output_tokens": 150}
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        summarization_model = genai.GenerativeModel(model_name=SUMMARIZATION_MODEL_NAME,
                                                    generation_config=generation_config,
                                                    safety_settings=safety_settings)

        tasks = []
        cluster_groups = clustered_df.groupby('cluster')['full_thread_body'].apply(list)
        for cluster_id, texts in cluster_groups.items():
            tasks.append(summarize_cluster_texts(cluster_id, texts, summarization_model))

        # Show progress with tqdm
        summaries_list = []
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            summaries_list.append(await f)

        summaries_map = dict(summaries_list)
        clustered_df['summary'] = clustered_df['cluster'].map(summaries_map)

        # 5. Aggregate results
        print("Aggregating cluster data...")
        agg_functions = {
            'start_id': lambda x: list(x),
            'full_thread_body': lambda x: list(x),
            'total_ups': 'sum',
            'total_downs': 'sum',
            'summary': 'first'
        }

        # Group by cluster and aggregate
        final_df = clustered_df.groupby('cluster').agg(agg_functions).reset_index()
        final_df['subreddit'] = subreddit_name

        # Rename columns for final output
        final_df.rename(columns={
            'cluster': 'cluster_id',
            'start_id': 'ids_in_cluster',
            'full_thread_body': 'texts'
        }, inplace=True)

        # Reorder columns to match request
        final_df = final_df[['subreddit', 'cluster_id', 'ids_in_cluster', 'texts', 'summary', 'total_ups', 'total_downs']]

        # 6. Save results
        output_path = os.path.join(OUTPUT_DIR, f"{subreddit_name}_clusters.parquet")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        final_df.to_parquet(output_path, index=False)
        print(f"Successfully saved clustered data to {output_path}")
    else:
        print("No clusters were found to save.")

    print(f"--- Finished processing for subreddit: {subreddit_name} ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cluster and summarize subreddit data using embeddings.")
    parser.add_argument(
        "subreddit",
        type=str,
        help="Name of the subreddit to process (e.g., 'AskReddit'). This should match the folder name in processed_data."
    )
    args = parser.parse_args()

    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found. Ensure it is set in your .env file.")
    else:
        asyncio.run(main(args.subreddit))