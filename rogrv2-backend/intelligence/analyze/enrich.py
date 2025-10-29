from __future__ import annotations
from typing import Dict, Any

from intelligence.claims.interpret import parse_claim_hybrid as parse_claim
# Phase 9: Precision handling enhancements (ADDED)
from intelligence.content.shared.semantic_depth import detect_negation, detect_hedging

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

    # Phase 9: Semantic depth analysis (ADDED)
    claim_text = base.get("text", "")

    # Detect negation (e.g., "not true", "no evidence")
    has_negation = detect_negation(claim_text)

    # Detect hedging (e.g., "might", "possibly", "approximately")
    hedging_result = detect_hedging(claim_text)

    # Extract precision context for numeric claims
    numbers = enrich.get("numbers", {})
    precision_context = {
        "has_numbers": bool(numbers.get("percents") or numbers.get("years") or numbers.get("pairs")),
        "has_percents": bool(numbers.get("percents")),
        "has_years": bool(numbers.get("years")),
        "has_units": bool(numbers.get("pairs")),
        "precision_required": bool(numbers.get("percents") or numbers.get("pairs"))
    }

    # Add semantic flags to enrichment
    semantic_flags = {
        "negation": has_negation,
        "hedging": hedging_result.get("has_hedging", False),
        "hedging_words": hedging_result.get("hedge_words", []),
        "precision_context": precision_context
    }

    # merge: base precedence for text/tier, enrichment adds structured fields
    out = {**enrich, "text": base.get("text",""), "tier": base.get("tier","primary"), "semantic_flags": semantic_flags}
    return out