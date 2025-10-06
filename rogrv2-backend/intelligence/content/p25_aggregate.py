from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math

def _item_strength(it: Dict[str, Any]) -> float:
    """
    Deterministic per-item strength in [0,1], combining:
      - best frame match score (0..1),
      - item_grade (0..1),
      - coverage weight (full > partial > snippet_only)
    """
    # frame top score
    fms = it.get("frame_matches") or []
    best_frame = 0.0
    for m in fms:
        try:
            sc = float(m.get("score", 0.0))
            if sc > best_frame:
                best_frame = sc
        except Exception:
            pass

    # item grade
    try:
        igr = float(it.get("item_grade", 0.0))
    except Exception:
        igr = 0.0

    # coverage factor
    cov = (it.get("coverage") or "unknown").lower()
    if cov == "full":
        cov_w = 1.0
    elif cov == "partial":
        cov_w = 0.75
    elif cov == "snippet_only":
        cov_w = 0.55
    else:
        cov_w = 0.6  # conservative default

    # combine (bounded)
    base = 0.55 * best_frame + 0.45 * igr
    strength = max(0.0, min(1.0, base * cov_w))
    return strength

def _arm_strength(items: List[Dict[str,Any]], top_k: int = 4) -> float:
    """
    Aggregate arm strength from item strengths with diminishing returns.
    """
    vals = sorted((_item_strength(it) for it in items), reverse=True)
    vals = vals[:top_k]
    # diminishing weights (softmax-like but deterministic)
    weights = [1.00, 0.70, 0.50, 0.35]
    total = 0.0
    for i, v in enumerate(vals):
        w = weights[i] if i < len(weights) else weights[-1] * (0.8 ** (i - len(weights) + 1))
        total += v * w
    # normalize by max possible (sum of weights)
    max_possible = sum(weights[:len(vals)]) if vals else 1.0
    return max(0.0, min(1.0, total / max_possible))

def _confidence_from_arms(sa: float, sb: float, n_items_a: int, n_items_b: int) -> float:
    """
    Confidence increases with total strength and imbalance between arms, and with item count.
    """
    total = max(0.0, min(1.0, 0.6 * max(sa, sb) + 0.4 * (sa + sb) / 2.0))
    count_factor = min(1.0, (n_items_a + n_items_b) / 6.0)  # saturate around 6 items
    balance = abs(sa - sb)
    # mix: enough evidence + clear lead => higher confidence
    conf = 0.4 * total + 0.4 * balance + 0.2 * count_factor
    return max(0.0, min(1.0, conf))

def aggregate_verdict(claim_text: str, arm_a_items: List[Dict[str,Any]], arm_b_items: List[Dict[str,Any]],
                      *, delta: float = 0.15) -> Dict[str, Any]:
    """
    Produce deterministic verdict from arm strengths.
    Returns:
      {
        "label": "supports|challenges|mixed|insufficient",
        "confidence": 0..1,
        "arm_strength": {"support": sa, "challenge": sb, "balance": sa - sb}
      }
    """
    sa = _arm_strength(arm_a_items)
    sb = _arm_strength(arm_b_items)

    # insufficient if both arms weak
    if sa < 0.12 and sb < 0.12:
        label = "insufficient"
    else:
        if (sa - sb) >= delta:
            label = "supports"
        elif (sb - sa) >= delta:
            label = "challenges"
        else:
            label = "mixed"

    conf = _confidence_from_arms(sa, sb, len(arm_a_items), len(arm_b_items))
    return {
        "label": label,
        "confidence": float(conf),
        "arm_strength": {"support": float(sa), "challenge": float(sb), "balance": float(sa - sb)},
    }
