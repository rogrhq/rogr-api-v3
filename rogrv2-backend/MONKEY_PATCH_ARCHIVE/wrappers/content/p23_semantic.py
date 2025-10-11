"""
P23 — Deterministic semantic reading wrapper (LIVE).
- Runs after P22 enrichment so content/coverage are present.
- For each claim in preview result, analyze items (arm_A/arm_B) and attach:
  * findings[] (quote, offsets, stance, signals, score)
  * item_grade (0..1), grade_label
- Additive only; no shape changes.
"""
from __future__ import annotations
import asyncio
import json
import os
from importlib import import_module
from typing import Any, Callable, Optional

from .semantic_read import analyze_item  # local deterministic analyzer

_DIAG = os.getenv("ROGR_DIAG", "").lower() in ("1","true","yes","on")
def _log(event: str, **fields: Any):
    if not _DIAG:
        return
    try:
        rec = {"event": f"p23.{event}"}
        rec.update(fields)
        print(json.dumps(rec, ensure_ascii=False))
    except Exception:
        pass

async def _post_analyze_preview(orig: Callable, *args, **kwargs):
    res = await orig(*args, **kwargs)
    try:
        claims = (res or {}).get("claims") or []
        changed = 0
        for c in claims:
            claim_text = c.get("text") or ""
            ev = c.get("evidence") or {}
            for arm_key in ("arm_A", "arm_B"):
                items = ev.get(arm_key) or []
                new_items = []
                for it in items:
                    if isinstance(it, dict):
                        new_items.append(analyze_item(claim_text, it))
                    else:
                        new_items.append(it)
                ev[arm_key] = new_items
            c["evidence"] = ev
            changed += 1
        _log("analyzed", claims=len(claims), changed=changed)
    except Exception as e:
        _log("analyze_error", error=str(e))
    return res

def _install():
    # Ensure P22 ran first (not strictly required, but preferred) — import it here
    try:
        import_module("intelligence.content.p22_ingest")
    except Exception:
        pass

    # Wrap pipeline.run.run_preview (preferred)
    try:
        run_mod = import_module("intelligence.pipeline.run")
    except Exception as e:
        _log("run_import_fail", error=str(e))
        return

    wrapped = None
    orig = getattr(run_mod, "run_preview", None)
    if orig and asyncio.iscoroutinefunction(orig):
        async def wrapped_run(*args, **kwargs):
            return await _post_analyze_preview(orig, *args, **kwargs)
        setattr(run_mod, "run_preview", wrapped_run)
        wrapped = wrapped_run
        _log("run_wrapped", target="run_preview")

    # Rebind api.analyses globals so the route uses our latest wrapper
    try:
        api_mod = import_module("api.analyses")
        if wrapped is not None and getattr(api_mod, "run_preview", None) is not wrapped:
            setattr(api_mod, "run_preview", wrapped)
            _log("rebound_api_names", run=True)
        else:
            _log("rebound_api_names", run=False)
    except Exception as e:
        _log("api_import_fail", error=str(e))

# Install at import (idempotent)
try:
    _install()
    __installed__ = True
    _log("installed", ok=True)
except Exception as _e:
    _log("install_error", error=str(_e))
