"""
P29 Telemetry & Reproducibility Structural Tests

Tests structural integrity of telemetry collection and manifest generation:
- LaneTelemetry field validation
- Manifest structure and fields
- Edge cases (empty data, zero calls, missing fields)
- Error handling
"""

import sys
sys.path.insert(0, '/Users/txtk/Documents/ROGR/github/rogrv2-backend')

from intelligence.telemetry.collect import LaneTelemetry, generate_manifest
import time


def test_lane_telemetry_initialization():
    """Test LaneTelemetry initializes correctly"""
    t = LaneTelemetry("R1")

    assert t.lane_id == "R1", "lane_id should match input"
    assert hasattr(t, 'start_time'), "Should have start_time attribute"
    assert hasattr(t, 'provider_calls'), "Should have provider_calls attribute"
    assert isinstance(t.provider_calls, dict), "provider_calls should be dict"
    assert len(t.provider_calls) == 0, "Should start with no provider calls"

    print(f"✓ LaneTelemetry initialization: lane_id={t.lane_id}")


def test_lane_telemetry_record_single_call():
    """Test recording a single provider call"""
    t = LaneTelemetry("R1")
    t.record_provider_call("google")

    assert "google" in t.provider_calls, "Should have google in provider_calls"
    assert t.provider_calls["google"] == 1, "Should have 1 google call"

    print(f"✓ Single provider call: {t.provider_calls}")


def test_lane_telemetry_record_multiple_calls():
    """Test recording multiple provider calls"""
    t = LaneTelemetry("R2")
    t.record_provider_call("google")
    t.record_provider_call("brave")
    t.record_provider_call("google")
    t.record_provider_call("bing")
    t.record_provider_call("google")

    assert t.provider_calls["google"] == 3, "Should have 3 google calls"
    assert t.provider_calls["brave"] == 1, "Should have 1 brave call"
    assert t.provider_calls["bing"] == 1, "Should have 1 bing call"

    print(f"✓ Multiple provider calls: {t.provider_calls}")


def test_lane_telemetry_finalize_structure():
    """Test finalize returns correct structure"""
    t = LaneTelemetry("R1")
    t.record_provider_call("google")
    time.sleep(0.05)  # Wait at least 50ms

    result = t.finalize()

    # Check structure
    assert isinstance(result, dict), "Result should be dict"
    assert "providers" in result, "Missing 'providers' field"
    assert "duration_ms" in result, "Missing 'duration_ms' field"

    # Check types
    assert isinstance(result["providers"], dict), "providers should be dict"
    assert isinstance(result["duration_ms"], int), "duration_ms should be int"

    # Check values
    assert result["providers"]["google"] == 1, "Should have 1 google call"
    assert result["duration_ms"] >= 50, f"Duration should be >= 50ms, got {result['duration_ms']}"

    print(f"✓ Finalize structure: providers={result['providers']}, duration_ms={result['duration_ms']}")


def test_lane_telemetry_finalize_no_calls():
    """Test finalize with no provider calls"""
    t = LaneTelemetry("R1")
    time.sleep(0.01)

    result = t.finalize()

    assert "providers" in result, "Should have providers field"
    assert "duration_ms" in result, "Should have duration_ms field"
    assert len(result["providers"]) == 0, "Should have no provider calls"
    assert result["duration_ms"] >= 10, "Should have positive duration"

    print(f"✓ Finalize no calls: {result}")


def test_generate_manifest_structure():
    """Test generate_manifest returns correct structure"""
    r1_config = {"providers": ["google", "brave"], "seed": 123, "queries_first3": {"A": ["q1"]}}
    r2_config = {"providers": ["brave", "google"], "seed": 456, "queries_first3": {"A": ["q2"]}}

    manifest = generate_manifest("Water boils at 100C", r1_config, r2_config)

    # Top-level fields
    assert isinstance(manifest, dict), "Manifest should be dict"
    assert "replay_id" in manifest, "Missing 'replay_id'"
    assert "claim_text" in manifest, "Missing 'claim_text'"
    assert "lanes" in manifest, "Missing 'lanes'"
    assert "created_at" in manifest, "Missing 'created_at'"

    # Lanes structure
    assert "R1" in manifest["lanes"], "Missing R1 in lanes"
    assert "R2" in manifest["lanes"], "Missing R2 in lanes"

    # R1 lane fields
    r1 = manifest["lanes"]["R1"]
    assert "providers" in r1, "Missing R1 providers"
    assert "seed" in r1, "Missing R1 seed"
    assert "queries_first3" in r1, "Missing R1 queries_first3"

    # R2 lane fields
    r2 = manifest["lanes"]["R2"]
    assert "providers" in r2, "Missing R2 providers"
    assert "seed" in r2, "Missing R2 seed"
    assert "queries_first3" in r2, "Missing R2 queries_first3"

    print(f"✓ Manifest structure: replay_id={manifest['replay_id'][:16]}...")


