"""
P26 Dual Researchers Structural Tests

Tests structural integrity of the dual-researcher orchestrator:
- Field validation (researchers array structure)
- Integration with P27/P28/P29 dependencies
- Edge cases (empty results, missing fields)
- Error handling
"""

import sys
sys.path.insert(0, '/Users/txtk/Documents/ROGR/github/rogrv2-backend')

import asyncio
from intelligence.orchestration.dual_lane import run_dual_researchers, merge_r1_r2_results


# Mock dependencies for testing
async def mock_enrichment_pipeline(claim_text, plan, lane_id, telemetry):
    """Mock enrichment pipeline"""
    telemetry.record_provider_call("google")
    return {
        "verdict": {
            "label": "supports" if lane_id == "R1" else "challenges",
            "confidence": 0.7
        },
        "evidence": {
            "arm_A": [{"content": f"{lane_id} evidence"}],
            "arm_B": []
        }
    }

def mock_diversify_fn(plan, lane_id, claim, providers):
    """Mock diversify function"""
    return plan, {
        "lane_id": lane_id,
        "providers": providers,
        "seed": 123 if lane_id == "R1" else 456,
        "queries_first3": {}
    }

class MockTelemetry:
    """Mock telemetry class"""
    def __init__(self, lane_id):
        self.lane_id = lane_id
        self.calls = {}

    def record_provider_call(self, provider):
        self.calls[provider] = self.calls.get(provider, 0) + 1

    def finalize(self):
        return {
            "providers": self.calls,
            "duration_ms": 100
        }


def test_run_dual_researchers_output_structure():
    """Test run_dual_researchers returns correct structure"""
    async def test():
        result = await run_dual_researchers(
            "Test claim",
            {"arms": []},
            mock_enrichment_pipeline,
            mock_diversify_fn,
            MockTelemetry
        )

        # Top-level fields
        assert isinstance(result, dict), "Result should be dict"
        assert "researchers" in result, "Missing 'researchers' field"
        assert "verdict" in result, "Missing 'verdict' field (backward compat)"
        assert "evidence" in result, "Missing 'evidence' field (backward compat)"

        # Researchers structure
        assert isinstance(result["researchers"], list), "researchers should be list"
        assert len(result["researchers"]) == 2, "Should have exactly 2 researchers"

        print("✓ Output structure validated")
        return result

    return asyncio.run(test())


def test_researchers_array_structure():
    """Test each researcher in array has correct fields"""
    async def test():
        result = await run_dual_researchers(
            "Test",
            {"arms": []},
            mock_enrichment_pipeline,
            mock_diversify_fn,
            MockTelemetry
        )

        for i, researcher in enumerate(result["researchers"]):
            assert isinstance(researcher, dict), f"Researcher {i} should be dict"
            assert "id" in researcher, f"Researcher {i} missing 'id'"
            assert "verdict" in researcher, f"Researcher {i} missing 'verdict'"
            assert "evidence" in researcher, f"Researcher {i} missing 'evidence'"
            assert "lane_config" in researcher, f"Researcher {i} missing 'lane_config'"
            assert "telemetry" in researcher, f"Researcher {i} missing 'telemetry'"

        print("✓ Researchers array structure validated")

    asyncio.run(test())


def test_researcher_ids():
    """Test researchers have correct IDs"""
    async def test():
        result = await run_dual_researchers(
            "Test",
            {"arms": []},
            mock_enrichment_pipeline,
            mock_diversify_fn,
            MockTelemetry
        )

        assert result["researchers"][0]["id"] == "R1", "First researcher should be R1"
        assert result["researchers"][1]["id"] == "R2", "Second researcher should be R2"

        print("✓ Researcher IDs: R1, R2")

    asyncio.run(test())


def test_verdict_structure():
    """Test verdict structure in researchers"""
    async def test():
        result = await run_dual_researchers(
            "Test",
            {"arms": []},
            mock_enrichment_pipeline,
            mock_diversify_fn,
            MockTelemetry
        )

        for researcher in result["researchers"]:
            verdict = researcher["verdict"]
            assert isinstance(verdict, dict), "verdict should be dict"
            # Check if verdict has expected fields (may vary by implementation)
            if verdict:  # Allow empty verdict
                assert "label" in verdict or len(verdict) == 0, "verdict should have label or be empty"

        print(f"✓ Verdict structure: R1={result['researchers'][0]['verdict'].get('label')}, R2={result['researchers'][1]['verdict'].get('label')}")

    asyncio.run(test())


