"""
P27 — Deterministic Consensus over Dual Researchers (LIVE)

Computes a consensus verdict from two independent researcher lanes (R1, R2)
already attached by P26 to each claim.

Adds per-claim:
  consensus: {
    label: "supports"|"challenges"|"mixed"|"insufficient",
    confidence: float in [0,1],
    rationale: {rule, support_mean, challenge_mean, delta, base_conf, bonus_or_penalty},
    agreement: {r1_label, r2_label, r1_conf, r2_conf, delta_balance}
  }

Notes:
- Add-only; preserves existing fields (top-level verdict remains as-is).
- Deterministic; no AI.
"""
from __future__ import annotations
import asyncio
import json
import os
from importlib import import_module
from typing import Any, Dict, List, Optional, Callable

_DIAG = os.getenv("ROGR_DIAG", "").lower() in ("1","true","yes","on")

def _log(event: str, **fields: Any) -> None:
    if not _DIAG:
        return
    try:
        rec = {"event": f"p27.{event}"}
        rec.update(fields)
        print(json.dumps(rec, ensure_ascii=False))
    except Exception:
        pass

_ALLOWED = {"supports","challenges","mixed","insufficient"}

def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x

def _lane(v: Dict[str, Any]) -> Dict[str, Any]:
    v = v or {}
    label = v.get("label") if v.get("label") in _ALLOWED else "insufficient"
    conf = float(v.get("confidence") or 0.0)
    arm = v.get("arm_strength") or {}
    support = float(arm.get("support") or 0.0)
    challenge = float(arm.get("challenge") or 0.0)
    return {"label": label, "confidence": _clamp01(conf), "support": support, "challenge": challenge}

def _consensus_for_pair(r1: Dict[str, Any], r2: Dict[str, Any]) -> Dict[str, Any]:
    L1, L2 = _lane(r1), _lane(r2)
    l1, c1 = L1["label"], L1["confidence"]
    l2, c2 = L2["label"], L2["confidence"]
    s_mean = (L1["support"] + L2["support"]) / 2.0
    c_mean = (L1["challenge"] + L2["challenge"]) / 2.0
    delta = s_mean - c_mean  # positive => supports stronger
    base_conf = (c1 + c2) / 2.0

    if l1 == l2:
        # Agreement: adopt label; add consistency bonus
        # Bonus depends mildly on agreement and closeness; clamp ≤ 0.95 to avoid overconfidence.
        bonus = min(0.20, 0.10 + 0.50 * abs(c1 - c2))
        conf = _clamp01(min(0.95, base_conf + bonus))
        label = l1
        rationale = {"rule": "agree_same_label", "support_mean": s_mean, "challenge_mean": c_mean,
                     "delta": delta, "base_conf": base_conf, "bonus_or_penalty": bonus}
    else:
        # Disagreement: check aggregate strengths; if gap ≥ 0.20 pick a side, else mixed.
        gap = abs(delta)
        if gap >= 0.20:
            label = "supports" if delta > 0 else "challenges"
        else:
            label = "mixed"
        # Penalize: be conservative; never exceed the stronger lane's confidence.
        penalty = min(0.30, 0.15 + 0.50 * abs(c1 - c2))
        conf = _clamp01(max(c1, c2) - penalty)
        rationale = {"rule": "disagree_gap_select" if gap >= 0.20 else "disagree_mixed",
                     "support_mean": s_mean, "challenge_mean": c_mean,
                     "delta": delta, "base_conf": base_conf, "bonus_or_penalty": -penalty}

    return {
        "label": label,
        "confidence": conf,
        "rationale": rationale,
        "agreement": {
            "r1_label": l1, "r2_label": l2,
            "r1_conf": c1, "r2_conf": c2,
            "delta_balance": delta
        }
    }

def _attach_consensus(res: Dict[str, Any]) -> Dict[str, Any]:
    # Mutates a shallow copy per claim, add-only.
    out = dict(res or {})
    claims: List[Dict[str, Any]] = (out.get("claims") or [])
    new_claims: List[Dict[str, Any]] = []
    for c in claims:
        cc = dict(c or {})
        lanes = cc.get("researchers") or []
        if len(lanes) >= 2:
            r1 = (lanes[0].get("verdict") or {})
            r2 = (lanes[1].get("verdict") or {})
            cc["consensus"] = _consensus_for_pair(r1, r2)
        else:
            # Fallback: no researchers; derive consensus from top-level verdict conservatively.
            tv = cc.get("verdict") or {}
            cc["consensus"] = {
                "label": tv.get("label") if tv.get("label") in _ALLOWED else "insufficient",
                "confidence": _clamp01(float(tv.get("confidence") or 0.0) * 0.8),
                "rationale": {"rule": "single_lane_fallback"},
                "agreement": {"r1_label": tv.get("label"), "r2_label": None,
                              "r1_conf": tv.get("confidence"), "r2_conf": None,
                              "delta_balance": 0.0}
            }
        new_claims.append(cc)
    out["claims"] = new_claims
    return out

async def _wrap_preview(orig, *args, **kwargs):
    res = await orig(*args, **kwargs)
    merged = _attach_consensus(res)
    _log("consensus_done", claims=len((merged or {}).get("claims") or []))
    return merged

def _install():
    # Ensure dual-researchers wrapper is installed first
    try:
        import_module("intelligence.content.p26_dual_researchers")
    except Exception as e:
        _log("p26_import_fail", error=str(e))

    try:
        run_mod = import_module("intelligence.pipeline.run")
    except Exception as e:
        _log("run_import_fail", error=str(e)); return

    orig = getattr(run_mod, "run_preview", None)
    if orig and asyncio.iscoroutinefunction(orig):
        async def wrapped_run(*args, **kwargs):
            return await _wrap_preview(orig, *args, **kwargs)
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

# Install wrapper at import time
try:
    _install()
    __installed__ = True
    _log("installed", ok=True)
except Exception as _e:
    _log("install_error", error=str(_e))
