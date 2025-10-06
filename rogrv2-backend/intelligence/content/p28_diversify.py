"""
P28 — Lane Diversification Knobs (LIVE)

Purpose:
- Deterministically diversify R1 and R2 lanes without introducing bias.
- Differences include query order (shuffle) and provider order, while the provider set remains identical.

Mechanics:
- Patch P26's _run_once to set lane context (R1/R2).
- Wrap intelligence.gather.online.run_plan to apply lane-specific plan tweaks (providers order, query shuffle).
- Wrap intelligence.pipeline.run.run_preview and enrich returned researchers[] with lane_config.
- **Rebind api.analyses to the wrapped run_preview** so FastAPI calls traverse P28.

Researchers now include:
  researchers[i].lane_config = { lane_id, providers, queries_first3?: {A: [...], B: [...]} }
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import os
import random
from contextvars import ContextVar
from importlib import import_module
from typing import Any, Dict, List, Tuple

_DIAG = os.getenv("ROGR_DIAG", "").lower() in ("1","true","yes","on")

def _log(event: str, **fields: Any) -> None:
    if not _DIAG:
        return
    try:
        rec = {"event": f"p28.{event}"}
        rec.update(fields)
        print(json.dumps(rec, ensure_ascii=False))
    except Exception:
        pass

# --- Lane context -------------------------------------------------------------
LANE_ID: ContextVar[str] = ContextVar("LANE_ID", default="R1")
LANE_POS: ContextVar[int] = ContextVar("LANE_POS", default=0)

def _set_lane_for_next_run() -> str:
    pos = LANE_POS.get()
    lane = "R1" if (pos % 2 == 0) else "R2"
    LANE_ID.set(lane)
    LANE_POS.set(pos + 1)
    os.environ["ROGR_LANE_ID"] = lane  # for any env-based probes downstream
    return lane

def _seed_for(lane: str, claim_text: str) -> int:
    key = f"{lane}::{claim_text}".encode("utf-8", errors="ignore")
    h = hashlib.md5(key).hexdigest()
    return int(h[:8], 16)

def _available_providers() -> List[str]:
    avail = []
    if os.getenv("GOOGLE_CSE_API_KEY") and (os.getenv("GOOGLE_CSE_ENGINE_ID") or os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")):
        avail.append("google")
    if os.getenv("BRAVE_API_KEY"):
        avail.append("brave")
    if os.getenv("BING_API_KEY") or os.getenv("BING_SUBSCRIPTION_KEY") or os.getenv("AZURE_BING_KEY"):
        avail.append("bing")
    # dedupe keep-order
    seen, out = set(), []
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

def _normalize_arms(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    arms = plan.get("arms") or []
    if isinstance(arms, dict):
        out = []
        for k, v in arms.items():
            if isinstance(v, dict):
                vv = dict(v)
                vv.setdefault("name", k)
                out.append(vv)
        return out
    elif isinstance(arms, list):
        return arms
    return []

def _lane_tweak_plan(plan: Dict[str, Any], lane: str, seed: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    rnd = random.Random(seed)
    providers_avail = _available_providers()
    lane_providers = _ordered_providers_for_lane(lane, providers_avail)

    tweaked = dict(plan or {})
    arms_in = _normalize_arms(tweaked)
    arms_out: List[Dict[str, Any]] = []
    sample_first3: Dict[str, List[str]] = {}
    for arm in arms_in:
        arm2 = dict(arm or {})
        q = list((arm2.get("queries") or []))
        rnd.shuffle(q)
        arm2["queries"] = q
        arm2["providers"] = list(lane_providers)
        arms_out.append(arm2)
        name = (arm2.get("name") or "").upper()
        if name in ("A","A_SUPPORT","ARM_A","A_SUPPORTING"):
            sample_first3["A"] = q[:3]
        elif name in ("B","B_CHALLENGE","ARM_B","B_CHALLENGING"):
            sample_first3["B"] = q[:3]
    tweaked["arms"] = arms_out

    lane_config = {
        "lane_id": lane,
        "providers": lane_providers,
        "queries_first3": sample_first3,
    }
    return tweaked, lane_config

# --- Wrappers ---------------------------------------------------------
async def _wrapped_run_plan(orig, plan: Dict[str, Any], *args, **kwargs):
    # Apply per-lane plan tweaks (providers order + query shuffle)
    lane = LANE_ID.get()
    claim_text = str(kwargs.get("claim_text") or kwargs.get("text") or "")
    seed = _seed_for(lane, claim_text)
    tweaked_plan, lane_cfg = _lane_tweak_plan(plan or {}, lane, seed)
    _log("apply", lane=lane,
         providers=(tweaked_plan.get("arms") and tweaked_plan["arms"][0].get("providers")),
         qA=(lane_cfg.get("queries_first3", {}).get("A") or []),
         qB=(lane_cfg.get("queries_first3", {}).get("B") or []))
    return await orig(tweaked_plan, *args, **kwargs)

async def _lane_run_once(orig_callable, *args, **kwargs):
    """
    Replace p26._run_once to set lane context (R1/R2).
    We do not mutate claims here (claims may be constructed later).
    """
    lane = _set_lane_for_next_run()
    _log("lane_set", lane=lane)
    return await orig_callable(*args, **kwargs)

def _inject_lane_config_into_preview_result(obj: Dict[str, Any]) -> int:
    """
    Ensure each researchers[] entry has lane_config. Derive by index:
      index 0 -> R1 template order
      index 1 -> R2 template order
    Returns number of lane_config entries added.
    """
    added = 0
    try:
        claims = obj.get("claims") or []
        providers_avail = _available_providers()
        for c in claims:
            researchers = (c or {}).get("researchers") or []
            for idx, r in enumerate(researchers):
                if not isinstance(r, dict):
                    continue
                if r.get("lane_config"):
                    continue
                lane_id = "R1" if idx == 0 else "R2"
                providers = _ordered_providers_for_lane(lane_id, providers_avail)
                r["lane_config"] = {"lane_id": lane_id, "providers": providers}
                added += 1
    except Exception:
        pass
    return added

async def _wrapped_run_preview(orig_preview, *args, **kwargs):
    """
    Wrap intelligence.pipeline.run.run_preview and inject lane_config in the returned object.
    """
    res = await orig_preview(*args, **kwargs)
    if isinstance(res, dict):
        added = _inject_lane_config_into_preview_result(res)
        _log("preview_enriched", added=added)
    return res

def _rebind_api_names() -> None:
    """
    Rebind api.analyses to the *current* intelligence.pipeline.run.run_preview
    so FastAPI calls traverse P28's wrapper.
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

