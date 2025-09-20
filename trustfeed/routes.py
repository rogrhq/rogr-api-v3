from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from trustfeed.models import TrustfeedEntry
from trustfeed.services import save_fact_check_to_trustfeed

# Create router for trustfeed endpoints
router = APIRouter(prefix="/trustfeed", tags=["trustfeed"])

# Pydantic models for API requests/responses
class TrustfeedEntryResponse(BaseModel):
    id: int
    claim_summary: str
    trust_score: Optional[float]
    grade: Optional[str]
    source_url: Optional[str]
    source_domain: Optional[str]
    claims_analyzed: int
    scan_mode: Optional[str]
    tags: Optional[List[str]]
    categories: Optional[List[str]]
    created_at: Optional[str]

class TrustfeedCreateRequest(BaseModel):
    claim_summary: str
    trust_score: Optional[float] = None
    grade: Optional[str] = None
    source_url: Optional[str] = None
    source_domain: Optional[str] = None
    claims_analyzed: int = 0
    scan_mode: Optional[str] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    full_capsule_data: Optional[dict] = None

# TODO: Implement the following endpoints when needed:

# @router.get("/", response_model=List[TrustfeedEntryResponse])
# async def get_trustfeed_entries(
#     limit: int = Query(100, ge=1, le=1000),
#     offset: int = Query(0, ge=0)
# ):
#     """Get paginated list of trustfeed entries."""
#     pass

# @router.get("/{entry_id}", response_model=TrustfeedEntryResponse)
# async def get_trustfeed_entry(entry_id: int):
#     """Get a specific trustfeed entry by ID."""
#     pass

# @router.post("/", response_model=TrustfeedEntryResponse)
# async def create_trustfeed_entry(entry: TrustfeedCreateRequest):
#     """Create a new trustfeed entry."""
#     pass

# @router.get("/search/", response_model=List[TrustfeedEntryResponse])
# async def search_trustfeed_entries(
#     q: str = Query(..., min_length=1),
#     limit: int = Query(50, ge=1, le=500)
# ):
#     """Search trustfeed entries by claim summary."""
#     pass

# @router.get("/domain/{domain}", response_model=List[TrustfeedEntryResponse])
# async def get_entries_by_domain(
#     domain: str,
#     limit: int = Query(50, ge=1, le=500)
# ):
#     """Get entries filtered by source domain."""
#     pass

# @router.get("/score-range/", response_model=List[TrustfeedEntryResponse])
# async def get_entries_by_score_range(
#     min_score: float = Query(0.0, ge=0.0, le=1.0),
#     max_score: float = Query(1.0, ge=0.0, le=1.0),
#     limit: int = Query(50, ge=1, le=500)
# ):
#     """Get entries within a trust score range."""
#     pass