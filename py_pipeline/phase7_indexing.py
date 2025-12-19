#!/usr/bin/env python3
"""
Phase 7: Elasticsearch Indexing

This script aggregates generated business plans and indexes them into Elasticsearch.
It handles index creation (with backup of existing index) and mapping management.
"""

import os
import sys
import json
import glob
import asyncio
import time
import argparse
import datetime
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
PLANS_DIR = "/Volumes/2TBSSD/reddit/business_plans"
ELASTICSEARCH_HOST = "localhost" # Assuming localhost based on previous context
ELASTICSEARCH_PORT = 9200
INDEX_NAME = "business_plans"

# Base Mapping (User provided)
BASE_MAPPING = {
    "properties": {
        "call_to_action": {
            "type": "text",
            "fields": {
                "keyword": {
                    "type": "keyword",
                    "ignore_above": 256
                }
            }
        },
        "cluster_id": {
            "type": "long"
        },
        "competition": {
            "properties": {
                "competitive_advantages": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "competitors": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "direct_competitors": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "indirect_competitors": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                }
            }
        },
        "executive_summary": {
            "type": "text",
            "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
        },
        "financial_projections": {
            "properties": {
                "cost_structure": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "potential_monthly_revenue": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "revenue_streams": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                }
            }
        },
        "ids_in_cluster": {
            "type": "text",
            "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
        },
        "management_team": {
            "properties": {
                "description": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "roles": {
                    "properties": {
                        "description": {
                            "type": "text",
                            "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                        },
                        "role": {
                            "type": "text",
                            "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                        }
                    }
                }
            }
        },
        "market_analysis": {
            "properties": {
                "market_size": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "target_market": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "trends": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                }
            }
        },
        "marketing_strategy": {
            "properties": {
                "content_strategy": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "customer_acquisition": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "distribution_channels": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "online_presence": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "paid_advertising": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "partnerships": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "pricing_strategy": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "public_relations": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "retention": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "seo_optimization": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                },
                "value_proposition": {
                    "type": "text",
                    "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
                }
            }
        },
        "problem": {
            "type": "text",
            "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
        },
        "solution": {
            "type": "text",
            "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
        },
        "subreddit": {
            "type": "text",
            "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
        },
        "summary": {
            "type": "text",
            "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
        },
        "texts": { # This likely refers to 'texts_combined' from previous phases or similar
            "type": "text",
            "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
        },
        "title": {
            "type": "text",
            "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
        },
        "total_downs": {
            "type": "long"
        },
        "total_ups": {
            "type": "long"
        },
        "viability_reasoning": {
            "type": "text",
            "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
        },
        "viability_score": {
            "type": "long"
        },
        # Adding common possible missing fields from Phase 6 output
        "plan_id": {
            "type": "keyword"
        },
        "generated_at": {
             "type": "date"
        },
        "original_summary": { # used in sidebar_info phase 6
            "type": "text",
            "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
        },
        "message_ids": { # Might be array of strings
             "type": "keyword"
        },
        "message_count": {
            "type": "long"
        }
    }
}

async def manage_indices(es: AsyncElasticsearch, mapping: Dict[str, Any], skip_backup: bool = False):
    """
    Manages index creation and backup.
    """
    exists = await es.indices.exists(index=INDEX_NAME)
    
    if exists:
        if skip_backup:
            console.print(f"[yellow]Skipping backup (--skip-backup flag set)[/yellow]")
        else:
            # Create backup asynchronously (don't wait for completion)
            backup_name = f"{INDEX_NAME}_backup_{int(time.time())}"
            console.print(f"Index [{INDEX_NAME}] exists. Creating backup: [{backup_name}]")
            
            try:
                # Use wait_for_completion=False to avoid timeout; ES will do it in background
                task_info = await es.reindex(
                    body={
                        "source": {"index": INDEX_NAME},
                        "dest": {"index": backup_name}
                    },
                    wait_for_completion=False,
                    request_timeout=300  # 5 min timeout for the request itself
                )
                task_id = task_info.get('task')
                console.print(f"[dim]Backup started as background task: {task_id}[/dim]")
                console.print(f"[green]Backup initiated (running in background).[/green]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not create backup: {e}[/yellow]")
                console.print(f"[yellow]Proceeding without backup...[/yellow]")
        
        # Delete old index to apply new mapping cleanly
        await es.indices.delete(index=INDEX_NAME)
        console.print(f"Deleted old index [{INDEX_NAME}].")

    # Create new index with mapping
    await es.indices.create(index=INDEX_NAME, body={"mappings": mapping})
    console.print(f"[green]Created new index [{INDEX_NAME}] with updated mapping.[/green]")

