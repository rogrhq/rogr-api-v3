"""
P27 Consensus Capability Tests

Tests core functionality of the consensus mechanism:
- Agreement scenarios (same labels)
- Disagreement scenarios (different labels with clear gap)
- Mixed scenarios (different labels with close values)
- Edge cases (ties, extreme imbalances, low confidence)
- Confidence adjustments (bonuses/penalties)
- Rationale transparency
"""

import sys
sys.path.insert(0, '/Users/txtk/Documents/ROGR/github/rogrv2-backend')

from intelligence.consensus.dual_lane import compute_consensus
from intelligence.consensus.aggregate import consensus_metrics


def test_agreement_high_confidence():
    """Test agreement between high-confidence researchers"""
    r1 = {
        "label": "supports",
        "confidence": 0.85,
        "arm_strength": {"support": 0.90, "challenge": 0.10, "balance": 0.80}
    }
    r2 = {
        "label": "supports",
        "confidence": 0.82,
        "arm_strength": {"support": 0.88, "challenge": 0.12, "balance": 0.76}
    }

    result = compute_consensus(r1, r2)

    # Expected: max(0.85, 0.82) + 0.10 = 0.95 (capped)
    assert result["label"] == "supports"
    assert abs(result["confidence"] - 0.95) < 0.01, f"Expected 0.95, got {result['confidence']}"
    assert result["rationale"]["rule"] == "agree_same_label"
    assert result["rationale"]["base_conf"] == 0.85
    assert result["rationale"]["bonus_or_penalty"] == 0.10

    print(f"✓ High confidence agreement: {result['label']}, conf={result['confidence']:.2f}")


def test_agreement_low_confidence():
    """Test agreement between low-confidence researchers"""
    r1 = {
        "label": "challenges",
        "confidence": 0.52,
        "arm_strength": {"support": 0.30, "challenge": 0.55, "balance": -0.25}
    }
    r2 = {
        "label": "challenges",
        "confidence": 0.48,
        "arm_strength": {"support": 0.35, "challenge": 0.58, "balance": -0.23}
    }

    result = compute_consensus(r1, r2)

    # Expected: max(0.52, 0.48) + 0.10 = 0.62
    assert result["label"] == "challenges"
    assert abs(result["confidence"] - 0.62) < 0.01, f"Expected 0.62, got {result['confidence']}"
    assert result["rationale"]["rule"] == "agree_same_label"

    print(f"✓ Low confidence agreement: {result['label']}, conf={result['confidence']:.2f}")


def test_disagreement_clear_support_win():
    """Test disagreement with clear support advantage"""
    r1 = {
        "label": "supports",
        "confidence": 0.75,
        "arm_strength": {"support": 0.85, "challenge": 0.15, "balance": 0.70}
    }
    r2 = {
        "label": "challenges",
        "confidence": 0.60,
        "arm_strength": {"support": 0.60, "challenge": 0.40, "balance": 0.20}
    }

    result = compute_consensus(r1, r2)

    # Calculate means
    support_mean = (0.85 + 0.60) / 2  # 0.725
    challenge_mean = (0.15 + 0.40) / 2  # 0.275
    delta = abs(support_mean - challenge_mean)  # 0.45

    print(f"  support_mean={support_mean:.3f}, challenge_mean={challenge_mean:.3f}, delta={delta:.3f}")

    assert delta >= 0.20, f"Test setup error: delta {delta} should be >= 0.20"
    assert result["label"] == "supports", "Should pick 'supports' with clear advantage"
    assert result["rationale"]["rule"] == "disagree_gap_select"
    # Expected: max(0.75, 0.60) - 0.05 = 0.70
    assert abs(result["confidence"] - 0.70) < 0.01, f"Expected 0.70, got {result['confidence']}"
    assert result["rationale"]["bonus_or_penalty"] == -0.05

    print(f"✓ Clear support win: {result['label']}, conf={result['confidence']:.2f}")


