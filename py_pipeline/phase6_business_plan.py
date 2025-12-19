#!/usr/bin/env python3
"""
Phase 6: Business Plan Generation

This script filters validated ideas from Phase 5 and generates comprehensive business plans.
It updates the original ideas with a reference UUID and saves the full plans.
"""

import os
import sys
import json
import asyncio
import uuid
import glob
import random
import time
import argparse
import re
from typing import List, Dict, Any, Optional

import polars as pl
import duckdb
import google.generativeai as genai
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

# Add project root for config if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

console = Console()

def clean_json_text(text: str) -> str:
    """
    Cleans common JSON syntax errors from LLM output, specifically unescaped backslashes.
    """
    # Remove markdown code blocks if present
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    
    # Fix invalid escape sequences (backslashes not followed by valid escape chars)
    # Valid escapes: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
    # We use a negative lookahead to identify backslashes that are NOT followed by a valid escape.
    # We checked for uXXXX specifically.
    text = re.sub(r'\\(?!([\\/bfnrt"]|u[0-9a-fA-F]{4}))', r'\\\\', text)
    
    return text.strip()

API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    console.print("[red]Error: GOOGLE_API_KEY not found in environment.[/red]")
    sys.exit(1)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

IDEAS_INPUT_DIR = "/Volumes/2TBSSD/reddit/ideas"
PLANS_OUTPUT_DIR = "/Volumes/2TBSSD/reddit/business_plans"

# Model Configuration
MODEL_NAME = "models/gemini-flash-lite-latest" # Use Flash Lite for speed/cost as per Phase 5 precedent or user pref? Phase 5 used flash-lite-latest. src uses 2.5-flash-lite.
# The user prompt mentions "Gemini 2.5 Pro" in memory, but code in src uses "2.5-flash-lite". I will use 1.5-flash logic or whatever is best. src uses `models/gemini-2.5-flash-lite`. I'll use that if available, or fall back to 1.5-flash.
# Let's stick to "gemini-2.5-flash-lite" as viewed in src code.

CONCURRENCY_LIMIT = 30 # Adjust based on rate limits

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------

business_plan_schema = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "executive_summary": {"type": "STRING"},
        "problem": {"type": "STRING"},
        "solution": {"type": "STRING"},
        "market_analysis": {
            "type": "OBJECT",
            "properties": {
                "target_market": {"type": "STRING"},
                "market_size": {"type": "STRING"},
                "trends": {"type": "ARRAY", "items": {"type": "STRING"}}
            },
            "required": ["target_market", "market_size", "trends"]
        },
        "competition": {
            "type": "OBJECT",
            "properties": {
                "competitors": {"type": "ARRAY", "items": {"type": "STRING"}},
                "direct_competitors": {"type": "ARRAY", "items": {"type": "STRING"}},
                "indirect_competitors": {"type": "ARRAY", "items": {"type": "STRING"}},
                "competitive_advantages": {"type": "ARRAY", "items": {"type": "STRING"}}
            },
            "required": ["competitors", "direct_competitors", "indirect_competitors", "competitive_advantages"]
        },
        "marketing_strategy": {
            "type": "OBJECT",
            "properties": {
                "value_proposition": {"type": "STRING"},
                "pricing_strategy": {"type": "STRING"},
                "distribution_channels": {"type": "STRING"},
                "online_presence": {"type": "STRING"},
                "content_strategy": {"type": "STRING"},
                "seo_optimization": {"type": "STRING"},
                "paid_advertising": {"type": "STRING"},
                "public_relations": {"type": "STRING"},
                "partnerships": {"type": "ARRAY", "items": {"type": "STRING"}},
                "customer_acquisition": {"type": "ARRAY", "items": {"type": "STRING"}},
                "retention": {"type": "ARRAY", "items": {"type": "STRING"}}
            },
            "required": [
                "value_proposition", "pricing_strategy", "distribution_channels",
                "online_presence", "content_strategy", "seo_optimization",
                "paid_advertising", "public_relations", "partnerships",
                "customer_acquisition", "retention"
            ]
        },
        "management_team": {
            "type": "OBJECT",
            "properties": {
                "description": {"type": "STRING"},
                "roles": {
                    "type": "ARRAY", 
                    "items": {
                        "type": "OBJECT", 
                        "properties": {
                            "role": {"type": "STRING"},
                            "description": {"type": "STRING"}
                        }
                    }
                }
            },
            "required": ["description", "roles"]
        },
        "financial_projections": {
            "type": "OBJECT",
            "properties": {
                "potential_monthly_revenue": {"type": "STRING"},
                "revenue_streams": {"type": "ARRAY", "items": {"type": "STRING"}},
                "cost_structure": {"type": "ARRAY", "items": {"type": "STRING"}}
            },
            "required": ["potential_monthly_revenue", "revenue_streams", "cost_structure"]
        },
        "call_to_action": {"type": "STRING"}
    },
    "required": [
        "title", "executive_summary", "problem", "solution", "market_analysis", 
        "competition", "marketing_strategy", "management_team", "financial_projections", "call_to_action"
    ]
}

