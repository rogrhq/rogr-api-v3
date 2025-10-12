"""
P29 Telemetry & Reproducibility Capability Tests

Tests core functionality of telemetry collection and manifest generation:
- Real-world telemetry tracking scenarios
- Replay ID uniqueness and determinism
- Manifest completeness for reproducibility
- Integration with P28 configs
"""

import sys
sys.path.insert(0, '/Users/txtk/Documents/ROGR/github/rogrv2-backend')

from intelligence.telemetry.collect import LaneTelemetry, generate_manifest
import time


def test_telemetry_realistic_research_session():
    """Test telemetry for a realistic research session"""
    # Simulate R1 doing research
    t_r1 = LaneTelemetry("R1")

    # R1 prefers Google, makes several calls
    t_r1.record_provider_call("google")
    t_r1.record_provider_call("google")
    t_r1.record_provider_call("google")
    # Also uses Brave as backup
    t_r1.record_provider_call("brave")

    time.sleep(0.05)
    result = t_r1.finalize()

    assert result["providers"]["google"] == 3, "R1 should have 3 google calls"
    assert result["providers"]["brave"] == 1, "R1 should have 1 brave call"
    assert result["duration_ms"] >= 50, "Should have measurable duration"

    print(f"✓ R1 research session: providers={result['providers']}, duration={result['duration_ms']}ms")


def test_telemetry_r1_vs_r2_patterns():
    """Test that R1 and R2 can have different telemetry patterns"""
    t_r1 = LaneTelemetry("R1")
    t_r2 = LaneTelemetry("R2")

    # R1 prefers Google
    for _ in range(5):
        t_r1.record_provider_call("google")
    t_r1.record_provider_call("brave")

    # R2 prefers Brave
    for _ in range(4):
        t_r2.record_provider_call("brave")
    t_r2.record_provider_call("google")
    t_r2.record_provider_call("google")

    r1_result = t_r1.finalize()
    r2_result = t_r2.finalize()

    # R1 should have more Google calls
    assert r1_result["providers"]["google"] > r2_result["providers"]["google"]
    # R2 should have more Brave calls
    assert r2_result["providers"]["brave"] > r1_result["providers"]["brave"]

    print(f"✓ R1 vs R2 patterns: R1_google={r1_result['providers']['google']}, R2_brave={r2_result['providers']['brave']}")


def test_manifest_with_p28_configs():
    """Test manifest generation with realistic P28-style configs"""
    # Simulate P28 diversification configs
    r1_config = {
        "providers": ["google", "bing", "brave"],
        "seed": 664729861,
        "queries_first3": {
            "A": ["water boils 100C", "boiling point water", "H2O temperature"],
            "B": ["water boiling myths", "boiling point altitude"]
        }
    }

    r2_config = {
        "providers": ["brave", "bing", "google"],
        "seed": 19819423,
        "queries_first3": {
            "A": ["boiling point water", "H2O temperature", "water boils 100C"],
            "B": ["boiling point altitude", "water boiling myths"]
        }
    }

    manifest = generate_manifest("Water boils at 100 degrees Celsius", r1_config, r2_config)

    # Verify complete config preservation
    assert manifest["lanes"]["R1"]["providers"] == r1_config["providers"]
    assert manifest["lanes"]["R1"]["seed"] == r1_config["seed"]
    assert manifest["lanes"]["R1"]["queries_first3"] == r1_config["queries_first3"]

    assert manifest["lanes"]["R2"]["providers"] == r2_config["providers"]
    assert manifest["lanes"]["R2"]["seed"] == r2_config["seed"]
    assert manifest["lanes"]["R2"]["queries_first3"] == r2_config["queries_first3"]

    print(f"✓ P28 config integration: replay_id={manifest['replay_id'][:20]}...")


def test_replay_id_enables_reproducibility():
    """Test that replay_id captures all inputs needed for reproducibility"""
    claim = "California unemployment is at 8 percent"
    r1_cfg = {"providers": ["google"], "seed": 452863345}
    r2_cfg = {"providers": ["brave"], "seed": 458476028}

    manifest = generate_manifest(claim, r1_cfg, r2_cfg)

    # Replay ID should be deterministic from these inputs
    replay_id_1 = manifest["replay_id"]

    # Same inputs should produce same replay ID
    manifest_2 = generate_manifest(claim, r1_cfg, r2_cfg)
    replay_id_2 = manifest_2["replay_id"]

    assert replay_id_1 == replay_id_2, "Same inputs should produce same replay_id"

    # Different claim should change replay ID
    manifest_3 = generate_manifest("Different claim", r1_cfg, r2_cfg)
    assert manifest_3["replay_id"] != replay_id_1, "Different claim should change replay_id"

    # Different seed should change replay ID
    r1_cfg_modified = {"providers": ["google"], "seed": 999999}
    manifest_4 = generate_manifest(claim, r1_cfg_modified, r2_cfg)
    assert manifest_4["replay_id"] != replay_id_1, "Different seed should change replay_id"

    print(f"✓ Reproducibility: replay_id={replay_id_1[:24]}...")


