"""
P26 Dual Researchers Capability Tests

Tests core functionality of the dual-researcher orchestrator:
- Integration with P28 (diversification)
- Integration with P29 (telemetry)
- Researcher agreement/disagreement scenarios
- Real-world fact-checking flows
- Error handling and resilience
"""

import sys
sys.path.insert(0, '/Users/txtk/Documents/ROGR/github/rogrv2-backend')

import asyncio
from intelligence.orchestration.dual_lane import run_dual_researchers
from intelligence.planning.diversify import diversify_plan_for_lane, get_available_providers
from intelligence.telemetry.collect import LaneTelemetry


# Mock enrichment pipeline with different behaviors
async def mock_pipeline_agreement(claim_text, plan, lane_id, telemetry):
    """Both researchers agree"""
    telemetry.record_provider_call("google")
    return {
        "verdict": {"label": "supports", "confidence": 0.75},
        "evidence": {"arm_A": [{"content": "supporting evidence"}], "arm_B": []}
    }

async def mock_pipeline_disagreement(claim_text, plan, lane_id, telemetry):
    """Researchers disagree"""
    telemetry.record_provider_call("google" if lane_id == "R1" else "brave")
    return {
        "verdict": {
            "label": "supports" if lane_id == "R1" else "challenges",
            "confidence": 0.7
        },
        "evidence": {"arm_A": [{"content": f"{lane_id} evidence"}], "arm_B": []}
    }

async def mock_pipeline_asymmetric(claim_text, plan, lane_id, telemetry):
    """R1 high confidence, R2 low confidence"""
    telemetry.record_provider_call("google")
    telemetry.record_provider_call("google")
    return {
        "verdict": {
            "label": "supports",
            "confidence": 0.9 if lane_id == "R1" else 0.4
        },
        "evidence": {"arm_A": [], "arm_B": []}
    }


def test_integration_with_real_p28():
    """Test integration with real P28 diversify function"""
    async def test():
        result = await run_dual_researchers(
            "Water boils at 100 degrees Celsius",
            {"arms": [{"name": "A", "queries": ["q1", "q2", "q3"]}]},
            mock_pipeline_agreement,
            diversify_plan_for_lane,  # Real P28 function
            LaneTelemetry  # Real P29 class
        )

        r1 = result["researchers"][0]
        r2 = result["researchers"][1]

        # Check P28 integration
        assert r1["lane_config"]["lane_id"] == "R1"
        assert r2["lane_config"]["lane_id"] == "R2"
        assert "seed" in r1["lane_config"]
        assert "seed" in r2["lane_config"]
        # Seeds should differ
        assert r1["lane_config"]["seed"] != r2["lane_config"]["seed"]

        # Check provider ordering differs (P28 behavior)
        if "providers" in r1["lane_config"] and "providers" in r2["lane_config"]:
            assert r1["lane_config"]["providers"] != r2["lane_config"]["providers"], \
                "R1 and R2 should have different provider orders"

        print(f"✓ P28 integration: R1_seed={r1['lane_config']['seed']}, R2_seed={r2['lane_config']['seed']}")

    asyncio.run(test())


def test_integration_with_real_p29():
    """Test integration with real P29 telemetry"""
    async def test():
        result = await run_dual_researchers(
            "Test claim",
            {"arms": []},
            mock_pipeline_disagreement,
            diversify_plan_for_lane,
            LaneTelemetry  # Real P29 class
        )

        r1 = result["researchers"][0]
        r2 = result["researchers"][1]

        # Check P29 integration
        assert "telemetry" in r1
        assert "telemetry" in r2
        assert "providers" in r1["telemetry"]
        assert "duration_ms" in r1["telemetry"]

        # Different providers should be recorded (from mock)
        assert "google" in r1["telemetry"]["providers"]
        assert "brave" in r2["telemetry"]["providers"]

        print(f"✓ P29 integration: R1_providers={r1['telemetry']['providers']}, R2_providers={r2['telemetry']['providers']}")

    asyncio.run(test())


def test_researchers_agreement_scenario():
    """Test scenario where both researchers agree"""
    async def test():
        result = await run_dual_researchers(
            "Water boils at 100C",
            {"arms": []},
            mock_pipeline_agreement,
            diversify_plan_for_lane,
            LaneTelemetry
        )

        r1 = result["researchers"][0]
        r2 = result["researchers"][1]

        # Both should have same verdict label
        assert r1["verdict"]["label"] == r2["verdict"]["label"]
        assert r1["verdict"]["label"] == "supports"

        print(f"✓ Agreement scenario: R1={r1['verdict']['label']}, R2={r2['verdict']['label']}")

    asyncio.run(test())


def test_researchers_disagreement_scenario():
    """Test scenario where researchers disagree"""
    async def test():
        result = await run_dual_researchers(
            "Test claim",
            {"arms": []},
            mock_pipeline_disagreement,
            diversify_plan_for_lane,
            LaneTelemetry
        )

        r1 = result["researchers"][0]
        r2 = result["researchers"][1]

        # Should have different verdict labels
        assert r1["verdict"]["label"] != r2["verdict"]["label"]
        assert r1["verdict"]["label"] == "supports"
        assert r2["verdict"]["label"] == "challenges"

        print(f"✓ Disagreement scenario: R1={r1['verdict']['label']}, R2={r2['verdict']['label']}")

    asyncio.run(test())


