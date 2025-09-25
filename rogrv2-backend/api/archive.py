from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from infrastructure.auth.deps import require_user
from infrastructure.http.limits import rate_limit_dep

router = APIRouter()

@router.get("/archive/search")
def archive_search(
    _rl=Depends(rate_limit_dep),
    _user=Depends(require_user),
    q: str = Query("", max_length=200),
    tags: str = Query("", description="comma-separated tags"),
    date_from: str | None = None,
    date_to: str | None = None,
):
    # Deterministic stub aligned to frontend_contracts/v1/archive_search.json
    return {
        "query": q or "budget",
        "filters": {
            "tags": [t for t in tags.split(",") if t] if tags else [],
            "date_from": date_from,
            "date_to": date_to
        },
        "results": [
            {
                "analysis_id": "analysis-1",
                "created_at": "2024-01-01T00:00:00Z",
                "claims": [
                    { "text": "Austin increased its 2024 city budget by 8%.", "tier": "primary", "score_numeric": 72, "label": "Mostly True" }
                ],
                "overall": { "score": 72, "label": "Mostly True" }
            }
        ],
        "next_cursor": None
    }