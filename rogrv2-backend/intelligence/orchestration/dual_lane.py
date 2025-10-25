from typing import Dict, Any, Callable, Type
import asyncio
import logging

LOG = logging.getLogger(__name__)

async def run_dual_researchers(
    claim_text: str,
    base_plan: Dict[str, Any],
    enrichment_pipeline: Callable,
    diversify_fn: Callable,
    telemetry_class: Type
) -> Dict[str, Any]:
    """
    Orchestrate R1 and R2 independent runs in parallel.

    Args:
        claim_text: Claim being fact-checked
        base_plan: Base search plan
        enrichment_pipeline: async def(claim_text, plan, lane_id, telemetry) -> Dict
        diversify_fn: def(plan, lane_id, claim, providers) -> Tuple[plan, config]
        telemetry_class: LaneTelemetry class

    Returns:
        {
            "researchers": [R1_result, R2_result],
            "verdict": R1_verdict,  # backward compat
            "evidence": R1_evidence  # backward compat
        }
    """

    # Get available providers
    from intelligence.planning.diversify import get_available_providers
    providers = get_available_providers()

    # Diversify plans
    r1_plan, r1_config = diversify_fn(base_plan, "R1", claim_text, providers)
    r2_plan, r2_config = diversify_fn(base_plan, "R2", claim_text, providers)

    LOG.info("🔀 Starting parallel researcher execution...")

    # Create telemetry objects
    r1_telemetry = telemetry_class("R1")
    r2_telemetry = telemetry_class("R2")

    # Run R1 and R2 in parallel using asyncio.gather()
    r1_task = enrichment_pipeline(claim_text, r1_plan, "R1", r1_telemetry)
    r2_task = enrichment_pipeline(claim_text, r2_plan, "R2", r2_telemetry)

    # Wait for both to complete, capturing exceptions
    results = await asyncio.gather(r1_task, r2_task, return_exceptions=True)

    # Handle R1 result
    r1_result = results[0]
    if isinstance(r1_result, Exception):
        LOG.error(f"❌ R1 failed: {r1_result}")
        raise r1_result

    # Handle R2 result
    r2_result = results[1]
    if isinstance(r2_result, Exception):
        LOG.error(f"❌ R2 failed: {r2_result}")
        raise r2_result

    # Finalize telemetry after both complete
    r1_telemetry_data = r1_telemetry.finalize()
    r2_telemetry_data = r2_telemetry.finalize()

    LOG.info(f"✅ Parallel execution complete")
    LOG.info(f"   R1: {len(r1_result.get('evidence', {}).get('arm_A', []) + r1_result.get('evidence', {}).get('arm_B', []))} items")
    LOG.info(f"   R2: {len(r2_result.get('evidence', {}).get('arm_A', []) + r2_result.get('evidence', {}).get('arm_B', []))} items")

    # Build researcher objects
    researchers = [
        {
            "id": "R1",
            "verdict": r1_result.get("verdict", {}),
            "evidence": r1_result.get("evidence", {}),
            "lane_config": r1_config,
            "telemetry": r1_telemetry_data
        },
        {
            "id": "R2",
            "verdict": r2_result.get("verdict", {}),
            "evidence": r2_result.get("evidence", {}),
            "lane_config": r2_config,
            "telemetry": r2_telemetry_data
        }
    ]

    # Backward compatibility
    return {
        "researchers": researchers,
        "verdict": r1_result.get("verdict", {}),
        "evidence": r1_result.get("evidence", {})
    }

def merge_r1_r2_results(r1: Dict, r2: Dict) -> Dict:
    """Merge R1 and R2 (backward compat helper)."""
    return {
        "researchers": [r1, r2],
        "verdict": r1.get("verdict", {}),
        "evidence": r1.get("evidence", {})
    }

# TEST with mocks
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

    import asyncio

    async def mock_pipeline(claim, plan, lane_id, telem):
        return {
            "verdict": {"label": "supports" if lane_id == "R1" else "challenges", "confidence": 0.7},
            "evidence": {"arm_A": [], "arm_B": []}
        }

    def mock_diversify(plan, lane_id, claim, providers):
        return plan, {"lane_id": lane_id, "providers": providers, "seed": 123}

    class MockTelem:
        def __init__(self, lid):
            pass
        def finalize(self):
            return {"providers": {}, "duration_ms": 100}

    async def test():
        result = await run_dual_researchers(
            "Test", {"arms": []}, mock_pipeline, mock_diversify, MockTelem
        )
        assert len(result['researchers']) == 2
        assert result['researchers'][0]['id'] == 'R1'
        print(f"R1: {result['researchers'][0]['verdict']['label']}")
        print(f"R2: {result['researchers'][1]['verdict']['label']}")
        print("✓ PASS")

    asyncio.run(test())
