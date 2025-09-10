from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import AsyncElasticsearch
from qdrant_client import QdrantClient, models
from typing import List, Dict, Any, Optional
import os
import random

# Configuration constants (should match business_plan_generation.py)
ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200
ELASTICSEARCH_INDEX = "business_plans"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_BUSINESS_PLANS_COLLECTION = "business_plans_embeddings"

app = FastAPI(title="Business Plan API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

es_client: Optional[AsyncElasticsearch] = None
qdrant_client: Optional[QdrantClient] = None

@app.on_event("startup")
async def startup_event():
    global es_client, qdrant_client
    es_client = AsyncElasticsearch(f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}")
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    try:
        await es_client.info()
        print("Connected to Elasticsearch.")
    except Exception as e:
        print(f"Error connecting to Elasticsearch on startup: {e}")
        # Depending on criticality, you might want to raise an exception here

@app.on_event("shutdown")
async def shutdown_event():
    if es_client:
        await es_client.close()
        print("Elasticsearch client closed.")

@app.get("/list_plans", response_model=Dict[str, Any])
async def list_plans(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
) -> Dict[str, Any]:
    """List all business plans with pagination."""
    if not es_client:
        raise HTTPException(status_code=500, detail="Elasticsearch client not initialized.")

    from_ = (page - 1) * page_size
    try:
        search_body = {
            "query": {"match_all": {}},
            "from": from_,
            "size": page_size
        }
        resp = await es_client.search(index=ELASTICSEARCH_INDEX, body=search_body)
        
        plans = [hit['_source'] for hit in resp['hits']['hits']]
        total_hits = resp['hits']['total']['value']

        return {"total": total_hits, "page": page, "page_size": page_size, "plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing plans: {e}")

@app.get("/search_plans", response_model=Dict[str, Any])
async def search_plans(
    query: str = Query(..., min_length=1, description="Search query string"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
) -> Dict[str, Any]:
    """Search business plans by keyword with pagination."""
    if not es_client:
        raise HTTPException(status_code=500, detail="Elasticsearch client not initialized.")

    from_ = (page - 1) * page_size
    try:
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "executive_summary^2", "problem", "solution", "market_analysis.*", "competition.*", "marketing_strategy.*", "call_to_action"]
                }
            },
            "from": from_,
            "size": page_size
        }
        resp = await es_client.search(index=ELASTICSEARCH_INDEX, body=search_body)
        
        plans = [hit['_source'] for hit in resp['hits']['hits']]
        total_hits = resp['hits']['total']['value']

        return {"total": total_hits, "page": page, "page_size": page_size, "plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching plans: {e}")

@app.get("/random_plan", response_model=Dict[str, Any])
async def get_random_plan() -> Dict[str, Any]:
    """Get a single random business plan."""
    if not es_client:
        raise HTTPException(status_code=500, detail="Elasticsearch client not initialized.")

    try:
        # Get total number of documents
        count_resp = await es_client.count(index=ELASTICSEARCH_INDEX)
        total_docs = count_resp['count']

        if total_docs == 0:
            raise HTTPException(status_code=404, detail="No business plans found.")

        # Pick a random offset
        random_offset = random.randint(0, total_docs - 1)

        # Retrieve one document at the random offset
        search_body = {
            "query": {"match_all": {}},
            "from": random_offset,
            "size": 1
        }
        resp = await es_client.search(index=ELASTICSEARCH_INDEX, body=search_body)

        if resp['hits']['hits']:
            return resp['hits']['hits'][0]['_source']
        else:
            # This case should ideally not happen if total_docs > 0 and random_offset is valid
            raise HTTPException(status_code=404, detail="Could not retrieve a random plan.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting random plan: {e}")

