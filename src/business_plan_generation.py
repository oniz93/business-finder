import asyncio
import os
import json
from typing import Dict, Any
import re
import uuid
import glob
import pandas as pd
import time
import argparse
import numpy as np

import google.generativeai as genai
from qdrant_client import QdrantClient, models
from elasticsearch import AsyncElasticsearch
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Configuration ---
SUMMARIES_DIR = "/home/coinsafe/business-finder/data/summaries"
ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200
ELASTICSEARCH_INDEX = "business_plans"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_BUSINESS_PLANS_COLLECTION = "business_plans_embeddings"

MODEL_RPMS = {
    "models/gemini-2.5-flash": 950,
    "models/gemini-2.5-pro": 135,
    "models/gemini-2.5-flash-lite": 3950,
}

# Global variable for embedding model (initialized once)
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def convert_ndarrays_to_lists(obj):
    if isinstance(obj, dict):
        return {k: convert_ndarrays_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_ndarrays_to_lists(elem) for elem in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

async def run_gemini_tasks_in_chunks(tasks, model_name: str):
    """Runs a list of asyncio tasks in chunks with rate limiting."""
    rpm = MODEL_RPMS.get(model_name, 150)  # Default to a safe RPM
    chunk_size = rpm  # Process up to a minute's worth of requests in each chunk
    results = []
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i+chunk_size]
        start_time = time.time()
        print(f"Processing chunk {i//chunk_size + 1}/{(len(tasks) + chunk_size - 1)//chunk_size} with {len(chunk)} tasks...")
        results.extend(await asyncio.gather(*chunk))
        end_time = time.time()
        elapsed = end_time - start_time
        
        if elapsed < 120 and i + chunk_size < len(tasks):
            sleep_time = 120 - elapsed
            print(f"Rate limit: sleeping for {sleep_time:.2f} seconds.")
            await asyncio.sleep(sleep_time)
    return results