def test_disagreement_clear_challenge_win():
    """Test disagreement with clear challenge advantage"""
    r1 = {
        "label": "supports",
        "confidence": 0.58,
        "arm_strength": {"support": 0.45, "challenge": 0.55, "balance": -0.10}
    }
    r2 = {
        "label": "challenges",
        "confidence": 0.72,
        "arm_strength": {"support": 0.20, "challenge": 0.80, "balance": -0.60}
    }

    result = compute_consensus(r1, r2)

    # Calculate means
    support_mean = (0.45 + 0.20) / 2  # 0.325
    challenge_mean = (0.55 + 0.80) / 2  # 0.675
    delta = abs(support_mean - challenge_mean)  # 0.35

    print(f"  support_mean={support_mean:.3f}, challenge_mean={challenge_mean:.3f}, delta={delta:.3f}")

    assert delta >= 0.20, f"Test setup error: delta {delta} should be >= 0.20"
    assert result["label"] == "challenges", "Should pick 'challenges' with clear advantage"
    assert result["rationale"]["rule"] == "disagree_gap_select"
    # Expected: max(0.58, 0.72) - 0.05 = 0.67
    assert abs(result["confidence"] - 0.67) < 0.01, f"Expected 0.67, got {result['confidence']}"

    print(f"✓ Clear challenge win: {result['label']}, conf={result['confidence']:.2f}")


def test_disagreement_mixed_close_values():
    """Test disagreement with very close arm strengths - should return mixed"""
    r1 = {
        "label": "supports",
        "confidence": 0.55,
        "arm_strength": {"support": 0.55, "challenge": 0.45, "balance": 0.10}
    }
    r2 = {
        "label": "challenges",
        "confidence": 0.52,
        "arm_strength": {"support": 0.48, "challenge": 0.52, "balance": -0.04}
    }

    result = compute_consensus(r1, r2)

    # Calculate means
    support_mean = (0.55 + 0.48) / 2  # 0.515
    challenge_mean = (0.45 + 0.52) / 2  # 0.485
    delta = abs(support_mean - challenge_mean)  # 0.03

    print(f"  support_mean={support_mean:.3f}, challenge_mean={challenge_mean:.3f}, delta={delta:.3f}")

    assert delta < 0.20, f"Test setup error: delta {delta} should be < 0.20"
    assert result["label"] == "mixed", "Close disagreement should return 'mixed'"
    assert result["rationale"]["rule"] == "disagree_mixed"
    # Expected: max(0.55, 0.52) - 0.10 = 0.45
    assert abs(result["confidence"] - 0.45) < 0.01, f"Expected 0.45, got {result['confidence']}"
    assert result["rationale"]["bonus_or_penalty"] == -0.10

    print(f"✓ Mixed verdict: {result['label']}, conf={result['confidence']:.2f}")


def test_disagreement_at_threshold():
    """Test disagreement slightly above the 0.20 threshold"""
    # Use values that create clear delta > 0.20 to avoid floating-point issues
    r1 = {
        "label": "supports",
        "confidence": 0.65,
        "arm_strength": {"support": 0.72, "challenge": 0.28, "balance": 0.44}
    }
    r2 = {
        "label": "challenges",
        "confidence": 0.60,
        "arm_strength": {"support": 0.50, "challenge": 0.50, "balance": 0.00}
    }

    result = compute_consensus(r1, r2)

    # Calculate means
    support_mean = (0.72 + 0.50) / 2  # 0.61
    challenge_mean = (0.28 + 0.50) / 2  # 0.39
    delta = abs(support_mean - challenge_mean)  # 0.22

    print(f"  support_mean={support_mean:.3f}, challenge_mean={challenge_mean:.3f}, delta={delta:.3f}")

    # Slightly above 0.20, should trigger gap_select rule
    assert delta >= 0.20, f"Delta should be above threshold, got {delta}"
    assert result["rationale"]["rule"] == "disagree_gap_select", "Should use gap_select above threshold"
    assert result["label"] == "supports", "Should pick 'supports' when support_mean > challenge_mean"

    print(f"✓ Threshold case: {result['label']}, conf={result['confidence']:.2f}, rule={result['rationale']['rule']}")