def test_manifest_completeness_for_replay():
    """Test manifest contains all info needed to replay a search"""
    r1_cfg = {
        "providers": ["google", "brave"],
        "seed": 123456,
        "queries_first3": {"A": ["q1", "q2", "q3"], "B": ["q4", "q5"]}
    }
    r2_cfg = {
        "providers": ["brave", "google"],
        "seed": 654321,
        "queries_first3": {"A": ["q6", "q7"], "B": ["q8", "q9", "q10"]}
    }

    manifest = generate_manifest("Test claim text", r1_cfg, r2_cfg)

    # All critical info should be present
    assert "replay_id" in manifest, "Need replay_id for identification"
    assert "claim_text" in manifest, "Need claim_text to know what was checked"
    assert "lanes" in manifest, "Need lane configs"
    assert "R1" in manifest["lanes"] and "R2" in manifest["lanes"], "Need both lanes"

    # Each lane should have complete config
    for lane_id in ["R1", "R2"]:
        lane = manifest["lanes"][lane_id]
        assert "providers" in lane, f"{lane_id} needs providers list"
        assert "seed" in lane, f"{lane_id} needs seed for determinism"
        assert "queries_first3" in lane, f"{lane_id} needs query preview"

    # Timestamp for ordering/debugging
    assert "created_at" in manifest, "Need timestamp"

    print(f"✓ Manifest completeness: all replay fields present")


def test_telemetry_accumulation_over_time():
    """Test telemetry accurately accumulates over multiple operations"""
    t = LaneTelemetry("R1")

    # Simulate multiple search rounds
    for round_num in range(3):
        # Round 1: Google calls
        t.record_provider_call("google")
        t.record_provider_call("google")

        # Round 2: Brave calls
        t.record_provider_call("brave")

        time.sleep(0.02)

    result = t.finalize()

    # Should have accumulated all calls
    assert result["providers"]["google"] == 6, "Should have 6 google calls (2*3 rounds)"
    assert result["providers"]["brave"] == 3, "Should have 3 brave calls (1*3 rounds)"
    assert result["duration_ms"] >= 60, "Should accumulate time across rounds"

    print(f"✓ Telemetry accumulation: {result['providers']}, {result['duration_ms']}ms")


def test_manifest_with_scientific_claim():
    """Test manifest generation for scientific claim scenario"""
    claim = "Water boils at 100 degrees Celsius at sea level"

    r1_cfg = {
        "providers": ["google", "bing", "brave"],
        "seed": 860098658,
        "queries_first3": {
            "A": ["water boiling point 100 celsius", "H2O boils 100C", "water phase transition"],
            "B": ["boiling point altitude", "pressure affects boiling", "water properties"]
        }
    }

    r2_cfg = {
        "providers": ["brave", "bing", "google"],
        "seed": 664729861,
        "queries_first3": {
            "A": ["H2O boils 100C", "water phase transition", "water boiling point 100 celsius"],
            "B": ["water properties", "pressure affects boiling", "boiling point altitude"]
        }
    }

    manifest = generate_manifest(claim, r1_cfg, r2_cfg)

    # Verify scientific claim is preserved exactly
    assert "100 degrees Celsius" in manifest["claim_text"]
    assert "sea level" in manifest["claim_text"]

    # Verify both lanes have query previews
    assert len(manifest["lanes"]["R1"]["queries_first3"]["A"]) == 3
    assert len(manifest["lanes"]["R2"]["queries_first3"]["A"]) == 3

    # Verify provider diversity
    assert manifest["lanes"]["R1"]["providers"][0] != manifest["lanes"]["R2"]["providers"][0]

    print(f"✓ Scientific claim: '{manifest['claim_text'][:40]}...'")


def test_manifest_with_policy_claim():
    """Test manifest generation for policy claim scenario"""
    claim = "California unemployment is at 8 percent"

    r1_cfg = {
        "providers": ["google", "brave"],
        "seed": 452863345,
        "queries_first3": {
            "A": ["California unemployment rate 8 percent", "CA jobless rate 8%"],
            "B": ["California unemployment actual numbers", "CA jobless rate different"]
        }
    }

    r2_cfg = {
        "providers": ["brave", "google"],
        "seed": 458476028,
        "queries_first3": {
            "A": ["CA jobless rate 8%", "California unemployment rate 8 percent"],
            "B": ["CA jobless rate different", "California unemployment actual numbers"]
        }
    }

    manifest = generate_manifest(claim, r1_cfg, r2_cfg)

    assert "California" in manifest["claim_text"]
    assert "8 percent" in manifest["claim_text"]
    assert manifest["lanes"]["R1"]["seed"] != manifest["lanes"]["R2"]["seed"]

    print(f"✓ Policy claim: '{manifest['claim_text']}'")


