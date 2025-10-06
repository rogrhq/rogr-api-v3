"""
P25 — Deterministic arm aggregation & verdict wrapper (LIVE).
- Runs after P24.
- Computes arm strengths and updates claims[i].verdict.{label, confidence, arm_strength}.
- Additive only; API shape stable.
"""
from __future__ import annotations
import asyncio
import json
import os
from importlib import import_module
from typing import Any, Callable

from .p25_aggregate import aggregate_verdict

_DIAG = os.getenv("ROGR_DIAG", "").lower() in ("1","true","yes","on")
def _log(event: str, **fields: Any):
    if not _DIAG:
        return
    try:
        rec = {"event": f"p25.{event}"}
        rec.update(fields)
        print(json.dumps(rec, ensure_ascii=False))
    except Exception:
        pass

async def _post_preview_aggregate(orig: Callable, *args, **kwargs):
    res = await orig(*args, **kwargs)
    try:
        claims = (res or {}).get("claims") or []
        changed = 0
        for c in claims:
            claim_text = c.get("text") or ""
            ev = c.get("evidence") or {}
            A = ev.get("arm_A") or []
            B = ev.get("arm_B") or []
            verdict = c.get("verdict") or {}
            agg = aggregate_verdict(claim_text, A, B, delta=0.15)
            # merge: preserve any existing fields, overwrite label/confidence/arm_strength
            verdict.update({
                "label": agg["label"],
                "confidence": agg["confidence"],
                "arm_strength": agg["arm_strength"],
            })
            c["verdict"] = verdict
            changed += 1
        _log("aggregated", claims=len(claims), changed=changed)
    except Exception as e:
        _log("aggregate_error", error=str(e))
    return res

def _install():
    # Ensure earlier stages present (best-effort)
    for m in ("intelligence.content.p22_ingest","intelligence.content.p23_semantic","intelligence.content.p24_semantic_frames"):
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
            return await _post_preview_aggregate(orig, *args, **kwargs)
        setattr(run_mod, "run_preview", wrapped_run)
        _log("run_wrapped", target="run_preview")

        # Rebind API to latest wrapped func
        try:
            api_mod = import_module("api.analyses")
            if getattr(api_mod, "run_preview", None) is not wrapped_run:
                setattr(api_mod, "run_preview", wrapped_run)
                _log("rebound_api_names", run=True)
            else:
                _log("rebound_api_names", run=False)
        except Exception as e:
            _log("api_import_fail", error=str(e))

# Install at import
try:
    _install()
    __installed__ = True
    _log("installed", ok=True)
except Exception as _e:
    _log("install_error", error=str(_e))
