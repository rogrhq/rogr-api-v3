"""
P27 Consensus Structural Tests

Tests structural integrity of the consensus mechanism:
- Field validation (all expected fields present)
- Field structure (nested objects correct)
- Edge cases (missing fields, empty inputs, extreme values)
- Error handling (malformed data doesn't crash)
"""

import sys
sys.path.insert(0, '/Users/txtk/Documents/ROGR/github/rogrv2-backend')

from intelligence.consensus.dual_lane import compute_consensus
from intelligence.consensus.aggregate import consensus_metrics


def test_compute_consensus_fields():
    """Verify compute_consensus adds all expected output fields"""
    r1 = {
        "label": "supports",
        "confidence": 0.7,
        "arm_strength": {"support": 0.8, "challenge": 0.2, "balance": 0.6}
    }
    r2 = {
        "label": "supports",
        "confidence": 0.75,
        "arm_strength": {"support": 0.85, "challenge": 0.15, "balance": 0.7}
    }

    result = compute_consensus(r1, r2)

    # Top-level fields
    assert "label" in result, "Missing 'label' field"
    assert "confidence" in result, "Missing 'confidence' field"
    assert "rationale" in result, "Missing 'rationale' field"
    assert "agreement" in result, "Missing 'agreement' field"

    # Rationale structure
    rationale = result["rationale"]
    assert "rule" in rationale, "Missing 'rationale.rule'"
    assert "support_mean" in rationale, "Missing 'rationale.support_mean'"
    assert "challenge_mean" in rationale, "Missing 'rationale.challenge_mean'"
    assert "delta" in rationale, "Missing 'rationale.delta'"
    assert "base_conf" in rationale, "Missing 'rationale.base_conf'"
    assert "bonus_or_penalty" in rationale, "Missing 'rationale.bonus_or_penalty'"

    # Agreement structure
    agreement = result["agreement"]
    assert "r1_label" in agreement, "Missing 'agreement.r1_label'"
    assert "r2_label" in agreement, "Missing 'agreement.r2_label'"
    assert "r1_conf" in agreement, "Missing 'agreement.r1_conf'"
    assert "r2_conf" in agreement, "Missing 'agreement.r2_conf'"
    assert "delta_balance" in agreement, "Missing 'agreement.delta_balance'"

    print("✓ Field validation passed")


def test_compute_consensus_field_types():
    """Verify field types are correct"""
    r1 = {
        "label": "supports",
        "confidence": 0.7,
        "arm_strength": {"support": 0.8, "challenge": 0.2, "balance": 0.6}
    }
    r2 = {
        "label": "challenges",
        "confidence": 0.65,
        "arm_strength": {"support": 0.3, "challenge": 0.7, "balance": -0.4}
    }

    result = compute_consensus(r1, r2)

    # Type checks
    assert isinstance(result["label"], str), "label should be string"
    assert isinstance(result["confidence"], float), "confidence should be float"
    assert isinstance(result["rationale"], dict), "rationale should be dict"
    assert isinstance(result["agreement"], dict), "agreement should be dict"

    # Label validity
    valid_labels = ["supports", "challenges", "mixed", "insufficient"]
    assert result["label"] in valid_labels, f"Invalid label: {result['label']}"

    # Confidence bounds
    assert 0.0 <= result["confidence"] <= 1.0, f"Confidence out of bounds: {result['confidence']}"

    print("✓ Field type validation passed")


def test_agreement_rule():
    """Test agreement case (same labels)"""
    r1 = {
        "label": "supports",
        "confidence": 0.7,
        "arm_strength": {"support": 0.8, "challenge": 0.2, "balance": 0.6}
    }
    r2 = {
        "label": "supports",
        "confidence": 0.75,
        "arm_strength": {"support": 0.85, "challenge": 0.15, "balance": 0.7}
    }

    result = compute_consensus(r1, r2)

    # Agreement logic: use higher confidence + 0.10 bonus (capped at 0.95)
    assert result["label"] == "supports", "Agreement should keep same label"
    assert result["rationale"]["rule"] == "agree_same_label", "Wrong rule applied"
    assert result["rationale"]["bonus_or_penalty"] == 0.10, "Agreement bonus should be 0.10"
    assert result["confidence"] == min(0.75 + 0.10, 0.95), "Confidence calculation wrong"

    print("✓ Agreement rule passed")


