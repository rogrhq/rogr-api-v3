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

    # Shuffle queries for each arm
    queries_preview = {}
    for arm in diversified.get("arms", []):
        original_queries = arm.get("queries", [])
        shuffled = _shuffle_queries_deterministic(original_queries, seed)
        arm["queries"] = shuffled
        queries_preview[arm.get("name", "?")] = shuffled[:3]

    # Config
    config = {
        "lane_id": lane_id,
        "providers": providers,
        "seed": seed,
        "queries_first3": queries_preview
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