# -----------------------------------------------------------------------------
# Logic
# -----------------------------------------------------------------------------

async def generate_plan(summary: str, sidebar_info: Dict[str, Any], semaphore: asyncio.Semaphore) -> Optional[Dict[str, Any]]:
    async with semaphore:
        prompt = f"""
        Generate a comprehensive and realistic business plan based on the following core business opportunity.
        The plan must be structured as a JSON object with the exact structure specified below.
        For each field, provide a detailed and well-researched answer.

        **Detailed Instructions for each section:**

        - **title**: A catchy and descriptive title for the business idea.
        - **executive_summary**: A concise overview of the entire business plan (2-3 paragraphs). It should be compelling and capture the essence of the business, including the problem, solution, target market, and financial potential.
        - **problem**: Clearly define the pain point or problem this business idea solves. Who is affected by it and why is it significant? Provide context and evidence.
        - **solution**: Describe your product or service and how it solves the identified problem. What are the key features and what makes your solution unique and superior to existing alternatives?
        - **market_analysis**:
            - **target_market**: Describe the ideal customer profile. Be specific about demographics (age, location, income), psychographics (interests, values, lifestyle), and behaviors.
            - **market_size**: Estimate the size of the target market (e.g., in number of potential customers or monetary value like TAM, SAM, SOM). Provide a brief justification for your estimate.
            - **trends**: List key trends in the market that could positively or negatively impact the business (e.g., technological advancements, social shifts, regulatory changes).
        - **competition**:
            - **competitors**: A general overview of the competitive landscape.
            - **direct_competitors**: List 2-3 companies that offer a very similar solution to the same target market.
            - **indirect_competitors**: List 2-3 companies that solve the same core problem but with a different type of solution.
            - **competitive_advantages**: What makes your business stronger than the competition? (e.g., proprietary technology, unique business model, key partnerships, lower cost, superior user experience).
        - **marketing_strategy**: A comprehensive plan to reach, attract, and retain customers.
            - **value_proposition**: A clear and compelling statement of the unique benefits you deliver to customers. Why should they choose you over anyone else?
            - **pricing_strategy**: How will you price your product/service? (e.g., subscription tiers, one-time fee, freemium, usage-based). Justify the choice.
            - **distribution_channels**: How will you deliver your product or service to your customers? (e.g., website, mobile app, physical stores, third-party marketplaces).
            - **online_presence**: Plan for your website, blog, and key social media platforms (e.g., Twitter, LinkedIn, Instagram).
            - **content_strategy**: What kind of content will you create to attract and engage your target audience? (e.g., blog posts, videos, tutorials, case studies).
            - **seo_optimization**: High-level plan to improve search engine rankings for relevant keywords.
            - **paid_advertising**: Strategy for using paid channels like Google Ads, social media ads, or sponsored content.
            - **public_relations**: How will you manage your public image and get media coverage? (e.g., press releases, outreach to journalists).
            - **partnerships**: Identify potential strategic partnerships to accelerate growth (e.g., with complementary businesses, influencers).
            - **customer_acquisition**: Specific tactics and channels you will use to acquire your first 1000 customers.
            - **retention**: Strategies to keep customers loyal, engaged, and reduce churn (e.g., email newsletters, community forums, loyalty programs).
        - **management_team**:
            - **description**: Describe the ideal founding team. What key skills, experience, and domain expertise are needed to make this business successful?
            - **roles**: List key roles to be filled in the first 1-2 years (e.g., CEO, CTO, CMO) and the primary responsibilities for each role.
        - **financial_projections**:
            - **potential_monthly_revenue**: A realistic, data-driven estimate of the potential monthly revenue in USD for the first 12-24 months. Provide a range and justify the number with a brief explanation.
            - **revenue_streams**: How will the business make money? List all potential sources of income.
            - **cost_structure**: What are the major anticipated costs and expenses?
        - **call_to_action**: A compelling final statement that summarizes the opportunity and encourages action or investment.

        Core Business Opportunity: {summary}

        Ensure the output follows the defined JSON schema.
        """

        try:
            model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=business_plan_schema
                )
            )

            # Retry logic
            for attempt in range(3):
                try:
                    response = await model.generate_content_async(prompt)
                    cleaned_text = clean_json_text(response.text)
                    result = json.loads(cleaned_text)
                    
                    # Merge sidebar info
                    result.update(sidebar_info)
                    return result

                except Exception as e:
                    if "429" in str(e):
                        wait_time = (2 ** attempt) + random.random()
                        # console.print(f"[yellow]Rate limit, retrying in {wait_time:.1f}s...[/yellow]")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise e
            
            return None

        except Exception as e:
            console.print(f"[red]Error generating plan: {e}[/red]")
            return None