def test_lane_config_integration():
    """Test lane_config is correctly attached from P28"""
    async def test():
        result = await run_dual_researchers(
            "Test",
            {"arms": []},
            mock_enrichment_pipeline,
            mock_diversify_fn,
            MockTelemetry
        )

        r1 = result["researchers"][0]
        r2 = result["researchers"][1]

        # Check lane_config presence
        assert "lane_config" in r1, "R1 missing lane_config"
        assert "lane_config" in r2, "R2 missing lane_config"

        # Check lane_config content
        assert r1["lane_config"]["lane_id"] == "R1"
        assert r2["lane_config"]["lane_id"] == "R2"
        assert "providers" in r1["lane_config"]
        assert "seed" in r1["lane_config"]

        print(f"✓ Lane config: R1_seed={r1['lane_config']['seed']}, R2_seed={r2['lane_config']['seed']}")

    asyncio.run(test())


def test_telemetry_integration():
    """Test telemetry is correctly attached from P29"""
    async def test():
        result = await run_dual_researchers(
            "Test",
            {"arms": []},
            mock_enrichment_pipeline,
            mock_diversify_fn,
            MockTelemetry
        )

        r1 = result["researchers"][0]
        r2 = result["researchers"][1]

        # Check telemetry presence
        assert "telemetry" in r1, "R1 missing telemetry"
        assert "telemetry" in r2, "R2 missing telemetry"

        # Check telemetry structure (from P29)
        assert "providers" in r1["telemetry"]
        assert "duration_ms" in r1["telemetry"]
        assert isinstance(r1["telemetry"]["providers"], dict)
        assert isinstance(r1["telemetry"]["duration_ms"], int)

        print(f"✓ Telemetry: R1={r1['telemetry']}, R2={r2['telemetry']}")

    asyncio.run(test())


def test_backward_compatibility_fields():
    """Test backward compatibility fields (verdict, evidence at top level)"""
    async def test():
        result = await run_dual_researchers(
            "Test",
            {"arms": []},
            mock_enrichment_pipeline,
            mock_diversify_fn,
            MockTelemetry
        )

        # Top-level fields should match R1 for backward compat
        assert result["verdict"] == result["researchers"][0]["verdict"], \
            "Top-level verdict should match R1"
        assert result["evidence"] == result["researchers"][0]["evidence"], \
            "Top-level evidence should match R1"

        print("✓ Backward compatibility: top-level verdict/evidence match R1")

    asyncio.run(test())


def test_merge_r1_r2_results_helper():
    """Test merge_r1_r2_results helper function"""
    r1 = {
        "verdict": {"label": "supports", "confidence": 0.8},
        "evidence": {"arm_A": ["e1"]}
    }
    r2 = {
        "verdict": {"label": "challenges", "confidence": 0.6},
        "evidence": {"arm_B": ["e2"]}
    }

    result = merge_r1_r2_results(r1, r2)

    assert "researchers" in result, "Should have researchers field"
    assert len(result["researchers"]) == 2, "Should have 2 researchers"
    assert result["verdict"] == r1["verdict"], "Top-level verdict should be R1"
    assert result["evidence"] == r1["evidence"], "Top-level evidence should be R1"

    print("✓ merge_r1_r2_results: combines R1+R2 correctly")


def test_edge_case_empty_pipeline_results():
    """Test handling of empty pipeline results"""
    async def empty_pipeline(claim_text, plan, lane_id, telemetry):
        return {}

    async def test():
        result = await run_dual_researchers(
            "Test",
            {"arms": []},
            empty_pipeline,
            mock_diversify_fn,
            MockTelemetry
        )

        assert "researchers" in result
        assert len(result["researchers"]) == 2

        # Should handle empty results gracefully
        for r in result["researchers"]:
            assert "verdict" in r
            assert "evidence" in r
            assert isinstance(r["verdict"], dict)
            assert isinstance(r["evidence"], dict)

        print("✓ Empty pipeline results handled gracefully")

    asyncio.run(test())


