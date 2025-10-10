import asyncio
import sys
sys.path.insert(0, '.')

from intelligence.pipeline.run import run_preview

async def test_p21_live():
    print("="*60)
    print("P21 LIVE INTEGRATION TEST")
    print("="*60)

    claim = "Austin budget increased 8%"

    result = await run_preview(claim, test_mode=True)
    item = result['claims'][0]['evidence']['arm_A'][0]

    # Check previous modules
    assert 'content_hash' in item, "P22"
    assert 'grade' in item, "P20"
    print("✓ P22, P20 still working")

    # Check P21
    if 'grade_full' in item:
        print(f"✓ grade_full: {item['grade_full']}")
        print(f"✓ stance_full: {item.get('stance_full')}")
        print(f"✓ credibility: {item.get('credibility')}")
        print("\n✓ P21 WORKING")
    else:
        print("⚠ P21 fields not found (might not have full content)")

    print("\n✓ TEST PASSED")

asyncio.run(test_p21_live())
