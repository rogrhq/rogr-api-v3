"""
P26 — Dual-Researcher Orchestrator (LIVE)

Adds two independent researcher lanes (R1, R2) to /analyses/preview:
- Runs the existing preview pipeline twice (after P22–P25).
- Attaches per-lane {id, evidence, verdict} to each claim under `researchers`.
- Preserves existing fields (including top-level `verdict`) for backward compatibility.
"""
from __future__ import annotations
import asyncio
import json
import os
from importlib import import_module
from typing import Any, Callable, Dict, List

_DIAG = os.getenv("ROGR_DIAG", "").lower() in ("1","true","yes","on")

def _log(event: str, **fields: Any) -> None:
    if not _DIAG:
        return
    try:
        rec = {"event": f"p26.{event}"}
        rec.update(fields)
        print(json.dumps(rec, ensure_ascii=False))
    except Exception:
        pass

async def _run_once(orig: Callable, *args, **kwargs) -> Dict[str, Any]:
    return await orig(*args, **kwargs)

def _extract_claims(res: Dict[str, Any]) -> List[Dict[str, Any]]:
    return (res or {}).get("claims") or []

def _researcher_payload(claim: Dict[str, Any], lane_id: str) -> Dict[str, Any]:
    return {
        "id": lane_id,
        "verdict": (claim.get("verdict") or {}),
        "evidence": (claim.get("evidence") or {}),
    }

def _merge_r1_r2(res_r1: Dict[str, Any], res_r2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Base output is R1 (back-compat). Attach researchers[] with R1 + R2 per claim index.
    """
    base = dict(res_r1 or {})
    c1 = _extract_claims(res_r1)
    c2 = _extract_claims(res_r2)
    out_claims: List[Dict[str, Any]] = []
    n = max(len(c1), len(c2))
    for i in range(n):
        r1c = c1[i] if i < len(c1) else {}
        r2c = c2[i] if i < len(c2) else {}
        merged = dict(r1c)  # preserve original fields from R1
        researchers = [
            _researcher_payload(r1c, "R1"),
            _researcher_payload(r2c, "R2"),
        ]
        merged["researchers"] = researchers
        out_claims.append(merged)
    base["claims"] = out_claims
    return base

async def _dual_preview(orig: Callable, *args, **kwargs) -> Dict[str, Any]:
    _log("dual_start")
    # Run sequentially to reduce provider rate limits; can parallelize later.
    r1 = await _run_once(orig, *args, **kwargs)
    r2 = await _run_once(orig, *args, **kwargs)
    merged = _merge_r1_r2(r1, r2)
    _log("dual_done", r1_claims=len(_extract_claims(r1)), r2_claims=len(_extract_claims(r2)))
    return merged

def _install():
    # Ensure earlier stages are loaded
    for m in (
        "intelligence.content.p22_ingest",
        "intelligence.content.p23_semantic",
        "intelligence.content.p24_semantic_frames",
        "intelligence.content.p25_semantic_aggregate",
    ):
        try:
            import_module(m)
        except Exception:
            pass

    try:
        run_mod = import_module("intelligence.pipeline.run")
    except Exception as e:
        _log("run_import_fail", error=str(e)); return

    orig = getattr(run_mod, "run_preview", None)
    if orig and asyncio.iscoroutinefunction(orig):
        async def wrapped_run(*args, **kwargs):
            return await _dual_preview(orig, *args, **kwargs)
        setattr(run_mod, "run_preview", wrapped_run)
        _log("run_wrapped", target="run_preview")

        # Rebind API to latest wrapped run
        try:
            api_mod = import_module("api.analyses")
            if getattr(api_mod, "run_preview", None) is not wrapped_run:
                setattr(api_mod, "run_preview", wrapped_run)
                _log("rebound_api_names", run=True)
            else:
                _log("rebound_api_names", run=False)
        except Exception as e:
            _log("api_import_fail", error=str(e))

# Install wrapper at import
try:
    _install()
    __installed__ = True
    _log("installed", ok=True)
except Exception as _e:
    _log("install_error", error=str(_e))
