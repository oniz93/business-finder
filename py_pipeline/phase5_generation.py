#!/usr/bin/env python3
"""
Phase 5: Business Idea Generation & Scoring

This script reads clustered reddit comments from Phase 4, and uses Gemini to:
1. Summarize the cluster into a business idea.
2. Validate business viability.
3. Score business viability.
4. Classify if it's a SaaS.
5. Classify if it's possible for a solo entrepreneur.

It outputs structured data to Parquet files.
"""

import os
import sys
import json
import glob
import fnmatch
import asyncio
import time
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import typing_extensions as typing

import polars as pl
import google.generativeai as genai
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

# Add project root for config if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

console = Console()

API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    console.print("[red]Error: GOOGLE_API_KEY not found in environment.[/red]")
    sys.exit(1)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

CLUSTERS_INPUT_DIR = "/Volumes/2TBSSD/reddit/clusters"
IDEAS_OUTPUT_DIR = "/Volumes/2TBSSD/reddit/ideas"

# Checkpointing
CHECKPOINT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoint")
PROGRESS_FILE = "phase5_progress.json"

# Model Configuration
MODEL_NAME = "models/gemini-flash-lite-latest"

# Rate Limiting
# Flash Lite should be fast. 
RPM_LIMIT = 1000  # Conservative limit, can be higher for Flash
CONCURRENCY_LIMIT = 50

# -----------------------------------------------------------------------------
# Data Structures
# -----------------------------------------------------------------------------

response_schema = {
    "type": "OBJECT",
    "properties": {
        "cluster_summary": {"type": "STRING"},
        "is_viable_business": {"type": "BOOLEAN"},
        "viability_score": {"type": "INTEGER"},
        "is_saas": {"type": "BOOLEAN"},
        "is_solo_entrepreneur_possible": {"type": "BOOLEAN"}
    },
    "required": [
        "cluster_summary",
        "is_viable_business",
        "viability_score",
        "is_saas",
        "is_solo_entrepreneur_possible"
    ]
}

# -----------------------------------------------------------------------------
# Processing Logic
# -----------------------------------------------------------------------------

@dataclass
class ClusterData:
    """Container for all cluster information."""
    cluster_id: int
    texts: List[str]
    message_ids: List[str]
    total_ups: int
    total_downs: int
    message_count: int

async def analyze_cluster(cluster_data: ClusterData, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
    """
    Analyzes a single cluster using Gemini with structured output.
    Returns the AI analysis merged with cluster metadata.
    """
    async with semaphore:
        # Pass all texts without truncation
        preview_text = "\n- ".join([t.replace("\n", " ") for t in cluster_data.texts])

        prompt = f"""
        Analyze the following cluster of Reddit comments/posts to identify a potential business opportunity.
        
        Input Texts:
        - {preview_text}
        
        Tasks:
        1. Summarize the core pain point or desire into a concise business idea/opportunity summary.
        2. Validate if this is a viable business (True/False). 
           - True if: Clear problem, willingness to pay, feasible solution.
           - False if: Just complaining without a solution, physically impossible, or illegal/harmful.
        3. Score the business viability from 1 to 10 (10 being immediate unicorn potential, 1 being garbage).
        4. Determine if this idea is a SaaS (Software as a Service) (True/False).
        5. Determine if this idea is possible to be built/started by a solo entrepreneur (True/False).
        
        Return the result as a JSON object matching the defined schema.
        """

        try:
            model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema
                )
            )
            
            # Helper to handle rate limits with retries
            for attempt in range(3):
                try:
                    response = await model.generate_content_async(prompt)
                    result = json.loads(response.text)
                    
                    # Add cluster metadata
                    result['cluster_id'] = cluster_data.cluster_id
                    result['message_ids'] = json.dumps(cluster_data.message_ids)  # JSON string for parquet
                    result['texts_combined'] = "\n\n---\n\n".join(cluster_data.texts)
                    result['total_ups'] = cluster_data.total_ups
                    result['total_downs'] = cluster_data.total_downs
                    result['message_count'] = cluster_data.message_count
                    result['generated_plan'] = ""  # Empty string, will store business plan ID when generated
                    
                    return result
                except Exception as e:
                    if "429" in str(e): # Rate limit
                        wait_time = (2 ** attempt) + random.random()
                        console.print(f"[yellow]Rate limit for cluster {cluster_data.cluster_id}, retrying in {wait_time:.1f}s...[/yellow]")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise e
            
            return None # Failed after retries

        except Exception as e:
            # console.print(f"[red]Error analyzing cluster {cluster_data.cluster_id}: {e}[/red]")
            return {
                'cluster_id': cluster_data.cluster_id, 
                'error': str(e),
                'is_viable_business': False,
                'viability_score': 0
            }

