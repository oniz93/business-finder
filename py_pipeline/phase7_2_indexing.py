#!/usr/bin/env python3
"""
Phase 7.2: Elasticsearch Indexing (Updated Mapping)

This script indexes the merged business plan datasets into Elasticsearch.
"""

import os
import sys
import glob
import asyncio
import time
import argparse
import datetime
import numpy as np
from typing import Dict, Any, List

import polars as pl
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

# Add project root for config if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()
console = Console()

# Configuration
PLANS_DIR = "/Volumes/2TBSSD/reddit/merged_dataset"
ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200
INDEX_NAME = "business_plans"

# Updated Mapping based on the merged dataset
BASE_MAPPING = {
    "properties": {
        "title": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
        "executive_summary": { "type": "text" },
        "problem": { "type": "text" },
        "solution": { "type": "text" },
        
        # Nested Objects
        "market_analysis": {
            "properties": {
                "market_size": { "type": "text" },
                "target_market": { "type": "text" },
                "trends": { "type": "text" } # Array of text
            }
        },
        "competition": {
            "properties": {
                "competitors": { "type": "text" },
                "direct_competitors": { "type": "text" },
                "indirect_competitors": { "type": "text" },
                "competitive_advantages": { "type": "text" }
            }
        },
        "marketing_strategy": {
            "properties": {
                "value_proposition": { "type": "text" },
                "pricing_strategy": { "type": "text" },
                "distribution_channels": { "type": "text" },
                "online_presence": { "type": "text" },
                "content_strategy": { "type": "text" },
                "seo_optimization": { "type": "text" },
                "paid_advertising": { "type": "text" },
                "public_relations": { "type": "text" },
                "partnerships": { "type": "text" },
                "customer_acquisition": { "type": "text" },
                "retention": { "type": "text" }
            }
        },
        "management_team": {
            "properties": {
                "description": { "type": "text" },
                "roles": {
                    "type": "object", # or nested
                    "properties": {
                        "role": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
                        "description": { "type": "text" }
                    }
                }
            }
        },
        "financial_projections": {
            "properties": {
                "potential_monthly_revenue": { "type": "text" },
                "revenue_streams": { "type": "text" },
                "cost_structure": { "type": "text" }
            }
        },
        
        "call_to_action": { "type": "text" },
        "plan_id": { "type": "keyword" },
        "cluster_id": { "type": "long" },
        "subreddit": { "type": "keyword" },
        "original_summary": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 512 } } },
        "cluster_summary": { "type": "text" },
        
        "is_viable_business": { "type": "boolean" },
        "viability_score": { "type": "long" },
        "is_saas": { "type": "boolean" },
        "is_solo_entrepreneur_possible": { "type": "boolean" },
        
        "message_ids": { "type": "keyword" }, # Stored as list of keywords (IDs)
        "texts_combined": { "type": "text" },
        "total_ups": { "type": "long" },
        "total_downs": { "type": "long" },
        "message_count": { "type": "long" },
        "generated_plan": { "type": "keyword" },
        
        "generated_at": { "type": "date" }
    }
}

