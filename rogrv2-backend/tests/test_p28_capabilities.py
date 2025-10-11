"""
P28 Query Diversification Capability Tests

Tests core functionality of the query diversification mechanism:
- Provider ordering differences between lanes
- Deterministic query shuffling
- Overlap reduction between R1 and R2
- Config metadata accuracy
- Real-world diversification scenarios
"""

import sys
sys.path.insert(0, '/Users/txtk/Documents/ROGR/github/rogrv2-backend')

from intelligence.planning.diversify import diversify_plan_for_lane


def test_r1_prefers_google():
    """Test that R1 consistently prefers Google first"""
    base_plan = {"arms": [{"name": "A", "queries": ["q1", "q2"]}]}

    _, config = diversify_plan_for_lane(
        base_plan, "R1", "Test claim", ["google", "brave", "bing"]
    )

    assert config["providers"][0] == "google", "R1 should prefer Google first"
    print(f"✓ R1 provider order: {config['providers']}")


def test_r2_prefers_brave():
    """Test that R2 consistently prefers Brave first"""
    base_plan = {"arms": [{"name": "A", "queries": ["q1", "q2"]}]}

    _, config = diversify_plan_for_lane(
        base_plan, "R2", "Test claim", ["google", "brave", "bing"]
    )

    assert config["providers"][0] == "brave", "R2 should prefer Brave first"
    print(f"✓ R2 provider order: {config['providers']}")


def test_lanes_have_different_provider_orders():
    """Test that R1 and R2 have different provider preferences"""
    base_plan = {"arms": [{"name": "A", "queries": ["q1"]}]}
    providers = ["google", "brave", "bing"]

    _, cfg_r1 = diversify_plan_for_lane(base_plan, "R1", "Test", providers)
    _, cfg_r2 = diversify_plan_for_lane(base_plan, "R2", "Test", providers)

    assert cfg_r1["providers"] != cfg_r2["providers"], "R1 and R2 should have different provider orders"
    assert cfg_r1["providers"][0] != cfg_r2["providers"][0], "R1 and R2 should prefer different first providers"

    print(f"✓ Provider differentiation: R1={cfg_r1['providers'][0]}, R2={cfg_r2['providers'][0]}")


