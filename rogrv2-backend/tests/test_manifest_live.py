import asyncio, sys
sys.path.insert(0, '.')
from intelligence.pipeline.run import run_preview

async def test():
    result = await run_preview("Test claim")

    manifest = result.get('run_manifest', {})

    print(f"Replay ID: {manifest['replay_id'][:30]}...")
    print(f"Lanes: {list(manifest['lanes'].keys())}")

    assert 'replay_id' in manifest
    assert 'lanes' in manifest
    assert 'R1' in manifest['lanes']
    assert 'R2' in manifest['lanes']

    # Test determinism
    result2 = await run_preview("Test claim")
    assert manifest['replay_id'] == result2['run_manifest']['replay_id']
    print("✓ Deterministic")

    print("✓ MANIFEST WORKING")

asyncio.run(test())
