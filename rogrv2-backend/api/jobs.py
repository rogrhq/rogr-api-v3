from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from infrastructure.auth.deps import require_user
from infrastructure.http.limits import rate_limit_dep
from workers import queue as Q
from workers.jobs import run_preview_job

router = APIRouter()

# Register handlers once at import
Q.register_handler("preview", run_preview_job)

class EnqueueBody(BaseModel):
    kind: str  # "preview"
    payload: Dict[str, Any]

@router.on_event("startup")
async def _startup():
    # Start queue worker
    Q.start()

@router.post("/jobs/enqueue")
async def enqueue_job(body: EnqueueBody, _rl=Depends(rate_limit_dep), _user=Depends(require_user)):
    if body.kind not in ("preview",):
        raise HTTPException(status_code=400, detail="unsupported job kind")
    jid = await Q.enqueue(body.kind, body.payload)
    return {"job_id": jid, "status": "queued"}

@router.get("/jobs/{job_id}")
def get_job(job_id: str, _rl=Depends(rate_limit_dep), _user=Depends(require_user)):
    snap = Q.snapshot_job(job_id)
    if not snap:
        raise HTTPException(status_code=404, detail="job not found")
    return snap