def test_insufficient_agreement():
    """Test agreement on 'insufficient' label"""
    r1 = {
        "label": "insufficient",
        "confidence": 0.30,
        "arm_strength": {"support": 0.15, "challenge": 0.10, "balance": 0.05}
    }
    r2 = {
        "label": "insufficient",
        "confidence": 0.35,
        "arm_strength": {"support": 0.20, "challenge": 0.15, "balance": 0.05}
    }

    result = compute_consensus(r1, r2)

    # Agreement on 'insufficient'
    assert result["label"] == "insufficient"
    assert result["rationale"]["rule"] == "agree_same_label"
    # Expected: max(0.30, 0.35) + 0.10 = 0.45
    assert abs(result["confidence"] - 0.45) < 0.01, f"Expected 0.45, got {result['confidence']}"

    print(f"✓ Insufficient agreement: {result['label']}, conf={result['confidence']:.2f}")


def test_asymmetric_confidence():
    """Test disagreement with very different confidence levels"""
    r1 = {
        "label": "supports",
        "confidence": 0.90,
        "arm_strength": {"support": 0.92, "challenge": 0.08, "balance": 0.84}
    }
    r2 = {
        "label": "challenges",
        "confidence": 0.40,
        "arm_strength": {"support": 0.30, "challenge": 0.70, "balance": -0.40}
    }

    result = compute_consensus(r1, r2)

    # Calculate means
    support_mean = (0.92 + 0.30) / 2  # 0.61
    challenge_mean = (0.08 + 0.70) / 2  # 0.39
    delta = abs(support_mean - challenge_mean)  # 0.22

    print(f"  support_mean={support_mean:.3f}, challenge_mean={challenge_mean:.3f}, delta={delta:.3f}")

    # Clear gap despite asymmetric confidence
    assert delta >= 0.20
    assert result["label"] == "supports"
    # Uses higher confidence (0.90) as base
    assert abs(result["rationale"]["base_conf"] - 0.90) < 0.01
    # Expected: 0.90 - 0.05 = 0.85
    assert abs(result["confidence"] - 0.85) < 0.01

    print(f"✓ Asymmetric confidence: {result['label']}, conf={result['confidence']:.2f}")


def test_perfect_balance():
    """Test disagreement with perfect 50/50 balance"""
    r1 = {
        "label": "supports",
        "confidence": 0.60,
        "arm_strength": {"support": 0.50, "challenge": 0.50, "balance": 0.00}
    }
    r2 = {
        "label": "challenges",
        "confidence": 0.58,
        "arm_strength": {"support": 0.50, "challenge": 0.50, "balance": 0.00}
    }

    result = compute_consensus(r1, r2)

    # Calculate means
    support_mean = (0.50 + 0.50) / 2  # 0.50
    challenge_mean = (0.50 + 0.50) / 2  # 0.50
    delta = abs(support_mean - challenge_mean)  # 0.00

    print(f"  support_mean={support_mean:.3f}, challenge_mean={challenge_mean:.3f}, delta={delta:.3f}")

    # Perfect balance - should be mixed
    assert delta < 0.20
    assert result["label"] == "mixed"
    assert result["rationale"]["rule"] == "disagree_mixed"

    print(f"✓ Perfect balance: {result['label']}, conf={result['confidence']:.2f}")


def test_consensus_metrics_overlap():
    """Test consensus_metrics overlap calculation"""
    # Scenario: 50% overlap
    arm_a = [
        {"source": {"dedupe_key": "url1"}, "stance": "support"},
        {"source": {"dedupe_key": "url2"}, "stance": "support"}
    ]
    arm_b = [
        {"source": {"dedupe_key": "url1"}, "stance": "support"},  # Overlap
        {"source": {"dedupe_key": "url3"}, "stance": "refute"}
    ]

    result = consensus_metrics(arm_a, arm_b)

    # Union: {url1, url2, url3} = 3
    # Intersection: {url1} = 1
    # Overlap: 1/3 = 0.333
    expected_overlap = 1 / 3
    assert abs(result["overlap_ratio"] - expected_overlap) < 0.01, \
        f"Expected overlap {expected_overlap:.3f}, got {result['overlap_ratio']}"

    print(f"✓ Overlap calculation: {result['overlap_ratio']:.3f}")


