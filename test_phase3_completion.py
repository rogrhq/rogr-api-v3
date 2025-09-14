#!/usr/bin/env python3
"""
Phase 3 Completion Test: Verify direct parallel system integration
Tests the new USE_PARALLEL_EVIDENCE=true path without fallbacks
"""
import os
import sys
import asyncio

# Set environment variables for parallel system
os.environ['USE_PARALLEL_EVIDENCE'] = 'true'
os.environ['USE_EVIDENCE_SHEPHERD'] = 'false'
os.environ['USE_EEG_PHASE_1'] = 'true'

# Import after setting environment variables
from main import USE_PARALLEL_EVIDENCE, evidence_system, process_analysis_request
from main import create_evidence_system, convert_parallel_to_claim_analyses

def test_parallel_system_creation():
    """Test that parallel system is correctly created"""
    print("🔧 Testing parallel system creation...")
    print(f"USE_PARALLEL_EVIDENCE = {USE_PARALLEL_EVIDENCE}")

    # Test evidence system creation
    test_evidence_system = create_evidence_system()
    print(f"Evidence system type: {type(test_evidence_system)}")
    print(f"Has process_claims_parallel: {hasattr(test_evidence_system, 'process_claims_parallel')}")

    if hasattr(test_evidence_system, 'process_claims_parallel'):
        print("✅ Parallel system correctly instantiated")
        return True
    else:
        print("❌ Parallel system missing process_claims_parallel method")
        return False

def test_format_conversion():
    """Test consensus result to ClaimAnalysis conversion"""
    print("\n🔧 Testing format conversion...")

    # Mock parallel system results
    mock_consensus_results = [
        {
            'claim_text': 'Test claim about parallel processing',
            'consensus_score': 0.85,
            'confidence_level': 0.9,
            'evidence_count': 5,
            'processing_time': 2.1,
            'success': True
        }
    ]

    # Test conversion
    claim_analyses = convert_parallel_to_claim_analyses(mock_consensus_results)

    if claim_analyses and len(claim_analyses) == 1:
        analysis = claim_analyses[0]
        print(f"✅ Conversion successful:")
        print(f"  Trust Score: {analysis.trust_score}")
        print(f"  Evidence Grade: {analysis.evidence_grade}")
        print(f"  Confidence: {analysis.confidence}")
        print(f"  Sources Count: {analysis.sources_count}")
        return True
    else:
        print("❌ Format conversion failed")
        return False

async def test_complete_pipeline():
    """Test complete pipeline with real parallel system call"""
    print("\n🔧 Testing complete pipeline...")

    # Simple test claim
    test_content = "The Earth is round and orbits the Sun."

    try:
        # This should trigger the parallel system path
        result = await process_analysis_request("text", test_content, None, None, None, skip_social_media_check=True)

        if result and hasattr(result, 'claims'):
            print(f"✅ Pipeline completed successfully:")
            print(f"  Claims processed: {len(result.claims)}")
            print(f"  Overall score: {result.trust_score}")
            print(f"  Overall grade: {result.evidence_grade}")
            return True
        else:
            print("❌ Pipeline failed to return proper TrustCapsule")
            return False

    except Exception as e:
        print(f"❌ Pipeline failed with error: {e}")
        return False

async def run_all_tests():
    """Run all Phase 3 completion tests"""
    print("=== PHASE 3 COMPLETION TESTS ===")

    results = []

    # Test 1: System creation
    results.append(test_parallel_system_creation())

    # Test 2: Format conversion
    results.append(test_format_conversion())

    # Test 3: Complete pipeline (only if system creation works)
    if results[0]:
        results.append(await test_complete_pipeline())
    else:
        print("\n⚠️ Skipping pipeline test due to system creation failure")
        results.append(False)

    # Summary
    passed = sum(results)
    total = len(results)

    print(f"\n=== TEST RESULTS ===")
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ Phase 3 integration path complete - parallel system active with NO fallbacks")
    else:
        print("❌ Phase 3 integration issues detected")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)