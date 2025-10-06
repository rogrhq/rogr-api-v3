"""
P29 — Deterministic Diversification Controls, Manifest & Telemetry (LIVE)

Add-ons on top of P28:
- Collect per-lane telemetry during gather (counts by provider, duration).
- Inject top-level run_manifest + stable replay_id for exact reproducibility.
- Attach lane knobs & telemetry into researchers[*] in the returned preview object.
- Rebind API module to ensure wrapper executes on live FastAPI requests.

Add-only; zero-bias preserved (same provider set across lanes).
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import os
import time
from contextvars import ContextVar
from importlib import import_module
from typing import Any, Dict, List

_DIAG = os.getenv("ROGR_DIAG", "").lower() in ("1","true","yes","on")

def _log(event: str, **fields: Any) -> None:
    if not _DIAG:
        return
    try:
        rec = {"event": f"p29.{event}"}
        rec.update(fields)
        print(json.dumps(rec, ensure_ascii=False))
    except Exception:
        pass

# ---- Lane context (cooperates with P28) --------------------------------------
LANE_ID_ENV = "ROGR_LANE_ID"
LANE_ID_DEFAULT = "R1"

# Per-lane telemetry stored in a ContextVar so nested async calls remain coherent.
_TELEM: ContextVar[Dict[str, Any]] = ContextVar("P29_TELEMETRY", default={"R1": {}, "R2": {}})

def _get_lane_id_fallback(idx: int) -> str:
    return "R1" if idx == 0 else "R2"

def _available_providers() -> List[str]:
    avail = []
    if os.getenv("GOOGLE_CSE_API_KEY") and (os.getenv("GOOGLE_CSE_ENGINE_ID") or os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")):
        avail.append("google")
    if os.getenv("BRAVE_API_KEY"):
        avail.append("brave")
    if os.getenv("BING_API_KEY") or os.getenv("BING_SUBSCRIPTION_KEY") or os.getenv("AZURE_BING_KEY"):
        avail.append("bing")
    # dedupe keep-order
    out, seen = [], set()
    for p in avail:
        if p not in seen:
            seen.add(p); out.append(p)
    return out

def _ordered_providers_for_lane(lane: str, providers: List[str]) -> List[str]:
    pref_r1 = ["google","brave","bing"]
    pref_r2 = ["brave","google","bing"]
    tpl = pref_r1 if lane == "R1" else pref_r2
    tpl_set = set(providers)
    ordered = [p for p in tpl if p in tpl_set]
    for p in providers:
        if p not in ordered:
            ordered.append(p)
    return ordered

def _seed_for(lane_id: str, claim_text: str) -> int:
    key = f"{lane_id}::{claim_text}".encode("utf-8", errors="ignore")
    h = hashlib.md5(key).hexdigest()
    return int(h[:8], 16)

def _telemetry_init(lane: str) -> None:
    d = _TELEM.get().copy()
    if lane not in d:
        d[lane] = {}
    d[lane].setdefault("providers", {})
    d[lane].setdefault("duration_ms", 0)
    _TELEM.set(d)

def _telemetry_add_candidates(lane: str, candidates: List[Dict[str, Any]]) -> None:
    d = _TELEM.get().copy()
    lane_d = d.setdefault(lane, {}).setdefault("providers", {})
    for c in candidates or []:
        p = c.get("provider")
        if not p:
            continue
        lane_d[p] = int(lane_d.get(p, 0)) + 1
    d[lane]["providers"] = lane_d
    _TELEM.set(d)

def _telemetry_add_duration(lane: str, dur_ms: int) -> None:
    d = _TELEM.get().copy()
    lane_d = d.setdefault(lane, {})
    lane_d["duration_ms"] = int(lane_d.get("duration_ms", 0)) + int(dur_ms)
    d[lane] = lane_d
    _TELEM.set(d)

def _build_run_manifest(claim_text: str, lane_providers: Dict[str, List[str]]) -> Dict[str, Any]:
    # Build a stable object and a replay_id hash
    base = {
        "claim_text": claim_text,
        "providers_available": _available_providers(),
        "lanes": {
            "R1": {
                "seed": _seed_for("R1", claim_text),
                "providers": lane_providers.get("R1") or _ordered_providers_for_lane("R1", _available_providers()),
                "knobs": {
                    "query_shuffle": True,
                    "timeout_jitter_ms": 0,
                    "max_per_provider": None,
                },
            },
            "R2": {
                "seed": _seed_for("R2", claim_text),
                "providers": lane_providers.get("R2") or _ordered_providers_for_lane("R2", _available_providers()),
                "knobs": {
                    "query_shuffle": True,
                    "timeout_jitter_ms": 0,
                    "max_per_provider": None,
                },
            },
        },
    }
    h = hashlib.md5(json.dumps(base, sort_keys=True).encode("utf-8")).hexdigest()
    base["replay_id"] = h
    return base

# ---- Wrappers ----------------------------------------------------------------
async def _wrapped_run_plan(orig, plan: Dict[str, Any], *args, **kwargs):
    # Which lane is this call for?
    lane = os.getenv(LANE_ID_ENV, LANE_ID_DEFAULT)
    _telemetry_init(lane)
    t0 = time.time()
    res = await orig(plan, *args, **kwargs)
    dur_ms = int((time.time() - t0) * 1000)
    _telemetry_add_duration(lane, dur_ms)
    try:
        _telemetry_add_candidates(lane, (res or {}).get("candidates") or [])
    except Exception:
        pass
    _log("run_plan_telemetry", lane=lane, duration_ms=dur_ms,
         counts=( _TELEM.get().get(lane, {}).get("providers", {}) ))
    return res

def _inject_manifest_and_lane_data(obj: Dict[str, Any], claim_text: str) -> int:
    """
    - Ensure top-level run_manifest and diversified flag.
    - Attach lane_config.knobs and telemetry onto each researchers[*].
    Returns number of researchers enriched.
    """
    added = 0
    try:
        claims = obj.get("claims") or []
        if not claims:
            return 0
        # Collect providers order actually used (from researchers if present)
        lane_providers: Dict[str, List[str]] = {}
        for c in claims:
            researchers = (c or {}).get("researchers") or []
            for idx, r in enumerate(researchers):
                lane_id = "R1" if idx == 0 else "R2"
                lc = (r or {}).get("lane_config") or {}
                if lc.get("providers"):
                    lane_providers[lane_id] = list(lc["providers"])
        # Build manifest
        manifest = _build_run_manifest(claim_text, lane_providers)
        obj["run_manifest"] = manifest
        obj["diversified"] = True

        # Pull telemetry snapshot
        telem = _TELEM.get()
        # Enrich researchers
        for c in claims:
            researchers = (c or {}).get("researchers") or []
            for idx, r in enumerate(researchers):
                if not isinstance(r, dict):
                    continue
                lane_id = "R1" if idx == 0 else "R2"
                r.setdefault("lane_config", {})
                r["lane_config"].setdefault("knobs", {
                    "query_shuffle": True,
                    "timeout_jitter_ms": 0,
                    "max_per_provider": None,
                    "seed": _seed_for(lane_id, claim_text),
                })
                # attach telemetry
                if telem.get(lane_id):
                    r["telemetry"] = {
                        "providers": telem[lane_id].get("providers", {}),
                        "duration_ms": telem[lane_id].get("duration_ms", 0),
                    }
                added += 1
        # Basic parity assertion (add-only)
        try:
            if claims and len((claims[0].get("researchers") or [])) >= 2:
                r1 = claims[0]["researchers"][0]
                r2 = claims[0]["researchers"][1]
                s1 = set((r1.get("lane_config", {}).get("providers") or []))
                s2 = set((r2.get("lane_config", {}).get("providers") or []))
                obj.setdefault("parity", {})["providers_equal"] = (s1 == s2)
        except Exception:
            pass
    except Exception:
        pass
    return added

async def _wrapped_run_preview(orig_preview, *args, **kwargs):
    # Attempt to discover claim_text for manifest seeding
    claim_text = ""
    for v in list(kwargs.values()):
        if isinstance(v, str) and len(v) > 0:
            claim_text = v
            break
        if isinstance(v, dict) and "text" in v:
            claim_text = str(v.get("text") or "")
            break
    if not claim_text and args:
        # heuristic: first str positional
        for a in args:
            if isinstance(a, str) and a:
                claim_text = a
                break

    res = await orig_preview(*args, **kwargs)
    if isinstance(res, dict):
        added = _inject_manifest_and_lane_data(res, claim_text)
        _log("preview_enriched", added=added)
    return res

def _rebind_api_names() -> None:
    """
    Ensure FastAPI endpoint calls traverse our wrapped preview.
    """
    try:
        apimod = import_module("api.analyses")
        runmod = import_module("intelligence.pipeline.run")
        wrapped = getattr(runmod, "run_preview", None)
        replaced = False
        for name in ("RUN_PREVIEW", "run_preview"):
            if hasattr(apimod, name) and wrapped:
                setattr(apimod, name, wrapped)
                replaced = True
        _log("rebound_api_names", run=replaced)
    except Exception as e:
        _log("rebind_fail", error=str(e))

def _install():
    # Wrap online.run_plan to collect telemetry
    try:
        online = import_module("intelligence.gather.online")
        orig_run_plan = getattr(online, "run_plan", None)
        if orig_run_plan and asyncio.iscoroutinefunction(orig_run_plan):
            async def wrapped_run_plan(plan: Dict[str, Any], *args, **kwargs):
                return await _wrapped_run_plan(orig_run_plan, plan, *args, **kwargs)
            setattr(online, "run_plan", wrapped_run_plan)
            _log("wrapped_run_plan", ok=True)
        else:
            _log("wrap_run_plan_skip", reason="not_found_or_not_async")
    except Exception as e:
        _log("wrap_run_plan_fail", error=str(e))

    # Wrap pipeline.run_preview and rebind API module
    try:
        runmod = import_module("intelligence.pipeline.run")
        orig_preview = getattr(runmod, "run_preview", None)
        if orig_preview and asyncio.iscoroutinefunction(orig_preview):
            async def wrapped_run_preview(*args, **kwargs):
                return await _wrapped_run_preview(orig_preview, *args, **kwargs)
            setattr(runmod, "run_preview", wrapped_run_preview)
            _log("wrapped_preview", ok=True)
            _rebind_api_names()
        else:
            _log("wrap_preview_skip", reason="not_found_or_not_async")
    except Exception as e:
        _log("wrap_preview_fail", error=str(e))

    _log("installed", ok=True)

# Install at import
try:
    _install()
    __installed__ = True
except Exception as _e:
    _log("install_error", error=str(_e))
