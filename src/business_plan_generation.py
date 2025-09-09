import asyncio
import csv
import os
import json
from typing import List, Dict, Any
import re # Import regex
import uuid # Import uuid

import google.generativeai as genai
from qdrant_client import QdrantClient, models
from elasticsearch import AsyncElasticsearch # For asynchronous Elasticsearch operations
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Configuration constants
SUMMARIES_CSV_PATH = "/home/coinsafe/business-finder/summaries.csv"
ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200
ELASTICSEARCH_INDEX = "business_plans"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_BUSINESS_PLANS_COLLECTION = "business_plans_embeddings"

# Global variable for embedding model (initialized once)
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2') # CPU-based for this part
    return _embedding_model

async def generate_business_plan(opportunity_summary: str) -> Dict[str, Any]:
    """
    Generates a detailed business plan using Google's Gemini 1.5 Flash model.
    """
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")

    prompt = f"""
    Generate a comprehensive business plan based on the following core business opportunity. 
    The plan should be structured as a JSON object with the following keys:
    - \"title\": A concise title for the business plan.
    - \"executive_summary\": A brief overview of the business idea, problem it solves, and solution.
    - \"problem\": Detailed description of the problem being addressed.
    - \"solution\": Detailed description of the proposed solution.
    - \"market_analysis\": Target market, market size, and trends.
    - \"competition\": Analysis of competitors and competitive advantages.
    - \"marketing_strategy\": How to reach the target market.
    - \"management_team\": Key team members and their roles (placeholder if not applicable).
    - \"financial_projections\": High-level revenue and cost estimates (placeholder if not applicable).
    - \"call_to_action\": Next steps or what is needed.

    Core Business Opportunity: {opportunity_summary}

    Ensure the output is ONLY a valid JSON object, with no additional text or formatting outside the JSON.
    """

    try:
        response = await model.generate_content_async(prompt)
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason = response.prompt_feedback.block_reason.name
            print(f"Business plan generation blocked for summary: {opportunity_summary[:50]}... due to: {block_reason}")
            return {"error": f"Blocked: {block_reason}", "summary": opportunity_summary}
        
        raw_response_text = response.text.strip()
        
        # Try to extract JSON block using regex
        json_match = re.search(r"```json\n(.*)\n```", raw_response_text, re.DOTALL)
        if json_match:
            json_string = json_match.group(1)
        else:
            json_string = raw_response_text # Assume the whole response is JSON if no ```json block

        # Attempt to parse the response as JSON
        try:
            business_plan = json.loads(json_string)
            business_plan["summary_text"] = opportunity_summary # Add original summary for reference
            return business_plan
        except json.JSONDecodeError:
            print(f"Failed to parse JSON for summary: {opportunity_summary[:50]}...\nRaw response: {raw_response_text}")
            return {"error": "JSON parsing failed", "raw_response": raw_response_text, "summary": opportunity_summary}

    except Exception as e:
        print(f"Error generating business plan for summary: {opportunity_summary[:50]}... Error: {e}")
        return {"error": f"Generation failed: {e}", "summary": opportunity_summary}

async def main_business_plan_generation():
    print("Starting Phase 4: Massively Parallel Business Plan Generation & Hybrid Storage...")

    # Read opportunity summaries from CSV
    opportunity_summaries = []
    if not os.path.exists(SUMMARIES_CSV_PATH):
        print(f"Error: Summaries CSV not found at {SUMMARIES_CSV_PATH}. Please run Phase 3 first.")
        return

    with open(SUMMARIES_CSV_PATH, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            opportunity_summaries.append(row['summary'])
    print(f"Loaded {len(opportunity_summaries)} opportunity summaries from CSV.")

    # Create tasks for parallel business plan generation
    print("Generating business plans using Gemini 1.5 Flash (asynchronously)...")
    generation_tasks = [generate_business_plan(summary) for summary in opportunity_summaries]
    business_plans = await asyncio.gather(*generation_tasks)
    print("Finished generating business plans.")

    # Initialize Elasticsearch client
    es_client = AsyncElasticsearch(f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}")
    
    # Check Elasticsearch connection
    try:
        await es_client.info()
        print("Connected to Elasticsearch.")
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}. Please ensure Elasticsearch is running.")
        return

    # Initialize Qdrant client
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Create Qdrant collection for business plan embeddings
    embedding_model = get_embedding_model()
    vector_size = embedding_model.get_sentence_embedding_dimension()
    print(f"Creating Qdrant collection '{QDRANT_BUSINESS_PLANS_COLLECTION}' with vector size {vector_size}...")
    qdrant_client.recreate_collection(
        collection_name=QDRANT_BUSINESS_PLANS_COLLECTION,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )
    print("Qdrant business plans collection created/recreated.")

    # Store business plans in Elasticsearch and Qdrant
    print("Storing business plans in Elasticsearch and Qdrant...")
    es_bulk_actions = []
    qdrant_points = []
    for i, plan in enumerate(business_plans):
        if "error" in plan:
            print(f"Skipping blocked/failed plan for summary: {plan['summary'][:50]}...") # Corrected f-string
            continue

        # Store in Elasticsearch
        es_bulk_actions.append({"index": {"_index": ELASTICSEARCH_INDEX, "_id": str(uuid.uuid4())}})
        es_bulk_actions.append(plan)

        # Generate embedding for executive summary and store in Qdrant
        executive_summary = plan.get("executive_summary", "")
        if executive_summary:
            embedding = embedding_model.encode(executive_summary).tolist()
            qdrant_points.append(models.PointStruct(
                id=str(uuid.uuid4().hex), # Unique ID for Qdrant point
                vector=embedding,
                payload={
                    "title": plan.get("title"),
                    "executive_summary": executive_summary,
                    "original_summary": plan.get("summary_text")
                }
            ))

        # Bulk insert into Elasticsearch and Qdrant periodically
        if len(es_bulk_actions) >= 500: # Batch size for Elasticsearch (note: this is 250 actual documents)
            await es_client.bulk(operations=es_bulk_actions)
            es_bulk_actions = []
        
        if len(qdrant_points) >= 100: # Batch size for Qdrant
            qdrant_client.upsert(collection_name=QDRANT_BUSINESS_PLANS_COLLECTION, points=qdrant_points)
            qdrant_points = []

    # Insert any remaining items
    if es_bulk_actions:
        await es_client.bulk(operations=es_bulk_actions)
    if qdrant_points:
        qdrant_client.upsert(collection_name=QDRANT_BUSINESS_PLANS_COLLECTION, points=qdrant_points)

    print("Finished storing business plans.")
    print("Phase 4: Massively Parallel Business Plan Generation & Hybrid Storage complete.")

if __name__ == "__main__":
    asyncio.run(main_business_plan_generation())