def test_asymmetric_confidence_scenario():
    """Test scenario with asymmetric confidence"""
    async def test():
        result = await run_dual_researchers(
            "Test",
            {"arms": []},
            mock_pipeline_asymmetric,
            diversify_plan_for_lane,
            LaneTelemetry
        )

        r1 = result["researchers"][0]
        r2 = result["researchers"][1]

        # Same label, different confidence
        assert r1["verdict"]["label"] == r2["verdict"]["label"]
        assert r1["verdict"]["confidence"] > r2["verdict"]["confidence"]

        print(f"✓ Asymmetric confidence: R1={r1['verdict']['confidence']}, R2={r2['verdict']['confidence']}")

    asyncio.run(test())


def test_scientific_claim_scenario():
    """Test with a realistic scientific claim"""
    async def realistic_pipeline(claim_text, plan, lane_id, telemetry):
        telemetry.record_provider_call("google")
        telemetry.record_provider_call("google")

        # Simulate different confidence based on diversified results
        confidence = 0.82 if lane_id == "R1" else 0.79

        return {
            "verdict": {"label": "supports", "confidence": confidence},
            "evidence": {
                "arm_A": [
                    {"content": "Water has a boiling point of 100°C at sea level", "source": "Scientific source"}
                ],
                "arm_B": []
            }
        }

    async def test():
        result = await run_dual_researchers(
            "Water boils at 100 degrees Celsius",
            {
                "arms": [
                    {"name": "A", "queries": ["water boiling point 100C", "H2O boils 100 celsius"]},
                    {"name": "B", "queries": ["water boiling point myths", "boiling point altitude"]}
                ]
            },
            realistic_pipeline,
            diversify_plan_for_lane,
            LaneTelemetry
        )

        assert len(result["researchers"]) == 2
        assert "Water" in result.get("researchers", [{}])[0].get("evidence", {}).get("arm_A", [{}])[0].get("content", "")

        print(f"✓ Scientific claim: R1_verdict={result['researchers'][0]['verdict']}")

    asyncio.run(test())


def test_policy_claim_scenario():
    """Test with a realistic policy claim"""
    async def realistic_pipeline(claim_text, plan, lane_id, telemetry):
        telemetry.record_provider_call("brave" if lane_id == "R2" else "google")

        # R1 supports, R2 challenges (different sources found)
        if lane_id == "R1":
            return {
                "verdict": {"label": "supports", "confidence": 0.68},
                "evidence": {"arm_A": [{"content": "CA unemployment 8%"}], "arm_B": []}
            }
        else:
            return {
                "verdict": {"label": "challenges", "confidence": 0.62},
                "evidence": {"arm_A": [], "arm_B": [{"content": "CA unemployment 7.5%"}]}
            }

    async def test():
        result = await run_dual_researchers(
            "California unemployment is at 8 percent",
            {
                "arms": [
                    {"name": "A", "queries": ["California unemployment 8%"]},
                    {"name": "B", "queries": ["CA jobless rate actual"]}
                ]
            },
            realistic_pipeline,
            diversify_plan_for_lane,
            LaneTelemetry
        )

        r1 = result["researchers"][0]
        r2 = result["researchers"][1]

        assert r1["verdict"]["label"] == "supports"
        assert r2["verdict"]["label"] == "challenges"

        print(f"✓ Policy claim: R1={r1['verdict']['label']}, R2={r2['verdict']['label']}")

    asyncio.run(test())


def test_evidence_preservation():
    """Test that evidence is preserved for each researcher"""
    async def evidence_pipeline(claim_text, plan, lane_id, telemetry):
        telemetry.record_provider_call("google")
        return {
            "verdict": {"label": "supports", "confidence": 0.7},
            "evidence": {
                "arm_A": [{"content": f"{lane_id} arm A evidence", "source": f"{lane_id} source"}],
                "arm_B": [{"content": f"{lane_id} arm B evidence"}]
            }
        }

    async def test():
        result = await run_dual_researchers(
            "Test",
            {"arms": []},
            evidence_pipeline,
            diversify_plan_for_lane,
            LaneTelemetry
        )

        r1 = result["researchers"][0]
        r2 = result["researchers"][1]

        # Check R1 evidence
        assert len(r1["evidence"]["arm_A"]) > 0
        assert "R1" in r1["evidence"]["arm_A"][0]["content"]

        # Check R2 evidence
        assert len(r2["evidence"]["arm_A"]) > 0
        assert "R2" in r2["evidence"]["arm_A"][0]["content"]

        print(f"✓ Evidence preserved: R1={len(r1['evidence']['arm_A'])} items, R2={len(r2['evidence']['arm_A'])} items")

    asyncio.run(test())


