from __future__ import annotations
from typing import List, Dict, Any

__all__ = ["rank_candidates"]


def _arm_label(it: Dict[str, Any]) -> str:
    arm = (it.get("arm") or "A").upper()
    return "B" if arm.startswith("B") else "A"


def _rank_within_arm(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Stable sort by score (desc); default score=0.0 if missing
    sorted_items = sorted(
        (dict(it) for it in items if isinstance(it, dict)),
        key=lambda x: float(x.get("score", 0.0)),
        reverse=True,
    )
    for idx, it in enumerate(sorted_items, start=1):
        it["rank"] = idx
    return sorted_items


def rank_candidates(
    items: List[Dict[str, Any]] | None = None,
    *,
    candidates: List[Dict[str, Any]] | None = None,
    claim_text: str | None = None,   # accepted for signature compatibility; unused in P15
    query: str | None = None,        # accepted for signature compatibility; unused in P15
    top_k: int | None = None,
    **kwargs: Any,                    # ignore extra kwargs for forward-compat
) -> List[Dict[str, Any]]:
    """Per-arm ranking for evidence candidates.
    Accepts either a positional flat list `items` or keyword `candidates=...`.
    Returns a flat list where items are grouped A then B, each arm independently ranked 1..N.
    Applies optional per-arm truncation when `top_k` is provided (> 0).
    """
    src = candidates if candidates is not None else items
    if not src:
        return []

    armA: List[Dict[str, Any]] = []
    armB: List[Dict[str, Any]] = []
    for it in src:
        if not isinstance(it, dict):
            # ignore non-dicts defensively
            continue
        (armA if _arm_label(it) == "A" else armB).append(it)

    ranked_A = _rank_within_arm(armA)
    ranked_B = _rank_within_arm(armB)

    if isinstance(top_k, int) and top_k > 0:
        ranked_A = ranked_A[:top_k]
        ranked_B = ranked_B[:top_k]
        # ranks already 1..N after _rank_within_arm; truncation preserves numbering

    # Concatenate A then B to preserve downstream expectations
    return ranked_A + ranked_B
