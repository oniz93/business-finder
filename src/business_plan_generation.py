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
    The plan must be structured as a JSON object with the exact structure specified below. Some fields are optional and can be omitted if not applicable, but the overall structure must be maintained.

    Here is a description of each field to guide you:
    - `title`: A concise and compelling title for the business.
    - `executive_summary`: A high-level overview of the entire business plan, including the problem, solution, and key business goals.
    - `problem`: The specific pain point, need, or gap in the market that the business aims to solve.
    - `solution`: A clear description of the product, service, or platform and how it addresses the identified problem.
    - `market_analysis`:
        - `target_market`: The specific demographic, psychographic, and behavioral characteristics of the ideal customer. Can be a string or a list of strings for multiple segments.
        - `market_size`: An estimate of the total addressable market (TAM), serviceable available market (SAM), and serviceable obtainable market (SOM).
        - `trends`: Key industry and consumer trends that could impact the business.
    - `competition`:
        - `competitors`: A list of known existing or potential competitors.
        - `direct_competitors`: Competitors offering a very similar solution to the same target market.
        - `indirect_competitors`: Competitors solving the same core problem but with a different solution.
        - `competitive_advantages`: The unique features, technology, partnerships, or strategies that give the business an edge.
    - `marketing_strategy`:
        - `approach`: The overall philosophy or methodology for marketing (e.g., inbound, growth hacking, community-led).
        - `channels`: The specific platforms and channels to be used (e.g., "Content Marketing", "SEO", "Twitter", "Reddit").
        - `content_strategy`: The plan for creating and distributing valuable content to attract and engage the target audience.
        - `community_building`: Strategies for fostering a community around the product or brand.
        - `customer_acquisition`: Specific tactics for acquiring new customers.
        - `digital_marketing`: Strategies for online marketing, including social media, email marketing, and PPC.
        - `distribution_channels`: How the product or service will be delivered to customers.
        - `influencer_marketing`: Plans for leveraging influencers to reach a wider audience.
        - `messaging`: The core messages and brand voice to be used in all communications.
        - `online_presence`: How the business will be represented online (e.g., website, social media profiles).
        - `outreach`: Proactive methods for connecting with potential customers, partners, or media.
        - `outreach_channels`: Specific channels for outreach (e.g., "Cold Email", "LinkedIn Messaging").
        - `outreach_methods`: The techniques to be used for outreach.
        - `partnerships`: Potential strategic partnerships to accelerate growth.
        - `paid_advertising`: The strategy for using paid ad platforms (e.g., "Google Ads", "Facebook Ads").
        - `pricing_strategy`: How the product or service will be priced.
        - `public_relations`: Strategies for managing public perception and media relations.
        - `reach_target_market`: How the marketing efforts will specifically connect with the defined target market.
        - `retention`: Strategies for keeping customers engaged and loyal.
        - `seo_optimization`: Plans for optimizing the website and content for search engines.
        - `value_proposition`: A clear statement of the benefits the business delivers to its customers.
    - `management_team`:
        - `placeholder`: A placeholder string if the team is not yet defined (e.g., "Team to be assembled").
        - `description`: A summary of the team's collective expertise and why they are suited to lead the business.
        - `founder`, `developer`, `community_manager`: Placeholder roles with a brief bio describing the ideal candidate.
        - `members`: A list of specific team members and their roles.
        - `roles`: A list of key roles needed for the business and their responsibilities.
    - `financial_projections`:
        - `placeholder`: A placeholder string if detailed financials are not yet available (e.g., "Financial projections to be developed").
        - `description`: A summary of the financial plan and key assumptions.
        - `projections`: High-level financial forecasts (e.g., revenue, profit for the first 3-5 years).
        - `notes`: Important assumptions or disclaimers about the financial projections.
        - `revenue_streams`: The different ways the business will generate revenue.
        - `revenue_sources`: Specific sources of income within each revenue stream.
        - `cost_structure`: An overview of the major fixed and variable costs.
        - `cost_drivers`: The key factors that influence the costs.
    - `call_to_action`: The immediate next steps for the business (e.g., "Seeking $50,000 in seed funding", "Build and launch MVP in Q4").

    JSON Structure to be generated:
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
        "approach": "String",
        "channels": ["String"],
        "content_strategy": "String",
        "community_building": ["String"],
        "customer_acquisition": ["String"],
        "digital_marketing": ["String"],
        "distribution_channels": "String",
        "influencer_marketing": ["String"],
        "messaging": "String",
        "online_presence": "String",
        "outreach": ["String"],
        "outreach_channels": ["String"],
        "outreach_methods": ["String"],
        "partnerships": ["String"],
        "paid_advertising": ["String"],
        "pricing_strategy": "String",
        "public_relations": ["String"],
        "reach_target_market": ["String"],
        "retention": ["String"],
        "seo_optimization": ["String"],
        "value_proposition": "String"
      }},
      "management_team": {{
        "placeholder": "String",
        "description": "String",
        "founder": {{
          "role": "String",
          "bio": "String"
        }},
        "developer": {{
          "role": "String",
          "bio": "String"
        }},
        "community_manager": {{
          "role": "String",
          "bio": "String"
        }},
        "members": [
          {{
            "name": "String",
            "role": "String"
          }}
        ],
        "roles": [
          {{
            "role": "String",
            "description": "String"
          }}
        ]
      }},
      "financial_projections": {{
        "placeholder": "String",
        "description": "String",
        "projections": "String",
        "notes": "String",
        "revenue_streams": ["String"],
        "revenue_sources": ["String"],
        "cost_structure": ["String"],
        "cost_drivers": ["String"]
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