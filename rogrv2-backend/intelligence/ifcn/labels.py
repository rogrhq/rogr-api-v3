from __future__ import annotations
from typing import Dict, List, Tuple

_ALLOWED = ("True","Mostly True","Mixed","Mostly False","False")

def label_for_score(score: int) -> str:
    """Map 0..100 numeric score to IFCN-style label."""
    s = max(0, min(100, int(score)))
    if s >= 85: return "True"
    if s >= 70: return "Mostly True"
    if s >= 40: return "Mixed"
    if s >= 20: return "Mostly False"
    return "False"

def scale_spec() -> Dict[str,str]:
    return {
        "True": "85-100",
        "Mostly True": "70-84",
        "Mixed": "40-69",
        "Mostly False": "20-39",
        "False": "0-19",
    }

def explanation_from_counts(claim_text: str, counts: Dict[str,int], top_sources: List[Tuple[str,str]]) -> str:
    """
    Build a short deterministic explanation for a verdict.
    counts: {"support": X, "refute": Y, "neutral": Z}
    top_sources: list of (title, publisher) for traceability
    """
    s = int(counts.get("support",0))
    r = int(counts.get("refute",0))
    n = int(counts.get("neutral",0))
    parts = []
    parts.append(f"Claim: {claim_text.strip()[:180]}")
    parts.append(f"Evidence summary — support:{s}, refute:{r}, neutral:{n}.")
    if top_sources:
        listed = "; ".join([f"{t} — {p}" for (t,p) in top_sources[:3]])
        parts.append(f"Top sources considered: {listed}.")
    parts.append("Method: A/B search arms, deduplication, lexical ranking, stance and quality scoring, consensus aggregation.")
    return " ".join(parts)