def test_generate_manifest_field_types():
    """Test manifest field types are correct"""
    r1_config = {"providers": ["google"], "seed": 100}
    r2_config = {"providers": ["brave"], "seed": 200}

    manifest = generate_manifest("Test claim", r1_config, r2_config)

    # Type checks
    assert isinstance(manifest["replay_id"], str), "replay_id should be string"
    assert isinstance(manifest["claim_text"], str), "claim_text should be string"
    assert isinstance(manifest["lanes"], dict), "lanes should be dict"
    assert isinstance(manifest["created_at"], str), "created_at should be string (ISO format)"

    # Lane type checks
    assert isinstance(manifest["lanes"]["R1"]["providers"], list), "R1 providers should be list"
    assert isinstance(manifest["lanes"]["R1"]["seed"], int), "R1 seed should be int"
    assert isinstance(manifest["lanes"]["R2"]["providers"], list), "R2 providers should be list"
    assert isinstance(manifest["lanes"]["R2"]["seed"], int), "R2 seed should be int"

    print(f"✓ Manifest field types validated")


def test_generate_manifest_claim_text_preserved():
    """Test claim text is preserved in manifest"""
    claim = "California unemployment is at 8 percent"
    r1_config = {"providers": ["google"], "seed": 1}
    r2_config = {"providers": ["brave"], "seed": 2}

    manifest = generate_manifest(claim, r1_config, r2_config)

    assert manifest["claim_text"] == claim, "Claim text should be preserved exactly"

    print(f"✓ Claim text preserved: '{manifest['claim_text']}'")


def test_generate_manifest_config_extraction():
    """Test manifest correctly extracts values from configs"""
    r1_config = {"providers": ["google", "bing"], "seed": 987, "queries_first3": {"A": ["q1", "q2"]}}
    r2_config = {"providers": ["brave"], "seed": 654, "queries_first3": {"B": ["q3"]}}

    manifest = generate_manifest("Test", r1_config, r2_config)

    # Check R1 extraction
    assert manifest["lanes"]["R1"]["providers"] == ["google", "bing"]
    assert manifest["lanes"]["R1"]["seed"] == 987
    assert manifest["lanes"]["R1"]["queries_first3"] == {"A": ["q1", "q2"]}

    # Check R2 extraction
    assert manifest["lanes"]["R2"]["providers"] == ["brave"]
    assert manifest["lanes"]["R2"]["seed"] == 654
    assert manifest["lanes"]["R2"]["queries_first3"] == {"B": ["q3"]}

    print(f"✓ Config extraction: R1_seed={manifest['lanes']['R1']['seed']}, R2_seed={manifest['lanes']['R2']['seed']}")


def test_generate_manifest_replay_id_deterministic():
    """Test replay_id is deterministic (same inputs = same id)"""
    r1_config = {"providers": ["google"], "seed": 111}
    r2_config = {"providers": ["brave"], "seed": 222}

    manifest1 = generate_manifest("Test claim", r1_config, r2_config)
    manifest2 = generate_manifest("Test claim", r1_config, r2_config)

    assert manifest1["replay_id"] == manifest2["replay_id"], "Same inputs should produce same replay_id"

    print(f"✓ Replay ID determinism: {manifest1['replay_id']}")


def test_generate_manifest_replay_id_different_for_different_inputs():
    """Test replay_id changes with different inputs"""
    r1_config = {"providers": ["google"], "seed": 111}
    r2_config = {"providers": ["brave"], "seed": 222}

    manifest1 = generate_manifest("Claim A", r1_config, r2_config)
    manifest2 = generate_manifest("Claim B", r1_config, r2_config)  # Different claim
    manifest3 = generate_manifest("Claim A", {"providers": ["google"], "seed": 999}, r2_config)  # Different seed

    assert manifest1["replay_id"] != manifest2["replay_id"], "Different claims should have different replay_id"
    assert manifest1["replay_id"] != manifest3["replay_id"], "Different seeds should have different replay_id"

    print(f"✓ Replay ID differentiation: ClaimA={manifest1['replay_id'][:12]}, ClaimB={manifest2['replay_id'][:12]}")


