from typing import List, Dict, Any
from intelligence.claims.models import ExtractedClaim

def build_search_plans(claims: List[ExtractedClaim]) -> List[Dict[str, Any]]:
    """
    Returns a list of plan dicts:
    { claim_text, tier, arm, seed, queries }
    """
    from intelligence.strategy.seed import seed_queries_for_claim
    plans: List[Dict[str, Any]] = []
    for c in claims:
        arms = seed_queries_for_claim(c)
        for arm, queries in arms.items():
            plans.append({
                "claim_text": c.text,
                "tier": c.tier.value,
                "arm": arm,
                "seed": "precision" if arm == "A" else "breadth",
                "queries": queries,
            })
    return plans