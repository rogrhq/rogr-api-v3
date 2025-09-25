import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from intelligence.claims.extract import extract_claims
from intelligence.strategy.plan import build_search_plans

_SAMPLE = (
    "The mayor says the new bridge will cost $250 million and open in 2027. "
    "Officials indicate prior estimates were lower because steel prices rose. "
    "Residents claim traffic has doubled since 2020. "
    "This announcement follows a year of public hearings."
)

def main():
    claims = extract_claims(_SAMPLE)
    assert isinstance(claims, list) and len(claims) >= 3, "Expected 3+ extracted claims"
    tiers = {c.tier.value for c in claims}
    # Expect primary/secondary/tertiary coverage
    for needed in ("primary", "secondary", "tertiary"):
        assert needed in tiers, f"Missing tier: {needed}"

    plans = build_search_plans(claims)
    assert isinstance(plans, list) and len(plans) >= (len(claims) * 2), "Each claim should have A and B arms"
    # Validate shape of first plan
    p0 = plans[0]
    for k in ("claim_text", "tier", "arm", "seed", "queries"):
        assert k in p0, f"Missing plan key: {k}"
    assert p0["arm"] in ("A", "B"), "Arm must be A or B"
    assert isinstance(p0["queries"], list) and len(p0["queries"]) >= 2, "Each arm needs multiple queries"

    print("PASS")
    # Also print a compact preview for human sanity (non-blocking)
    preview = {
        "claims": [{"text": c.text, "tier": c.tier.value} for c in claims[:3]],
        "first_plan": p0
    }
    print(json.dumps(preview, ensure_ascii=False)[:400])

if __name__ == "__main__":
    main()