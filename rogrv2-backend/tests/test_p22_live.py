import asyncio
import sys
sys.path.insert(0, '.')

from intelligence.pipeline.run import run_preview

async def test_p22_live():
    print("="*60)
    print("P22 LIVE INTEGRATION TEST")
    print("="*60)

    claim = "Austin budget increased 8%"
    print(f"\nTesting claim: {claim}")

    try:
        result = await run_preview(claim, test_mode=True)

        print("✓ Pipeline executed successfully")

        # Check structure
        assert 'claims' in result, "Missing claims"
        claims = result.get('claims', [])
        assert len(claims) > 0, "No claims returned"

        claim_obj = claims[0]
        evidence = claim_obj.get('evidence', {})

        # Check arms exist
        arm_a = evidence.get('arm_A', [])
        arm_b = evidence.get('arm_B', [])

        print(f"✓ Arm A: {len(arm_a)} items")
        print(f"✓ Arm B: {len(arm_b)} items")

        # Check P22 enrichment
        if len(arm_a) > 0:
            item = arm_a[0]

            has_content_hash = 'content_hash' in item
            has_coverage = 'coverage' in item
            has_content = 'content' in item or 'content_excerpt' in item

            print(f"\nP22 Enrichment Check (Arm A, item 0):")
            print(f"  content_hash: {'✓' if has_content_hash else '✗ MISSING'}")
            print(f"  coverage: {'✓' if has_coverage else '✗ MISSING'}")
            print(f"  content: {'✓' if has_content else '✗ MISSING'}")

            if has_coverage:
                print(f"  coverage value: {item['coverage']}")

            # Assertions
            assert has_content_hash, "P22 should add content_hash"
            assert has_coverage, "P22 should add coverage"
            assert item['coverage'] in ['full', 'partial', 'snippet_only'], f"Invalid coverage: {item['coverage']}"

            print("\n✓ P22 ENRICHMENT WORKING")
        else:
            print("\n⚠ No Arm A items (might be normal for some claims)")

        print("\n" + "="*60)
        print("✓ P22 LIVE INTEGRATION TEST PASSED")
        print("="*60)

    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_p22_live())
