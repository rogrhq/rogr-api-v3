from __future__ import annotations
from fastapi import APIRouter, Depends
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
def preview(body: PreviewBody, _user=Depends(require_user)) -> Dict[str, Any]:
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

    return res