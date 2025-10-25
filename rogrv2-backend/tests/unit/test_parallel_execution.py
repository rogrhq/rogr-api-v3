"""
Unit tests for parallel researcher execution.

Tests that R1 and R2 run in parallel (not sequentially) using asyncio.gather().

Spec: Section 5.2.7
"""

import pytest
import asyncio
import time
from intelligence.orchestration.dual_lane import run_dual_researchers


@pytest.mark.asyncio
async def test_parallel_execution_timing():
    """Test that R1 and R2 run in parallel, not sequentially."""

    # Mock pipeline with artificial delay
    async def mock_pipeline(claim, plan, lane_id, telem):
        """Simulates a 2-second researcher run."""
        await asyncio.sleep(2)  # Simulate work
        return {
            "verdict": {"label": "supports" if lane_id == "R1" else "challenges", "confidence": 0.7},
            "evidence": {"arm_A": [{"url": f"test_{lane_id}_1"}], "arm_B": [{"url": f"test_{lane_id}_2"}]}
        }

    def mock_diversify(plan, lane_id, claim, providers):
        """Mock diversification."""
        return plan, {"lane_id": lane_id, "providers": providers, "seed": 123}

    class MockTelem:
        """Mock telemetry."""
        def __init__(self, lid):
            self.lane_id = lid

        def finalize(self):
            return {"providers": {}, "duration_ms": 2000}

    # Run dual researchers
    start_time = time.time()
    result = await run_dual_researchers(
        "Water boils at 100 degrees Celsius",
        {"arms": []},
        mock_pipeline,
        mock_diversify,
        MockTelem
    )
    elapsed = time.time() - start_time

    # If sequential: 2s + 2s = 4s
    # If parallel: max(2s, 2s) = ~2s
    # Allow 0.5s overhead for Python/async
    assert elapsed < 3.0, f"Took {elapsed:.2f}s - should be <3s if parallel (sequential would be 4s)"
    assert elapsed >= 2.0, f"Took {elapsed:.2f}s - sanity check failed (too fast)"

    # Verify both researchers completed
    assert len(result['researchers']) == 2
    assert result['researchers'][0]['id'] == 'R1'
    assert result['researchers'][1]['id'] == 'R2'


@pytest.mark.asyncio
async def test_parallel_execution_independence():
    """Test that R1 and R2 don't interfere with each other."""

    execution_order = []

    async def mock_pipeline(claim, plan, lane_id, telem):
        """Track execution order."""
        execution_order.append(f"{lane_id}_start")
        await asyncio.sleep(0.1)
        execution_order.append(f"{lane_id}_end")
        return {
            "verdict": {"label": "supports", "confidence": 0.7},
            "evidence": {"arm_A": [], "arm_B": []}
        }

    def mock_diversify(plan, lane_id, claim, providers):
        return plan, {"lane_id": lane_id}

    class MockTelem:
        def __init__(self, lid):
            pass
        def finalize(self):
            return {}

    result = await run_dual_researchers(
        "Test claim",
        {},
        mock_pipeline,
        mock_diversify,
        MockTelem
    )

    # If parallel, we should see interleaved execution:
    # ["R1_start", "R2_start", "R1_end", "R2_end"]
    # (or R2 could finish first)
    # NOT sequential: ["R1_start", "R1_end", "R2_start", "R2_end"]

    assert len(execution_order) == 4
    assert "R1_start" in execution_order
    assert "R2_start" in execution_order
    assert "R1_end" in execution_order
    assert "R2_end" in execution_order

    # Both should start before either finishes (parallel execution)
    r1_start_idx = execution_order.index("R1_start")
    r2_start_idx = execution_order.index("R2_start")
    r1_end_idx = execution_order.index("R1_end")
    r2_end_idx = execution_order.index("R2_end")

    # Both should start near the beginning
    assert r1_start_idx < 2, "R1 should start early"
    assert r2_start_idx < 2, "R2 should start early"

    # Both should end near the end
    assert r1_end_idx >= 2, "R1 should end late"
    assert r2_end_idx >= 2, "R2 should end late"


@pytest.mark.asyncio
async def test_exception_handling_r1_fails():
    """Test that R1 exception is properly raised."""

    async def mock_pipeline(claim, plan, lane_id, telem):
        """R1 raises exception, R2 succeeds."""
        if lane_id == "R1":
            raise ValueError("R1 intentional failure")
        return {
            "verdict": {"label": "supports", "confidence": 0.7},
            "evidence": {"arm_A": [], "arm_B": []}
        }

    def mock_diversify(plan, lane_id, claim, providers):
        return plan, {"lane_id": lane_id}

    class MockTelem:
        def __init__(self, lid):
            pass
        def finalize(self):
            return {}

    # Should raise ValueError from R1
    with pytest.raises(ValueError, match="R1 intentional failure"):
        await run_dual_researchers(
            "Test claim",
            {},
            mock_pipeline,
            mock_diversify,
            MockTelem
        )


