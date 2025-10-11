"""
P28 Query Diversification Structural Tests

Tests structural integrity of the query diversification mechanism:
- Field validation (all expected fields present)
- Field structure (nested objects correct)
- Edge cases (empty inputs, missing fields, format variations)
- Error handling (malformed data doesn't crash)
"""

import sys
sys.path.insert(0, '/Users/txtk/Documents/ROGR/github/rogrv2-backend')

from intelligence.planning.diversify import (
    get_available_providers,
    diversify_plan_for_lane,
    _generate_seed,
    _ordered_providers_for_lane,
    _shuffle_queries_deterministic
)


def test_get_available_providers():
    """Test provider detection from environment"""
    # This will return actual providers from env or default to ['google']
    providers = get_available_providers()

    assert isinstance(providers, list), "Should return list"
    assert len(providers) > 0, "Should have at least one provider"
    assert all(isinstance(p, str) for p in providers), "All providers should be strings"

    print(f"✓ Provider detection: {providers}")


def test_generate_seed_deterministic():
    """Test seed generation is deterministic"""
    seed1 = _generate_seed("R1", "Test claim")
    seed2 = _generate_seed("R1", "Test claim")
    seed3 = _generate_seed("R2", "Test claim")
    seed4 = _generate_seed("R1", "Different claim")

    assert seed1 == seed2, "Same lane + claim should produce same seed"
    assert seed1 != seed3, "Different lanes should produce different seeds"
    assert seed1 != seed4, "Different claims should produce different seeds"
    assert isinstance(seed1, int), "Seed should be integer"

    print(f"✓ Seed generation: R1={seed1}, R2={seed3}")


def test_ordered_providers_for_lane():
    """Test provider ordering differs by lane"""
    providers = ["google", "brave", "bing"]

    r1_order = _ordered_providers_for_lane("R1", providers)
    r2_order = _ordered_providers_for_lane("R2", providers)

    assert isinstance(r1_order, list), "Should return list"
    assert len(r1_order) == len(providers), "Should have all providers"
    assert set(r1_order) == set(providers), "Should contain same providers"

    # R1 prefers google
    assert r1_order[0] == "google", "R1 should prefer google first"

    # R2 prefers brave
    assert r2_order[0] == "brave", "R2 should prefer brave first"

    print(f"✓ Provider ordering: R1={r1_order}, R2={r2_order}")


def test_shuffle_queries_deterministic():
    """Test query shuffling is deterministic"""
    queries = ["q1", "q2", "q3", "q4", "q5"]
    seed = 12345

    shuffled1 = _shuffle_queries_deterministic(queries, seed)
    shuffled2 = _shuffle_queries_deterministic(queries, seed)
    shuffled3 = _shuffle_queries_deterministic(queries, 67890)

    assert shuffled1 == shuffled2, "Same seed should produce same shuffle"
    assert shuffled1 != shuffled3, "Different seeds should produce different shuffle"
    assert set(shuffled1) == set(queries), "Should contain all original queries"
    assert len(shuffled1) == len(queries), "Should have same count"

    print(f"✓ Query shuffling: original={queries[:3]}, shuffled={shuffled1[:3]}")


def test_diversify_plan_output_structure():
    """Test diversify_plan_for_lane returns correct structure"""
    base_plan = {
        "arms": [
            {"name": "A", "queries": ["q1", "q2", "q3"]},
            {"name": "B", "queries": ["q4", "q5", "q6"]}
        ]
    }

    diversified, config = diversify_plan_for_lane(
        base_plan, "R1", "Test claim", ["google", "brave"]
    )

    # Check diversified plan structure
    assert isinstance(diversified, dict), "Plan should be dict"
    assert "arms" in diversified, "Plan should have 'arms'"
    assert isinstance(diversified["arms"], list), "Arms should be list"

    # Check config structure
    assert isinstance(config, dict), "Config should be dict"
    assert "lane_id" in config, "Config missing 'lane_id'"
    assert "providers" in config, "Config missing 'providers'"
    assert "seed" in config, "Config missing 'seed'"
    assert "queries_first3" in config, "Config missing 'queries_first3'"

    # Check config values
    assert config["lane_id"] == "R1", "lane_id should match input"
    assert isinstance(config["providers"], list), "providers should be list"
    assert isinstance(config["seed"], int), "seed should be int"
    assert isinstance(config["queries_first3"], dict), "queries_first3 should be dict"

    print("✓ Output structure validation passed")


def test_diversify_plan_arm_format_normalization():
    """Test that dict format arms are normalized to list format"""
    # Dict format (old style)
    base_plan_dict = {
        "arms": {
            "A": {"queries": ["q1", "q2", "q3"]},
            "B": {"queries": ["q4", "q5", "q6"]}
        }
    }

    diversified, config = diversify_plan_for_lane(
        base_plan_dict, "R1", "Test", ["google"]
    )

    # Should normalize to list format
    assert isinstance(diversified["arms"], list), "Arms should be normalized to list"
    assert len(diversified["arms"]) == 2, "Should have 2 arms"

    # Check arms have 'name' field
    for arm in diversified["arms"]:
        assert "name" in arm, "Each arm should have 'name' field"
        assert "queries" in arm, "Each arm should have 'queries' field"

    print("✓ Arm format normalization passed")


