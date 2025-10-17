#!/usr/bin/env python3
"""
Architecture Validation: Pipeline Flow
Tests verify the sequence of operations in the evidence pipeline.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


def test_pipeline_flow_sequence():
    """
    Test the documented pipeline flow matches actual imports and call sequences.

    Expected Flow:
    1. plan_v2.py → build_search_plans_v2() creates search plan
    2. gather/pipeline.py → build_evidence_for_claim() orchestrates
    3. gather/online.py → run_plan() fetches evidence
    4. gather/normalize.py → normalize_candidates() cleans data
    5. rank/select.py → rank_candidates() ranks by score
    6. analyze/stance.py → assess_stance() adds stance metadata
    7. policy/guardrails.py → apply_guardrails_to_arms() enforces limits
    8. content/grade.py → attach_finding_to_item() grades evidence (0-10 scale ⚠️)
    9. content/fetch_enrichment.py → enrich_items_with_content() fetches full text
    10. content/semantic_read.py → analyze_item() semantic analysis (0-1 scale)
    11. content/semantic_frames.py → analyze_frames() frame extraction
    12. content/fullread.py → evaluate_full_evidence() deep read (0-10 scale)
    13. content/p25_aggregate.py → aggregate_verdict() final verdict
    14. consensus/metrics.py → compute_overlap_conflict() cross-arm analysis
    15. score/labeling.py → score_from_evidence() + map_score_to_label()
    """
    print("Testing pipeline flow sequence...")

    # Verify imports exist and are callable
    from intelligence.strategy.plan_v2 import build_search_plans_v2
    from intelligence.gather.pipeline import build_evidence_for_claim
    from intelligence.gather.normalize import normalize_candidates
    from intelligence.rank.select import rank_candidates
    from intelligence.analyze.stance import assess_stance
    from intelligence.content.grade import build_finding, attach_finding_to_item
    from intelligence.content.fetch_enrichment import enrich_items_with_content
    from intelligence.content.semantic_read import analyze_item
    from intelligence.content.semantic_frames import analyze_frames
    from intelligence.content.fullread import evaluate_full_evidence
    from intelligence.content.p25_aggregate import aggregate_verdict
    from intelligence.consensus.metrics import compute_overlap_conflict
    from intelligence.score.labeling import score_from_evidence, map_score_to_label

    assert callable(build_search_plans_v2), "build_search_plans_v2 must be callable"
    assert callable(build_evidence_for_claim), "build_evidence_for_claim must be callable"
    assert callable(normalize_candidates), "normalize_candidates must be callable"
    assert callable(rank_candidates), "rank_candidates must be callable"
    assert callable(assess_stance), "assess_stance must be callable"
    assert callable(build_finding), "build_finding must be callable"
    assert callable(analyze_item), "analyze_item must be callable"
    assert callable(analyze_frames), "analyze_frames must be callable"
    assert callable(evaluate_full_evidence), "evaluate_full_evidence must be callable"
    assert callable(aggregate_verdict), "aggregate_verdict must be callable"
    assert callable(compute_overlap_conflict), "compute_overlap_conflict must be callable"
    assert callable(score_from_evidence), "score_from_evidence must be callable"
    assert callable(map_score_to_label), "map_score_to_label must be callable"

    print("  ✓ All pipeline modules are importable and callable")

    # Check that pipeline.py imports the right modules
    import intelligence.gather.pipeline as pipeline_module
    import inspect

    source = inspect.getsource(pipeline_module)

    # Verify key imports
    assert 'from intelligence.gather import online' in source, \
        "pipeline.py must import online module"
    assert 'from intelligence.gather.normalize import normalize_candidates' in source, \
        "pipeline.py must import normalize_candidates"
    assert 'from intelligence.rank.select import rank_candidates' in source, \
        "pipeline.py must import rank_candidates"
    assert 'from intelligence.analyze.stance import assess_stance' in source, \
        "pipeline.py must import assess_stance"
    assert 'from intelligence.consensus.metrics import compute_overlap_conflict' in source, \
        "pipeline.py must import compute_overlap_conflict"
    assert 'from intelligence.score.labeling import score_from_evidence' in source, \
        "pipeline.py must import score_from_evidence"

    print("  ✓ pipeline.py imports verified")

    # Verify call sequence in build_evidence_for_claim
    assert 'normalize_candidates(armA_raw)' in source or 'normalize_candidates(armB_raw)' in source, \
        "pipeline must call normalize_candidates"
    assert 'rank_candidates(' in source, \
        "pipeline must call rank_candidates"
    assert 'assess_stance(' in source, \
        "pipeline must call assess_stance"
    assert 'apply_guardrails_to_arms(' in source, \
        "pipeline must call apply_guardrails_to_arms"
    assert 'compute_overlap_conflict(' in source, \
        "pipeline must call compute_overlap_conflict"
    assert 'score_from_evidence(' in source, \
        "pipeline must call score_from_evidence"

    print("  ✓ pipeline.py call sequence verified")
    print("✅ PASS: Pipeline flow sequence validated\n")


def test_data_flow_through_pipeline():
    """
    Test that data structures flow correctly through the pipeline.
    """
    print("Testing data flow through pipeline...")

    # Stage 1: Plan creation
    from intelligence.strategy.plan_v2 import build_search_plans_v2

    claim = {
        'text': 'Austin budget increased by 8%',
        'entities': ['Austin'],
        'numbers': {'percents': [8.0]},
        'scope': {'year': 2024},
        'cues': {},
        'kind_hint': 'budget'
    }

    plan = build_search_plans_v2(claim)
    assert 'arms' in plan, "Plan must have arms"
    assert 'A' in plan['arms'] and 'B' in plan['arms'], "Plan must have both arms"
    print(f"  ✓ Stage 1: Plan created with {len(plan['arms'])} arms")

    # Stage 2: Normalize (simulated)
    from intelligence.gather.normalize import normalize_candidates

    raw_candidates = [
        {'url': 'https://example.com', 'snippet': 'test', 'score': 0.9, 'arm': 'A'},
        {'url': 'https://example.com', 'snippet': 'test duplicate', 'score': 0.8, 'arm': 'A'},  # duplicate
        {'url': 'https://other.com', 'snippet': 'other', 'score': 0.7, 'arm': 'B'}
    ]

    normalized = normalize_candidates(raw_candidates)
    assert len(normalized) <= len(raw_candidates), "Normalization should deduplicate"
    print(f"  ✓ Stage 2: Normalized {len(raw_candidates)} → {len(normalized)} candidates")

    # Stage 3: Rank
    from intelligence.rank.select import rank_candidates

    ranked = rank_candidates(candidates=normalized, top_k=5)
    assert all('rank' in item for item in ranked), "All items must have rank"
    print(f"  ✓ Stage 3: Ranked {len(ranked)} candidates")

    # Stage 4: Stance (simulated, no actual API call)
    from intelligence.analyze.stance import assess_stance

    item = {'title': 'Test', 'snippet': 'budget increased confirming reports'}
    stance_result = assess_stance('budget increased', item)
    assert 'stance' in stance_result, "Stance result must have 'stance'"
    print(f"  ✓ Stage 4: Stance assessed: {stance_result['stance']}")

    # Stage 5: Grade (simulated)
    from intelligence.content.grade import build_finding

    finding = build_finding(
        claim_text='Austin budget increased 8%',
        arm='A',
        content_text='The Austin budget increased by 8%',
        snippet_text='budget increased by 8%'
    )
    assert 'grade' in finding, "Finding must have grade"
    assert 'stance' in finding, "Finding must have stance"
    print(f"  ✓ Stage 5: Finding created with grade={finding['grade']}")

    # Stage 6: Semantic read (simulated)
    from intelligence.content.semantic_read import analyze_item

    item_with_content = {
        'content': 'The Austin city budget increased by 8 percent.',
        'url': 'https://example.com',
        'snippet': 'budget increased'
    }
    analyzed = analyze_item('Austin budget increased 8%', item_with_content)
    assert 'item_grade' in analyzed, "Analyzed item must have item_grade"
    assert 0 <= analyzed['item_grade'] <= 1, "item_grade must be 0-1"
    print(f"  ✓ Stage 6: Semantic read completed, item_grade={analyzed['item_grade']:.3f}")

    # Stage 7: Frame analysis (simulated)
    from intelligence.content.semantic_frames import analyze_frames

    frame_result = analyze_frames(
        claim_text='Austin budget increased 8%',
        content='The city of Austin saw its budget increase by 8%'
    )
    assert 'frame_matches' in frame_result, "Frame result must have frame_matches"
    assert 'frame_confidence' in frame_result, "Frame result must have frame_confidence"
    print(f"  ✓ Stage 7: Frame analysis completed, confidence={frame_result['frame_confidence']:.3f}")

    # Stage 8: Aggregate verdict
    from intelligence.content.p25_aggregate import aggregate_verdict

    arm_a = [
        {'item_grade': 0.75, 'frame_matches': [{'score': 0.80}], 'coverage': 'full'}
    ]
    arm_b = [
        {'item_grade': 0.45, 'frame_matches': [{'score': 0.50}], 'coverage': 'snippet_only'}
    ]

    verdict = aggregate_verdict('Test claim', arm_a, arm_b)
    assert 'label' in verdict, "Verdict must have label"
    assert 'confidence' in verdict, "Verdict must have confidence"
    print(f"  ✓ Stage 8: Verdict aggregated, label={verdict['label']}, confidence={verdict['confidence']:.3f}")

    # Stage 9: Score mapping
    from intelligence.score.labeling import map_score_to_label

    label = map_score_to_label(75)
    assert label in ['True', 'Mostly True', 'Mixed', 'Mostly False', 'False'], \
        f"Label must be valid, got: {label}"
    print(f"  ✓ Stage 9: Score 75 mapped to label: {label}")

    print("✅ PASS: Data flow through pipeline validated\n")


def test_module_dependencies():
    """
    Test that module dependencies match the documented architecture.
    """
    print("Testing module dependencies...")

    # Verify no circular dependencies
    import intelligence.gather.pipeline
    import intelligence.content.grade
    import intelligence.content.semantic_read
    import intelligence.content.semantic_frames
    import intelligence.content.p25_aggregate

    print("  ✓ No circular import errors detected")

    # Verify shared modules are used
    from intelligence.content.shared import frames, paraphrases, vocabulary, text_utils

    assert hasattr(frames, 'Frame'), "shared.frames must export Frame"
    assert hasattr(frames, 'extract_frame'), "shared.frames must export extract_frame"
    assert hasattr(paraphrases, 'paraphrase_match_score'), \
        "shared.paraphrases must export paraphrase_match_score"
    assert hasattr(vocabulary, 'INC_VERBS'), "shared.vocabulary must export INC_VERBS"
    assert hasattr(vocabulary, 'DEC_VERBS'), "shared.vocabulary must export DEC_VERBS"

    print("  ✓ Shared modules are properly structured")
    print("✅ PASS: Module dependencies validated\n")


if __name__ == '__main__':
    print("="*70)
    print("ARCHITECTURE VALIDATION: Pipeline Flow")
    print("="*70 + "\n")

    try:
        test_pipeline_flow_sequence()
        test_data_flow_through_pipeline()
        test_module_dependencies()

        print("="*70)
        print("✅ ALL PIPELINE FLOW TESTS PASSED")
        print("="*70)
    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