async def main():
    console.rule("[bold purple]Phase 6: Business Plan Generation[/bold purple]")

    # 1. Scan for actionable ideas using DuckDB
    console.print(f"Scanning {IDEAS_INPUT_DIR} for viable ideas...")
    
    # We look for files recursively
    # We select path, cluster_id
    query = f"""
    SELECT 
        filename,
        cluster_id,
        cluster_summary,
        texts_combined,
        generated_plan
    FROM read_parquet('{os.path.join(IDEAS_INPUT_DIR, '**', '*.parquet')}', filename=true, hive_partitioning=true)
    WHERE 
        is_viable_business = true 
        AND is_saas = true 
        AND is_solo_entrepreneur_possible = true
    """
    
    try:
        con = duckdb.connect()
        # We need to filter out already generated ones.
        # But we also need to know if the file content matches our "actionable" criteria
        # DuckDB `read_parquet` handles globs.
        
        # Execute query
        df_candidates = con.execute(query).pl()
        
        # Filter where generated_plan is empty or null
        # Note: generated_plan might be empty string or null depending on writer
        candidates = df_candidates.filter(
            (pl.col("generated_plan").is_null()) | (pl.col("generated_plan") == "")
        )
        
        total_candidates = len(candidates)
        console.print(f"Found {total_candidates} viable ideas needing business plans (out of {len(df_candidates)} total viable).")
        
        if total_candidates == 0:
            console.print("[green]No new ideas to process. Exiting.[/green]")
            return

        # Group by filename to process file-by-file
        files_to_process = candidates["filename"].unique().to_list()
        
    except Exception as e:
        console.print(f"[red]Error during DuckDB scan: {e}[/red]")
        return
    
    # 2. Process each file
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} files"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        files_task = progress.add_task("Processing files...", total=len(files_to_process))
        
        for file_path in files_to_process:
            subreddit_name = os.path.basename(os.path.dirname(file_path)) # Parent dir usually subreddit
            progress.update(files_task, description=f"Processing {subreddit_name}")
            
            try:
                # Read entire file with Polars
                df_file = pl.read_parquet(file_path)
                
                # Identify rows to update
                # We use file candidates to filter memory df
                # Get the cluster_ids that need processing for this file
                target_clusters = candidates.filter(pl.col("filename")==file_path)["cluster_id"].to_list()
                
                if not target_clusters:
                    progress.advance(files_task)
                    continue

                # Prepare tasks
                tasks = []
                # Map cluster_id to row index or just iterate rows?
                # Polars iteration is fast enough for typical file sizes here
                
                rows_to_update = df_file.filter(pl.col("cluster_id").is_in(target_clusters))
                
                task_args = []
                for row in rows_to_update.iter_rows(named=True):
                    # We need to generate a UUID first? Or after?
                    # User says: "Add an uuid for each generated business plan. Update the corresponding idea marking generated_plan with the uuid"
                    plan_id = str(uuid.uuid4())
                    
                    # Store info for embedding/saving
                    sidebar_info = {
                        "plan_id": plan_id,
                        "cluster_id": row['cluster_id'],
                        "subreddit": subreddit_name,
                        "original_summary": row['cluster_summary']
                    }
                    
                    tasks.append(generate_plan(row['cluster_summary'], sidebar_info, semaphore))
                    task_args.append((row['cluster_id'], plan_id))

                # Run generation
                results = await asyncio.gather(*tasks)
                
                # Filter None
                valid_results = [r for r in results if r is not None]
                
                if not valid_results:
                    progress.advance(files_task)
                    continue
                
                # 3. Save Business Plans
                # We save per subreddit in PLANS_OUTPUT_DIR
                plans_subdir = os.path.join(PLANS_OUTPUT_DIR, subreddit_name or "unknown")
                os.makedirs(plans_subdir, exist_ok=True)
                
                plans_df = pl.DataFrame(valid_results)
                # Ensure complex types are handled or saved as is (Parquet supports nested)
                # Just in case, Polars handles nested structs/lists well for Parquet
                plans_file = os.path.join(plans_subdir, f"plans_{int(time.time())}.parquet")
                plans_df.write_parquet(plans_file)
                
                # 4. Update Ideas File
                # We need to update `generated_plan` column
                # Create a mapping dictionary or usage of join
                
                # Create a mapping dataframe
                updates_df = pl.DataFrame({
                    "cluster_id": [cid for cid, pid in task_args if any(r['plan_id'] == pid for r in valid_results)],
                    "new_plan_id": [pid for cid, pid in task_args if any(r['plan_id'] == pid for r in valid_results)]
                })
                
                # Join and update
                # Perform a left join on cluster_id
                # Then coalesce generated_plan
                
                # Cast cluster_id to match type if needed (assuming int64)
                
                joined = df_file.join(updates_df, on="cluster_id", how="left")
                
                # Update generated_plan column
                # If new_plan_id is present, use it, else keep original
                
                # Check if generated_plan exists, if not create it
                if "generated_plan" not in joined.columns:
                    joined = joined.with_columns(pl.lit("").alias("generated_plan"))
                
                # Use when/then/otherwise
                updated = joined.with_columns(
                    pl.when(pl.col("new_plan_id").is_not_null())
                    .then(pl.col("new_plan_id"))
                    .otherwise(pl.col("generated_plan"))
                    .alias("generated_plan")
                ).drop("new_plan_id")
                
                # Write back (overwrite)
                updated.write_parquet(file_path)
                
                console.log(f"Generated {len(valid_results)} plans for {subreddit_name}")

            except Exception as e:
                console.print(f"[red]Error processing {file_path}: {e}[/red]")
                import traceback
                traceback.print_exc()
            
            progress.advance(files_task)

if __name__ == "__main__":
    asyncio.run(main())