def _patch_p26() -> None:
    # Patch p26 to set lane context and forward lane_config if claims already carry it
    try:
        p26 = import_module("intelligence.content.p26_dual_researchers")
    except Exception as e:
        _log("p26_import_fail", error=str(e)); return

    try:
        orig_run_once = getattr(p26, "_run_once", None)
        if orig_run_once and asyncio.iscoroutinefunction(orig_run_once):
            async def patched_run_once(orig_callable, *args, **kwargs):
                return await _lane_run_once(orig_callable, *args, **kwargs)
            setattr(p26, "_run_once", patched_run_once)
            _log("patched_p26_run_once", ok=True)
    except Exception as e:
        _log("patch_run_once_fail", error=str(e))

    # Forward claim.lane_config if present (kept for compatibility; preview wrapper ensures final presence)
    try:
        orig_payload = getattr(p26, "_researcher_payload", None)
        if callable(orig_payload):
            def _payload(claim: Dict[str, Any], lane_id: str) -> Dict[str, Any]:
                base = orig_payload(claim, lane_id)
                cfg = (claim or {}).get("lane_config") or {}
                if cfg:
                    base["lane_config"] = cfg
                return base
            setattr(p26, "_researcher_payload", _payload)
            _log("patched_p26_payload", ok=True)
    except Exception as e:
        _log("patch_payload_fail", error=str(e))

def _patch_gather_online() -> None:
    # Wrap online.run_plan (closure-captured orig)
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

def _patch_preview_and_rebind() -> None:
    # Wrap pipeline.run_preview, then rebind api.analyses to this wrapper
    try:
        runmod = import_module("intelligence.pipeline.run")
        orig_preview = getattr(runmod, "run_preview", None)
        if orig_preview and asyncio.iscoroutinefunction(orig_preview):
            async def wrapped_run_preview(*args, **kwargs):
                return await _wrapped_run_preview(orig_preview, *args, **kwargs)
            setattr(runmod, "run_preview", wrapped_run_preview)
            _log("wrapped_preview", ok=True)
            _rebind_api_names()  # <- ensure API calls traverse wrapped preview
        else:
            _log("wrap_preview_skip", reason="not_found_or_not_async")
    except Exception as e:
        _log("wrap_preview_fail", error=str(e))

def _install():
    _patch_p26()
    _patch_gather_online()
    _patch_preview_and_rebind()
    _log("installed", ok=True)

# Install at import time
try:
    _install()
    __installed__ = True
except Exception as _e:
    _log("install_error", error=str(_e))
