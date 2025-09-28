from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from infrastructure.auth.deps import require_user
from intelligence.pipeline.run import run_preview
from infrastructure.logging.jtrace import error_event, format_exc

router = APIRouter()

class PreviewBody(BaseModel):
    # MVP: text input; extensible for media later
    text: str
    test_mode: bool = False
    input_type: str | None = None
    original_uri: str | None = None

@router.get("/analyses/healthcheck")
def analyses_healthcheck(_user=Depends(require_user)):
    return {"ok": True}

@router.post("/analyses/preview")
def preview(body: PreviewBody, _user=Depends(require_user)):
    """
    Crash-proof preview:
    - Never throws unhandled exceptions
    - Always returns minimal shape: overall, claims, methodology
    """
    try:
        res = run_preview(text=body.text, test_mode=body.test_mode)
        if not isinstance(res, dict):
            res = {}
        res.setdefault("overall", {"score": 50, "label": "Mixed"})
        res.setdefault("claims", [])
        res.setdefault("methodology", {"version": "S1", "notes": []})
        return res
    except Exception as e:
        rid = error_event(
            "preview_failed",
            text=body.text[:200],
            test_mode=body.test_mode,
            detail=str(e),
            traceback=format_exc(e),
        )
        raise HTTPException(
            status_code=500,
            detail={"error": "server_error", "request_id": rid, "hint": "see server logs"},
        )