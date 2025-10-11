import asyncio, sys
sys.path.insert(0, '.')
from intelligence.pipeline.run import run_preview

async def test():
    print("="*60)
    print("DUAL RESEARCHERS LIVE TEST")
    print("="*60)

    result = await run_preview("Austin budget increased 8%")

    print("✓ Pipeline executed")

    # Check structure
    assert 'claims' in result
    assert 'diversified' in result
    assert result['diversified'] == True

    claim = result['claims'][0]
    researchers = claim.get('researchers', [])

    # Check researchers
    assert len(researchers) == 2, f"Expected 2, got {len(researchers)}"
    assert researchers[0]['id'] == 'R1'
    assert researchers[1]['id'] == 'R2'

    print(f"✓ R1: {researchers[0]['verdict']['label']}")
    print(f"✓ R2: {researchers[1]['verdict']['label']}")

    # Check diversification
    r1_providers = researchers[0]['lane_config']['providers']
    r2_providers = researchers[1]['lane_config']['providers']

    print(f"\nDiversification:")
    print(f"  R1 providers: {r1_providers}")
    print(f"  R2 providers: {r2_providers}")

    if r1_providers != r2_providers:
        print("  ✓ Different provider orders")

    # Check telemetry
    assert 'telemetry' in researchers[0]
    assert 'telemetry' in researchers[1]
    print(f"  ✓ Telemetry tracked")

    # Check backward compat
    assert 'verdict' in claim
    assert 'evidence' in claim
    print("  ✓ Backward compatibility")

    print("\n✓ DUAL RESEARCHERS WORKING")
    print("="*60)

asyncio.run(test())