async def process_subreddit(subreddit_path: str, output_base_dir: str):
    """
    Process all clusters in a subreddit.
    """
    subreddit_name = os.path.basename(subreddit_path)
    
    # Check output
    try:
        rel_path = os.path.relpath(subreddit_path, CLUSTERS_INPUT_DIR)
    except ValueError:
        rel_path = os.path.basename(subreddit_path)
        
    output_dir = os.path.join(output_base_dir, rel_path)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "ideas.parquet")
    
    if os.path.exists(output_file):
        # Skip if already exists (basic checkpointing)
        console.print(f"[dim]Skipping {subreddit_name}, already processed.[/dim]")
        return

    # Find clustered parquet
    cluster_files = glob.glob(os.path.join(subreddit_path, "*.parquet"))
    if not cluster_files:
        return

    try:
        # Load Data
        df = pl.concat([pl.read_parquet(f) for f in cluster_files])
        
        # Check output structure from Phase 4
        # Phase 4 output has columns: cluster_id, cluster_size, avg_quality_score, representative_texts (JSON string)
        # If it's the `phase4_clusterer.py` output, it has: cluster_id, and original cols (body, etc)
        
        # We need to handle both cases or assume the latest `phase4_clusterer.py` which outputs `clustered.parquet` with ALL cols.
        # Let's verify columns
        cols = df.columns
        
        cluster_data = []

        if "representative_texts" in cols:
            # This is from phase4_analytics.py (aggregated)
            # cluster_id, representative_texts (json string list)
            # We iterate rows
            for row in df.iter_rows(named=True):
                cid = row['cluster_id']
                if cid == -1: continue
                
                texts = json.loads(row['representative_texts'])
                # For aggregated format, we don't have individual message IDs
                cluster_data.append(ClusterData(
                    cluster_id=cid,
                    texts=texts,
                    message_ids=[],
                    total_ups=row.get('total_ups', 0) or 0,
                    total_downs=row.get('total_downs', 0) or 0,
                    message_count=len(texts)
                ))
                
        elif "cluster_id" in cols:
             # This is from phase4_clusterer.py (raw rows with cluster_id)
             # We need to group by cluster_id
             # Find text column
            text_col = None
            for col in ["body", "text", "selftext", "content", "message"]:
                if col in cols:
                    text_col = col
                    break
            
            if not text_col:
                console.print(f"[yellow]No text column found for {subreddit_name}[/yellow]")
                return
            
            # Find ID column
            id_col = None
            for col in ["id", "message_id", "comment_id", "post_id", "name"]:
                if col in cols:
                    id_col = col
                    break

            # Group by cluster_id
            # In newer Polars, groupby is now group_by
            df_filtered = df.filter(pl.col("cluster_id") != -1)
            
            for cluster_id in df_filtered["cluster_id"].unique().to_list():
                group_df = df_filtered.filter(pl.col("cluster_id") == cluster_id)
                texts = group_df[text_col].to_list()
                
                # Get message IDs
                message_ids = []
                if id_col:
                    message_ids = [str(x) for x in group_df[id_col].to_list()]
                
                # Get upvotes/downvotes
                total_ups = 0
                total_downs = 0
                if "ups" in cols:
                    total_ups = int(group_df["ups"].sum() or 0)
                if "downs" in cols:
                    total_downs = int(group_df["downs"].sum() or 0)
                if "score" in cols and "ups" not in cols:
                    total_ups = int(group_df["score"].sum() or 0)
                
                cluster_data.append(ClusterData(
                    cluster_id=cluster_id,
                    texts=texts,
                    message_ids=message_ids,
                    total_ups=total_ups,
                    total_downs=total_downs,
                    message_count=len(texts)
                ))
        else:
            console.print(f"[red]Unknown schema for {subreddit_name}[/red]")
            return

        if not cluster_data:
            return

        console.print(f"Analyzing [cyan]{subreddit_name}[/cyan] ({len(cluster_data)} clusters)...")
        
        # Run Analysis
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
        tasks = [analyze_cluster(cd, semaphore) for cd in cluster_data]
        
        results = await asyncio.gather(*tasks)
        results = [r for r in results if r is not None and "error" not in r]
        
        if not results:
            return

        # Save Results
        result_df = pl.DataFrame(results)
        result_df.write_parquet(output_file)
        console.print(f"  Saved {len(results)} ideas to [green]{output_file}[/green]")

    except Exception as e:
        console.print(f"[red]Error processing subreddit {subreddit_name}: {e}[/red]")
        import traceback
        traceback.print_exc()

