from __future__ import annotations
from typing import Any, Dict, List
from urllib.parse import urlparse

def _host(u: str) -> str:
    try:
        return (urlparse(u or "").netloc or "").lower()
    except Exception:
        return ""

def _title_set(lst: List[Dict[str, Any]]) -> set:
    return set((x.get("title") or "").lower() for x in lst or [])

def _host_set(lst: List[Dict[str, Any]]) -> set:
    return set(_host(x.get("url","")) for x in lst or [])

def _stance_hint(snippet: str) -> int:
    """
    Very light stance hint from language cues:
      +1 support-ish, -1 challenge-ish, 0 neutral/unknown
    (This is a placeholder until full stance analyzers; deterministic & bounded.)
    """
    s = (snippet or "").lower()
    pos = any(k in s for k in ["confirms", "supports", "corroborate", "in line with"])
    neg = any(k in s for k in ["disputes", "contradicts", "refutes", "debunk"])
    return 1 if pos and not neg else (-1 if neg and not pos else 0)

def compute_overlap_conflict(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Produces:
      overlap_ratio: Jaccard on hosts & titles (avg)
      conflict_score: fraction of pairs with opposing stance hints
      stability: 1 - conflict_score, bounded [0,1]
    """
    a = a or []
    b = b or []
    if not a and not b:
        return {"overlap_ratio": 0.0, "conflict_score": 0.0, "stability": 1.0}

    th_a, th_b = _title_set(a), _title_set(b)
    hh_a, hh_b = _host_set(a), _host_set(b)

    def jacc(x: set, y: set) -> float:
        if not x and not y:
            return 0.0
        inter = len(x & y)
        union = len(x | y) or 1
        return inter / union

    titles_overlap = jacc(th_a, th_b)
    hosts_overlap  = jacc(hh_a, hh_b)
    overlap_ratio  = round((titles_overlap + hosts_overlap) / 2.0, 3)

    # conflict via stance hints on top-k (up to 6 each)
    conflicts = 0
    total = 0
    for i in range(min(6, len(a))):
        for j in range(min(6, len(b))):
            sa = _stance_hint(a[i].get("snippet",""))
            sb = _stance_hint(b[j].get("snippet",""))
            if sa == 0 or sb == 0:
                continue
            total += 1
            if sa != sb:
                conflicts += 1
    conflict_score = round((conflicts / total) if total else 0.0, 3)
    stability = round(max(0.0, 1.0 - conflict_score), 3)

    return {"overlap_ratio": overlap_ratio, "conflict_score": conflict_score, "stability": stability}