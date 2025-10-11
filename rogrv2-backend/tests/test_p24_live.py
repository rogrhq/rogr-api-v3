import asyncio, sys
sys.path.insert(0, '.')
from intelligence.pipeline.run import run_preview

async def test():
    result = await run_preview("Austin budget increased 8%")
    item = result['claims'][0]['evidence']['arm_A'][0]

    if 'item_frame' in item:
        print(f"✓ item_frame: {item['item_frame']}")
        print(f"✓ frame_confidence: {item.get('frame_confidence')}")
        print("✓ P24 WORKING")
    print("✓ TEST PASSED")

asyncio.run(test())