def test_telemetry_timing_accuracy():
    """Test that duration measurement is reasonably accurate"""
    t = LaneTelemetry("R1")

    # Record some calls
    t.record_provider_call("google")

    # Wait a known amount of time
    time.sleep(0.1)  # 100ms

    t.record_provider_call("brave")

    result = t.finalize()

    # Duration should be >= 100ms (we slept for that long)
    assert result["duration_ms"] >= 100, f"Expected >= 100ms, got {result['duration_ms']}ms"

    # Duration should be < 200ms (should be close to 100ms, not way off)
    assert result["duration_ms"] < 200, f"Expected < 200ms, got {result['duration_ms']}ms (too high)"

    print(f"✓ Timing accuracy: {result['duration_ms']}ms (expected ~100ms)")


def test_replay_id_uniqueness_across_different_scenarios():
    """Test that different scenarios produce unique replay IDs"""
    configs = []

    # Scenario 1: Scientific claim
    configs.append((
        "Water boils at 100C",
        {"providers": ["google"], "seed": 100},
        {"providers": ["brave"], "seed": 200}
    ))

    # Scenario 2: Policy claim (different claim)
    configs.append((
        "Unemployment is 8 percent",
        {"providers": ["google"], "seed": 100},
        {"providers": ["brave"], "seed": 200}
    ))

    # Scenario 3: Same claim, different seeds
    configs.append((
        "Water boils at 100C",
        {"providers": ["google"], "seed": 999},
        {"providers": ["brave"], "seed": 888}
    ))

    # Scenario 4: Different claim, different seeds
    configs.append((
        "Climate change is real",
        {"providers": ["brave"], "seed": 777},
        {"providers": ["google"], "seed": 666}
    ))

    # Generate manifests
    replay_ids = []
    for claim, r1, r2 in configs:
        manifest = generate_manifest(claim, r1, r2)
        replay_ids.append(manifest["replay_id"])

    # All replay IDs should be unique (replay_id = hash(claim + r1_seed + r2_seed))
    # Note: Provider ordering doesn't affect replay_id since it's deterministic from seeds
    assert len(replay_ids) == len(set(replay_ids)), "All replay IDs should be unique"

    print(f"✓ Replay ID uniqueness: {len(replay_ids)} unique IDs generated")


def test_manifest_integration_with_diversification():
    """Test that manifest correctly captures P28 diversification state"""
    # Simulate complete P28 diversification output
    r1_config = {
        "lane_id": "R1",
        "providers": ["google", "bing", "brave"],  # R1 ordering
        "seed": 664729861,
        "queries_first3": {
            "A": ["q2", "q3", "q1"],  # Shuffled
            "B": ["q6", "q4", "q5"]
        }
    }

    r2_config = {
        "lane_id": "R2",
        "providers": ["brave", "bing", "google"],  # R2 ordering (different)
        "seed": 19819423,  # Different seed
        "queries_first3": {
            "A": ["q1", "q3", "q2"],  # Different shuffle
            "B": ["q5", "q4", "q6"]
        }
    }

    manifest = generate_manifest("Test claim", r1_config, r2_config)

    # Manifest should preserve diversification
    assert manifest["lanes"]["R1"]["providers"] != manifest["lanes"]["R2"]["providers"], "Provider order should differ"
    assert manifest["lanes"]["R1"]["seed"] != manifest["lanes"]["R2"]["seed"], "Seeds should differ"

    # Query previews should show different orders
    r1_queries_a = manifest["lanes"]["R1"]["queries_first3"]["A"]
    r2_queries_a = manifest["lanes"]["R2"]["queries_first3"]["A"]
    assert r1_queries_a != r2_queries_a, "Query orders should differ between lanes"

    print(f"✓ Diversification integration: R1_provider={manifest['lanes']['R1']['providers'][0]}, R2_provider={manifest['lanes']['R2']['providers'][0]}")


def run_all_tests():
    """Run all capability tests"""
    print("\n" + "="*60)
    print("P29 TELEMETRY & REPRODUCIBILITY - CAPABILITY TESTS")
    print("="*60 + "\n")

    tests = [
        ("Realistic Research Session", test_telemetry_realistic_research_session),
        ("R1 vs R2 Patterns", test_telemetry_r1_vs_r2_patterns),
        ("Manifest with P28 Configs", test_manifest_with_p28_configs),
        ("Replay ID Reproducibility", test_replay_id_enables_reproducibility),
        ("Manifest Completeness", test_manifest_completeness_for_replay),
        ("Telemetry Accumulation", test_telemetry_accumulation_over_time),
        ("Scientific Claim Manifest", test_manifest_with_scientific_claim),
        ("Policy Claim Manifest", test_manifest_with_policy_claim),
        ("Timing Accuracy", test_telemetry_timing_accuracy),
        ("Replay ID Uniqueness", test_replay_id_uniqueness_across_different_scenarios),
        ("Diversification Integration", test_manifest_integration_with_diversification)
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
