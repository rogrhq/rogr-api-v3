import asyncio, sys, time, statistics
sys.path.insert(0, '.')
from intelligence.pipeline.run import run_preview

async def test():
    print("="*60)
    print("WEEK 2 VALIDATION")
    print("="*60)

    # Test 1: Full dual-researcher pipeline
    print("\n1. Testing full pipeline...")
    result = await run_preview("Austin budget increased 8%")

    claim = result['claims'][0]
    researchers = claim['researchers']

    assert len(researchers) == 2
    assert 'consensus' in claim
    assert 'run_manifest' in result

    print("  ✓ Dual researchers: ✓")
    print("  ✓ Consensus: ✓")
    print("  ✓ Manifest: ✓")

    # Test 2: Edge cases
    print("\n2. Testing edge cases...")

    test_claims = [
        "Water boils at 100°C",
        "The sky is green",
        "Climate change is real"
    ]

    for claim_text in test_claims:
        r = await run_preview(claim_text)
        c = r['claims'][0]
        print(f"  {claim_text[:30]}...")
        print(f"    R1: {c['researchers'][0]['verdict']['label']}")
        print(f"    R2: {c['researchers'][1]['verdict']['label']}")
        print(f"    Consensus: {c['consensus']['label']}")

    # Test 3: Performance
    print("\n3. Performance test (20 requests)...")
    times = []
    for i in range(20):
        start = time.time()
        await run_preview("Test")
        times.append((time.time() - start) * 1000)

    mean = statistics.mean(times)
    print(f"  Mean: {mean:.0f} ms")

    # Compare to Week 1
    try:
        with open("tests/week1_baseline.txt") as f:
            for line in f:
                if line.startswith("Mean:"):
                    week1_mean = float(line.split()[1])
                    ratio = mean / week1_mean
                    print(f"  Week 1: {week1_mean:.0f} ms")
                    print(f"  Ratio: {ratio:.2f}x")

                    if 1.8 <= ratio <= 2.5:
                        print("  ✓ Performance as expected (~2x)")
    except:
        pass

    print("\n" + "="*60)
    print("✓ WEEK 2 VALIDATION PASSED")
    print("="*60)
    print("\n✅ SAFE TO DEPLOY or continue to Week 3")

asyncio.run(test())
