from __future__ import annotations
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from infrastructure.auth.deps import require_user
from infrastructure.http.limits import rate_limit_dep
from intelligence.pipeline.run import run_preview
from database.repo import save_analysis_with_claims, load_feed_page, load_feed_page_for_user, search_archive
from database.users import get_or_create_user_id
from workers import queue as Q
from database.notify import create_notification

router = APIRouter()

class PreviewBody(BaseModel):
    text: str
    test_mode: bool = True

@router.post("/mobile/preview")
def mobile_preview(body: PreviewBody, _rl=Depends(rate_limit_dep), _user=Depends(require_user)) -> Dict[str, Any]:
    res = run_preview(body.text, test_mode=body.test_mode)
    claims_out = []
    for c in res.get("claims", []):
        claims_out.append({
            "text": c.get("text", ""),
            "tier": c.get("tier", "primary"),
            "priority": c.get("priority", 0),
            "score_numeric": c.get("score_numeric", 0),
            "label": c.get("label", ""),
        })
    methodology = res.get("methodology", {}) or {}
    meth_small = {
        "version": methodology.get("version", "1.0"),
        "strategy": methodology.get("strategy", "A/B"),
        "test_mode": methodology.get("test_mode", True),
        "events_count": len(methodology.get("events", [])) if isinstance(methodology.get("events", []), list) else 0,
    }
    return {"claims": claims_out, "overall": res.get("overall", {}), "methodology": meth_small}

class CommitBody(BaseModel):
    text: str
    test_mode: bool = True
    input_type: str = "text"
    original_uri: Optional[str] = None

@router.post("/mobile/commit")
async def mobile_commit(body: CommitBody, _rl=Depends(rate_limit_dep), user=Depends(require_user)) -> Dict[str, Any]:
    res = run_preview(body.text, test_mode=body.test_mode)
    analysis_id = await save_analysis_with_claims(
        user_id=user.get("sub"),
        input_type=body.input_type,
        original_uri=body.original_uri,
        result=res,
    )
    return {"analysis_id": analysis_id, "overall": res.get("overall", {}), "claims_count": len(res.get("claims", []))}

@router.get("/mobile/feed")
async def mobile_feed(
    _rl=Depends(rate_limit_dep),
    user=Depends(require_user),
    cursor: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    following_only: bool = Query(False),
) -> Dict[str, Any]:
    uid = await get_or_create_user_id(user.get("sub",""))
    items, next_cursor = await load_feed_page_for_user(uid, following_only, cursor, limit)
    return {"items": items, "next_cursor": next_cursor}

@router.get("/mobile/archive/search")
async def mobile_archive_search(
    _rl=Depends(rate_limit_dep),
    _user=Depends(require_user),
    q: str = Query("", max_length=200),
    limit: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    results = await search_archive(q, limit=limit)
    return {"query": q or "", "results": results, "next_cursor": None}

@router.get("/mobile/jobs/{job_id}")
async def mobile_job_status(job_id: str, _rl=Depends(rate_limit_dep), user=Depends(require_user)) -> Dict[str, Any]:
    snap = Q.snapshot_job(job_id)
    if not snap:
        raise HTTPException(status_code=404, detail="job not found")
    out = {"job_id": job_id, "status": snap.get("status","unknown")}
    if "result" in snap:
        out["result"] = snap["result"]
    if "error" in snap:
        out["error"] = snap["error"]
    # Idempotent notification when terminal state observed (awaited to guarantee delivery)
    status = out.get("status")
    if status in ("completed", "failed"):
        dedupe = f"job:{job_id}:{status}"
        await create_notification(
            user_id=user.get("sub",""),
            kind="job_completed" if status == "completed" else "job_failed",
            payload={"job_id": job_id, "status": status},
            dedupe_key=dedupe,
        )
    return out