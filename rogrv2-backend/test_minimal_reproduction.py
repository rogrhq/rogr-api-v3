"""
Minimal reproduction case for integration test deadlock.

Tests whether the deadlock is:
- asyncio + ML models issue (script hangs)
- pytest async handling issue (script works, pytest hangs)
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from dotenv import load_dotenv
load_dotenv(override=True)

import asyncio
import sys
import time

print("=" * 70)
print("MINIMAL REPRODUCTION TEST")
print("=" * 70)

print("\n1. Testing model loading...")
start = time.time()
from intelligence.content.shared.embeddings import get_embeddings
embeddings = get_embeddings()
print(f"   ✓ Models loaded in {time.time() - start:.2f}s")

print("\n2. Testing pipeline import...")
start = time.time()
from intelligence.pipeline.run import run_preview
print(f"   ✓ Pipeline imported in {time.time() - start:.2f}s")

print("\n3. Running pipeline with parallel R1/R2...")
claim_text = "Water boils at 100 degrees Celsius"

async def test_pipeline():
    """Run the full pipeline."""
    print(f"   Starting pipeline: {claim_text}")
    start = time.time()

    try:
        result = await run_preview(claim_text, test_mode=False)
        elapsed = time.time() - start
        print(f"   ✓ Pipeline completed in {elapsed:.1f}s")

        # Extract basic info
        if "claims" in result and len(result["claims"]) > 0:
            claim_result = result["claims"][0]
            verdict = claim_result.get("verdict", {})
            evidence = claim_result.get("evidence", {})

            print(f"\n4. Results:")
            print(f"   Verdict: {verdict.get('label', 'unknown')} (confidence: {verdict.get('confidence', 0):.2f})")
            print(f"   Arm A items: {len(evidence.get('arm_A', []))}")
            print(f"   Arm B items: {len(evidence.get('arm_B', []))}")

            return True
        else:
            print(f"   ✗ No claims in result")
            return False

    except Exception as e:
        elapsed = time.time() - start
        print(f"   ✗ Pipeline failed after {elapsed:.1f}s: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n   Starting async event loop...")

    # Run with a timeout to detect hangs
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Set a 3-minute timeout
        task = loop.create_task(test_pipeline())
        result = loop.run_until_complete(asyncio.wait_for(task, timeout=180))

        if result:
            print("\n" + "=" * 70)
            print("✓ MINIMAL REPRODUCTION TEST PASSED")
            print("=" * 70)
            sys.exit(0)
        else:
            print("\n" + "=" * 70)
            print("✗ MINIMAL REPRODUCTION TEST FAILED")
            print("=" * 70)
            sys.exit(1)

    except asyncio.TimeoutError:
        print("\n" + "=" * 70)
        print("✗ TIMEOUT: Pipeline hung for 3 minutes")
        print("=" * 70)
        print("\nDEADLOCK CONFIRMED: asyncio + ML models issue")
        sys.exit(2)

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)

    finally:
        loop.close()