async def main():
    parser = argparse.ArgumentParser(description="Phase 5: Idea Generation")
    parser.add_argument("--subreddit", type=str, help="Specific subreddit to process")
    parser.add_argument("--pattern", type=str, help="Glob-like pattern to match subreddits (e.g., '*business*')")
    args = parser.parse_args()

    console.rule("[bold purple]Phase 5: Business Idea Generation[/bold purple]")
    
    subreddits = []
    
    if args.subreddit:
        console.print(f"Searching for {args.subreddit}...")
        # Search for specific subreddit
        # optimization: check partitions directly
        candidates = glob.glob(os.path.join(CLUSTERS_INPUT_DIR, "*", args.subreddit))
        candidates.extend(glob.glob(os.path.join(CLUSTERS_INPUT_DIR, args.subreddit)))
        
        if candidates:
            subreddits.extend(candidates)
        else:
            # Fallback to walk if not found in first 2 levels
            for root, dirs, files in os.walk(CLUSTERS_INPUT_DIR):
                if args.subreddit in dirs:
                    subreddits.append(os.path.join(root, args.subreddit))
                    break
        
        if not subreddits:
            console.print(f"[red]Subreddit {args.subreddit} not found in {CLUSTERS_INPUT_DIR}[/red]")
            return
    elif args.pattern:
        # Pattern matching mode (e.g., "*business*")
        console.print(f"Searching for pattern: {args.pattern}...")
        for root, dirs, files in os.walk(CLUSTERS_INPUT_DIR):
            for d in dirs:
                if fnmatch.fnmatch(d.lower(), args.pattern.lower()):
                    subreddits.append(os.path.join(root, d))
        
        if not subreddits:
            console.print(f"[red]No subreddits matching pattern '{args.pattern}' found.[/red]")
            return
        console.print(f"Found {len(subreddits)} subreddits matching pattern.")
    else:
        # Scan all
        console.print(f"Scanning {CLUSTERS_INPUT_DIR}...")
        for root, dirs, files in os.walk(CLUSTERS_INPUT_DIR):
            for d in dirs:
                # Basic check if it looks like a subreddit dir (contains parquet or is a leaf)
                # We can rely on existence of .parquet files inside in the process function
                # But to avoid walking too deep into partitions, we can check typical structure
                # The input is like /clusters/00/AskReddit or /clusters/AskReddit
                # We just add all dirs and let process_subreddit check for parquet files
                subreddits.append(os.path.join(root, d))
    
    # Process
    total = len(subreddits)
    console.print(f"Found {total} potential directories.")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} subreddits"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Generating Ideas...", total=total)
        
        # We can process subreddits sequentially (as each has parallelism internally)
        # or parallel subreddits. Given internal parallelism is constrained by SEMAPHORE, 
        # sequential subreddits is safer for memory.
        
        for subdir in subreddits:
            progress.update(task, description=f"Processing {os.path.basename(subdir)}")
            await process_subreddit(subdir, IDEAS_OUTPUT_DIR)
            progress.advance(task)

if __name__ == "__main__":
    asyncio.run(main())
