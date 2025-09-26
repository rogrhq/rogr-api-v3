from __future__ import annotations
from typing import Any, Dict
import asyncio
from intelligence.pipeline.run import run_preview

async def run_preview_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Payload:
      { "text": str, "test_mode": bool (default True) }
    Returns a compact summary (counts/overall) plus echo of inputs.
    """
    text = payload.get("text") or ""
    test_mode = bool(payload.get("test_mode", True))
    # run synchronously in this worker task
    res = run_preview(text, test_mode=test_mode)
    claims = res.get("claims", [])
    overall = res.get("overall", {})
    return {
        "inputs": {"test_mode": test_mode, "text_len": len(text)},
        "counts": {"claims": len(claims)},
        "overall": overall,
    }