from __future__ import annotations
from fastapi import APIRouter, Depends
from typing import Any, Dict, List
import os
from intelligence.gather import online as live_gather
from pydantic import BaseModel
from typing import Any, Dict

from infrastructure.auth.deps import require_user
from intelligence.pipeline.run import run_preview
from infrastructure.audit.log import finalize_capsule, provider_set_from_env

router = APIRouter()

class PreviewBody(BaseModel):
    text: str
    test_mode: bool = True

@router.post("/analyses/preview")
async def preview(body: PreviewBody, _user=Depends(require_user)) -> Dict[str, Any]:
    """
    Runs the preview pipeline and ALWAYS returns a methodology capsule.
    """
    res: Dict[str, Any] = run_preview(body.text, test_mode=body.test_mode)

    # Ensure methodology capsule is present with required fields (version, etc.)
    if "methodology" not in res or not isinstance(res["methodology"], dict) or "version" not in res["methodology"]:
        res["methodology"] = finalize_capsule({
            "test_mode": body.test_mode,
            "provider_set": provider_set_from_env(body.test_mode),
            "counts": {"claims": len(res.get("claims", []))},
            "consensus_summary": {},
        })

    # --- live/diagnostic shim ---
    requested_test_mode = bool(getattr(body, "test_mode", True))
    force_live = os.getenv("FORCE_LIVE_GATHER") == "1"
    will_use_live = (not requested_test_mode) or force_live
    live_candidates: List[Dict[str, Any]] = []
    if will_use_live and (body.text or "").strip():
        try:
            pay = await live_gather.run((body.text or "")[:400], max_per_arm=3)
            live_candidates = pay.get("candidates", []) or []
        except Exception:
            live_candidates = []
    if live_candidates:
        ev = []
        for c in live_candidates:
            ev.append({
                "url": c.get("url"), "title": c.get("title"), "snippet": c.get("snippet"),
                "stance": "neutral", "quality_letter": "", "snapshot": c.get("snapshot")
            })
        res["evidence"] = ev
    res.setdefault("debug", {}).update({
        "requested_test_mode": requested_test_mode,
        "force_live": force_live,
        "will_use_live": will_use_live,
        "live_candidates_seen": len(live_candidates)
    })

    return res