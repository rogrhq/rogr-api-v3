from typing import List, Dict, Tuple, Any
import os
import random
import hashlib


def get_available_providers() -> List[str]:
    """Detect providers from environment variables."""
    providers = []
    if os.getenv('GOOGLE_CSE_API_KEY'):
        providers.append('google')
    if os.getenv('BRAVE_API_KEY'):
        providers.append('brave')
    if os.getenv('BING_API_KEY'):
        providers.append('bing')
    return providers if providers else ['google']


def _generate_seed(lane_id: str, claim_text: str) -> int:
    """Generate deterministic seed from lane + claim."""
    combined = f"{lane_id}:{claim_text}"
    hash_obj = hashlib.md5(combined.encode())
    return int(hash_obj.hexdigest(), 16) % (2**31)


def _ordered_providers_for_lane(lane_id: str, available: List[str]) -> List[str]:
    """Get provider order for lane."""
    if lane_id == "R1":
        # Prefer google first
        return sorted(available, key=lambda p: (p != 'google', p))
    else:  # R2
        # Prefer brave first
        return sorted(available, key=lambda p: (p != 'brave', p))


def _shuffle_queries_deterministic(queries: List[str], seed: int) -> List[str]:
    """Shuffle queries deterministically."""
    shuffled = queries.copy()
    random.Random(seed).shuffle(shuffled)
    return shuffled


def diversify_plan_for_lane(
    base_plan: Dict[str, Any],
    lane_id: str,
    claim_text: str,
    available_providers: List[str]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Create lane-specific diversified plan.

    Args:
        base_plan: Base search plan with arms and queries
        lane_id: "R1" or "R2"
        claim_text: Claim being fact-checked
        available_providers: List of available provider names

    Returns:
        Tuple of (diversified_plan, lane_config)
    """
    # Generate seed
    seed = _generate_seed(lane_id, claim_text)

    # Order providers
    providers = _ordered_providers_for_lane(lane_id, available_providers)

    # Copy plan
    import copy
    diversified = copy.deepcopy(base_plan)

    # NORMALIZE: Handle both dict and list format for arms
    arms = diversified.get("arms", {})
    if isinstance(arms, dict):
        # Convert dict format {"A": {...}, "B": {...}} to list format
        arms_list = []
        for name, arm_data in arms.items():
            arms_list.append({"name": name, **arm_data})
        diversified["arms"] = arms_list

    # Phase 5: Generate lane-specific queries (CHANGED)
    from intelligence.strategy.plan_v2 import generate_queries_r1, generate_queries_r2
    import sys

    # DEBUG
    print(f"\n[DEBUG diversify] Lane {lane_id} before query generation:", file=sys.stderr)
    for arm in diversified.get("arms", []):
        print(f"  {arm.get('name')}: {arm.get('queries', [])[:2]}", file=sys.stderr)

    # Extract claim data from plan (added by Part A above)
    claim_data = diversified.get("claim", {})
    claim_entities = claim_data.get("entities", [])

    # Convert numbers dict to list of {"value": ...} dicts (bug fix for TASK 2.1)
    numbers_dict = claim_data.get("numbers", {})
    claim_numbers = []
    if isinstance(numbers_dict, dict):
        # Add percents
        for percent in numbers_dict.get('percents', []):
            claim_numbers.append({"value": percent})
        # Add years
        for year in numbers_dict.get('years', []):
            claim_numbers.append({"value": year})
        # Add number_units (tuples of (value, unit))
        for num_unit in numbers_dict.get('number_units', []):
            if isinstance(num_unit, (list, tuple)) and len(num_unit) >= 2:
                claim_numbers.append({"value": num_unit[0], "unit": num_unit[1]})
            elif isinstance(num_unit, (list, tuple)) and len(num_unit) == 1:
                claim_numbers.append({"value": num_unit[0]})
            else:
                # Fallback if structure is different
                claim_numbers.append({"value": num_unit})
    elif isinstance(numbers_dict, list):
        # Already a list
        claim_numbers = numbers_dict
    else:
        claim_numbers = []

    queries_preview = {}
    for arm in diversified.get("arms", []):
        arm_name = arm.get("name", "")

        # Determine arm label (A or B)
        arm_label = "A" if "A" in arm_name.upper() else "B"

        # Reconstruct full claim dict with concept/dimension from meta
        claim_dict = {
            "text": claim_text,
            "entities": claim_entities,
            "numbers": claim_data.get("numbers", {}),
            "concept": diversified.get("meta", {}).get("concept", ""),
            "dimension": diversified.get("meta", {}).get("dimension", "")
        }

        print(f"  [DEBUG] claim_dict: concept='{claim_dict['concept']}', dimension='{claim_dict['dimension']}', entities={len(claim_entities)}", file=sys.stderr)

        # Generate queries based on lane strategy
        if lane_id == "R1":
            # R1: Precision - semantic queries, high similarity
            new_queries = generate_queries_r1(claim_dict, arm_label, diversified)
            print(f"  [DEBUG] generate_queries_r1 returned {len(new_queries)} queries for {arm_name}", file=sys.stderr)
        else:  # R2
            # R2: Recall - semantic queries, broader exploration
            new_queries = generate_queries_r2(claim_dict, arm_label, diversified)
            print(f"  [DEBUG] generate_queries_r2 returned {len(new_queries)} queries for {arm_name}", file=sys.stderr)

        # Replace queries (not shuffle)
        arm["queries"] = new_queries
        queries_preview[arm_name] = new_queries[:3]

        # DEBUG
        print(f"  [DEBUG diversify] {arm_name} NEW queries: {new_queries[:2]}", file=sys.stderr)

    # Prefer Brave for R1 (precision), Google for R2 (recall)
    preferred_providers = ["brave", "google"] if lane_id == "R1" else ["google", "brave"]

    # Add strategy info to config
    config = {
        "lane_id": lane_id,
        "strategy": "precision" if lane_id == "R1" else "recall",
        "providers": preferred_providers,  # Provider order matters
        "seed": seed,
        "queries_first3": queries_preview,
        "note": "R1=Brave first (precision), R2=Google first (recall)"
    }

    return diversified, config


# TEST
if __name__ == "__main__":
    base = {"arms": [{"name": "A", "queries": ["q1", "q2", "q3"]}]}

    r1_plan, r1_cfg = diversify_plan_for_lane(base, "R1", "Test", ["google", "brave"])
    r2_plan, r2_cfg = diversify_plan_for_lane(base, "R2", "Test", ["google", "brave"])

    print(f"R1 providers: {r1_cfg['providers']}")
    print(f"R2 providers: {r2_cfg['providers']}")
    print(f"R1 queries: {r1_plan['arms'][0]['queries']}")
    print(f"R2 queries: {r2_plan['arms'][0]['queries']}")

    # Verify provider ordering differs
    assert r1_cfg['providers'] != r2_cfg['providers'], "R1 and R2 should have different provider orders"

    # Verify that shuffling changed the order from original
    original_order = base['arms'][0]['queries']
    r1_shuffled = r1_plan['arms'][0]['queries']
    assert r1_shuffled != original_order, "Queries should be shuffled from original order"

    # Test determinism
    r1_plan2, _ = diversify_plan_for_lane(base, "R1", "Test", ["google", "brave"])
    assert r1_plan['arms'][0]['queries'] == r1_plan2['arms'][0]['queries'], "Same lane should produce deterministic results"

    print("✓ PASS")