def test_consensus_metrics_conflict():
    """Test consensus_metrics conflict scoring"""
    # Scenario: High conflict (opposing stances)
    arm_a = [
        {"source": {"dedupe_key": "url1"}, "stance": "support"},
        {"source": {"dedupe_key": "url2"}, "stance": "support"},
        {"source": {"dedupe_key": "url3"}, "stance": "support"}
    ]
    arm_b = [
        {"source": {"dedupe_key": "url4"}, "stance": "refute"},
        {"source": {"dedupe_key": "url5"}, "stance": "refute"}
    ]

    result = consensus_metrics(arm_a, arm_b)

    # Total: 3 support + 2 refute = 5
    # Conflict: |3 - 2| / 5 = 0.2
    expected_conflict = abs(3 - 2) / 5
    assert abs(result["conflict_score"] - expected_conflict) < 0.01, \
        f"Expected conflict {expected_conflict:.3f}, got {result['conflict_score']}"

    print(f"✓ Conflict scoring: {result['conflict_score']:.3f}")


def test_consensus_metrics_stability():
    """Test consensus_metrics stability (stance agreement on overlaps)"""
    # Scenario: Overlap with stance agreement
    arm_a = [
        {"source": {"dedupe_key": "url1"}, "stance": "support"},
        {"source": {"dedupe_key": "url2"}, "stance": "support"}
    ]
    arm_b = [
        {"source": {"dedupe_key": "url1"}, "stance": "support"},  # Same stance
        {"source": {"dedupe_key": "url2"}, "stance": "refute"}   # Different stance
    ]

    result = consensus_metrics(arm_a, arm_b)

    # 2 overlapping items, 1 agrees in stance
    # Stability: 1/2 = 0.5
    expected_stability = 0.5
    assert abs(result["stability"] - expected_stability) < 0.01, \
        f"Expected stability {expected_stability:.3f}, got {result['stability']}"

    print(f"✓ Stability calculation: {result['stability']:.3f}")


def test_agreement_metadata():
    """Test that agreement metadata is correctly populated"""
    r1 = {
        "label": "supports",
        "confidence": 0.75,
        "arm_strength": {"support": 0.80, "challenge": 0.20, "balance": 0.60}
    }
    r2 = {
        "label": "challenges",
        "confidence": 0.68,
        "arm_strength": {"support": 0.35, "challenge": 0.65, "balance": -0.30}
    }

    result = compute_consensus(r1, r2)

    # Check agreement metadata
    agreement = result["agreement"]
    assert agreement["r1_label"] == "supports"
    assert agreement["r2_label"] == "challenges"
    assert abs(agreement["r1_conf"] - 0.75) < 0.01
    assert abs(agreement["r2_conf"] - 0.68) < 0.01
    # Delta balance: 0.60 - (-0.30) = 0.90
    assert abs(agreement["delta_balance"] - 0.90) < 0.01

    print(f"✓ Agreement metadata: r1={agreement['r1_label']}, r2={agreement['r2_label']}, delta_balance={agreement['delta_balance']:.2f}")


def run_all_tests():
    """Run all capability tests"""
    print("\n" + "="*60)
    print("P27 CONSENSUS - CAPABILITY TESTS")
    print("="*60 + "\n")

    tests = [
        ("Agreement High Confidence", test_agreement_high_confidence),
        ("Agreement Low Confidence", test_agreement_low_confidence),
        ("Disagreement Clear Support Win", test_disagreement_clear_support_win),
        ("Disagreement Clear Challenge Win", test_disagreement_clear_challenge_win),
        ("Disagreement Mixed Close", test_disagreement_mixed_close_values),
        ("Disagreement At Threshold", test_disagreement_at_threshold),
        ("Insufficient Agreement", test_insufficient_agreement),
        ("Asymmetric Confidence", test_asymmetric_confidence),
        ("Perfect Balance", test_perfect_balance),
        ("Metrics Overlap", test_consensus_metrics_overlap),
        ("Metrics Conflict", test_consensus_metrics_conflict),
        ("Metrics Stability", test_consensus_metrics_stability),
        ("Agreement Metadata", test_agreement_metadata)
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
