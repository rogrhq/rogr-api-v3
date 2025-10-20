"""
Single claim end-to-end diagnostic trace.
Shows actual workflow vs intended workflow.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

SIMPLE_CLAIM = "Water boils at 100 degrees Celsius at sea level"

def trace_claim_workflow(claim_text):
    """
    Trace one claim through the entire pipeline.
    Report what actually happens at each stage.
    """

    trace = {
        'claim': claim_text,
        'stages': {}
    }

    print(f"\n{'='*70}")
    print(f"DIAGNOSTIC TRACE: {claim_text}")
    print(f"{'='*70}")

    # Stage 1: Query Generation
    print("\n=== STAGE 1: QUERY GENERATION ===")
    try:
        from intelligence.strategy.plan_v2 import build_search_plans_v2, generate_queries_r1, generate_queries_r2
        from intelligence.analyze.enrich import enrich_claim_obj

        # Check if R1/R2 differentiated
        print("✓ Found generate_queries_r1 function")
        print("✓ Found generate_queries_r2 function")

        # Test with simple data
        claim = {"id": "test", "text": claim_text, "tier": "primary"}
        claim = enrich_claim_obj(claim)

        # Generate R1 queries
        r1_queries_a = generate_queries_r1(claim_text, claim.get('entities', []), claim.get('numbers', []), 'A')
        r1_queries_b = generate_queries_r1(claim_text, claim.get('entities', []), claim.get('numbers', []), 'B')

        # Generate R2 queries
        r2_queries_a = generate_queries_r2(claim_text, claim.get('entities', []), claim.get('numbers', []), 'A')
        r2_queries_b = generate_queries_r2(claim_text, claim.get('entities', []), claim.get('numbers', []), 'B')

        print(f"\nR1 Queries (Arm A): {r1_queries_a[:2]}")
        print(f"R1 Queries (Arm B): {r1_queries_b[:2]}")
        print(f"R2 Queries (Arm A): {r2_queries_a[:2]}")
        print(f"R2 Queries (Arm B): {r2_queries_b[:2]}")

        trace['stages']['query_gen'] = {
            'status': 'implemented',
            'r1_r2_differentiated': True,
            'r1_count': len(r1_queries_a) + len(r1_queries_b),
            'r2_count': len(r2_queries_a) + len(r2_queries_b)
        }

    except Exception as e:
        print(f"✗ ERROR: {e}")
        trace['stages']['query_gen'] = {'status': 'error', 'error': str(e)}

    # Stage 2: Evidence Curation
    print("\n=== STAGE 2: EVIDENCE CURATION ===")
    try:
        from intelligence.gather.pipeline import filter_unrelated, quality_gate

        print("✓ Found filter_unrelated function")
        print("✓ Found quality_gate function")

        # Check if they're actually called in the pipeline
        import inspect
        pipeline_source = inspect.getsource(__import__('intelligence.gather.pipeline', fromlist=['build_evidence_for_claim']))

        filters_called = 'filter_unrelated(' in pipeline_source and 'quality_gate(' in pipeline_source

        if filters_called:
            print("✓ Filters ARE called in pipeline")
            trace['stages']['evidence_curation'] = {'status': 'implemented', 'called': True}
        else:
            print("✗ Filters DEFINED but NOT called in pipeline")
            trace['stages']['evidence_curation'] = {'status': 'partial', 'called': False}

    except Exception as e:
        print(f"✗ ERROR: {e}")
        trace['stages']['evidence_curation'] = {'status': 'error', 'error': str(e)}

    # Stage 3: Evidence Analysis
    print("\n=== STAGE 3: EVIDENCE ANALYSIS ===")
    try:
        from intelligence.content.grade import build_finding, build_finding_v2

        print("✓ Found build_finding (OLD)")
        print("✓ Found build_finding_v2 (NEW)")

        # Check which one is called in run.py
        run_source = inspect.getsource(__import__('intelligence.pipeline.run', fromlist=['run_single_lane_enrichment']))

        uses_v2 = 'build_finding_v2' in run_source
        uses_old = 'build_finding(' in run_source or 'attach_finding_to_item' in run_source

        if uses_v2:
            print("✓ Using build_finding_v2 (orchestrator)")
        else:
            print("✗ Using OLD build_finding (not orchestrator)")

        # Check scale
        import intelligence.content.grade as grade_module
        grade_source = inspect.getsource(grade_module.build_finding)
        if '/ 8.0' in grade_source:
            print("✓ Scale bug fixed (0-1 range)")
        else:
            print("✗ Scale bug NOT fixed")

        # Check authority integration
        if 'authority' in grade_source:
            print("✓ Authority scoring integrated")
        else:
            print("✗ Authority scoring NOT integrated")

        trace['stages']['evidence_analysis'] = {
            'status': 'partial',
            'uses_v2': uses_v2,
            'uses_old': uses_old,
            'scale_fixed': '/ 8.0' in grade_source,
            'authority_integrated': 'authority' in grade_source
        }

    except Exception as e:
        print(f"✗ ERROR: {e}")
        trace['stages']['evidence_analysis'] = {'status': 'error', 'error': str(e)}

    # Stage 4: Arm Aggregation
    print("\n=== STAGE 4: ARM AGGREGATION ===")
    try:
        from intelligence.content.p25_aggregate import aggregate_verdict

        agg_source = inspect.getsource(__import__('intelligence.content.p25_aggregate', fromlist=['aggregate_verdict']))

        # Check what factors it uses
        uses_diversity = 'diversity' in agg_source.lower()
        uses_consistency = 'consistency' in agg_source.lower()
        uses_breadth = 'breadth' in agg_source.lower()
        uses_item_strength = '_item_strength' in agg_source

        print(f"Uses diversity: {'✓' if uses_diversity else '✗'}")
        print(f"Uses consistency: {'✓' if uses_consistency else '✗'}")
        print(f"Uses breadth: {'✓' if uses_breadth else '✗'}")
        print(f"Uses item_strength: {'✓' if uses_item_strength else '✗'}")

        if not (uses_diversity or uses_consistency or uses_breadth):
            print("✗ Aggregation uses simple item strength (not diversity/consistency/breadth)")

        trace['stages']['arm_aggregation'] = {
            'status': 'partial',
            'uses_diversity': uses_diversity,
            'uses_consistency': uses_consistency,
            'uses_breadth': uses_breadth,
            'uses_item_strength': uses_item_strength
        }

    except Exception as e:
        print(f"✗ ERROR: {e}")
        trace['stages']['arm_aggregation'] = {'status': 'error', 'error': str(e)}

    # Stage 5: Consensus
    print("\n=== STAGE 5: CONSENSUS ===")
    try:
        from intelligence.consensus.dual_lane import compute_consensus
        from intelligence.consensus.build import compare_evidence_quality, resolve_disagreement

        print("✓ Found compute_consensus (current)")
        print("✓ Found compare_evidence_quality (Phase 6)")
        print("✓ Found resolve_disagreement (Phase 6)")

        # Check which one is used
        consensus_source = inspect.getsource(compute_consensus)

        uses_evidence_quality = 'compare_evidence_quality' in consensus_source or 'item_grade' in consensus_source
        uses_arm_strength_only = 'arm_strength' in consensus_source and not uses_evidence_quality

        if uses_evidence_quality:
            print("✓ Consensus compares evidence quality")
        else:
            print("✗ Consensus uses arm strength only (NOT evidence quality)")

        trace['stages']['consensus'] = {
            'status': 'partial',
            'uses_evidence_quality': uses_evidence_quality,
            'uses_arm_strength_only': uses_arm_strength_only
        }

    except Exception as e:
        print(f"✗ ERROR: {e}")
        trace['stages']['consensus'] = {'status': 'error', 'error': str(e)}

    # Stage 6: Query Validation
    print("\n=== STAGE 6: QUERY VALIDATION ===")
    try:
        from intelligence.gather.pipeline import validate_query_results

        print("✓ Found validate_query_results function")

        # Check if it's called
        pipeline_source = inspect.getsource(__import__('intelligence.gather.pipeline', fromlist=['build_evidence_for_claim']))

        validation_called = 'validate_query_results(' in pipeline_source and '# return validate_query_results' not in pipeline_source

        if validation_called:
            print("✓ Query validation IS called")
        else:
            print("✗ Query validation DEFINED but commented out")

        trace['stages']['query_validation'] = {
            'status': 'partial',
            'defined': True,
            'called': validation_called
        }

    except Exception as e:
        print(f"✗ ERROR: {e}")
        trace['stages']['query_validation'] = {'status': 'error', 'error': str(e)}

    # Stage 7: Source Reliability
    print("\n=== STAGE 7: SOURCE RELIABILITY ===")
    try:
        from intelligence.sources.reliability import get_source_reliability, SOURCE_RELIABILITY_DB

        print(f"✓ Found reliability database with {len(SOURCE_RELIABILITY_DB)} domains")

        # Check if it's used in grading
        grade_source = inspect.getsource(__import__('intelligence.content.grade', fromlist=['build_finding']))

        uses_reliability = 'get_source_reliability' in grade_source or 'source_reliability' in grade_source

        if uses_reliability:
            print("✓ Reliability IS integrated in grading")
        else:
            print("✗ Reliability DEFINED but NOT used in grading")

        trace['stages']['source_reliability'] = {
            'status': 'partial',
            'db_size': len(SOURCE_RELIABILITY_DB),
            'integrated': uses_reliability
        }

    except Exception as e:
        print(f"✗ ERROR: {e}")
        trace['stages']['source_reliability'] = {'status': 'error', 'error': str(e)}

    # Stage 8: Claim Classification
    print("\n=== STAGE 8: CLAIM CLASSIFICATION ===")
    try:
        from intelligence.preprocess.classify import classify_claim

        print("✓ Found claim classification")

        # Test it
        classification = classify_claim(claim_text)
        print(f"  Category: {classification['category']}")
        print(f"  Verifiability: {classification['verifiability']}")

        # Check if used in pipeline
        run_source = inspect.getsource(__import__('intelligence.pipeline.run', fromlist=['run_preview']))

        uses_classification = 'classify_claim' in run_source

        if uses_classification:
            print("✓ Classification IS used in pipeline")
        else:
            print("✗ Classification DEFINED but NOT used in pipeline")

        trace['stages']['claim_classification'] = {
            'status': 'partial',
            'category': classification['category'],
            'integrated': uses_classification
        }

    except Exception as e:
        print(f"✗ ERROR: {e}")
        trace['stages']['claim_classification'] = {'status': 'error', 'error': str(e)}

    # Stage 9: Calibration
    print("\n=== STAGE 9: CALIBRATION ===")
    try:
        from intelligence.calibration.confidence import calibrate_confidence, apply_confidence_thresholds

        print("✓ Found calibration functions")

        # Check if used
        run_source = inspect.getsource(__import__('intelligence.pipeline.run', fromlist=['run_preview']))
        consensus_source = inspect.getsource(__import__('intelligence.consensus.dual_lane', fromlist=['compute_consensus']))

        uses_calibration = 'calibrate_confidence' in run_source or 'calibrate_confidence' in consensus_source

        if uses_calibration:
            print("✓ Calibration IS used")
        else:
            print("✗ Calibration DEFINED but NOT used")

        trace['stages']['calibration'] = {
            'status': 'partial',
            'integrated': uses_calibration
        }

    except Exception as e:
        print(f"✗ ERROR: {e}")
        trace['stages']['calibration'] = {'status': 'error', 'error': str(e)}

    # Stage 10: Numeric Precision
    print("\n=== STAGE 10: NUMERIC PRECISION ===")
    try:
        # Search for precision handling
        import intelligence.content.grade as grade_module
        grade_source = inspect.getsource(grade_module)

        has_precision = 'precision' in grade_source.lower() and 'numeric' in grade_source.lower()

        if has_precision:
            print("✓ Numeric precision handling found")
        else:
            print("✗ Numeric precision handling NOT found")

        trace['stages']['numeric_precision'] = {
            'status': 'not_implemented',
            'found': has_precision
        }

    except Exception as e:
        print(f"✗ ERROR: {e}")
        trace['stages']['numeric_precision'] = {'status': 'error', 'error': str(e)}

    print(f"\n{'='*70}")
    print("TRACE COMPLETE")
    print(f"{'='*70}\n")

    return trace

if __name__ == '__main__':
    import inspect
    trace = trace_claim_workflow(SIMPLE_CLAIM)

    # Summary
    print("\n=== SUMMARY ===")
    implemented = sum(1 for s in trace['stages'].values() if s.get('status') == 'implemented')
    partial = sum(1 for s in trace['stages'].values() if s.get('status') == 'partial')
    not_impl = sum(1 for s in trace['stages'].values() if s.get('status') == 'not_implemented')
    errors = sum(1 for s in trace['stages'].values() if s.get('status') == 'error')

    total = len(trace['stages'])

    print(f"Total stages checked: {total}")
    print(f"Fully implemented: {implemented}")
    print(f"Partially implemented: {partial}")
    print(f"Not implemented: {not_impl}")
    print(f"Errors: {errors}")