def test_generate_manifest_created_at_format():
    """Test created_at is in ISO format with Z suffix"""
    r1_config = {"providers": ["google"], "seed": 1}
    r2_config = {"providers": ["brave"], "seed": 2}

    manifest = generate_manifest("Test", r1_config, r2_config)

    created_at = manifest["created_at"]
    assert created_at.endswith("Z"), "created_at should end with 'Z' (UTC timezone)"
    assert "T" in created_at, "created_at should contain 'T' (ISO 8601 format)"

    print(f"✓ Created at format: {created_at}")


def test_edge_case_empty_providers():
    """Test manifest with empty provider lists"""
    r1_config = {"providers": [], "seed": 100}
    r2_config = {"providers": [], "seed": 200}

    manifest = generate_manifest("Test", r1_config, r2_config)

    assert manifest["lanes"]["R1"]["providers"] == []
    assert manifest["lanes"]["R2"]["providers"] == []
    assert "replay_id" in manifest, "Should still generate replay_id"

    print(f"✓ Empty providers: replay_id={manifest['replay_id'][:16]}")


def test_edge_case_missing_config_fields():
    """Test manifest with missing config fields (should use defaults)"""
    r1_config = {"seed": 100}  # Missing providers and queries_first3
    r2_config = {"providers": ["brave"]}  # Missing seed and queries_first3

    manifest = generate_manifest("Test", r1_config, r2_config)

    # Should use empty list/dict as defaults
    assert manifest["lanes"]["R1"]["providers"] == []
    assert manifest["lanes"]["R1"]["queries_first3"] == {}
    assert manifest["lanes"]["R2"]["seed"] == 0  # Default seed
    assert manifest["lanes"]["R2"]["queries_first3"] == {}

    print(f"✓ Missing config fields handled with defaults")


def test_edge_case_empty_claim_text():
    """Test manifest with empty claim text"""
    r1_config = {"providers": ["google"], "seed": 1}
    r2_config = {"providers": ["brave"], "seed": 2}

    manifest = generate_manifest("", r1_config, r2_config)

    assert manifest["claim_text"] == ""
    assert "replay_id" in manifest, "Should still generate replay_id for empty claim"
    assert len(manifest["replay_id"]) > 0, "replay_id should not be empty"

    print(f"✓ Empty claim text: replay_id={manifest['replay_id'][:16]}")


def test_lane_telemetry_multiple_lanes():
    """Test multiple LaneTelemetry instances don't interfere"""
    t1 = LaneTelemetry("R1")
    t2 = LaneTelemetry("R2")

    t1.record_provider_call("google")
    t1.record_provider_call("google")
    t2.record_provider_call("brave")

    r1 = t1.finalize()
    r2 = t2.finalize()

    assert r1["providers"]["google"] == 2, "R1 should have 2 google calls"
    assert "brave" not in r1["providers"], "R1 should not have brave calls"
    assert r2["providers"]["brave"] == 1, "R2 should have 1 brave call"
    assert "google" not in r2["providers"], "R2 should not have google calls"

    print(f"✓ Multiple lanes: R1={r1['providers']}, R2={r2['providers']}")


def run_all_tests():
    """Run all structural tests"""
    print("\n" + "="*60)
    print("P29 TELEMETRY & REPRODUCIBILITY - STRUCTURAL TESTS")
    print("="*60 + "\n")

    tests = [
        ("LaneTelemetry Initialization", test_lane_telemetry_initialization),
        ("Single Provider Call", test_lane_telemetry_record_single_call),
        ("Multiple Provider Calls", test_lane_telemetry_record_multiple_calls),
        ("Finalize Structure", test_lane_telemetry_finalize_structure),
        ("Finalize No Calls", test_lane_telemetry_finalize_no_calls),
        ("Manifest Structure", test_generate_manifest_structure),
        ("Manifest Field Types", test_generate_manifest_field_types),
        ("Claim Text Preservation", test_generate_manifest_claim_text_preserved),
        ("Config Extraction", test_generate_manifest_config_extraction),
        ("Replay ID Determinism", test_generate_manifest_replay_id_deterministic),
        ("Replay ID Differentiation", test_generate_manifest_replay_id_different_for_different_inputs),
        ("Created At Format", test_generate_manifest_created_at_format),
        ("Empty Providers", test_edge_case_empty_providers),
        ("Missing Config Fields", test_edge_case_missing_config_fields),
        ("Empty Claim Text", test_edge_case_empty_claim_text),
        ("Multiple Lanes", test_lane_telemetry_multiple_lanes)
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
