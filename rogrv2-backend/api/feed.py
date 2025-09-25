from __future__ import annotations
from fastapi import APIRouter, Depends
from infrastructure.auth.deps import require_user
from infrastructure.http.limits import rate_limit_dep

router = APIRouter()

@router.get("/feed")
def get_feed(_rl=Depends(rate_limit_dep), _user=Depends(require_user)):
    # Deterministic stub aligned to frontend_contracts/v1/feed.json
    return {
        "items": [
            {
                "id": "post-1",
                "analysis_id": "analysis-1",
                "author_handle": "user123",
                "visibility": "public",
                "created_at": "2024-01-01T00:00:00Z",
                "headline": "City budget increased by 8%",
                "overall": { "score": 72, "label": "Mostly True" }
            }
        ],
        "next_cursor": None
    }