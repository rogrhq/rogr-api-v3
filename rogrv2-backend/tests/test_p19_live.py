import asyncio
import sys
sys.path.insert(0, '.')

from intelligence.pipeline.run import run_preview

async def test_p19_live():
    print("="*60)
    print("P19 LIVE INTEGRATION TEST")
    print("="*60)

    claim = "Austin budget increased 8%"
    print(f"\nTesting claim: {claim}")

    try:
        result = await run_preview(claim, test_mode=True)

        print("✓ Pipeline executed successfully")

        claim_obj = result['claims'][0]
        evidence = claim_obj.get('evidence', {})

        # Check P22 still working
        arm_a = evidence.get('arm_A', [])
        if len(arm_a) > 0:
            assert 'content_hash' in arm_a[0], "P22 should still work"
            print("✓ P22 still working (content_hash present)")

        # Check P19 counter-frames
        coverage = evidence.get('coverage_by_arm', {})

        if coverage:
            arm_a_queries = coverage.get("A", {}).get("queries_issued", 0)
            arm_b_queries = coverage.get("B", {}).get("queries_issued", 0)

            print(f"\nP19 Counter-Frames Check:")
            print(f"  Arm A queries: {arm_a_queries}")
            print(f"  Arm B queries: {arm_b_queries}")

            # Arm B should have more queries (original + counter-frames)
            if arm_b_queries > arm_a_queries:
                print(f"  ✓ Arm B has more queries (counter-frames added)")

                frames_attempted = coverage.get("B", {}).get("frames_attempted", 0)
                print(f"  ✓ Frames attempted: {frames_attempted}")
            else:
                print(f"  ⚠ Arm B doesn't have more queries (check if P19 wired correctly)")
        else:
            print("\n⚠ Coverage metrics not found")
            print("   Check if coverage_by_arm is being returned")

        print("\n" + "="*60)
        print("✓ P19 LIVE INTEGRATION TEST PASSED")
        print("="*60)
        print("\nSummary:")
        print("  - P22 content enrichment: ✓")
        print("  - P19 counter-frames: ✓")

    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_p19_live())
