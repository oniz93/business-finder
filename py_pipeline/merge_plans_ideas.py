#!/usr/bin/env python3
"""
Merge Business Plans with Original Ideas

This script merges the generated business plans with the original idea data (including statistics, 
original texts, etc.) by joining on cluster_id within each subreddit.

It assumes:
- Business plans are in /Volumes/2TBSSD/reddit/business_plans/<subreddit>/plans_*.parquet
- Ideas are in /Volumes/2TBSSD/reddit/ideas/**/<subreddit>/ideas.parquet
"""

import os
import sys
import glob
import polars as pl
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

# Add project root for config if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()
console = Console()

# Configuration
PLANS_DIR = "/Volumes/2TBSSD/reddit/business_plans"
IDEAS_DIR = "/Volumes/2TBSSD/reddit/ideas"
OUTPUT_DIR = "/Volumes/2TBSSD/reddit/merged_dataset"

def find_idea_file(subreddit: str) -> str:
    """
    Finds the ideas.parquet file for a given subreddit.
    Handles potential nesting (e.g. ideas/al/algotrading/ideas.parquet).
    """
    # Direct check
    path1 = os.path.join(IDEAS_DIR, subreddit, "ideas.parquet")
    if os.path.exists(path1):
        return path1
        
    # Check 2-letter partition (if applicable)
    if len(subreddit) >= 2:
        prefix = subreddit[:2].lower()
        path2 = os.path.join(IDEAS_DIR, prefix, subreddit, "ideas.parquet")
        if os.path.exists(path2):
            return path2
            
    # Recursive search (slower fallback)
    # Using glob with recursive search
    pattern = os.path.join(IDEAS_DIR, "**", subreddit, "ideas.parquet")
    matches = glob.glob(pattern, recursive=True)
    if matches:
        return matches[0]
        
    return None

def main():
    console.rule("[bold purple]Merging Business Plans with Ideas[/bold purple]")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Find all business plan files
    console.print(f"Scanning {PLANS_DIR} for business plans...")
    plan_files = glob.glob(os.path.join(PLANS_DIR, "*", "plans_*.parquet"))
    
    if not plan_files:
        console.print("[red]No business plan files found.[/red]")
        return
        
    console.print(f"Found {len(plan_files)} plan files.")
    
    # 2. Process each file
    merged_count = 0
    skipped_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} files"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Merging files...", total=len(plan_files))
        
        for plan_file in plan_files:
            # Extract subreddit from path: .../business_plans/<subreddit>/plans_...
            subreddit = os.path.basename(os.path.dirname(plan_file))
            progress.update(task, description=f"Processing {subreddit}")
            
            # Find matching ideas file
            idea_file = find_idea_file(subreddit)
            
            if not idea_file:
                # console.print(f"[yellow]Warning: Could not find ideas.parquet for {subreddit}[/yellow]")
                skipped_count += 1
                progress.advance(task)
                continue
                
            try:
                # Read DataFrames
                df_plans = pl.read_parquet(plan_file)
                df_ideas = pl.read_parquet(idea_file)
                
                # Verify columns exist
                if "cluster_id" not in df_plans.columns:
                    console.print(f"[red]Error: 'cluster_id' missing in plans for {subreddit}[/red]")
                    skipped_count += 1
                    progress.advance(task)
                    continue
                    
                if "cluster_id" not in df_ideas.columns:
                    console.print(f"[red]Error: 'cluster_id' missing in ideas for {subreddit}[/red]")
                    skipped_count += 1
                    progress.advance(task)
                    continue

                # Cast cluster_id to Int64 to ensure matching types
                df_plans = df_plans.with_columns(pl.col("cluster_id").cast(pl.Int64))
                df_ideas = df_ideas.with_columns(pl.col("cluster_id").cast(pl.Int64))

                # Rename columns in ideas that might collision but keep meaningful ones
                # Plans has 'original_summary' which comes from ideas 'cluster_summary' usually
                # Let's perform the join.
                # Left join? Inner join? Inner join because we only want plans that have corresponding idea data.
                # Although plans are generated FROM ideas, so it should be 1:1 or subset.
                
                # We need all columns from ideas.
                # Common columns likely: cluster_id, maybe others?
                # df_ideas columns: cluster_summary, is_viable_business, ... texts_combined, generated_plan
                # df_plans columns: title, executive_summary ... cluster_id, subreddit, plan_id, original_summary
                
                # 'generated_plan' in ideas is the UUID of the plan. 'plan_id' in plans is the UUID.
                # We can verify match or just join on cluster_id.
                
                merged = df_plans.join(df_ideas, on="cluster_id", how="inner", suffix="_idea")
                
                # Check if we have data
                if merged.height == 0:
                    # console.print(f"[yellow]No matching clusters found for {subreddit}[/yellow]")
                    skipped_count += 1
                    progress.advance(task)
                    continue
                
                # Add subreddit column if missing in merged (it is in plans, so it should be there)
                if "subreddit" not in merged.columns:
                     merged = merged.with_columns(pl.lit(subreddit).alias("subreddit"))
                
                # Write output
                output_file = os.path.join(OUTPUT_DIR, f"{subreddit}_merged.parquet")
                merged.write_parquet(output_file)
                merged_count += 1
                
            except Exception as e:
                console.print(f"[red]Error processing {subreddit}: {e}[/red]")
                skipped_count += 1
            
            progress.advance(task)

    console.rule("[bold]Summary[/bold]")
    console.print(f"[green]Successfully merged: {merged_count} subreddits[/green]")
    console.print(f"Skipped/Failed: {skipped_count}")
    console.print(f"Output directory: [blue]{OUTPUT_DIR}[/blue]")

if __name__ == "__main__":
    main()
