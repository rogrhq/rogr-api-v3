import asyncio, sys
sys.path.insert(0, '.')
from intelligence.pipeline.run import run_preview

async def test():
    result = await run_preview("Water boils at 100°C")

    claim = result['claims'][0]
    consensus = claim.get('consensus', {})

    print(f"R1: {claim['researchers'][0]['verdict']['label']}")
    print(f"R2: {claim['researchers'][1]['verdict']['label']}")
    print(f"Consensus: {consensus['label']}")
    print(f"Rule: {consensus['rationale']['rule']}")

    assert 'label' in consensus
    assert 'confidence' in consensus
    assert 'rationale' in consensus

    print("✓ CONSENSUS WORKING")

asyncio.run(test())
