from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import AsyncElasticsearch
from qdrant_client import QdrantClient, models
from typing import List, Dict, Any, Optional
import os
import random
from pydantic import BaseModel, EmailStr

# Configuration constants (should match business_plan_generation.py)
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
ELASTICSEARCH_INDEX = "business_plans"
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
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

# --- Pydantic Models ---
class WaitlistRequest(BaseModel):
    email: EmailStr

class CommentRequest(BaseModel):
    content: str

class CommentReplyRequest(BaseModel):
    content: str


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

@app.post("/api/waitlist")
async def add_to_waitlist(request: WaitlistRequest):
    """Adds an email to the premium waitlist."""
    # For now, we'll just log the email. In a real application, you'd save this to a database.
    print(f"New waitlist signup: {request.email}")
    return {"success": True}

@app.get("/api/plans/{id}", response_model=Dict[str, Any])
async def get_plan_by_id(id: str) -> Dict[str, Any]:
    """Retrieves a business plan by ID."""
    if not es_client:
        raise HTTPException(status_code=500, detail="Elasticsearch client not initialized.")
    try:
        resp = await es_client.get(index=ELASTICSEARCH_INDEX, id=id)
        return resp['_source']
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Plan with ID {id} not found.")

@app.get("/api/plans/{id}/comments", response_model=List[Dict[str, Any]])
async def get_plan_comments(id: str):
    """Retrieves comments for a business plan (mocked)."""
    # Mock data - in a real app, you'd fetch this from a database
    return [
        {"id": 1, "author": "Alice", "content": "This is a great idea!"},
        {"id": 2, "author": "Bob", "content": "I have some suggestions for the marketing plan."},
    ]

@app.post("/api/plans/{id}/comments", response_model=Dict[str, Any])
async def add_plan_comment(id: str, request: CommentRequest):
    """Adds a comment to a business plan (mocked)."""
    # Mock data - in a real app, you'd save this and return the created object
    print(f"New comment for plan {id}: {request.content}")
    return {"id": 3, "author": "CurrentUser", "content": request.content}

@app.post("/api/comments/{id}/reply", response_model=Dict[str, Any])
async def reply_to_comment(id: int, request: CommentReplyRequest):
    """Replies to a comment (mocked)."""
    # Mock data
    print(f"New reply to comment {id}: {request.content}")
    return {"id": 4, "author": "CurrentUser", "content": request.content, "parent_comment_id": id}