def test_diversify_plan_preserves_arms():
    """Test that all arms are preserved in diversified plan"""
    base_plan = {
        "arms": [
            {"name": "A", "queries": ["q1", "q2", "q3"]},
            {"name": "B", "queries": ["q4", "q5"]}
        ]
    }

    diversified, _ = diversify_plan_for_lane(
        base_plan, "R1", "Test", ["google"]
    )

    assert len(diversified["arms"]) == 2, "Should preserve both arms"

    arm_names = [arm["name"] for arm in diversified["arms"]]
    assert "A" in arm_names, "Arm A should be preserved"
    assert "B" in arm_names, "Arm B should be preserved"

    # Check query counts
    for arm in diversified["arms"]:
        if arm["name"] == "A":
            assert len(arm["queries"]) == 3, "Arm A should have 3 queries"
        elif arm["name"] == "B":
            assert len(arm["queries"]) == 2, "Arm B should have 2 queries"

    print("✓ Arm preservation passed")


def test_diversify_plan_queries_first3():
    """Test queries_first3 preview in config"""
    base_plan = {
        "arms": [
            {"name": "A", "queries": ["q1", "q2", "q3", "q4", "q5"]}
        ]
    }

    _, config = diversify_plan_for_lane(
        base_plan, "R1", "Test", ["google"]
    )

    assert "A" in config["queries_first3"], "Should have preview for arm A"
    preview = config["queries_first3"]["A"]
    assert isinstance(preview, list), "Preview should be list"
    assert len(preview) <= 3, "Preview should have at most 3 queries"

    print(f"✓ Query preview: {preview}")


def test_edge_case_empty_arms():
    """Test handling of empty arms"""
    base_plan = {"arms": []}

    diversified, config = diversify_plan_for_lane(
        base_plan, "R1", "Test", ["google"]
    )

    assert "arms" in diversified, "Should have arms field"
    assert isinstance(diversified["arms"], list), "Arms should be list"
    assert len(diversified["arms"]) == 0, "Empty arms should remain empty"

    print("✓ Empty arms handling passed")


def test_edge_case_empty_queries():
    """Test handling of empty queries"""
    base_plan = {
        "arms": [
            {"name": "A", "queries": []}
        ]
    }

    diversified, config = diversify_plan_for_lane(
        base_plan, "R1", "Test", ["google"]
    )

    assert len(diversified["arms"]) == 1, "Should preserve arm"
    assert len(diversified["arms"][0]["queries"]) == 0, "Empty queries should remain empty"
    assert config["queries_first3"]["A"] == [], "Preview should be empty"

    print("✓ Empty queries handling passed")


def test_edge_case_single_query():
    """Test handling of single query"""
    base_plan = {
        "arms": [
            {"name": "A", "queries": ["only_query"]}
        ]
    }

    diversified, config = diversify_plan_for_lane(
        base_plan, "R1", "Test", ["google"]
    )

    assert len(diversified["arms"][0]["queries"]) == 1, "Should preserve single query"
    assert diversified["arms"][0]["queries"][0] == "only_query", "Query should be unchanged"

    print("✓ Single query handling passed")


def test_determinism_same_inputs():
    """Test that same inputs always produce same outputs"""
    base_plan = {
        "arms": [
            {"name": "A", "queries": ["q1", "q2", "q3", "q4", "q5"]}
        ]
    }

    div1, cfg1 = diversify_plan_for_lane(base_plan, "R1", "Claim", ["google", "brave"])
    div2, cfg2 = diversify_plan_for_lane(base_plan, "R1", "Claim", ["google", "brave"])

    # Seeds should match
    assert cfg1["seed"] == cfg2["seed"], "Seeds should be identical"

    # Provider order should match
    assert cfg1["providers"] == cfg2["providers"], "Provider order should be identical"

    # Query shuffle should match
    assert div1["arms"][0]["queries"] == div2["arms"][0]["queries"], "Query order should be identical"

    print("✓ Determinism verified")


def test_different_lanes_produce_different_results():
    """Test that R1 and R2 produce different diversifications"""
    base_plan = {
        "arms": [
            {"name": "A", "queries": ["q1", "q2", "q3", "q4", "q5"]}
        ]
    }

    div_r1, cfg_r1 = diversify_plan_for_lane(base_plan, "R1", "Claim", ["google", "brave"])
    div_r2, cfg_r2 = diversify_plan_for_lane(base_plan, "R2", "Claim", ["google", "brave"])

    # Seeds should differ
    assert cfg_r1["seed"] != cfg_r2["seed"], "R1 and R2 should have different seeds"

    # Provider order should differ
    assert cfg_r1["providers"] != cfg_r2["providers"], "R1 and R2 should have different provider orders"

    # Query order should differ (with high probability for 5+ queries)
    assert div_r1["arms"][0]["queries"] != div_r2["arms"][0]["queries"], "R1 and R2 should have different query orders"

    print(f"✓ R1 vs R2 differentiation: R1_providers={cfg_r1['providers']}, R2_providers={cfg_r2['providers']}")


def run_all_tests():
    """Run all structural tests"""
    print("\n" + "="*60)
    print("P28 QUERY DIVERSIFICATION - STRUCTURAL TESTS")
    print("="*60 + "\n")

    tests = [
        ("Provider Detection", test_get_available_providers),
        ("Seed Generation", test_generate_seed_deterministic),
        ("Provider Ordering", test_ordered_providers_for_lane),
        ("Query Shuffling", test_shuffle_queries_deterministic),
        ("Output Structure", test_diversify_plan_output_structure),
        ("Arm Format Normalization", test_diversify_plan_arm_format_normalization),
        ("Arm Preservation", test_diversify_plan_preserves_arms),
        ("Query Preview", test_diversify_plan_queries_first3),
        ("Empty Arms", test_edge_case_empty_arms),
        ("Empty Queries", test_edge_case_empty_queries),
        ("Single Query", test_edge_case_single_query),
        ("Determinism", test_determinism_same_inputs),
        ("Lane Differentiation", test_different_lanes_produce_different_results)
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            print(f"\nTest: {name}")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