def make_serializable(obj):
    """Recursively convert numpy types to python types."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    return obj

async def manage_indices(es: AsyncElasticsearch, mapping: Dict[str, Any], skip_backup: bool = False):
    """
    Manages index creation and backup.
    """
    exists = await es.indices.exists(index=INDEX_NAME)
    
    if exists:
        if skip_backup:
            console.print(f"[yellow]Skipping backup (--skip-backup flag set)[/yellow]")
        else:
            backup_name = f"{INDEX_NAME}_backup_{int(time.time())}"
            console.print(f"Index [{INDEX_NAME}] exists. Creating backup: [{backup_name}]")
            
            try:
                task_info = await es.reindex(
                    body={
                        "source": {"index": INDEX_NAME},
                        "dest": {"index": backup_name}
                    },
                    wait_for_completion=False,
                    request_timeout=300
                )
                task_id = task_info.get('task')
                console.print(f"[dim]Backup started as background task: {task_id}[/dim]")
                console.print(f"[green]Backup initiated (running in background).[/green]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not create backup: {e}[/yellow]")
    
        # Delete old index to apply new mapping cleanly
        await es.indices.delete(index=INDEX_NAME)
        console.print(f"Deleted old index [{INDEX_NAME}].")

    # Create new index with mapping
    await es.indices.create(index=INDEX_NAME, body={"mappings": mapping})
    console.print(f"[green]Created new index [{INDEX_NAME}] with updated mapping.[/green]")

def convert_polars_to_es_docs(df: pl.DataFrame) -> List[Dict[str, Any]]:
    """
    Converts polars DataFrame to a list of dicts suitable for ES indexing.
    """
    # Convert to dicts
    docs = df.to_dicts()
    
    # Process docs
    processed_docs = []
    for doc in docs:
        # Ensure serialization (handle numpy arrays etc)
        doc = make_serializable(doc)
        
        # Parse message_ids if it's a string looking like a JSON list
        if "message_ids" in doc and isinstance(doc["message_ids"], str) and doc["message_ids"].startswith("["):
            try:
                doc["message_ids"] = json.loads(doc["message_ids"])
            except:
                pass # Leave as string if parse fails

        doc["_index"] = INDEX_NAME
        if "plan_id" in doc and doc["plan_id"]:
            doc["_id"] = doc["plan_id"]
        
        doc["generated_at"] = datetime.datetime.now().isoformat()
        processed_docs.append(doc)
        
    return processed_docs

async def main(skip_backup: bool = False):
    console.rule("[bold purple]Phase 7.2: Elasticsearch Indexing (Merged)[/bold purple]")
    
    # 1. Connect to ES
    es = AsyncElasticsearch(
        f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}",
        request_timeout=120
    )
    try:
        info = await es.info()
        console.print(f"Connected to Elasticsearch: {info['version']['number']}")
    except Exception as e:
        console.print(f"[red]Error connecting to Elasticsearch: {e}[/red]")
        return

    # 2. Gather Data
    console.print(f"Scanning {PLANS_DIR} for parquet files...")
    # Look for the specific file pattern or just all parquet files?
    # User mentioned "AItradingOpportunity_merged.parquet".
    # We will search for all .parquet in that dir.
    parquet_files = glob.glob(os.path.join(PLANS_DIR, "*.parquet"))
    
    if not parquet_files:
        console.print("[red]No parquet files found in merged_dataset directory.[/red]")
        await es.close()
        return

    console.print(f"Found {len(parquet_files)} files. Reading data...")
    
    # 4. Manage Indices
    await manage_indices(es, BASE_MAPPING, skip_backup=skip_backup)
    
    # 5. Index Data sequentially
    total_indexed = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} files"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Indexing files...", total=len(parquet_files))
        
        for file_path in parquet_files:
            try:
                console.print(f"Processing {os.path.basename(file_path)}...")
                df = pl.read_parquet(file_path)
                
                docs = convert_polars_to_es_docs(df)
                
                if not docs:
                    progress.advance(task)
                    continue
                
                success, failed = await async_bulk(es, docs, chunk_size=500, stats_only=True)
                total_indexed += success
                
                if failed:
                    console.print(f"[yellow]Failed {failed} docs in {os.path.basename(file_path)}[/yellow]")
                    
            except Exception as e:
                console.print(f"[red]Error processing {os.path.basename(file_path)}: {e}[/red]")
                import traceback
                traceback.print_exc()
            
            progress.advance(task)
    
    console.print(f"[green]Successfully indexed total: {total_indexed}[/green]")
    
    await es.close()
    console.print("[bold green]Phase 7.2 Complete![/bold green]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 7.2: Index merged business plans to Elasticsearch")
    parser.add_argument("--skip-backup", action="store_true", help="Skip backing up the existing index")
    args = parser.parse_args()
    
    asyncio.run(main(skip_backup=args.skip_backup))
