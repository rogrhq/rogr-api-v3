from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
from sqlalchemy import select

from infrastructure.auth.deps import require_user
from infrastructure.http.limits import rate_limit_dep
from intelligence.pipeline.run import run_preview
from infrastructure.ifcn.export import build_ifcn_bundle
from database.session import Session
from database.models import Analysis, Claim

router = APIRouter()

class ExportPreviewBody(BaseModel):
    text: str
    test_mode: bool = True
    input_type: str = "text"
    original_uri: Optional[str] = None

@router.post("/analyses/export/ifcn_preview")
def export_ifcn_preview(body: ExportPreviewBody, _rl=Depends(rate_limit_dep), _user=Depends(require_user)) -> Dict[str, Any]:
    """
    Runs preview and returns an IFCN export bundle (not persisted).
    """
    res = run_preview(body.text, test_mode=body.test_mode)
    meta = {
        "test_mode": body.test_mode,
        "input_type": body.input_type,
        "original_uri": body.original_uri,
        "text_len": len(body.text or ""),
    }
    return build_ifcn_bundle(result=res, input_meta=meta)

@router.get("/analyses/{analysis_id}/export/ifcn")
async def export_ifcn_persisted(analysis_id: str, _rl=Depends(rate_limit_dep), _user=Depends(require_user)) -> Dict[str, Any]:
    """
    Returns an IFCN export bundle for a persisted analysis.
    Evidence ledger may be empty in MVP since raw evidence is not persisted (by design).
    """
    async with Session() as s:
        an = await s.get(Analysis, analysis_id)
        if not an:
            raise HTTPException(status_code=404, detail="analysis not found")
        # pull a representative claim if present (for minimal context)
        claims: List[Claim] = (await s.execute(
            select(Claim).where(Claim.analysis_id == analysis_id).order_by(Claim.priority, Claim.id)
        )).scalars().all()
    # Minimal "result-like" structure from stored fields
    result_like: Dict[str, Any] = {
        "claims": [{"text": c.text, "tier": c.tier, "score_numeric": an.total_grade_numeric or 0, "label": an.total_label or ""} for c in claims],
        "overall": {"score": an.total_grade_numeric or 0, "label": an.total_label or ""},
        "methodology": an.ifcn_methodology_json or {},
        "evidence": {},  # not stored
    }
    meta = {
        "test_mode": False,
        "input_type": an.input_type if hasattr(an, "input_type") else "text",
        "original_uri": an.original_uri,
        "text_len": 0,
        "analysis_id": analysis_id,
    }
    return build_ifcn_bundle(result=result_like, input_meta=meta)