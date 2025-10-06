"""
P24 — Deterministic semantic frames wrapper (LIVE).
- Runs after P22/P23.
- For each evidence item (arm_A/arm_B), attach:
  * item_frame {entity[], action, quantity[], year[], scope}
  * frame_matches[] [{label, score, slots[], rules[], quote, offset_*}]
  * frame_confidence (0..1)
- Additive only; no API shape changes.
"""
from __future__ import annotations
import json
import os
import asyncio
from importlib import import_module
from typing import Any, Callable, Optional

from .semantic_frames import analyze_frames

_DIAG = os.getenv("ROGR_DIAG", "").lower() in ("1","true","yes","on")
def _log(event: str, **fields: Any):
    if not _DIAG:
        return
    try:
        rec = {"event": f"p24.{event}"}
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
            for arm_key in ("arm_A","arm_B"):
                items = ev.get(arm_key) or []
                new_items = []
                for it in items:
                    if not isinstance(it, dict):
                        new_items.append(it); continue
                    content = it.get("content") or it.get("content_excerpt") or ""
                    if content:
                        frames = analyze_frames(claim_text, content, window=3)
                        it.update(frames)
                    else:
                        # still attach empty structures deterministically
                        it.setdefault("item_frame", {"entity": [], "action":"unknown","quantity":[],"year":[],"scope":"unknown"})
                        it.setdefault("frame_matches", [])
                        it.setdefault("frame_confidence", 0.0)
                    new_items.append(it)
                ev[arm_key] = new_items
            c["evidence"] = ev
            changed += 1
        _log("analyzed", claims=len(claims), changed=changed)
    except Exception as e:
        _log("analyze_error", error=str(e))
    return res

def _install():
    # Ensure prior stages have installed
    try:
        import_module("intelligence.content.p22_ingest")
    except Exception:
        pass
    try:
        import_module("intelligence.content.p23_semantic")
    except Exception:
        pass

    # Wrap pipeline.run.run_preview
    try:
        run_mod = import_module("intelligence.pipeline.run")
    except Exception as e:
        _log("run_import_fail", error=str(e)); return

    wrapped = None
    orig = getattr(run_mod, "run_preview", None)
    if orig and asyncio.iscoroutinefunction(orig):
        async def wrapped_run(*args, **kwargs):
            return await _post_analyze_preview(orig, *args, **kwargs)
        setattr(run_mod, "run_preview", wrapped_run)
        wrapped = wrapped_run
        _log("run_wrapped", target="run_preview")

    # Rebind api.analyses preview to latest wrapped func
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
