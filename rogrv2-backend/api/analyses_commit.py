from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Any, Dict, Optional, List, Tuple

from infrastructure.auth.deps import require_user
from infrastructure.http.limits import rate_limit_dep
from intelligence.pipeline.run import run_preview
from database.repo import save_analysis_with_claims, load_feed_page, search_archive

router = APIRouter()

class CommitBody(BaseModel):
    text: str
    test_mode: bool = True
    input_type: str = "text"
    original_uri: Optional[str] = None

@router.post("/analyses/commit")
async def commit_analysis(body: CommitBody, _rl=Depends(rate_limit_dep), user=Depends(require_user)) -> Dict[str, Any]:
    # Run pipeline deterministically by default
    result = run_preview(body.text, test_mode=body.test_mode)
    analysis_id = await save_analysis_with_claims(
        user_id=user.get("sub"),
        input_type=body.input_type,
        original_uri=body.original_uri,
        result=result,
    )
    return {"analysis_id": analysis_id, "overall": result.get("overall", {}), "claims": result.get("claims", [])}

@router.get("/feed")
async def get_feed(
    _rl=Depends(rate_limit_dep),
    _user=Depends(require_user),
    cursor: Optional[str] = Query(None, description="ISO cursor for pagination"),
    limit: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    items, next_cursor = await load_feed_page(cursor, limit)
    return {"items": items, "next_cursor": next_cursor}

@router.get("/archive/search")
async def archive_search(
    _rl=Depends(rate_limit_dep),
    _user=Depends(require_user),
    q: str = Query("", max_length=200),
    limit: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    results = await search_archive(q, limit=limit)
    return {"query": q or "", "filters": {"tags": [], "date_from": None, "date_to": None}, "results": results, "next_cursor": None}