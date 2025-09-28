from __future__ import annotations
from typing import Dict, Any

from intelligence.claims.interpret import parse_claim

def enrich_claim_obj(claim: Any) -> Dict[str, Any]:
    """
    Accepts either a string claim or an existing claim dict with at least 'text'.
    Returns a dict: { text, tier?, ...enrichment }
    """
    if isinstance(claim, str):
        base = {"text": claim, "tier": "primary"}
    elif isinstance(claim, dict):
        base = {"tier": claim.get("tier","primary"), "text": claim.get("text","")}
        # keep any existing fields but they'll be overwritten by deterministic enrichment keys where relevant
        base.update({k:v for k,v in claim.items() if k not in ("text","tier")})
    else:
        base = {"text": str(claim), "tier": "primary"}

    enrich = parse_claim(base.get("text",""))
    # merge: base precedence for text/tier, enrichment adds structured fields
    out = {**enrich, "text": base.get("text",""), "tier": base.get("tier","primary")}
    return out