def test_edge_case_missing_verdict():
    """Test handling when enrichment pipeline doesn't return verdict"""
    async def no_verdict_pipeline(claim_text, plan, lane_id, telemetry):
        return {"evidence": {"arm_A": []}}  # No verdict

    async def test():
        result = await run_dual_researchers(
            "Test",
            {"arms": []},
            no_verdict_pipeline,
            mock_diversify_fn,
            MockTelemetry
        )

        # Should use empty dict as default
        for r in result["researchers"]:
            assert "verdict" in r
            assert isinstance(r["verdict"], dict)

        print("✓ Missing verdict handled with empty dict")

    asyncio.run(test())


def test_diversification_applied():
    """Test that diversify_fn is called for both lanes"""
    calls = []

    def tracking_diversify(plan, lane_id, claim, providers):
        calls.append(lane_id)
        return plan, {"lane_id": lane_id, "providers": providers, "seed": 0}

    async def test():
        await run_dual_researchers(
            "Test",
            {"arms": []},
            mock_enrichment_pipeline,
            tracking_diversify,
            MockTelemetry
        )

        assert len(calls) == 2, "Should call diversify twice"
        assert "R1" in calls, "Should diversify R1"
        assert "R2" in calls, "Should diversify R2"

        print(f"✓ Diversification applied: {calls}")

    asyncio.run(test())


def test_telemetry_instantiated_per_lane():
    """Test that telemetry is instantiated separately for each lane"""
    instantiated = []

    class TrackingTelemetry:
        def __init__(self, lane_id):
            instantiated.append(lane_id)
            self.lane_id = lane_id

        def record_provider_call(self, provider):
            pass

        def finalize(self):
            return {"providers": {}, "duration_ms": 0}

    async def test():
        await run_dual_researchers(
            "Test",
            {"arms": []},
            mock_enrichment_pipeline,
            mock_diversify_fn,
            TrackingTelemetry
        )

        assert len(instantiated) == 2, "Should instantiate telemetry twice"
        assert instantiated[0] == "R1", "First instantiation should be R1"
        assert instantiated[1] == "R2", "Second instantiation should be R2"

        print(f"✓ Telemetry instantiated per lane: {instantiated}")

    asyncio.run(test())


def test_sequential_execution():
    """Test that R1 and R2 run sequentially (not parallel)"""
    execution_order = []

    async def tracking_pipeline(claim_text, plan, lane_id, telemetry):
        execution_order.append(f"{lane_id}_start")
        await asyncio.sleep(0.01)  # Simulate work
        execution_order.append(f"{lane_id}_end")
        return {"verdict": {}, "evidence": {}}

    async def test():
        await run_dual_researchers(
            "Test",
            {"arms": []},
            tracking_pipeline,
            mock_diversify_fn,
            MockTelemetry
        )

        # If sequential: R1_start, R1_end, R2_start, R2_end
        # If parallel: R1_start, R2_start, R1_end, R2_end
        assert execution_order == ["R1_start", "R1_end", "R2_start", "R2_end"], \
            "Should execute R1 then R2 sequentially"

        print(f"✓ Sequential execution: {execution_order}")

    asyncio.run(test())


def run_all_tests():
    """Run all structural tests"""
    print("\n" + "="*60)
    print("P26 DUAL RESEARCHERS - STRUCTURAL TESTS")
    print("="*60 + "\n")

    tests = [
        ("Output Structure", test_run_dual_researchers_output_structure),
        ("Researchers Array Structure", test_researchers_array_structure),
        ("Researcher IDs", test_researcher_ids),
        ("Verdict Structure", test_verdict_structure),
        ("Lane Config Integration (P28)", test_lane_config_integration),
        ("Telemetry Integration (P29)", test_telemetry_integration),
        ("Backward Compatibility", test_backward_compatibility_fields),
        ("merge_r1_r2_results Helper", test_merge_r1_r2_results_helper),
        ("Empty Pipeline Results", test_edge_case_empty_pipeline_results),
        ("Missing Verdict", test_edge_case_missing_verdict),
        ("Diversification Applied", test_diversification_applied),
        ("Telemetry Per Lane", test_telemetry_instantiated_per_lane),
        ("Sequential Execution", test_sequential_execution)
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
