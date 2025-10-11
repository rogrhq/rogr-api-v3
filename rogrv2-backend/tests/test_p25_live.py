import asyncio, sys
sys.path.insert(0, '.')
from intelligence.pipeline.run import run_preview

async def test():
    result = await run_preview("Austin budget increased 8%")
    verdict = result['claims'][0].get('verdict', {})

    print(f"✓ label: {verdict.get('label')}")
    print(f"✓ confidence: {verdict.get('confidence')}")
    print(f"✓ arm_strength: {verdict.get('arm_strength')}")

    assert 'label' in verdict
    assert verdict['label'] in ['supports', 'challenges', 'mixed', 'insufficient']
    print("✓ P25 WORKING")
    print("✓ TEST PASSED")

asyncio.run(test())
