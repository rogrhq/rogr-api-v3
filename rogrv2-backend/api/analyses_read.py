from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from infrastructure.auth.deps import require_user
from infrastructure.http.limits import rate_limit_dep

router = APIRouter()

@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str, _rl=Depends(rate_limit_dep), _user=Depends(require_user)):
    # Stubbed until persistence lands (Packet 11/12). Return 404 with stable shape.
    raise HTTPException(status_code=404, detail={"id": analysis_id, "error": "not found"})