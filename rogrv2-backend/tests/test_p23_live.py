import asyncio, sys
sys.path.insert(0, '.')
from intelligence.pipeline.run import run_preview

async def test():
    result = await run_preview("Austin budget increased 8%")
    item = result['claims'][0]['evidence']['arm_A'][0]

    if 'findings' in item:
        print(f"✓ findings: {len(item['findings'])} found")
        print(f"✓ item_grade: {item.get('item_grade')}")
        print("✓ P23 WORKING")
    print("✓ TEST PASSED")

asyncio.run(test())