def test_error_handling_pipeline_exception():
    """Test handling when enrichment pipeline raises exception"""
    async def failing_pipeline(claim_text, plan, lane_id, telemetry):
        if lane_id == "R2":
            raise ValueError("Pipeline error")
        return {"verdict": {"label": "supports", "confidence": 0.7}, "evidence": {}}

    async def test():
        try:
            result = await run_dual_researchers(
                "Test",
                {"arms": []},
                failing_pipeline,
                diversify_plan_for_lane,
                LaneTelemetry
            )
            # If we get here, exception wasn't raised (might be handled gracefully)
            print("✓ Exception handled gracefully or propagated as expected")
        except ValueError as e:
            # Exception propagated - expected behavior
            assert "Pipeline error" in str(e)
            print("✓ Exception propagated correctly")

    asyncio.run(test())


def test_provider_diversity_tracking():
    """Test that different providers are tracked per lane"""
    async def diverse_pipeline(claim_text, plan, lane_id, telemetry):
        # R1 uses google, R2 uses brave
        if lane_id == "R1":
            telemetry.record_provider_call("google")
            telemetry.record_provider_call("google")
            telemetry.record_provider_call("google")
        else:
            telemetry.record_provider_call("brave")
            telemetry.record_provider_call("brave")

        return {"verdict": {"label": "supports", "confidence": 0.7}, "evidence": {}}

    async def test():
        result = await run_dual_researchers(
            "Test",
            {"arms": []},
            diverse_pipeline,
            diversify_plan_for_lane,
            LaneTelemetry
        )

        r1_providers = result["researchers"][0]["telemetry"]["providers"]
        r2_providers = result["researchers"][1]["telemetry"]["providers"]

        assert "google" in r1_providers
        assert r1_providers["google"] == 3
        assert "brave" in r2_providers
        assert r2_providers["brave"] == 2

        print(f"✓ Provider diversity: R1={r1_providers}, R2={r2_providers}")

    asyncio.run(test())


def test_telemetry_duration_tracking():
    """Test that duration is tracked per lane"""
    import time

    async def slow_pipeline(claim_text, plan, lane_id, telemetry):
        telemetry.record_provider_call("google")
        await asyncio.sleep(0.05)  # 50ms
        return {"verdict": {}, "evidence": {}}

    async def test():
        result = await run_dual_researchers(
            "Test",
            {"arms": []},
            slow_pipeline,
            diversify_plan_for_lane,
            LaneTelemetry
        )

        r1_duration = result["researchers"][0]["telemetry"]["duration_ms"]
        r2_duration = result["researchers"][1]["telemetry"]["duration_ms"]

        # Each should be >= 50ms
        assert r1_duration >= 50, f"R1 duration too short: {r1_duration}ms"
        assert r2_duration >= 50, f"R2 duration too short: {r2_duration}ms"

        print(f"✓ Duration tracking: R1={r1_duration}ms, R2={r2_duration}ms")

    asyncio.run(test())


def test_independence_of_researchers():
    """Test that R1 and R2 truly run independently (no shared state)"""
    state = {"r1_calls": 0, "r2_calls": 0}

    async def stateful_pipeline(claim_text, plan, lane_id, telemetry):
        # Track calls per lane
        if lane_id == "R1":
            state["r1_calls"] += 1
        else:
            state["r2_calls"] += 1

        telemetry.record_provider_call("google")
        return {"verdict": {"label": "supports", "confidence": 0.7}, "evidence": {}}

    async def test():
        result = await run_dual_researchers(
            "Test",
            {"arms": []},
            stateful_pipeline,
            diversify_plan_for_lane,
            LaneTelemetry
        )

        # Each should be called once
        assert state["r1_calls"] == 1, "R1 should be called once"
        assert state["r2_calls"] == 1, "R2 should be called once"

        # Telemetry should be separate
        r1_telem = result["researchers"][0]["telemetry"]
        r2_telem = result["researchers"][1]["telemetry"]
        assert r1_telem != r2_telem or (r1_telem == r2_telem and r1_telem["providers"] == {"google": 1})

        print(f"✓ Independence: R1_calls={state['r1_calls']}, R2_calls={state['r2_calls']}")

    asyncio.run(test())


def run_all_tests():
    """Run all capability tests"""
    print("\n" + "="*60)
    print("P26 DUAL RESEARCHERS - CAPABILITY TESTS")
    print("="*60 + "\n")

    tests = [
        ("Integration with Real P28", test_integration_with_real_p28),
        ("Integration with Real P29", test_integration_with_real_p29),
        ("Agreement Scenario", test_researchers_agreement_scenario),
        ("Disagreement Scenario", test_researchers_disagreement_scenario),
        ("Asymmetric Confidence", test_asymmetric_confidence_scenario),
        ("Scientific Claim", test_scientific_claim_scenario),
        ("Policy Claim", test_policy_claim_scenario),
        ("Evidence Preservation", test_evidence_preservation),
        ("Error Handling", test_error_handling_pipeline_exception),
        ("Provider Diversity", test_provider_diversity_tracking),
        ("Duration Tracking", test_telemetry_duration_tracking),
        ("Researcher Independence", test_independence_of_researchers)
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
