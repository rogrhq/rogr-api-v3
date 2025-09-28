from __future__ import annotations
from typing import Dict, Any, List

_SUPPORT_SYNS = ["approved","adopted","announced","report","data","official","passed"]
_REFUTE_SYNS  = ["false","not true","incorrect","debunk","myth","disputed","overstated"]

def _uniq(xs: List[str]) -> List[str]:
    out = []
    seen = set()
    for x in xs:
        x2 = (x or "").strip()
        if not x2: continue
        if x2 in seen: continue
        seen.add(x2); out.append(x2)
    return out

def build(parsed: Dict[str, Any]) -> Dict[str, Any]:
    claim = (parsed.get("text") or "").strip()
    ents  = parsed.get("entities") or []
    year  = parsed.get("year")
    pct   = parsed.get("percent")
    base: List[str] = [claim]

    # entity/numeric/year expansions
    base += [f"{claim} {e}" for e in ents[:3]]
    if pct:  base += [f"{claim} {pct}%"]
    if year: base += [f"{claim} {year}"]

    # support arm: official sources and doc types
    gov   = [f"{q} site:.gov" for q in base]
    edu   = [f"{q} site:.edu" for q in base]
    pdf   = [f"{q} filetype:pdf" for q in base]
    syns  = [f"{claim} {w}" for w in _SUPPORT_SYNS]
    support_q = _uniq(base + gov + edu + pdf + syns)

    # refute arm: challenge/negation
    refute_base = [f"{claim} {w}" for w in _REFUTE_SYNS]
    if year: refute_base += [f"{claim} controversy {year}"]
    refute_q = _uniq(refute_base)

    arms = [
        {"name": "A_support", "providers": ["google","brave"], "queries": support_q[:12], "reason": "Affirmation & official sources (.gov/.edu/pdf)"},
        {"name": "B_refute",  "providers": ["google","brave"], "queries": refute_q[:8],    "reason": "Challenge/contradiction discovery"},
    ]
    return {
        "claim": claim,
        "hints": {"entities": ents, "year": year, "percent": pct},
        "arms": arms,
        "notes": [
            "Deterministic expansion with entity/numeric/year hints",
            "Support arm emphasizes .gov/.edu/pdf and reporting verbs",
            "Refute arm emphasizes contradiction/negation cues",
        ],
    }

# --- Packet Hotfix: provide the legacy API expected by the pipeline ---
# Many older imports call `build_search_plans(...)`. Expose a thin wrapper
# that forwards to the new `build(...)` to keep the pipeline stable.

def build_search_plans(claim: Dict[str, Any], **kw) -> Dict[str, Any]:
    """
    Backwards-compatible wrapper. Delegates to `build(...)`.
    Accepts arbitrary kwargs so callers with older signatures don't break.
    """
    return build(claim, **kw)