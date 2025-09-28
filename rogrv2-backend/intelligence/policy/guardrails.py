from __future__ import annotations
import re
from typing import Dict, Any, List, Tuple

_DOMAIN_RE = re.compile(r"^(?:https?://)?([^/]+)", re.I)

def _domain(u: str) -> str:
    if not u:
        return ""
    m = _DOMAIN_RE.match(u.strip())
    return (m.group(1).lower() if m else "").replace("www.", "")

def _typed(item: Dict[str, Any]) -> str:
    # evidence item shape is provider-normalized; 'type' optional
    t = (item.get("type") or "").strip().lower()
    if t:
        return t
    # light heuristic from URL
    d = _domain(item.get("url",""))
    if any(k in d for k in ("gov","state.","city.","county.","nasa.","nih.","nps.")):
        return "government"
    return "web"

def enforce_diversity(
    items: List[Dict[str, Any]],
    max_per_domain: int = 1,
    min_total: int = 2,
    prefer_types: Tuple[str, ...] = ("peer_review","government","news","web"),
) -> Dict[str, Any]:
    """
    Enforce domain diversity caps and keep top-N per domain by existing 'rank' (lower is better),
    falling back to list order. Returns {kept: [...], dropped: [...], stats: {...}}.
    """
    if not items:
        return {"kept": [], "dropped": [], "stats": {"total": 0, "domains": {}}}

    # group by domain
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for i, it in enumerate(items):
        it = dict(it)  # copy
        it.setdefault("rank", i)  # ensure stable
        dom = _domain(it.get("url",""))
        buckets.setdefault(dom, []).append(it)

    kept: List[Dict[str, Any]] = []
    dropped: List[Dict[str, Any]] = []
    dom_stats: Dict[str, int] = {}

    # within each domain, sort by rank asc (best first), keep at most K
    for dom, lst in buckets.items():
        lst_sorted = sorted(lst, key=lambda x: (x.get("rank", 1_000_000)))
        take, drop = lst_sorted[:max_per_domain], lst_sorted[max_per_domain:]
        kept.extend(take)
        dropped.extend(drop)
        dom_stats[dom or ""] = len(take)

    # If after per-domain cap we have fewer than min_total, refill by best of dropped, different domains first
    if len(kept) < min_total and dropped:
        # prefer items from domains not yet represented, then by rank
        represented = { _domain(k.get("url","")) for k in kept }
        dropped_sorted = sorted(dropped, key=lambda x: (_domain(x.get("url","")) in represented, x.get("rank", 1_000_000)))
        for it in dropped_sorted:
            if len(kept) >= min_total:
                break
            kept.append(it)

    # Stable order by 'rank'
    kept = sorted(kept, key=lambda x: x.get("rank", 1_000_000))

    # Annotate kept with coarse 'type' if missing
    for it in kept:
        it.setdefault("type", _typed(it))

    # Provide quick type coverage stats
    type_counts: Dict[str, int] = {}
    for it in kept:
        t = (it.get("type") or "").lower()
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "kept": kept,
        "dropped": dropped,
        "stats": {
            "total": len(items),
            "kept": len(kept),
            "dropped": len(dropped),
            "domains": dom_stats,
            "types": type_counts,
            "parameters": {
                "max_per_domain": max_per_domain,
                "min_total": min_total,
                "prefer_types": list(prefer_types),
                "version": "s2p9-1",
            },
        },
    }

def apply_guardrails_to_arms(evidence_bundle: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Input bundle like {"A":{"candidates":[...]}, "B":{"candidates":[...]}}
    Returns (new_bundle, guardrails_report)
    """
    if not isinstance(evidence_bundle, dict):
        return evidence_bundle, {"error": "invalid_bundle"}

    out: Dict[str, Any] = {}
    report: Dict[str, Any] = {}

    for arm in ("A","B"):
        cand = (((evidence_bundle.get(arm) or {}).get("candidates")) or [])
        res = enforce_diversity(cand, max_per_domain=1, min_total=2)
        out[arm] = {"candidates": res["kept"]}
        report[arm] = res["stats"]

    report["version"] = "s2p9-1"
    return out, report