def test_query_order_differs_between_lanes():
    """Test that R1 and R2 shuffle queries differently"""
    base_plan = {
        "arms": [
            {"name": "A", "queries": ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8"]}
        ]
    }

    div_r1, _ = diversify_plan_for_lane(base_plan, "R1", "Claim", ["google"])
    div_r2, _ = diversify_plan_for_lane(base_plan, "R2", "Claim", ["google"])

    r1_queries = div_r1["arms"][0]["queries"]
    r2_queries = div_r2["arms"][0]["queries"]

    # With 8 queries, probability of same order is extremely low
    assert r1_queries != r2_queries, "R1 and R2 should have different query orders"

    # Verify they contain the same queries (just reordered)
    assert set(r1_queries) == set(r2_queries), "Both lanes should have same query set"

    print(f"✓ Query order differentiation: R1={r1_queries[:3]}, R2={r2_queries[:3]}")


def test_determinism_across_calls():
    """Test that same lane + claim always produces same diversification"""
    base_plan = {
        "arms": [
            {"name": "A", "queries": ["q1", "q2", "q3", "q4", "q5"]}
        ]
    }

    div1, cfg1 = diversify_plan_for_lane(base_plan, "R1", "Water boils at 100C", ["google", "brave"])
    div2, cfg2 = diversify_plan_for_lane(base_plan, "R1", "Water boils at 100C", ["google", "brave"])

    # Configs should match
    assert cfg1["lane_id"] == cfg2["lane_id"]
    assert cfg1["providers"] == cfg2["providers"]
    assert cfg1["seed"] == cfg2["seed"]

    # Query orders should match
    assert div1["arms"][0]["queries"] == div2["arms"][0]["queries"]

    print(f"✓ Determinism verified: seed={cfg1['seed']}, queries={div1['arms'][0]['queries'][:3]}")


def test_different_claims_produce_different_shuffles():
    """Test that different claims result in different query orders"""
    base_plan = {
        "arms": [
            {"name": "A", "queries": ["q1", "q2", "q3", "q4", "q5", "q6"]}
        ]
    }

    div1, cfg1 = diversify_plan_for_lane(base_plan, "R1", "Claim A", ["google"])
    div2, cfg2 = diversify_plan_for_lane(base_plan, "R1", "Claim B", ["google"])

    # Seeds should differ
    assert cfg1["seed"] != cfg2["seed"], "Different claims should produce different seeds"

    # Query orders should differ
    assert div1["arms"][0]["queries"] != div2["arms"][0]["queries"], "Different claims should shuffle differently"

    print(f"✓ Claim differentiation: ClaimA_seed={cfg1['seed']}, ClaimB_seed={cfg2['seed']}")


def test_multi_arm_diversification():
    """Test diversification works correctly with multiple arms"""
    base_plan = {
        "arms": [
            {"name": "A", "queries": ["q1", "q2", "q3", "q4"]},
            {"name": "B", "queries": ["q5", "q6", "q7", "q8"]}
        ]
    }

    diversified, config = diversify_plan_for_lane(base_plan, "R1", "Test", ["google"])

    # Both arms should be shuffled
    assert len(diversified["arms"]) == 2
    assert len(diversified["arms"][0]["queries"]) == 4
    assert len(diversified["arms"][1]["queries"]) == 4

    # Preview should show both arms
    assert "A" in config["queries_first3"]
    assert "B" in config["queries_first3"]
    assert len(config["queries_first3"]["A"]) <= 3
    assert len(config["queries_first3"]["B"]) <= 3

    print(f"✓ Multi-arm: A={config['queries_first3']['A']}, B={config['queries_first3']['B']}")


def test_overlap_reduction_intent():
    """Test that lanes query the same content with different orders/providers"""
    # Use more queries to ensure different shuffles (probability of collision = 1/10! ≈ 0)
    base_plan = {
        "arms": [
            {"name": "support", "queries": [
                "water boils 100C",
                "boiling point water",
                "H2O temperature",
                "water phase transition",
                "100 celsius boiling",
                "water vapor pressure",
                "standard boiling point",
                "water thermal properties"
            ]},
            {"name": "challenge", "queries": [
                "water boiling myths",
                "boiling point altitude",
                "water properties pressure",
                "boiling temperature varies"
            ]}
        ]
    }

    div_r1, cfg_r1 = diversify_plan_for_lane(base_plan, "R1", "Water boils at 100C", ["google", "brave"])
    div_r2, cfg_r2 = diversify_plan_for_lane(base_plan, "R2", "Water boils at 100C", ["google", "brave"])

    # Same query sets (content preserved)
    r1_all = div_r1["arms"][0]["queries"] + div_r1["arms"][1]["queries"]
    r2_all = div_r2["arms"][0]["queries"] + div_r2["arms"][1]["queries"]
    assert set(r1_all) == set(r2_all), "Both lanes should search same content"

    # Different order (overlap reduced) - with 8 queries, collision is virtually impossible
    assert div_r1["arms"][0]["queries"] != div_r2["arms"][0]["queries"], "Support arm order should differ"

    # Different providers (diversity increased)
    assert cfg_r1["providers"] != cfg_r2["providers"], "Provider preference should differ"

    print(f"✓ Overlap reduction: R1={div_r1['arms'][0]['queries'][0]}, R2={div_r2['arms'][0]['queries'][0]}")


def test_real_world_scenario_scientific_claim():
    """Test diversification for a realistic scientific claim"""
    base_plan = {
        "arms": [
            {
                "name": "support",
                "queries": [
                    "water boiling point 100 celsius",
                    "H2O boils 100C standard pressure",
                    "water phase transition temperature",
                    "boiling point water sea level"
                ]
            },
            {
                "name": "challenge",
                "queries": [
                    "water boiling point not always 100",
                    "altitude affects boiling point",
                    "water boils lower temperature mountains",
                    "pressure changes boiling point"
                ]
            }
        ]
    }

    div_r1, cfg_r1 = diversify_plan_for_lane(
        base_plan, "R1", "Water boils at 100 degrees Celsius", ["google", "brave", "bing"]
    )
    div_r2, cfg_r2 = diversify_plan_for_lane(
        base_plan, "R2", "Water boils at 100 degrees Celsius", ["google", "brave", "bing"]
    )

    # Verify structure
    assert len(div_r1["arms"]) == 2
    assert len(div_r2["arms"]) == 2

    # Verify differentiation
    assert cfg_r1["providers"] != cfg_r2["providers"]
    assert cfg_r1["seed"] != cfg_r2["seed"]

    # Verify content preservation
    r1_support = set(div_r1["arms"][0]["queries"])
    r2_support = set(div_r2["arms"][0]["queries"])
    assert r1_support == r2_support, "Query content should be preserved"

    # Verify order diversity
    r1_first_query = div_r1["arms"][0]["queries"][0]
    r2_first_query = div_r2["arms"][0]["queries"][0]
    print(f"✓ Scientific claim: R1_first='{r1_first_query}', R2_first='{r2_first_query}'")


def test_real_world_scenario_policy_claim():
    """Test diversification for a realistic policy claim"""
    base_plan = {
        "arms": [
            {
                "name": "support",
                "queries": [
                    "California unemployment rate 8 percent 2023",
                    "CA jobless rate 8% recent data",
                    "California labor statistics 2023"
                ]
            },
            {
                "name": "challenge",
                "queries": [
                    "California unemployment rate actual numbers",
                    "CA jobless rate different than reported",
                    "unemployment measurement methodology CA"
                ]
            }
        ]
    }

    div_r1, cfg_r1 = diversify_plan_for_lane(
        base_plan, "R1", "California unemployment is at 8 percent", ["google", "brave"]
    )
    div_r2, cfg_r2 = diversify_plan_for_lane(
        base_plan, "R2", "California unemployment is at 8 percent", ["google", "brave"]
    )

    # Different provider preferences
    assert cfg_r1["providers"][0] == "google", "R1 should prefer google"
    assert cfg_r2["providers"][0] == "brave", "R2 should prefer brave"

    # Different query orders
    assert div_r1["arms"][0]["queries"] != div_r2["arms"][0]["queries"]

    # But same query content
    assert set(div_r1["arms"][0]["queries"]) == set(div_r2["arms"][0]["queries"])

    print(f"✓ Policy claim: R1_provider={cfg_r1['providers'][0]}, R2_provider={cfg_r2['providers'][0]}")


def test_seed_based_reproducibility():
    """Test that seed ensures reproducible shuffles"""
    base_plan = {
        "arms": [
            {"name": "A", "queries": ["q1", "q2", "q3", "q4", "q5", "q6", "q7"]}
        ]
    }

    # Run 5 times with same inputs
    results = []
    for i in range(5):
        div, cfg = diversify_plan_for_lane(base_plan, "R1", "Test claim", ["google"])
        results.append({
            "seed": cfg["seed"],
            "queries": div["arms"][0]["queries"]
        })

    # All should have same seed
    seeds = [r["seed"] for r in results]
    assert len(set(seeds)) == 1, "All runs should produce same seed"

    # All should have same query order
    for i in range(1, 5):
        assert results[0]["queries"] == results[i]["queries"], f"Run {i+1} produced different order"

    print(f"✓ Reproducibility verified across 5 runs: seed={results[0]['seed']}")


def test_config_metadata_accuracy():
    """Test that config accurately reflects diversification"""
    base_plan = {
        "arms": [
            {"name": "A", "queries": ["q1", "q2", "q3"]},
            {"name": "B", "queries": ["q4", "q5"]}
        ]
    }

    diversified, config = diversify_plan_for_lane(
        base_plan, "R2", "Claim text", ["google", "brave"]
    )

    # Config should match inputs
    assert config["lane_id"] == "R2"
    assert set(config["providers"]) == {"google", "brave"}

    # Config preview should match actual queries
    for arm in diversified["arms"]:
        arm_name = arm["name"]
        actual_first3 = arm["queries"][:3]
        preview_first3 = config["queries_first3"][arm_name]
        assert actual_first3 == preview_first3, f"Preview mismatch for arm {arm_name}"

    print(f"✓ Config metadata accurate: lane={config['lane_id']}, providers={config['providers']}")


def run_all_tests():
    """Run all capability tests"""
    print("\n" + "="*60)
    print("P28 QUERY DIVERSIFICATION - CAPABILITY TESTS")
    print("="*60 + "\n")

    tests = [
        ("R1 Prefers Google", test_r1_prefers_google),
        ("R2 Prefers Brave", test_r2_prefers_brave),
        ("Lane Provider Differences", test_lanes_have_different_provider_orders),
        ("Query Order Differences", test_query_order_differs_between_lanes),
        ("Determinism", test_determinism_across_calls),
        ("Claim Differentiation", test_different_claims_produce_different_shuffles),
        ("Multi-Arm Diversification", test_multi_arm_diversification),
        ("Overlap Reduction Intent", test_overlap_reduction_intent),
        ("Scientific Claim Scenario", test_real_world_scenario_scientific_claim),
        ("Policy Claim Scenario", test_real_world_scenario_policy_claim),
        ("Seed Reproducibility", test_seed_based_reproducibility),
        ("Config Metadata Accuracy", test_config_metadata_accuracy)
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