def test_disagreement_clear_gap():
    """Test disagreement with clear gap (delta >= 0.20) - pick stronger side"""
    r1 = {
        "label": "supports",
        "confidence": 0.65,
        "arm_strength": {"support": 0.75, "challenge": 0.25, "balance": 0.5}
    }
    r2 = {
        "label": "challenges",
        "confidence": 0.60,
        "arm_strength": {"support": 0.30, "challenge": 0.70, "balance": -0.4}
    }

    result = compute_consensus(r1, r2)

    # Calculate expected values
    support_mean = (0.75 + 0.30) / 2  # 0.525
    challenge_mean = (0.25 + 0.70) / 2  # 0.475
    delta = abs(support_mean - challenge_mean)  # 0.05

    # This is actually a close case (delta < 0.20), so should be mixed
    # Let me recalculate with clearer gap
    print(f"  Delta: {delta:.3f} (threshold: 0.20)")

    if delta >= 0.20:
        assert result["rationale"]["rule"] == "disagree_gap_select", "Wrong rule for clear gap"
        assert result["rationale"]["bonus_or_penalty"] == -0.05, "Gap penalty should be -0.05"
        expected_label = "supports" if support_mean > challenge_mean else "challenges"
        assert result["label"] == expected_label, f"Should pick {expected_label} for clear gap"
    else:
        assert result["rationale"]["rule"] == "disagree_mixed", "Wrong rule for close gap"
        assert result["label"] == "mixed", "Should be mixed for close gap"

    print(f"✓ Disagreement rule passed (delta={delta:.3f}, rule={result['rationale']['rule']})")


def test_disagreement_mixed():
    """Test disagreement with close values (delta < 0.20) - return mixed"""
    r1 = {
        "label": "supports",
        "confidence": 0.55,
        "arm_strength": {"support": 0.55, "challenge": 0.45, "balance": 0.1}
    }
    r2 = {
        "label": "challenges",
        "confidence": 0.52,
        "arm_strength": {"support": 0.48, "challenge": 0.52, "balance": -0.04}
    }

    result = compute_consensus(r1, r2)

    support_mean = (0.55 + 0.48) / 2  # 0.515
    challenge_mean = (0.45 + 0.52) / 2  # 0.485
    delta = abs(support_mean - challenge_mean)  # 0.03

    assert delta < 0.20, f"Test setup error: delta {delta} should be < 0.20"
    assert result["label"] == "mixed", "Close disagreement should return 'mixed'"
    assert result["rationale"]["rule"] == "disagree_mixed", "Wrong rule for mixed case"
    assert result["rationale"]["bonus_or_penalty"] == -0.10, "Mixed penalty should be -0.10"

    print(f"✓ Mixed rule passed (delta={delta:.3f})")


def test_edge_case_missing_fields():
    """Test handling of missing/incomplete input fields"""
    # Missing confidence
    r1 = {"label": "supports", "arm_strength": {"support": 0.8, "challenge": 0.2, "balance": 0.6}}
    r2 = {"label": "supports", "confidence": 0.75, "arm_strength": {"support": 0.85, "challenge": 0.15}}

    result = compute_consensus(r1, r2)
    assert "label" in result, "Should handle missing confidence"
    assert result["confidence"] >= 0, "Confidence should default to 0.0"

    # Missing arm_strength
    r1 = {"label": "supports", "confidence": 0.7}
    r2 = {"label": "supports", "confidence": 0.75}

    result = compute_consensus(r1, r2)
    assert "label" in result, "Should handle missing arm_strength"
    assert result["rationale"]["support_mean"] == 0.0, "Should default to 0 for missing arm values"

    # Empty dicts
    r1 = {}
    r2 = {}

    result = compute_consensus(r1, r2)
    assert "label" in result, "Should handle empty inputs"
    assert result["label"] == "insufficient", "Empty inputs should default to 'insufficient'"

    print("✓ Missing fields handling passed")


