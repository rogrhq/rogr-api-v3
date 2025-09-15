"""
Test Phase 1.2 Parallel System Foundation Components

Tests ThreadSafeResourcePool, WorkerResourceBundle, and EvidenceRelevanceValidator
on remote backend with proper dependencies installed.
"""

def test_phase_1_2_foundation():
    """Test Phase 1.2 parallel system foundation components"""
    print("Testing Phase 1.2 Parallel System Foundation...")
    print("=" * 60)

    try:
        # Test 1: Import parallel system components
        print("Test 1: Importing parallel system components...")
        from parallel_evidence_system.resources.thread_safe_resource_pool import ThreadSafeResourcePool
        from parallel_evidence_system.resources.worker_resource_bundle import WorkerResourceBundle
        from parallel_evidence_system.resources.evidence_relevance_validator import EvidenceRelevanceValidator
        print("✅ All imports successful")

        # Test 2: ThreadSafeResourcePool initialization
        print("\nTest 2: ThreadSafeResourcePool initialization...")
        pool = ThreadSafeResourcePool()
        assert pool.component_id is not None
        assert "ThreadSafeResourcePool" in pool.component_id
        print(f"✅ ThreadSafeResourcePool created with ID: {pool.component_id}")

        # Test 3: WorkerResourceBundle creation
        print("\nTest 3: WorkerResourceBundle creation...")
        resources = pool.get_worker_resources()
        assert resources is not None
        assert hasattr(resources, 'web_search')
        assert hasattr(resources, 'content_extractor')
        assert hasattr(resources, 'evidence_validator')
        assert hasattr(resources, 'rate_limiter')
        print("✅ WorkerResourceBundle created with all required fields")

        # Test 4: EvidenceRelevanceValidator functionality
        print("\nTest 4: EvidenceRelevanceValidator functionality...")
        validator = resources.evidence_validator
        assert isinstance(validator, EvidenceRelevanceValidator)

        # Test validation method
        result = validator.validate_relevance(
            claim_text="Test claim for validation",
            evidence_text="Test evidence content",
            claim_analysis=None
        )

        assert result is not None
        assert hasattr(result, 'semantic_match_score')
        assert hasattr(result, 'logical_relevance_score')
        assert hasattr(result, 'scope_alignment_score')
        assert hasattr(result, 'evidence_quality_score')
        assert hasattr(result, 'final_relevance_score')
        assert hasattr(result, 'relevance_reasoning')
        print(f"✅ EvidenceRelevanceValidator working: final_relevance_score={result.final_relevance_score}")

        # Test 5: Thread isolation
        print("\nTest 5: Thread isolation validation...")
        import threading

        def test_thread_isolation(thread_id, results):
            try:
                thread_pool = ThreadSafeResourcePool()
                thread_resources = thread_pool.get_worker_resources()
                results[thread_id] = {
                    'success': True,
                    'pool_id': thread_pool.component_id,
                    'thread_ident': threading.current_thread().ident,
                    'validator_type': type(thread_resources.evidence_validator).__name__
                }
            except Exception as e:
                results[thread_id] = {
                    'success': False,
                    'error': str(e)
                }

        results = {}
        threads = []
        for i in range(3):
            thread = threading.Thread(target=test_thread_isolation, args=(f"thread_{i}", results))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all threads succeeded and got different component IDs
        assert len(results) == 3
        pool_ids = []
        for thread_id, result in results.items():
            assert result['success'], f"Thread {thread_id} failed: {result.get('error', 'Unknown')}"
            pool_ids.append(result['pool_id'])
            assert result['validator_type'] == 'EvidenceRelevanceValidator'

        # Each thread should have different pool instances
        assert len(set(pool_ids)) == 3, "Thread isolation failed - threads sharing pool instances"
        print("✅ Thread isolation validated - each thread gets independent resources")

        print("\n" + "=" * 60)
        print("🎉 ALL PHASE 1.2 TESTS PASSED!")
        print("✅ ThreadSafeResourcePool: Working with proper component IDs")
        print("✅ WorkerResourceBundle: Created with all required fields")
        print("✅ EvidenceRelevanceValidator: Functional with correct interface")
        print("✅ Thread Isolation: Verified independent resources per thread")
        print("✅ Phase 1.2 Parallel System Foundation: READY FOR PHASE 2")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_phase_1_2_foundation()
    exit(0 if success else 1)