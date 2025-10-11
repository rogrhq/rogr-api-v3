import asyncio, sys, time
sys.path.insert(0, '.')
from intelligence.pipeline.run import run_preview

async def test():
    print("Load test (100 requests)...")

    start = time.time()

    for i in range(100):
        await run_preview("Test claim")
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/100...")

    elapsed = time.time() - start

    print(f"\n✓ Completed 100 requests in {elapsed:.1f}s")
    print(f"✓ Throughput: {100/elapsed:.2f} req/s")

asyncio.run(test())
