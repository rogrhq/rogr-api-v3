from __future__ import annotations
from fastapi import APIRouter, Depends
from typing import Dict, Any
from infrastructure.http.limits import rate_limit_dep
from infrastructure.metrics import snapshot, diagnostics

router = APIRouter()

@router.get("/metrics")
def get_metrics(_rl=Depends(rate_limit_dep)) -> Dict[str, Any]:
    # Try to enrich with job stats (best-effort)
    extra = {}
    try:
        from workers import queue as Q  # type: ignore
        s = Q.stats() if hasattr(Q, "stats") else {}
        if isinstance(s, dict):
            extra["jobs"] = {
                "enqueued": int(s.get("enqueued", 0)),
                "in_progress": int(s.get("in_progress", 0)),
                "completed": int(s.get("completed", 0)),
                "failed": int(s.get("failed", 0)),
            }
    except Exception:
        pass
    return snapshot(additional=extra)

@router.get("/diagnostics")
def get_diagnostics(_rl=Depends(rate_limit_dep)) -> Dict[str, Any]:
    return diagnostics()