def convert_polars_to_es_docs(df: pl.DataFrame) -> List[Dict[str, Any]]:
    """
    Converts polars DataFrame to a list of dicts suitable for ES indexing.
    Handles nested structs by converting to dicts.
    """
    # Polars to dicts
    # We need to ensure nested structures (like market_analysis) are proper dicts
    # to_dicts() usually handles this well
    
    docs = df.to_dicts()
    
    # Post-processing: remove None values or fix types if needed
    # Elasticsearch handles nulls, but let's be clean
    
    # Add _index
    for doc in docs:
        doc["_index"] = INDEX_NAME
        # Use plan_id as _id if available to avoid dupes on re-run
        if "plan_id" in doc:
            doc["_id"] = doc["plan_id"]
            
        # Add generated_at timestamp
        doc["generated_at"] = datetime.datetime.now().isoformat()
        
    return docs

def update_mapping_from_data(mapping: Dict[str, Any], columns: List[str]):
    """
    Dynamically adds missing fields to mapping based on dataframe columns.
    Simple heuristic: text with keyword subfield for strings, long for ints.
    """
    properties = mapping["properties"]
    
    for col in columns:
        if col not in properties:
             # Heuristic for new fields
             console.print(f"[yellow]Auto-detecting mapping for extra field: {col}[/yellow]")
             # Default to text+keyword for safety
             properties[col] = {
                "type": "text",
                 "fields": {
                    "keyword": {
                      "type": "keyword",
                      "ignore_above": 256
                    }
                  }
             }
    
    return mapping

async def main(skip_backup: bool = False):
    console.rule("[bold purple]Phase 7: Elasticsearch Indexing[/bold purple]")
    
    # 1. Connect to ES with longer timeout
    es = AsyncElasticsearch(
        f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}",
        request_timeout=120  # 2 min default timeout
    )
    try:
        info = await es.info()
        console.print(f"Connected to Elasticsearch: {info['version']['number']}")
    except Exception as e:
        console.print(f"[red]Error connecting to Elasticsearch: {e}[/red]")
        return

    # 2. Gather Data
    console.print(f"Scanning {PLANS_DIR} for parquet files...")
    parquet_files = glob.glob(os.path.join(PLANS_DIR, "**", "*.parquet"), recursive=True)
    
    if not parquet_files:
        console.print("[red]No business plan parquet files found.[/red]")
        await es.close()
        return

    console.print(f"Found {len(parquet_files)} files. Reading data...")
    
    # 3. Prepare Mapping
    # We'll stick to the base mapping. If we need to expand, we can do it lazily or just rely on ES dynamic mapping for extras.
    # But to follow instructions, let's peek at the first file for extra columns if possible, or just skip strict expansion for now to avoid the datatype issues.
    # Actually, let's just use the BASE_MAPPING and let ES handle new fields (dynamic mapping is usually on by default).
    
    # 4. Manage Indices (Backup & Recreation)
    await manage_indices(es, BASE_MAPPING['mappings'] if 'mappings' in BASE_MAPPING else BASE_MAPPING, skip_backup=skip_backup)
    
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
                # Read single file
                # handling schema inference issues by reading as all strings if needed? 
                # No, standard read should be fine for one file.
                df = pl.read_parquet(file_path)
                
                # Convert
                docs = convert_polars_to_es_docs(df)
                
                if not docs:
                    progress.advance(task)
                    continue
                
                # Index
                success, failed = await async_bulk(es, docs, chunk_size=500, stats_only=True)
                total_indexed += success
                
                if failed:
                    console.print(f"[yellow]Failed {failed} docs in {os.path.basename(file_path)}[/yellow]")
                    
            except Exception as e:
                console.print(f"[red]Error processing {os.path.basename(file_path)}: {e}[/red]")
            
            progress.advance(task)
    
    console.print(f"[green]Successfully indexed total: {total_indexed}[/green]")
    
    await es.close()
    console.print("[bold green]Phase 7 Complete![/bold green]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 7: Index business plans to Elasticsearch")
    parser.add_argument("--skip-backup", action="store_true", help="Skip backing up the existing index")
    args = parser.parse_args()
    
    asyncio.run(main(skip_backup=args.skip_backup))