@pytest.mark.asyncio
async def test_exception_handling_r2_fails():
    """Test that R2 exception is properly raised."""

    async def mock_pipeline(claim, plan, lane_id, telem):
        """R1 succeeds, R2 raises exception."""
        if lane_id == "R2":
            raise RuntimeError("R2 intentional failure")
        return {
            "verdict": {"label": "supports", "confidence": 0.7},
            "evidence": {"arm_A": [], "arm_B": []}
        }

    def mock_diversify(plan, lane_id, claim, providers):
        return plan, {"lane_id": lane_id}

    class MockTelem:
        def __init__(self, lid):
            pass
        def finalize(self):
            return {}

    # Should raise RuntimeError from R2
    with pytest.raises(RuntimeError, match="R2 intentional failure"):
        await run_dual_researchers(
            "Test claim",
            {},
            mock_pipeline,
            mock_diversify,
            MockTelem
        )


@pytest.mark.asyncio
async def test_both_researchers_complete():
    """Test that both researchers produce complete results."""

    async def mock_pipeline(claim, plan, lane_id, telem):
        """Return complete researcher results."""
        return {
            "verdict": {
                "label": "supports" if lane_id == "R1" else "challenges",
                "confidence": 0.8
            },
            "evidence": {
                "arm_A": [{"url": f"{lane_id}_a1"}, {"url": f"{lane_id}_a2"}],
                "arm_B": [{"url": f"{lane_id}_b1"}]
            }
        }

    def mock_diversify(plan, lane_id, claim, providers):
        return plan, {"lane_id": lane_id, "providers": []}

    class MockTelem:
        def __init__(self, lid):
            self.lane_id = lid
        def finalize(self):
            return {"providers": {}, "duration_ms": 100}

    result = await run_dual_researchers(
        "Water boils at 100°C",
        {"arms": []},
        mock_pipeline,
        mock_diversify,
        MockTelem
    )

    # Verify structure
    assert "researchers" in result
    assert len(result["researchers"]) == 2

    # Verify R1
    r1 = result["researchers"][0]
    assert r1["id"] == "R1"
    assert r1["verdict"]["label"] == "supports"
    assert r1["verdict"]["confidence"] == 0.8
    assert len(r1["evidence"]["arm_A"]) == 2
    assert len(r1["evidence"]["arm_B"]) == 1
    assert r1["lane_config"]["lane_id"] == "R1"
    assert "telemetry" in r1

    # Verify R2
    r2 = result["researchers"][1]
    assert r2["id"] == "R2"
    assert r2["verdict"]["label"] == "challenges"
    assert r2["verdict"]["confidence"] == 0.8
    assert len(r2["evidence"]["arm_A"]) == 2
    assert len(r2["evidence"]["arm_B"]) == 1
    assert r2["lane_config"]["lane_id"] == "R2"
    assert "telemetry" in r2

    # Verify backward compatibility
    assert result["verdict"]["label"] == "supports"  # R1's verdict
    assert result["evidence"]["arm_A"][0]["url"] == "R1_a1"  # R1's evidence


@pytest.mark.asyncio
async def test_performance_speedup():
    """Test that parallel execution provides ~2x speedup."""

    call_count = {"count": 0}

    async def mock_pipeline(claim, plan, lane_id, telem):
        """Track calls and simulate work."""
        call_count["count"] += 1
        await asyncio.sleep(1)
        return {
            "verdict": {"label": "supports", "confidence": 0.7},
            "evidence": {"arm_A": [], "arm_B": []}
        }

    def mock_diversify(plan, lane_id, claim, providers):
        return plan, {"lane_id": lane_id}

    class MockTelem:
        def __init__(self, lid):
            pass
        def finalize(self):
            return {}

    start = time.time()
    result = await run_dual_researchers(
        "Test",
        {},
        mock_pipeline,
        mock_diversify,
        MockTelem
    )
    elapsed = time.time() - start

    # Both researchers should be called
    assert call_count["count"] == 2

    # Should take ~1s (parallel), not ~2s (sequential)
    assert elapsed < 1.5, f"Took {elapsed:.2f}s - expected ~1s for parallel execution"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