async def generate_business_plan(opportunity_data: Dict[str, Any], model) -> Dict[str, Any]:
    """
    Generates a detailed business plan using Google's Gemini 2.5 Flash model,
    and merges it with the original opportunity data.
    """
    opportunity_summary = opportunity_data.get("summary", "")

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
        - **target_market**: Describe the ideal customer profile. Be specific about demographics (age, location, income), psychographics (interests, values, lifestyle), and behaviors. Can be a string or a list of strings for multiple segments.
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
        - **potential_monthly_revenue**: A realistic, data-driven estimate of the potential monthly revenue in USD for the first 12-24 months. Provide a range and justify the number with a brief explanation (e.g., based on market size, pricing, and a conservative customer acquisition rate).
        - **revenue_streams**: How will the business make money? List all potential sources of income (e.g., subscription fees, advertising, data monetization).
        - **cost_structure**: What are the major anticipated costs and expenses? (e.g., salaries, marketing spend, software/hosting, rent, legal fees).
    - **call_to_action**: A compelling final statement that summarizes the opportunity and encourages action or investment.

    **JSON Structure to be generated:**
    {{
      "title": "String",
      "executive_summary": "String",
      "problem": "String",
      "solution": "String",
      "market_analysis": {{
        "target_market": "String OR Array of Strings",
        "market_size": "String",
        "trends": ["String"]
      }},
      "competition": {{
        "competitors": ["String"],
        "direct_competitors": ["String"],
        "indirect_competitors": ["String"],
        "competitive_advantages": ["String"]
      }},
      "marketing_strategy": {{
        "value_proposition": "String",
        "pricing_strategy": "String",
        "distribution_channels": "String",
        "online_presence": "String",
        "content_strategy": "String",
        "seo_optimization": "String",
        "paid_advertising": "String",
        "public_relations": "String",
        "partnerships": ["String"],
        "customer_acquisition": ["String"],
        "retention": ["String"]
      }},
      "management_team": {{
        "description": "String",
        "roles": [
          {{
            "role": "String",
            "description": "String"
          }}
        ]
      }},
      "financial_projections": {{
        "potential_monthly_revenue": "String (e.g., '$10,000 - $25,000 USD. Justification: ...')",
        "revenue_streams": ["String"],
        "cost_structure": ["String"]
      }},
      "call_to_action": "String"
    }}

    Core Business Opportunity: {opportunity_summary}

    Ensure the output is ONLY a valid JSON object, with no additional text or formatting outside the JSON.
    """

    try:
        response = await model.generate_content_async(prompt)
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason = response.prompt_feedback.block_reason.name
            print(f"Business plan generation blocked for summary: {opportunity_summary[:50]}... due to: {block_reason}")
            return {**opportunity_data, "error": f"Blocked: {block_reason}"}

        raw_response_text = response.text.strip()
        json_match = re.search(r"```json\n(.*)\n```", raw_response_text, re.DOTALL)
        json_string = json_match.group(1) if json_match else raw_response_text

        try:
            business_plan = json.loads(json_string)
            # Merge original data with the new plan
            return {**opportunity_data, **business_plan}
        except json.JSONDecodeError:
            print(f"Failed to parse JSON for summary: {opportunity_summary[:50]}...")
            return {**opportunity_data, "error": "JSON parsing failed", "raw_response": raw_response_text}

    except Exception as e:
        print(f"Error generating business plan for summary: {opportunity_summary[:50]}... Error: {e}")
        return {**opportunity_data, "error": f"Generation failed: {e}"}

async def score_business_viability(summary: str, model) -> Dict[str, Any]:
    """Scores a business opportunity summary using a Gemini prompt."""
    prompt = f"""
    Evaluate if this is a REAL business opportunity (score 0-10):
    - Is there a clear, solvable problem? (not just venting)
    - Would people actually pay money for a solution?
    - Is it actionable (not "someone should invent teleportation")?
    - Does a viable market likely exist?

    Text: {summary}

    Return ONLY a JSON: {{"score": X, "reasoning": "brief explanation"}}
    """
    try:
        response = await model.generate_content_async(prompt)
        # Extract JSON from the response, handling potential markdown code blocks
        raw_response_text = response.text.strip()
        json_match = re.search(r"```json\n(.*)\n```", raw_response_text, re.DOTALL)
        json_string = json_match.group(1) if json_match else raw_response_text
        
        result = json.loads(json_string)
        return result
    except Exception as e:
        print(f"Error during scoring for summary: {summary[:50]}... Error: {e}")
        return {"score": 0, "reasoning": f"Scoring failed: {e}"}

async def validate_business_viability(summary: str, model) -> bool:
    """Quick validation before expensive business plan generation"""
    
    prompt = f"""
    Is this a REALISTIC business opportunity or just wishful thinking/complaining?
    
    RED FLAGS (answer NO if present):
    - Requires breakthrough technology that doesn't exist
    - "Someone should just..." without feasible path
    - Solves a problem that doesn't actually bother people enough to pay
    - Requires government/major corporations to change fundamentally
    
    GREEN FLAGS (answer YES if present):
    - Clear customer pain point with willingness to pay
    - Feasible with current technology
    - Similar businesses exist (proves market)
    - Actionable by small team
    
    Summary: {summary}
    
    Answer ONLY: YES or NO
    """
    
    try:
        response = await model.generate_content_async(prompt)
        return "YES" in response.text.upper()
    except Exception as e:
        print(f"Error during viability validation for summary: {summary[:50]}... Error: {e}")
        return False

async def main_business_plan_generation(start_from: str = None):
    print("Starting Phase 4: Massively Parallel Business Plan Generation & Hybrid Storage...")

    opportunities = []
    scored_opportunities = []
    viable_opportunities = []
    business_plans = []

    # --- Stage 1: Load initial data or from checkpoint ---
    if start_from is None:
        print("Starting from the beginning...")
        parquet_files = glob.glob(os.path.join(SUMMARIES_DIR, "*_clusters.parquet"))
        if not parquet_files:
            print(f"Error: No summary parquet files found in {SUMMARIES_DIR}. Please run Phase 3 first.")
            return
        df = pd.concat([pd.read_parquet(f) for f in parquet_files], ignore_index=True)
        opportunities = df.to_dict('records')
        print(f"Loaded {len(opportunities)} opportunity summaries from {len(parquet_files)} files.")
    else:
        print(f"Attempting to start from checkpoint: {start_from}")

    # --- Stage 2: Scoring ---
    if start_from is None:
        print(f"Scoring {len(opportunities)} opportunities...")
        scoring_model_name = "models/gemini-1.5-flash-latest"
        scoring_model = genai.GenerativeModel(scoring_model_name)
        scoring_tasks = [score_business_viability(opp['summary'], scoring_model) for opp in opportunities]
        scoring_results = await run_gemini_tasks_in_chunks(scoring_tasks, scoring_model_name)

        for opp, result in zip(opportunities, scoring_results):
            if result.get('score', 0) >= 7:
                opp['viability_score'] = result['score']
                opp['viability_reasoning'] = result.get('reasoning', '')
                scored_opportunities.append(opp)
        print(f"Scoring complete. Found {len(scored_opportunities)} opportunities with a score >= 7.")
        if scored_opportunities:
            pd.DataFrame(scored_opportunities).to_parquet(os.path.join(SUMMARIES_DIR, "01_scored_opportunities.parquet"))
            print(f"Saved {len(scored_opportunities)} scored opportunities to checkpoint file.")
    elif start_from in ["01_scored_opportunities.parquet", "02_validated_opportunities.parquet", "03_generated_business_plans.parquet"]:
        print("Skipping scoring step.")
        scored_opportunities_df = pd.read_parquet(os.path.join(SUMMARIES_DIR, "01_scored_opportunities.parquet"))
        scored_opportunities = scored_opportunities_df.to_dict('records')

    # --- Stage 3: Validation ---
    if start_from is None or start_from == "01_scored_opportunities.parquet":
        print(f"Validating {len(scored_opportunities)} scored opportunities...")
        validation_model_name = "models/gemini-1.5-flash-latest"
        validation_model = genai.GenerativeModel(validation_model_name)
        validation_tasks = [validate_business_viability(opp['summary'], validation_model) for opp in scored_opportunities]
        validation_results = await run_gemini_tasks_in_chunks(validation_tasks, validation_model_name)
        
        viable_opportunities = [opp for opp, is_viable in zip(scored_opportunities, validation_results) if is_viable]
        print(f"Validation complete. Found {len(viable_opportunities)} viable opportunities.")
        if viable_opportunities:
            pd.DataFrame(viable_opportunities).to_parquet(os.path.join(SUMMARIES_DIR, "02_validated_opportunities.parquet"))
            print(f"Saved {len(viable_opportunities)} validated opportunities to checkpoint file.")
    elif start_from in ["02_validated_opportunities.parquet", "03_generated_business_plans.parquet"]:
        print("Skipping validation step.")
        viable_opportunities_df = pd.read_parquet(os.path.join(SUMMARIES_DIR, "02_validated_opportunities.parquet"))
        viable_opportunities = viable_opportunities_df.to_dict('records')

    # --- Stage 4: Business Plan Generation ---
    if start_from in [None, "01_scored_opportunities.parquet", "02_validated_opportunities.parquet"]:
        if not viable_opportunities:
            print("No viable opportunities to generate business plans for. Exiting.")
            return
        print(f"Generating {len(viable_opportunities)} business plans using Gemini (asynchronously)...")
        generation_model_name = "models/gemini-2.5-flash-lite"
        generation_model = genai.GenerativeModel(generation_model_name)
        generation_tasks = [generate_business_plan(opp, generation_model) for opp in viable_opportunities]
    business_plans = await run_gemini_tasks_in_chunks(generation_tasks, generation_model_name)
    print("Finished generating business plans.")

    # Convert any numpy arrays to lists before saving
    business_plans = [convert_ndarrays_to_lists(plan) for plan in business_plans]

    # --- Checkpoint 3: Generated Business Plans ---
    if business_plans:
        # Fix for pyarrow error: convert complex columns to JSON strings
        df_to_save = pd.DataFrame(business_plans)
        for col in ['market_analysis', 'competition', 'marketing_strategy', 'management_team', 'financial_projections']:
            if col in df_to_save.columns:
                df_to_save[col] = df_to_save[col].apply(json.dumps)
        df_to_save.to_parquet(os.path.join(SUMMARIES_DIR, "03_generated_business_plans.parquet"))
        print(f"Saved {len(business_plans)} generated business plans to checkpoint file.")
    elif start_from == "03_generated_business_plans.parquet":
        print("Skipping business plan generation step.")
        business_plans_df = pd.read_parquet(os.path.join(SUMMARIES_DIR, "03_generated_business_plans.parquet"))
        business_plans = business_plans_df.to_dict('records')

    # --- Stage 5: Backup and Storage ---
    if not business_plans:
        print("No business plans to process for backup and storage. Exiting.")
        return

    backup_file_path = os.path.join(SUMMARIES_DIR, "business_plans_backup.ndjson")
    print(f"Creating a backup of generated plans at: {backup_file_path}")
    with open(backup_file_path, "w") as f:
        count = 0
        for plan in business_plans:
            if "error" not in plan:
                f.write(json.dumps(plan) + "\n")
                count += 1
    print(f"Successfully backed up {count} business plans.")

    # Initialize clients
    es_client = AsyncElasticsearch(f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}")
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Setup Elasticsearch and Qdrant
    try:
        await es_client.info()
        print("Connected to Elasticsearch.")
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}. Please ensure it is running.")
        return

    embedding_model = get_embedding_model()
    vector_size = embedding_model.get_sentence_embedding_dimension()
    print(f"Recreating Qdrant collection '{QDRANT_BUSINESS_PLANS_COLLECTION}' with vector size {vector_size}...")
    qdrant_client.recreate_collection(
        collection_name=QDRANT_BUSINESS_PLANS_COLLECTION,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )
    print("Qdrant collection created/recreated.")

    # Store business plans in Elasticsearch and Qdrant
    print("Storing business plans in Elasticsearch and Qdrant...")
    es_bulk_actions = []
    qdrant_points = []
    for plan in business_plans:
        if "error" in plan:
            print(f"Skipping blocked/failed plan for summary: {plan.get('summary', 'N/A')[:50]}...")
            continue

        es_bulk_actions.append({"index": {"_index": ELASTICSEARCH_INDEX, "_id": str(uuid.uuid4())}})
        es_bulk_actions.append(plan)

        executive_summary = plan.get("executive_summary", "")
        if executive_summary:
            embedding = embedding_model.encode(executive_summary).tolist()
            qdrant_points.append(models.PointStruct(
                id=str(uuid.uuid4().hex),
                vector=embedding,
                payload={
                    "title": plan.get("title"),
                    "executive_summary": executive_summary,
                    "original_summary": plan.get("summary"),
                    "subreddit": plan.get("subreddit"),
                    "cluster_id": int(plan.get("cluster_id", -1))
                }
            ))

        if len(es_bulk_actions) >= 500:
            await es_client.bulk(operations=es_bulk_actions)
            es_bulk_actions = []
        if len(qdrant_points) >= 100:
            qdrant_client.upsert(collection_name=QDRANT_BUSINESS_PLANS_COLLECTION, points=qdrant_points)
            qdrant_points = []

    if es_bulk_actions: await es_client.bulk(operations=es_bulk_actions)
    if qdrant_points: qdrant_client.upsert(collection_name=QDRANT_BUSINESS_PLANS_COLLECTION, points=qdrant_points)

    print("Finished storing business plans.")

    await es_client.close()
    qdrant_client.close()

    print("Phase 4 complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate business plans from Reddit summaries.")
    parser.add_argument("--start-from", type=str, choices=["01_scored_opportunities.parquet", "02_validated_opportunities.parquet", "03_generated_business_plans.parquet"], help="Start the process from a specific checkpoint file.")
    args = parser.parse_args()

    asyncio.run(main_business_plan_generation(start_from=args.start_from))