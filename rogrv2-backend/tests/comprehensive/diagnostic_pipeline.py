"""
Pipeline Diagnostic Tool
Tests pipeline step-by-step to identify failures
"""

import sys
import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("="*70)
print("PIPELINE DIAGNOSTIC")
print("="*70)
print()

# Test 1: Import pipeline
print("[1/7] Testing pipeline import...")
try:
    from intelligence.pipeline.run import run_preview
    print("  ✓ Pipeline imported successfully")
except Exception as e:
    print(f"  ✗ FAILED to import pipeline: {e}")
    sys.exit(1)

print()

# Test 2: Simple claim test
print("[2/7] Testing simple claim through pipeline...")
test_claim = "Water boils at 100 degrees Celsius at sea level"
print(f"  Claim: {test_claim}")

async def test_pipeline():
    try:
        result = await run_preview(test_claim)
        print("  ✓ Pipeline executed without error")
        return result
    except Exception as e:
        print(f"  ✗ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None

result = asyncio.run(test_pipeline())

if result is None:
    print("\n❌ CRITICAL: Pipeline failed to execute")
    sys.exit(1)

print()

# Test 3: Check result structure
print("[3/7] Analyzing result structure...")
print(f"  Result type: {type(result)}")
print(f"  Top-level keys: {list(result.keys()) if isinstance(result, dict) else 'NOT A DICT'}")

if not isinstance(result, dict):
    print("  ✗ Result is not a dictionary!")
    sys.exit(1)

print("  ✓ Result is a dictionary")
print()

# Test 4: Check consensus
print("[4/7] Checking consensus...")
consensus = result.get('consensus', {})
print(f"  Consensus exists: {bool(consensus)}")
print(f"  Consensus type: {type(consensus)}")

if consensus:
    print(f"  Consensus keys: {list(consensus.keys())}")
    label = consensus.get('label', 'MISSING')
    confidence = consensus.get('confidence', -1)
    print(f"  Label: {label}")
    print(f"  Confidence: {confidence}")

    if label == 'UNKNOWN' or confidence == 0.0:
        print("  ⚠️  WARNING: Consensus returned UNKNOWN/0.0")
else:
    print("  ✗ No consensus in result")

print()

# Test 5: Check researchers
print("[5/7] Checking researchers...")
researchers = result.get('researchers', [])
print(f"  Number of researchers: {len(researchers)}")

if researchers:
    for i, researcher in enumerate(researchers, 1):
        print(f"\n  Researcher {i}:")
        print(f"    Keys: {list(researcher.keys())}")
        verdict = researcher.get('verdict', {})
        print(f"    Verdict: {verdict.get('label', 'MISSING')}")
        print(f"    Confidence: {verdict.get('confidence', -1)}")
        evidence = researcher.get('evidence', {})
        print(f"    Evidence arms: {list(evidence.keys()) if isinstance(evidence, dict) else 'NONE'}")
        if isinstance(evidence, dict):
            arm_a = evidence.get('arm_A', [])
            arm_b = evidence.get('arm_B', [])
            print(f"    Arm A items: {len(arm_a)}")
            print(f"    Arm B items: {len(arm_b)}")
else:
    print("  ✗ No researchers in result")

print()

# Test 6: Full result dump
print("[6/7] Full result structure:")
print("="*70)
print(json.dumps(result, indent=2, default=str))
print("="*70)
print()

# Test 7: Summary
print("[7/7] DIAGNOSTIC SUMMARY")
print("="*70)

issues = []
warnings = []

if not result:
    issues.append("Pipeline returned None/empty result")
elif not isinstance(result, dict):
    issues.append("Pipeline returned non-dict result")
else:
    # Check consensus
    if not consensus:
        issues.append("Missing consensus in result")
    elif consensus.get('label') == 'UNKNOWN':
        warnings.append(f"Consensus label is UNKNOWN")
    elif consensus.get('confidence', 0) == 0.0:
        warnings.append(f"Consensus confidence is 0.0")

    # Check researchers
    if not researchers:
        issues.append("No researchers in result")
    elif len(researchers) < 2:
        warnings.append(f"Only {len(researchers)} researcher (expected 2)")

    # Check evidence
    has_evidence = False
    for researcher in researchers:
        evidence = researcher.get('evidence', {})
        if isinstance(evidence, dict):
            arm_a = evidence.get('arm_A', [])
            arm_b = evidence.get('arm_B', [])
            if arm_a or arm_b:
                has_evidence = True
                break

    if not has_evidence:
        warnings.append("No evidence found in any researcher")

if issues:
    print("\n❌ CRITICAL ISSUES:")
    for issue in issues:
        print(f"  - {issue}")

if warnings:
    print("\n⚠️  WARNINGS:")
    for warning in warnings:
        print(f"  - {warning}")

if not issues and not warnings:
    print("\n✓ All checks passed! Pipeline appears to be working correctly.")
elif not issues:
    print("\n⚠️  Pipeline is working but with warnings.")
else:
    print("\n❌ Pipeline has critical issues that need fixing.")

print()
