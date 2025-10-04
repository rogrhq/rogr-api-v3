from __future__ import annotations
from typing import List, Dict, Any

__all__ = ["compute_verdict", "compute_verdict_content_first"]

def _topk_sum(items: List[Dict[str, Any]], k: int = 3) -> float:
    if not items:
        return 0.0
    s = 0.0
    for it in items[:max(0, k)]:
        try:
            s += float(it.get("score", 0.0))
        except Exception:
            s += 0.0
    return float(max(0.0, min(3.0, s)))


def _refs_from(items: List[Dict[str, Any]], n: int) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for it in items[:max(0, n)]:
        url = it.get("url")
        if url:
            out.append({"url": url})
    return out


def compute_verdict(arm_A: List[Dict[str, Any]], arm_B: List[Dict[str, Any]], k: int = 3) -> Dict[str, Any]:
    """
    Deterministic, symmetric verdict using neutral scores only.
    Inputs: ranked arm_A and arm_B (items have 'score' in [0,1]).
    Output: {'label', 'confidence', 'rationale_refs'}
    """
    sA = _topk_sum(arm_A, k=k)
    sB = _topk_sum(arm_B, k=k)
    total = sA + sB
    if total <= 1e-6 or total < 0.30:
        return {"label": "insufficient", "confidence": 0.0, "rationale_refs": []}

    pA = sA / (total + 1e-9)
    pB = 1.0 - pA

    if 0.45 <= pA <= 0.55:
        return {
            "label": "mixed",
            "confidence": 0.4,
            "rationale_refs": (_refs_from(arm_A, 2) + _refs_from(arm_B, 2))[:4],
        }
    if pA > 0.55:
        return {
            "label": "support",
            "confidence": float(min(1.0, max(0.0, pA))),
            "rationale_refs": _refs_from(arm_A, 3),
        }
    return {
        "label": "challenge",
        "confidence": float(min(1.0, max(0.0, pB))),
        "rationale_refs": _refs_from(arm_B, 3),
    }


def compute_verdict_content_first(arm_A: List[Dict[str, Any]], arm_B: List[Dict[str, Any]], k: int = 3) -> Dict[str, Any]:
    """Prefer content_score when present; otherwise fall back to score.
    Keeps the same symmetric mapping to {label, confidence, rationale_refs}.
    """
    def _eff(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            sc = it.get("content_score")
            if isinstance(sc, (int, float)) and sc > 0:
                out.append({**it, "_eff": float(sc)})
            else:
                out.append({**it, "_eff": float(it.get("score", 0.0))})
        return out

    A = _eff(arm_A)
    B = _eff(arm_B)

    sA = sum(x.get("_eff", 0.0) for x in A[:max(0, k)])
    sB = sum(x.get("_eff", 0.0) for x in B[:max(0, k)])
    total = sA + sB
    if total <= 1e-6 or total < 0.30:
        return {"label": "insufficient", "confidence": 0.0, "rationale_refs": []}

    pA = sA / (total + 1e-9)
    pB = 1.0 - pA
    if 0.45 <= pA <= 0.55:
        return {
            "label": "mixed",
            "confidence": 0.4,
            "rationale_refs": (_refs_from(arm_A, 2) + _refs_from(arm_B, 2))[:4],
        }
    if pA > 0.55:
        return {
            "label": "support",
            "confidence": float(min(1.0, max(0.0, pA))),
            "rationale_refs": _refs_from(arm_A, 3),
        }
    return {
        "label": "challenge",
        "confidence": float(min(1.0, max(0.0, pB))),
        "rationale_refs": _refs_from(arm_B, 3),
    }
