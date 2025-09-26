from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc

from infrastructure.auth.deps import require_admin, require_user
from infrastructure.auth.freeze import freeze as freeze_user, unfreeze as unfreeze_user, is_frozen
from infrastructure.http.limits import rate_limit_dep
from database.session import Session
from database.models import Analysis, AuditEvent, Claim
from infrastructure.ifcn.export import build_ifcn_bundle

router = APIRouter()

@router.get("/admin/analyses")
async def admin_list_analyses(
    _rl=Depends(rate_limit_dep),
    _admin=Depends(require_admin),
    limit: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    async with Session() as s:
        q = select(Analysis).order_by(desc(Analysis.created_at)).limit(limit)
        rows = (await s.execute(q)).scalars().all()
        items: List[Dict[str, Any]] = []
        for a in rows:
            items.append({
                "id": a.id,
                "user_id": a.user_id,
                "created_at": a.created_at.replace(microsecond=0).isoformat() + "Z",
                "status": a.status,
                "overall": {"score": a.total_grade_numeric or 0, "label": a.total_label or ""},
            })
        return {"items": items}

@router.get("/admin/audit/analyses/{analysis_id}")
async def admin_audit_for_analysis(
    analysis_id: str,
    _rl=Depends(rate_limit_dep),
    _admin=Depends(require_admin),
) -> Dict[str, Any]:
    async with Session() as s:
        q = select(AuditEvent).where(AuditEvent.analysis_id == analysis_id).order_by(AuditEvent.created_at.desc())
        rows = (await s.execute(q)).scalars().all()
        items = [{
            "id": ev.id,
            "actor": ev.actor,
            "action": ev.action,
            "metadata": ev.metadata_json,
            "created_at": ev.created_at.replace(microsecond=0).isoformat() + "Z",
        } for ev in rows]
        return {"items": items}

@router.get("/admin/ifcn/analyses/{analysis_id}")
async def admin_ifcn_export_for_analysis(
    analysis_id: str,
    _rl=Depends(rate_limit_dep),
    _admin=Depends(require_admin),
) -> Dict[str, Any]:
    # Assemble a "result-like" structure from persisted fields and claims
    async with Session() as s:
        a = await s.get(Analysis, analysis_id)
        if not a:
            raise HTTPException(status_code=404, detail="analysis not found")
        claims = (await s.execute(select(Claim).where(Claim.analysis_id == analysis_id).order_by(Claim.priority, Claim.id))).scalars().all()
    result_like: Dict[str, Any] = {
        "claims": [{"text": c.text, "tier": c.tier, "score_numeric": a.total_grade_numeric or 0, "label": a.total_label or ""} for c in claims],
        "overall": {"score": a.total_grade_numeric or 0, "label": a.total_label or ""},
        "methodology": a.ifcn_methodology_json or {},
        "evidence": {},
    }
    meta = {"analysis_id": analysis_id, "test_mode": False, "input_type": a.input_type, "original_uri": a.original_uri, "text_len": 0}
    return build_ifcn_bundle(result=result_like, input_meta=meta)

class FreezeBody:
    sub: str
    frozen: bool = True

@router.post("/admin/users/freeze")
def admin_freeze_user(
    body: Dict[str, Any],
    _rl=Depends(rate_limit_dep),
    _admin=Depends(require_admin),
) -> Dict[str, Any]:
    sub = str(body.get("sub",""))
    frozen = bool(body.get("frozen", True))
    if not sub:
        raise HTTPException(status_code=400, detail="missing sub")
    if frozen:
        freeze_user(sub)
    else:
        unfreeze_user(sub)
    return {"ok": True, "sub": sub, "frozen": is_frozen(sub)}