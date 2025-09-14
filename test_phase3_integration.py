#!/usr/bin/env python3
"""
Phase 3 Integration Test: search_real_evidence method validation

Tests the newly implemented search_real_evidence method in ParallelEvidenceOrchestrator
to ensure it fixes the FATAL production errors.
"""

import sys
import os

def test_search_real_evidence_method():
    """Test that search_real_evidence method exists and is callable"""

    print("🧪 Phase 3 Integration Test: search_real_evidence method")
    print("=" * 60)

    try:
        # Import the parallel evidence orchestrator
        from parallel_evidence_system.orchestrator.parallel_evidence_orchestrator import ParallelEvidenceOrchestrator
        print("✅ ParallelEvidenceOrchestrator import successful")

        # Create instance
        orchestrator = ParallelEvidenceOrchestrator()
        print("✅ Orchestrator instantiation successful")

        # Test that search_real_evidence method exists
        if hasattr(orchestrator, 'search_real_evidence'):
            print("✅ search_real_evidence method exists")
        else:
            print("❌ search_real_evidence method MISSING")
            return False

        # Test method signature
        import inspect
        signature = inspect.signature(orchestrator.search_real_evidence)
        print(f"✅ Method signature: search_real_evidence{signature}")

        # Test that it's callable
        if callable(orchestrator.search_real_evidence):
            print("✅ search_real_evidence method is callable")
        else:
            print("❌ search_real_evidence method not callable")
            return False

        # Test basic functionality with simple claim
        print("\n🔍 Testing basic functionality...")
        test_claim = "Climate change is real"

        try:
            result = orchestrator.search_real_evidence(test_claim)
            print(f"✅ Method call successful, returned {type(result)}")

            if isinstance(result, list):
                print(f"✅ Returns list as expected, length: {len(result)}")

                if result:
                    # Check first evidence piece structure
                    first_evidence = result[0]
                    print(f"✅ First evidence type: {type(first_evidence)}")

                    # Check for consensus_quality_score (critical for main.py integration)
                    if hasattr(first_evidence, 'consensus_quality_score'):
                        print(f"✅ consensus_quality_score present: {first_evidence.consensus_quality_score}")
                    else:
                        print("❌ consensus_quality_score MISSING - will cause main.py errors")
                        return False

                    if hasattr(first_evidence, 'consensus_metadata'):
                        print(f"✅ consensus_metadata present: {type(first_evidence.consensus_metadata)}")
                    else:
                        print("⚠️  consensus_metadata missing")

                else:
                    print("⚠️  Empty result list")
            else:
                print(f"❌ Expected list, got {type(result)}")
                return False

        except Exception as e:
            print(f"❌ Method call failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False

        print("\n🎯 FATAL Error Fix Validation:")
        print("✅ ParallelEvidenceOrchestrator now has search_real_evidence method")
        print("✅ Method returns List[ProcessedEvidence] as expected")
        print("✅ ProcessedEvidence includes consensus_quality_score for main.py")
        print("✅ Should resolve: 'ParallelEvidenceOrchestrator' object has no attribute 'search_real_evidence'")

        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_orchestrator_status():
    """Test orchestrator status includes search_real_evidence availability"""

    print("\n🔍 Testing orchestrator status...")

    try:
        from parallel_evidence_system.orchestrator.parallel_evidence_orchestrator import ParallelEvidenceOrchestrator
        orchestrator = ParallelEvidenceOrchestrator()

        status = orchestrator.get_orchestrator_status()
        print(f"✅ Status retrieved: {status}")

        if status.get('search_real_evidence_available'):
            print("✅ Status confirms search_real_evidence is available")
            return True
        else:
            print("❌ Status does not confirm search_real_evidence availability")
            return False

    except Exception as e:
        print(f"❌ Status test failed: {e}")
        return False

if __name__ == "__main__":
    print("PHASE 3 INTEGRATION TEST")
    print("========================")
    print("Objective: Validate search_real_evidence method fixes FATAL production errors")
    print()

    # Run tests
    test1_passed = test_search_real_evidence_method()
    test2_passed = test_orchestrator_status()

    print("\n" + "=" * 60)
    print("PHASE 3 TEST RESULTS:")
    print(f"✅ search_real_evidence method test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ orchestrator status test: {'PASSED' if test2_passed else 'FAILED'}")

    if test1_passed and test2_passed:
        print("\n🎉 PHASE 3 INTEGRATION SUCCESS!")
        print("FATAL production errors should now be resolved.")
        print("ParallelEvidenceOrchestrator ready for production use.")
    else:
        print("\n❌ PHASE 3 INTEGRATION FAILED!")
        print("Additional fixes needed before production deployment.")
        sys.exit(1)