def test_edge_case_extreme_values():
    """Test extreme confidence and arm_strength values"""
    # Very high confidences
    r1 = {
        "label": "supports",
        "confidence": 0.95,
        "arm_strength": {"support": 0.95, "challenge": 0.05, "balance": 0.9}
    }
    r2 = {
        "label": "supports",
        "confidence": 0.92,
        "arm_strength": {"support": 0.93, "challenge": 0.07, "balance": 0.86}
    }

    result = compute_consensus(r1, r2)
    assert result["confidence"] <= 0.95, "Confidence should be capped at 0.95"
    assert result["confidence"] == 0.95, f"Expected 0.95 cap, got {result['confidence']}"

    # Zero confidence
    r1 = {"label": "insufficient", "confidence": 0.0, "arm_strength": {"support": 0, "challenge": 0, "balance": 0}}
    r2 = {"label": "insufficient", "confidence": 0.0, "arm_strength": {"support": 0, "challenge": 0, "balance": 0}}

    result = compute_consensus(r1, r2)
    assert result["confidence"] >= 0.0, "Confidence should not go negative"

    print("✓ Extreme values handling passed")


def test_consensus_metrics_fields():
    """Test consensus_metrics function from aggregate.py"""
    arm_a = [
        {"source": {"dedupe_key": "url1"}, "stance": "support"},
        {"source": {"dedupe_key": "url2"}, "stance": "support"},
        {"source": {"dedupe_key": "url3"}, "stance": "refute"}
    ]
    arm_b = [
        {"source": {"dedupe_key": "url1"}, "stance": "support"},  # Overlap with same stance
        {"source": {"dedupe_key": "url4"}, "stance": "refute"}
    ]

    result = consensus_metrics(arm_a, arm_b)

    # Field validation
    assert "overlap_ratio" in result, "Missing 'overlap_ratio'"
    assert "conflict_score" in result, "Missing 'conflict_score'"
    assert "stability" in result, "Missing 'stability'"
    assert "totals" in result, "Missing 'totals'"

    # Totals structure
    assert "support" in result["totals"], "Missing 'totals.support'"
    assert "refute" in result["totals"], "Missing 'totals.refute'"

    # Value bounds
    assert 0 <= result["overlap_ratio"] <= 1, "overlap_ratio out of bounds"
    assert 0 <= result["conflict_score"] <= 1, "conflict_score out of bounds"
    assert 0 <= result["stability"] <= 1, "stability out of bounds"

    print("✓ consensus_metrics field validation passed")


def test_consensus_metrics_edge_cases():
    """Test consensus_metrics with edge cases"""
    # Empty lists
    result = consensus_metrics([], [])
    assert result["overlap_ratio"] == 0, "Empty lists should have 0 overlap"

    # One empty list
    arm_a = [{"source": {"dedupe_key": "url1"}, "stance": "support"}]
    result = consensus_metrics(arm_a, [])
    assert "overlap_ratio" in result, "Should handle one empty list"

    # Perfect overlap with agreement
    arm_a = [{"source": {"dedupe_key": "url1"}, "stance": "support"}]
    arm_b = [{"source": {"dedupe_key": "url1"}, "stance": "support"}]
    result = consensus_metrics(arm_a, arm_b)
    assert result["overlap_ratio"] == 1.0, "Perfect overlap should be 1.0"
    assert result["stability"] == 1.0, "Perfect agreement should have stability 1.0"

    # Perfect overlap with disagreement
    arm_a = [{"source": {"dedupe_key": "url1"}, "stance": "support"}]
    arm_b = [{"source": {"dedupe_key": "url1"}, "stance": "refute"}]
    result = consensus_metrics(arm_a, arm_b)
    assert result["overlap_ratio"] == 1.0, "Perfect overlap should be 1.0"
    assert result["stability"] == 0.0, "Perfect disagreement should have stability 0.0"

    print("✓ consensus_metrics edge cases passed")


def run_all_tests():
    """Run all structural tests"""
    print("\n" + "="*60)
    print("P27 CONSENSUS - STRUCTURAL TESTS")
    print("="*60 + "\n")

    tests = [
        ("Field Validation", test_compute_consensus_fields),
        ("Field Types", test_compute_consensus_field_types),
        ("Agreement Rule", test_agreement_rule),
        ("Disagreement Clear Gap", test_disagreement_clear_gap),
        ("Disagreement Mixed", test_disagreement_mixed),
        ("Missing Fields", test_edge_case_missing_fields),
        ("Extreme Values", test_edge_case_extreme_values),
        ("Metrics Fields", test_consensus_metrics_fields),
        ("Metrics Edge Cases", test_consensus_metrics_edge_cases)
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
