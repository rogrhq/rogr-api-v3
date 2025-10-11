import asyncio, sys
sys.path.insert(0, '.')
from intelligence.pipeline.run import run_preview

claims = [
    "Water boils at 100°C",
    "The sky is green",
    "Austin budget increased 8%",
    "Climate change is real",
    "Paris is in France"
]

async def test():
    print("Testing multiple claims...")

    for claim in claims:
        result = await run_preview(claim)
        c = result['claims'][0]

        print(f"\n{claim}")
        print(f"  R1: {c['researchers'][0]['verdict']['label']}")
        print(f"  R2: {c['researchers'][1]['verdict']['label']}")
        print(f"  Consensus: {c['consensus']['label']}")

    print("\n✓ ALL CLAIMS PROCESSED")

asyncio.run(test())
