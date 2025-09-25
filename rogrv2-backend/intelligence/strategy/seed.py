from typing import Dict, List
from intelligence.claims.models import ExtractedClaim

def _shorten(text: str, limit: int = 128) -> str:
    t = " ".join(text.split())
    return t if len(t) <= limit else t[:limit].rsplit(" ", 1)[0]

def seed_queries_for_claim(claim: ExtractedClaim) -> Dict[str, List[str]]:
    """
    Arm A: high-precision factual phrasing (quoted + variations)
    Arm B: breadth & challenge phrasing (unquoted variants, counter-terms)
    No domains; bias-neutral; deterministic string ops only.
    """
    base = _shorten(claim.text)
    # Extract a minimal keyword spine (drop tiny tokens)
    keywords = " ".join([w for w in base.split() if len(w) > 3])[:128].strip()
    if not keywords:
        keywords = base

    arm_a = [
        f"\"{base}\"",
        f"\"{base}\" facts data sources",
        f"{keywords} timeline chronology"
    ]
    arm_b = [
        f"{keywords} critique counter evidence",
        f"{keywords} methodology reliability",
        f"{keywords} official records report"
    ]
    # De-duplicate while preserving order
    def _dedupe(xs: List[str]) -> List[str]:
        seen, out = set(), []
        for q in xs:
            if q not in seen:
                seen.add(q); out.append(q)
        return out

    return {"A": _dedupe(arm_a), "B": _dedupe(arm_b)}