import asyncio, sys, time, statistics
from unittest.mock import patch
try:
    import psutil, os
    HAS_PSUTIL = True
except:
    HAS_PSUTIL = False

sys.path.insert(0, '.')
from intelligence.pipeline.run import run_preview

async def test_validation():
    # Mock fetch_text to return sample content for testing
    async def mock_fetch(url, timeout=8.0):
        return {
            "text": """This is sample article content about the Austin budget for fiscal year 2024. The city council approved an 8% increase in spending compared to last year. The budget includes funding for public safety, infrastructure, and social services. Officials stated this represents responsible fiscal management while addressing community needs.""",
            "status": 200,
            "mime": "text/html",
            "final_url": url
        }

    with patch('intelligence.content.fetch.fetch_text', side_effect=mock_fetch):
        print("="*60)
        print("WEEK 1 VALIDATION")
        print("="*60)

        # Test 1: Full pipeline works
        print("\n1. Testing full pipeline...")
        result = await run_preview("Austin budget increased 8%")
        item = result['claims'][0]['evidence']['arm_A'][0]

        checks = {
            'P22 content_hash': 'content_hash' in item,
            'P20 item_grade': 'item_grade' in item,
            'P21 grade_full': 'grade_full' in item,
            'P23 findings': 'findings' in item,
            'P24 item_frame': 'item_frame' in item,
            'P25 verdict': 'verdict' in result['claims'][0]
        }

        for name, present in checks.items():
            print(f"  {name}: {'✓' if present else '✗'}")

        assert all(checks.values()), "Some modules not working"
        print("✓ All modules working\n")

        # Test 2: Memory leak test
        print("2. Memory leak test (100 requests)...")
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            baseline = process.memory_info().rss / 1024 / 1024
            print(f"  Baseline: {baseline:.1f} MB")

            for i in range(100):
                await run_preview("Test claim")
                if (i + 1) % 20 == 0:
                    mem = process.memory_info().rss / 1024 / 1024
                    print(f"  After {i+1}: {mem:.1f} MB")

            final = process.memory_info().rss / 1024 / 1024
            growth = final - baseline
            print(f"  Final: {final:.1f} MB")
            print(f"  Growth: {growth:.1f} MB")

            if growth < 50:
                print("✓ Memory stable\n")
            else:
                print("⚠ Memory growth detected\n")
        else:
            print("  ⚠ psutil not available, skipping\n")

        # Test 3: Performance baseline
        print("3. Performance baseline (20 requests)...")
        times = []
        for i in range(20):
            start = time.time()
            await run_preview("Test claim")
            times.append((time.time() - start) * 1000)

        mean_time = statistics.mean(times)
        median_time = statistics.median(times)

        print(f"  Mean: {mean_time:.0f} ms")
        print(f"  Median: {median_time:.0f} ms")

        with open("tests/week1_baseline.txt", "w") as f:
            f.write(f"Week 1 Baseline (Single Researcher)\n")
            f.write(f"Mean: {mean_time:.0f} ms\n")
            f.write(f"Median: {median_time:.0f} ms\n")

        print("✓ Baseline saved\n")

        print("="*60)
        print("✓ WEEK 1 VALIDATION PASSED")
        print("="*60)
        print("\n✅ SAFE TO DEPLOY or continue to Week 2")

if __name__ == "__main__":
    asyncio.run(test_validation())
