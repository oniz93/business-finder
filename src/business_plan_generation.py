import asyncio
import os
import json
from typing import Dict, Any
import re
import uuid
import glob
import pandas as pd

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

# Global variable for embedding model (initialized once)
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

async def generate_business_plan(opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a detailed business plan using Google's Gemini 2.5 Flash model,
    and merges it with the original opportunity data.
    """
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
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

async def main_business_plan_generation():
    print("Starting Phase 4: Massively Parallel Business Plan Generation & Hybrid Storage...")

    # Read opportunity summaries from all parquet files in the directory
    parquet_files = glob.glob(os.path.join(SUMMARIES_DIR, "*_clusters.parquet"))
    if not parquet_files:
        print(f"Error: No summary parquet files found in {SUMMARIES_DIR}. Please run Phase 3 first.")
        return

    df = pd.concat([pd.read_parquet(f) for f in parquet_files], ignore_index=True)
    opportunities = df.to_dict('records')
    print(f"Loaded {len(opportunities)} opportunity summaries from {len(parquet_files)} files.")

    # Move processed files to a 'computed' subdirectory to prevent re-ingestion
    computed_dir = os.path.join(SUMMARIES_DIR, "computed")
    os.makedirs(computed_dir, exist_ok=True)
    print(f"Moving {len(parquet_files)} processed file(s) to '{computed_dir}'...")
    for file_path in parquet_files:
        try:
            file_name = os.path.basename(file_path)
            destination_path = os.path.join(computed_dir, file_name)
            os.rename(file_path, destination_path)
        except OSError as e:
            print(f"Error moving file {file_path}: {e}")

    # Create tasks for parallel business plan generation
    print(f"Generating {len(opportunities)} business plans using Gemini (asynchronously)...")
    generation_tasks = [generate_business_plan(opp) for opp in opportunities]
    business_plans = await asyncio.gather(*generation_tasks)
    print("Finished generating business plans.")

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

        # The 'plan' dictionary now contains the full merged data
        es_bulk_actions.append({"index": {"_index": ELASTICSEARCH_INDEX, "_id": str(uuid.uuid4())}})
        es_bulk_actions.append(plan)

        # Generate embedding for executive summary and store in Qdrant
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

        # Bulk insert periodically
        if len(es_bulk_actions) >= 500:
            await es_client.bulk(operations=es_bulk_actions)
            es_bulk_actions = []
        if len(qdrant_points) >= 100:
            qdrant_client.upsert(collection_name=QDRANT_BUSINESS_PLANS_COLLECTION, points=qdrant_points)
            qdrant_points = []

    # Insert any remaining items
    if es_bulk_actions: await es_client.bulk(operations=es_bulk_actions)
    if qdrant_points: qdrant_client.upsert(collection_name=QDRANT_BUSINESS_PLANS_COLLECTION, points=qdrant_points)

    print("Finished storing business plans.")

    # Close client connections
    await es_client.close()
    qdrant_client.close()

    print("Phase 4 complete.")

if __name__ == "__main__":
    asyncio.run(main_business_plan_generation())