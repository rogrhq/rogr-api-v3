from __future__ import annotations
from typing import Dict, List, Any, Tuple

def _infer_item_stance(item: Dict[str, Any]) -> str:
    """
    Very lightweight stance guesser.
    Priority:
      1) explicit 'stance' field on evidence item if present
      2) cues set (if present)
      3) fallback: 'neutral'
    """
    s = (item.get("stance") or "").strip().lower()
    if s in ("pro","support","for","agree","affirm"): return "pro"
    if s in ("con","challenge","against","disagree","refute"): return "con"

    cues = item.get("cues") or {}
    if isinstance(cues, dict):
        # If pipeline has already tagged polarity (S2P5+), respect it
        pol = (cues.get("polarity") or "").lower()
        if pol in ("pro","support","for","agree","affirm"): return "pro"
        if pol in ("con","challenge","against","disagree","refute"): return "con"

    return "neutral"

def compute_source_balance(arm_items: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count pro/con/neutral items for a given evidence arm.
    """
    pro = con = neu = 0
    for it in arm_items or []:
        st = _infer_item_stance(it)
        if st == "pro": pro += 1
        elif st == "con": con += 1
        else: neu += 1
    return {"pro": pro, "con": con, "neutral": neu}

def summarize_balance(arm_a: List[Dict[str, Any]], arm_b: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Provide per-arm counts plus a combined rollup.
    """
    a = compute_source_balance(arm_a)
    b = compute_source_balance(arm_b)
    rollup = {"pro": a["pro"] + b["pro"], "con": a["con"] + b["con"], "neutral": a["neutral"] + b["neutral"]}
    return {"A": a, "B": b, "all": rollup}