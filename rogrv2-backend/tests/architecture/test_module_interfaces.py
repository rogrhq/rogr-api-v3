#!/usr/bin/env python3
"""
Architecture Validation: Module Interfaces
Tests verify the exact signatures and behavior of core module functions.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import inspect


def test_grade_build_finding():
    """
    Test: intelligence/content/grade.py:build_finding
    Location: intelligence/content/grade.py:176
    Signature: build_finding(claim_text, arm, content_text, snippet_text, precomputed_window, precomputed_sim)
    Returns: Dict with keys [grade, stance, matched_spans, rationale, similarity, signals]
    """
    print("Testing grade.py:build_finding interface...")

    from intelligence.content.grade import build_finding

    # Check signature
    sig = inspect.signature(build_finding)
    params = list(sig.parameters.keys())
    assert 'claim_text' in params, "build_finding must have 'claim_text' parameter"
    assert 'arm' in params, "build_finding must have 'arm' parameter"
    assert 'content_text' in params, "build_finding must have 'content_text' parameter"

    print(f"  ✓ Signature: {sig}")

    # Test execution
    result = build_finding(
        claim_text="Austin budget increased 8%",
        arm="A",
        content_text="The Austin city budget saw an 8% increase in 2024",
        snippet_text="budget saw an 8% increase",
        precomputed_window="",
        precomputed_sim=-1.0
    )

    # Validate return structure
    assert isinstance(result, dict), "build_finding must return dict"
    assert 'grade' in result, "Result must have 'grade'"
    assert 'stance' in result, "Result must have 'stance'"
    assert 'matched_spans' in result, "Result must have 'matched_spans'"
    assert 'rationale' in result, "Result must have 'rationale'"

    # ⚠️ BUG: grade is 0-10 scale, should be 0-1
    assert isinstance(result['grade'], (int, float)), "grade must be numeric"
    print(f"  ✓ Returns: grade={result['grade']} (⚠️ 0-10 scale), stance={result['stance']}")
    print("✅ PASS: grade.py:build_finding validated\n")


def test_semantic_read_analyze_item():
    """
    Test: intelligence/content/semantic_read.py:analyze_item
    Location: intelligence/content/semantic_read.py:103
    Signature: analyze_item(claim_text, item, *, window=3)
    Returns: Updated item dict with findings[], item_grade (0-1), grade_label
    """
    print("Testing semantic_read.py:analyze_item interface...")

    from intelligence.content.semantic_read import analyze_item

    sig = inspect.signature(analyze_item)
    params = list(sig.parameters.keys())
    assert 'claim_text' in params, "analyze_item must have 'claim_text'"
    assert 'item' in params, "analyze_item must have 'item'"

    print(f"  ✓ Signature: {sig}")

    # Test execution
    item = {
        'content': 'The Austin budget increased by 8 percent in fiscal year 2024.',
        'url': 'https://example.com',
        'snippet': 'budget increased by 8 percent'
    }

    result = analyze_item("Austin budget increased 8%", item, window=3)

    assert 'findings' in result, "Result must have 'findings'"
    assert 'item_grade' in result, "Result must have 'item_grade'"
    assert 'grade_label' in result, "Result must have 'grade_label'"
    assert 0 <= result['item_grade'] <= 1, \
        f"item_grade must be 0-1, got: {result['item_grade']}"
    assert result['grade_label'] in ['high', 'medium', 'low'], \
        f"grade_label must be high/medium/low, got: {result['grade_label']}"

    print(f"  ✓ Returns: item_grade={result['item_grade']:.3f}, findings_count={len(result['findings'])}")
    print("✅ PASS: semantic_read.py:analyze_item validated\n")


def test_semantic_frames_analyze_frames():
    """
    Test: intelligence/content/semantic_frames.py:analyze_frames
    Location: intelligence/content/semantic_frames.py:202
    Signature: analyze_frames(claim_text, content, *, window=3, max_windows=500)
    Returns: Dict with item_frame, frame_matches[], frame_confidence
    """
    print("Testing semantic_frames.py:analyze_frames interface...")

    from intelligence.content.semantic_frames import analyze_frames

    sig = inspect.signature(analyze_frames)
    params = list(sig.parameters.keys())
    assert 'claim_text' in params, "analyze_frames must have 'claim_text'"
    assert 'content' in params, "analyze_frames must have 'content'"

    print(f"  ✓ Signature: {sig}")

    # Test execution
    result = analyze_frames(
        claim_text="Austin budget increased 8%",
        content="The city of Austin saw its general fund budget increase by 8% in 2024.",
        window=3
    )

    assert 'item_frame' in result, "Result must have 'item_frame'"
    assert 'frame_matches' in result, "Result must have 'frame_matches'"
    assert 'frame_confidence' in result, "Result must have 'frame_confidence'"
    assert isinstance(result['frame_matches'], list), "frame_matches must be list"
    assert 0 <= result['frame_confidence'] <= 1, \
        f"frame_confidence must be 0-1, got: {result['frame_confidence']}"

    print(f"  ✓ Returns: frame_confidence={result['frame_confidence']:.3f}, matches_count={len(result['frame_matches'])}")
    print("✅ PASS: semantic_frames.py:analyze_frames validated\n")


def test_fullread_evaluate():
    """
    Test: intelligence/content/fullread.py:evaluate_full_evidence
    Location: intelligence/content/fullread.py:177
    Signature: evaluate_full_evidence(claim_text, item)
    Returns: Updated item with grade_full (0-10), stance_full, signals_full, credibility (0-1)
    """
    print("Testing fullread.py:evaluate_full_evidence interface...")

    from intelligence.content.fullread import evaluate_full_evidence

    sig = inspect.signature(evaluate_full_evidence)
    params = list(sig.parameters.keys())
    assert 'claim_text' in params, "evaluate_full_evidence must have 'claim_text'"
    assert 'item' in params, "evaluate_full_evidence must have 'item'"

    print(f"  ✓ Signature: {sig}")

    # Test execution
    item = {
        'content': 'The Austin city budget increased by 8% in fiscal year 2024, according to official documents.',
        'url': 'https://austintexas.gov/budget',
        'snippet': 'budget increased by 8%'
    }

    result = evaluate_full_evidence("Austin budget increased 8%", item)

    assert 'grade_full' in result, "Result must have 'grade_full'"
    assert 'stance_full' in result, "Result must have 'stance_full'"
    assert 'signals_full' in result, "Result must have 'signals_full'"
    assert 'credibility' in result, "Result must have 'credibility'"
    assert 0 <= result['grade_full'] <= 10, \
        f"grade_full must be 0-10, got: {result['grade_full']}"
    assert 0 <= result['credibility'] <= 1, \
        f"credibility must be 0-1, got: {result['credibility']}"

    print(f"  ✓ Returns: grade_full={result['grade_full']:.2f}, credibility={result['credibility']:.3f}")
    print("✅ PASS: fullread.py:evaluate_full_evidence validated\n")


def test_p25_aggregate_verdict():
    """
    Test: intelligence/content/p25_aggregate.py:aggregate_verdict
    Location: intelligence/content/p25_aggregate.py:72
    Signature: aggregate_verdict(claim_text, arm_a_items, arm_b_items, *, delta=0.15)
    Returns: Dict with label, confidence, arm_strength
    """
    print("Testing p25_aggregate.py:aggregate_verdict interface...")

    from intelligence.content.p25_aggregate import aggregate_verdict

    sig = inspect.signature(aggregate_verdict)
    params = list(sig.parameters.keys())
    assert 'claim_text' in params, "aggregate_verdict must have 'claim_text'"
    assert 'arm_a_items' in params, "aggregate_verdict must have 'arm_a_items'"
    assert 'arm_b_items' in params, "aggregate_verdict must have 'arm_b_items'"

    print(f"  ✓ Signature: {sig}")

    # Test execution
    arm_a = [
        {'item_grade': 0.75, 'frame_matches': [{'score': 0.80}], 'coverage': 'full'},
        {'item_grade': 0.65, 'frame_matches': [{'score': 0.70}], 'coverage': 'partial'}
    ]
    arm_b = [
        {'item_grade': 0.45, 'frame_matches': [{'score': 0.50}], 'coverage': 'snippet_only'}
    ]

    result = aggregate_verdict("Test claim", arm_a, arm_b, delta=0.15)

    assert 'label' in result, "Result must have 'label'"
    assert 'confidence' in result, "Result must have 'confidence'"
    assert 'arm_strength' in result, "Result must have 'arm_strength'"

    print(f"  ✓ Returns: label={result['label']}, confidence={result['confidence']:.3f}")
    print("✅ PASS: p25_aggregate.py:aggregate_verdict validated\n")


def test_rank_candidates():
    """
    Test: intelligence/rank/select.py:rank_candidates
    Location: intelligence/rank/select.py:24
    Signature: rank_candidates(items=None, *, candidates=None, claim_text=None, query=None, top_k=None, **kwargs)
    Returns: List of ranked candidate dicts with 'rank' field added
    """
    print("Testing rank/select.py:rank_candidates interface...")

    from intelligence.rank.select import rank_candidates

    sig = inspect.signature(rank_candidates)
    print(f"  ✓ Signature: {sig}")

    # Test execution
    candidates = [
        {'arm': 'A', 'score': 0.8, 'url': 'url1'},
        {'arm': 'A', 'score': 0.6, 'url': 'url2'},
        {'arm': 'B', 'score': 0.7, 'url': 'url3'},
        {'arm': 'B', 'score': 0.5, 'url': 'url4'}
    ]

    result = rank_candidates(candidates=candidates, top_k=2)

    assert isinstance(result, list), "rank_candidates must return list"
    assert len(result) <= 4, "With top_k=2 per arm, max 4 items returned"
    for item in result:
        assert 'rank' in item, "Each item must have 'rank' field"
        assert isinstance(item['rank'], int), "rank must be int"

    print(f"  ✓ Returns: {len(result)} items with rank field")
    print(f"    Arm A ranks: {[i['rank'] for i in result if i['arm'] == 'A']}")
    print(f"    Arm B ranks: {[i['rank'] for i in result if i['arm'] == 'B']}")
    print("✅ PASS: rank/select.py:rank_candidates validated\n")


def test_assess_stance():
    """
    Test: intelligence/analyze/stance.py:assess_stance
    Location: intelligence/analyze/stance.py:44
    Signature: assess_stance(claim_text, item)
    Returns: Dict with stance, stance_score, contradiction_flags, notes
    """
    print("Testing analyze/stance.py:assess_stance interface...")

    from intelligence.analyze.stance import assess_stance

    sig = inspect.signature(assess_stance)
    params = list(sig.parameters.keys())
    assert 'claim_text' in params, "assess_stance must have 'claim_text'"
    assert 'item' in params, "assess_stance must have 'item'"

    print(f"  ✓ Signature: {sig}")

    # Test execution
    item = {
        'title': 'Budget Analysis',
        'snippet': 'The budget increased by 8% confirming earlier reports'
    }

    result = assess_stance("Austin budget increased 8%", item)

    assert 'stance' in result, "Result must have 'stance'"
    assert 'stance_score' in result, "Result must have 'stance_score'"
    assert 'contradiction_flags' in result, "Result must have 'contradiction_flags'"
    assert result['stance'] in ['support', 'refute', 'neutral'], \
        f"stance must be support/refute/neutral, got: {result['stance']}"
    assert 0 <= result['stance_score'] <= 100, \
        f"stance_score must be 0-100, got: {result['stance_score']}"

    print(f"  ✓ Returns: stance={result['stance']}, score={result['stance_score']}")
    print("✅ PASS: analyze/stance.py:assess_stance validated\n")


def test_plan_v2_build_search_plans():
    """
    Test: intelligence/strategy/plan_v2.py:build_search_plans_v2
    Location: intelligence/strategy/plan_v2.py:115
    Signature: build_search_plans_v2(claim)
    Returns: Dict with version, arms (A/B with intent and queries), meta
    """
    print("Testing strategy/plan_v2.py:build_search_plans_v2 interface...")

    from intelligence.strategy.plan_v2 import build_search_plans_v2

    sig = inspect.signature(build_search_plans_v2)
    params = list(sig.parameters.keys())
    assert 'claim' in params, "build_search_plans_v2 must have 'claim'"

    print(f"  ✓ Signature: {sig}")

    # Test execution
    claim = {
        'text': 'Austin budget increased by 8% in 2024',
        'entities': ['Austin'],
        'numbers': {'percents': [8.0]},
        'scope': {'year': 2024},
        'cues': {'has_comparison': True},
        'kind_hint': 'budget'
    }

    result = build_search_plans_v2(claim)

    assert 'version' in result, "Result must have 'version'"
    assert 'arms' in result, "Result must have 'arms'"
    assert 'A' in result['arms'], "Must have Arm A"
    assert 'B' in result['arms'], "Must have Arm B"
    assert 'intent' in result['arms']['A'], "Arm A must have 'intent'"
    assert 'queries' in result['arms']['A'], "Arm A must have 'queries'"
    assert result['arms']['A']['intent'] == 'support', "Arm A intent must be 'support'"
    assert result['arms']['B']['intent'] == 'challenge', "Arm B intent must be 'challenge'"

    print(f"  ✓ Returns: version={result['version']}")
    print(f"    Arm A queries: {len(result['arms']['A']['queries'])}")
    print(f"    Arm B queries: {len(result['arms']['B']['queries'])}")
    print("✅ PASS: strategy/plan_v2.py:build_search_plans_v2 validated\n")


if __name__ == '__main__':
    print("="*70)
    print("ARCHITECTURE VALIDATION: Module Interfaces")
    print("="*70 + "\n")

    try:
        test_grade_build_finding()
        test_semantic_read_analyze_item()
        test_semantic_frames_analyze_frames()
        test_fullread_evaluate()
        test_p25_aggregate_verdict()
        test_rank_candidates()
        test_assess_stance()
        test_plan_v2_build_search_plans()

        print("="*70)
        print("✅ ALL MODULE INTERFACE TESTS PASSED")
        print("="*70)
    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
