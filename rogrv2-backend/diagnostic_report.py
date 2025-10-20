#!/usr/bin/env python3
"""Generate detailed diagnostic report showing where pipeline breaks down"""
import json
import sys

def diagnostic_report(result):
    """Generate detailed diagnostic report"""

    print("=" * 80)
    print("DIAGNOSTIC REPORT: PIPELINE DATA FLOW")
    print("=" * 80)

    # Overall verdict
    overall = result.get('overall', {})
    print(f"\n1. OVERALL VERDICT")
    print(f"   Label: {overall.get('label')}")
    print(f"   Score: {overall.get('score')}")
    if overall.get('score', 0) < 70:
        print(f"   ❌ ISSUE: Should be TRUE/high score for water boiling fact")
    else:
        print(f"   ✅ OK: High confidence verdict")

    # Claims
    claims = result.get('claims', [])
    if not claims:
        print("\n   ❌ CRITICAL: No claims in result")
        return

    claim = claims[0]

    # Classification
    print(f"\n2. CLAIM CLASSIFICATION (TASK 1.1)")
    classification = claim.get('classification', {})
    if classification:
        print(f"   Category: {classification.get('category')}")
        print(f"   Verifiability: {classification.get('verifiability')}")
        print(f"   ✅ Classification exists")
    else:
        print(f"   ❌ MISSING: No classification")

    # Evidence
    print(f"\n3. EVIDENCE GATHERING")
    evidence = claim.get('evidence', {})
    arm_a = evidence.get('arm_A', [])
    arm_b = evidence.get('arm_B', [])

    print(f"   Arm A (Support): {len(arm_a)} items")
    print(f"   Arm B (Challenge): {len(arm_b)} items")

    if not arm_a and not arm_b:
        print(f"   ❌ CRITICAL: No evidence found")
        return

    # Check each item in detail
    print(f"\n4. EVIDENCE ITEM ANALYSIS")

    issues = []
    total_items = len(arm_a) + len(arm_b)
    unrelated_count = 0
    zero_grade_count = 0
    low_cred_count = 0

    for i, item in enumerate(arm_a + arm_b, 1):
        arm_label = "A" if i <= len(arm_a) else "B"
        print(f"\n   Item {i} (Arm {arm_label}):")
        print(f"     Title: {item.get('title', 'NO TITLE')[:60]}")
        print(f"     Domain: {item.get('domain', 'NO DOMAIN')}")

        stance = item.get('stance', 'NO STANCE')
        grade = item.get('grade', 0)
        credibility = item.get('credibility', 0)

        print(f"     Stance: {stance}")
        print(f"     Grade: {grade}")
        print(f"     Credibility: {credibility:.3f}")

        # Check for issues
        if stance == 'unrelated':
            print(f"     ⚠️ ISSUE: Marked as unrelated")
            unrelated_count += 1
        elif stance == 'support':
            print(f"     ✅ Good stance")

        if grade == 0:
            print(f"     ❌ ISSUE: Grade is 0 (P20 fusion not working)")
            zero_grade_count += 1

        if credibility < 0.3:
            print(f"     ⚠️ ISSUE: Very low credibility")
            low_cred_count += 1

    # Researchers
    print(f"\n5. DUAL RESEARCHERS (TASK 2.1)")
    researchers = claim.get('researchers', [])
    if len(researchers) >= 2:
        print(f"   R1 (Skeptic):")
        r1 = researchers[0].get('verdict', {})
        print(f"     Label: {r1.get('label')}")
        print(f"     Confidence: {r1.get('confidence'):.3f}" if r1.get('confidence') else "     Confidence: MISSING")

        print(f"   R2 (Explorer):")
        r2 = researchers[1].get('verdict', {})
        print(f"     Label: {r2.get('label')}")
        print(f"     Confidence: {r2.get('confidence'):.3f}" if r2.get('confidence') else "     Confidence: MISSING")

        # Check agreement
        if r1.get('label') == r2.get('label'):
            print(f"   ✅ Researchers agree")
        else:
            print(f"   ⚠️ Researchers disagree")
    else:
        print(f"   ❌ ISSUE: Less than 2 researchers")

    # Consensus
    print(f"\n6. CONSENSUS (TASK 3.3)")
    consensus = claim.get('consensus', {})
    if consensus:
        print(f"   Label: {consensus.get('label')}")
        conf = consensus.get('confidence', 0)
        print(f"   Confidence: {conf:.3f}" if isinstance(conf, (int, float)) else f"   Confidence: {conf}")
        rationale = consensus.get('rationale', 'NO RATIONALE')
        if isinstance(rationale, dict):
            print(f"   Rationale: {str(rationale)[:100]}...")
        else:
            print(f"   Rationale: {rationale[:100]}...")
    else:
        print(f"   ❌ MISSING: No consensus")

    # Summary
    print(f"\n7. SUMMARY (TASK 15)")
    summary = claim.get('summary', '')
    if summary:
        print(f"   Length: {len(summary)} chars")
        print(f"   Preview: {summary[:150]}...")

        # Check for issues
        if "support:0" in summary:
            print(f"   ❌ ISSUE: Shows support:0 (no supporting evidence counted)")
        if "neutral:" in summary:
            # Extract neutral count
            import re
            match = re.search(r'neutral:(\d+)', summary)
            if match and int(match.group(1)) > 0:
                print(f"   ⚠️ ISSUE: Has neutral evidence (should be support/refute)")
    else:
        print(f"   ❌ MISSING: No summary")

    print(f"\n{'=' * 80}")
    print("ISSUE SUMMARY:")
    print("=" * 80)

    print(f"\n📊 Evidence Quality:")
    print(f"   Total items: {total_items}")
    print(f"   Unrelated: {unrelated_count}/{total_items} ({100*unrelated_count/total_items if total_items else 0:.1f}%)")
    print(f"   Zero grade: {zero_grade_count}/{total_items} ({100*zero_grade_count/total_items if total_items else 0:.1f}%)")
    print(f"   Low credibility: {low_cred_count}/{total_items} ({100*low_cred_count/total_items if total_items else 0:.1f}%)")

    print(f"\n🔍 Root Causes:")

    if zero_grade_count == total_items:
        print(f"   ❌ CRITICAL: All grades are 0 → P20 fusion formula not executing")
        print(f"      Location: intelligence/content/grade.py:fuse_module_grades()")

    if unrelated_count >= total_items * 0.8:
        print(f"   ❌ CRITICAL: Most evidence marked 'unrelated' → Semantic analysis broken")
        print(f"      Location: intelligence/content/semantic_read.py:analyze_item()")

    if low_cred_count >= total_items * 0.8:
        print(f"   ❌ CRITICAL: Low credibility across board → Authority scoring broken")
        print(f"      Location: intelligence/content/authority.py or P21")

    if overall.get('score', 0) < 70:
        print(f"   ❌ CRITICAL: Wrong verdict → Consensus not using evidence properly")
        print(f"      Location: intelligence/consensus/dual_lane.py:compute_consensus()")

    print(f"\n📋 Next Steps:")
    print(f"   1. Check if P20 fusion formula (fuse_module_grades) is being called")
    print(f"   2. Check if semantic_read (analyze_item) is being called")
    print(f"   3. Check if stance detection is working correctly")
    print(f"   4. Verify authority scoring is computing credibility")
    print(f"   5. Trace consensus calculation with evidence")

if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'diagnostic_result.json'

    try:
        with open(input_file, 'r') as f:
            result = json.load(f)
        diagnostic_report(result)
    except FileNotFoundError:
        print(f"❌ Error: File '{input_file}' not found")
        print(f"Run the diagnostic test first to generate the result file")
        sys.exit(1)
