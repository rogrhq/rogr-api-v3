"""
Complete Pipeline Diagnostic Test

Shows EVERY step of the pipeline with actual data at each stage.
Use this to diagnose ANY pipeline issue.

Based on verified function names from ACTUAL_PIPELINE_STRUCTURE.md
"""

import asyncio
import json
import sys
from typing import Dict, Any
from datetime import datetime

# Create timestamped output file
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_filename = f'docs/pipeline_diagnostics/diagnostic_{timestamp}.md'
output_file = open(output_filename, 'w')
sys.stdout = output_file

# Print header with timestamp
print(f"# Pipeline Diagnostic Report")
print(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"**Output File:** {output_filename}")
print("")


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)


def print_subsection(title: str):
    """Print formatted subsection"""
    print(f"\n--- {title} ---")


def truncate(text: str, max_len: int = 100) -> str:
    """Truncate text for display"""
    if not text:
        return ""
    text = str(text)
    return text[:max_len] + "..." if len(text) > max_len else text


async def diagnose_complete_pipeline(claim_text: str):
    """
    Trace complete pipeline execution showing every step.

    Stages:
    1. Claim enrichment
    2. Base plan generation
    3. Query diversification (R1/R2)
    4. Evidence gathering
    5. Content fetching
    6. Evidence grading (P21, P23, P24 fusion)
    7. Verdict aggregation (P25)
    8. Consensus (R1 + R2)
    9. Final output
    """

    print_section("COMPLETE PIPELINE DIAGNOSTIC")
    print(f"Claim: {claim_text}")

    # ========================================================================
    # STAGE 1: CLAIM ENRICHMENT
    # ========================================================================
    print_section("STAGE 1: CLAIM ENRICHMENT")

    from intelligence.analyze.enrich import enrich_claim_obj

    claim = {"text": claim_text}
    enriched_claim = enrich_claim_obj(claim)

    print(f"Input: {claim}")
    print(f"\nEnriched claim fields: {list(enriched_claim.keys())}")
    print(f"  text: {enriched_claim.get('text')}")
    print(f"  entities: {enriched_claim.get('entities', [])}")
    print(f"  numbers: {enriched_claim.get('numbers', {})}")
    print(f"  concept: {enriched_claim.get('concept', 'MISSING')}")
    print(f"  dimension: {enriched_claim.get('dimension', 'MISSING')}")
    print(f"  cues: {enriched_claim.get('cues', {})}")
    print(f"  kind_hint: {enriched_claim.get('kind_hint', 'MISSING')}")

    # ========================================================================
    # STAGE 2: BASE PLAN GENERATION
    # ========================================================================
    print_section("STAGE 2: BASE PLAN GENERATION (build_search_plans_v2)")

    from intelligence.strategy.plan_v2 import build_search_plans_v2

    base_plan = build_search_plans_v2(enriched_claim)

    print(f"Base plan version: {base_plan.get('version')}")
    print(f"Base plan meta: {base_plan.get('meta', {})}")

    print_subsection("Arm A (Support-seeking) Queries")
    arm_a_queries = base_plan.get('arms', {}).get('A', {}).get('queries', [])
    for i, q in enumerate(arm_a_queries, 1):
        print(f"  {i}. {q}")

    print_subsection("Arm B (Challenge-seeking) Queries")
    arm_b_queries = base_plan.get('arms', {}).get('B', {}).get('queries', [])
    for i, q in enumerate(arm_b_queries, 1):
        print(f"  {i}. {q}")

    # ========================================================================
    # STAGE 3: QUERY DIVERSIFICATION (R1/R2)
    # ========================================================================
    print_section("STAGE 3: QUERY DIVERSIFICATION (R1/R2)")

    from intelligence.planning.diversify import diversify_plan_for_lane

    # Get available providers from environment
    import os
    providers = []
    if os.getenv("BRAVE_API_KEY"):
        providers.append("brave")
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_SEARCH_API_KEY"):
        providers.append("google")

    print(f"Available providers: {providers}")

    # R1 diversification
    print_subsection("R1 (Precision) Queries")
    r1_plan, r1_preview = diversify_plan_for_lane(base_plan, "R1", claim_text, providers)

    print(f"R1 strategy: {r1_preview.get('strategy')}")
    print(f"R1 providers: {r1_preview.get('providers')}")

    # Arms returned as LIST format: [{"name": "A", ...}, {"name": "B", ...}]
    r1_arms_list = r1_plan.get('arms', [])
    for arm in r1_arms_list:
        arm_name = arm.get('name')
        queries = arm.get('queries', [])
        intent = arm.get('intent', '')

        print(f"  Arm {arm_name} ({intent}): {len(queries)} queries")
        for i, q in enumerate(queries[:3], 1):
            print(f"    {i}. {q}")

    # R2 diversification
    print_subsection("R2 (Recall) Queries")
    r2_plan, r2_preview = diversify_plan_for_lane(base_plan, "R2", claim_text, providers)

    print(f"R2 strategy: {r2_preview.get('strategy')}")
    print(f"R2 providers: {r2_preview.get('providers')}")

    # Arms returned as LIST format: [{"name": "A", ...}, {"name": "B", ...}]
    r2_arms_list = r2_plan.get('arms', [])
    for arm in r2_arms_list:
        arm_name = arm.get('name')
        queries = arm.get('queries', [])
        intent = arm.get('intent', '')

        print(f"  Arm {arm_name} ({intent}): {len(queries)} queries")
        for i, q in enumerate(queries[:3], 1):
            print(f"    {i}. {q}")

    # ========================================================================
    # STAGE 4-9: FULL PIPELINE EXECUTION
    # ========================================================================
    print_section("STAGE 4-9: FULL PIPELINE EXECUTION")

    from intelligence.pipeline.run import run_preview

    print("Running complete pipeline with both researchers...")
    print("This includes:")
    print("  - Evidence gathering (P19)")
    print("  - Content fetching (P22)")
    print("  - Grading (P20: P21+P23+P24 fusion)")
    print("  - Aggregation (P25)")
    print("  - Consensus")

    result = await run_preview(claim_text, test_mode=False)

    claims = result.get("claims", [])
    if not claims:
        print("\n❌ No claims returned from pipeline")
        return

    claim_result = claims[0]
    researchers = claim_result.get("researchers", [])

    # ========================================================================
    # STAGE 5: RESEARCHER RESULTS
    # ========================================================================
    print_section("STAGE 5: RESEARCHER RESULTS")

    for researcher in researchers:
        lane_id = researcher.get("lane_id", "UNKNOWN")

        print_subsection(f"{lane_id} Results")

        # Verdict
        r_verdict = researcher.get("verdict", {})
        print(f"  Verdict: {r_verdict.get('label', 'MISSING')}")
        print(f"  Confidence: {r_verdict.get('confidence', 0):.3f}")
        print(f"  Arm strength: {r_verdict.get('arm_strength', {})}")

        # Evidence counts
        evidence = researcher.get("evidence", {})
        arm_a_items = evidence.get("arm_A", [])
        arm_b_items = evidence.get("arm_B", [])

        print(f"  Evidence items: {len(arm_a_items)} arm_A, {len(arm_b_items)} arm_B")

        # Analyze first item in detail
        if arm_a_items:
            print_subsection(f"{lane_id} - First Arm A Item Details")
            item = arm_a_items[0]

            print(f"    Title: {truncate(item.get('title', 'MISSING'), 60)}")
            print(f"    URL: {truncate(item.get('url', 'MISSING'), 60)}")
            print(f"    Domain: {item.get('domain', 'MISSING')}")
            print(f"    Coverage: {item.get('coverage', 'MISSING')}")
            print(f"    Item grade: {item.get('item_grade', 'MISSING')}")
            print(f"    Stance: {item.get('stance', 'MISSING')}")

            # Check for quote field
            has_quote = 'quote' in item
            print(f"    Has top-level quote field: {has_quote}")

            # Check finding structure
            finding = item.get('finding', {})
            if finding:
                features = finding.get('features', {})

                print(f"\n    Finding features available: {list(features.keys())}")

                # P21 Credibility
                if 'p21' in features:
                    p21 = features['p21']
                    print(f"    P21 credibility: {p21.get('credibility', 'MISSING')}")
                    print(f"    P21 domain_authority: {p21.get('domain_authority', 'MISSING')}")

                # P23 Stance
                if 'p23' in features:
                    p23 = features['p23']
                    print(f"    P23 item_grade: {p23.get('item_grade', 'MISSING')}")
                    print(f"    P23 stance: {p23.get('stance', 'MISSING')}")

                    findings = p23.get('findings', [])
                    if findings:
                        first_finding = findings[0]
                        print(f"    P23 finding stance: {first_finding.get('stance', 'MISSING')}")
                        print(f"    P23 finding score: {first_finding.get('score', 'MISSING')}")
                        quote = first_finding.get('quote', '')
                        print(f"    P23 nested quote: {truncate(quote, 80)}")

                # P24 Frames
                if 'p24' in features:
                    p24 = features['p24']
                    print(f"    P24 frame_confidence: {p24.get('frame_confidence', 'MISSING')}")

                # Authority
                print(f"    Authority (combined): {item.get('authority', 'MISSING')}")

    # ========================================================================
    # STAGE 6: FINAL CONSENSUS
    # ========================================================================
    print_section("STAGE 6: FINAL CONSENSUS")

    verdict = claim_result.get("verdict", {})

    print(f"Final verdict label: {verdict.get('label', 'MISSING')}")
    print(f"Final confidence: {verdict.get('confidence', 0):.3f}")
    print(f"Arm strength: {verdict.get('arm_strength', {})}")
    print(f"Quality multipliers: {verdict.get('quality_multipliers', {})}")

    # Check summary
    summary = verdict.get('summary', '')
    print(f"\nSummary present: {bool(summary)}")
    if summary:
        print(f"Summary: {truncate(summary, 200)}")
    else:
        print("Summary: MISSING ❌")

    # ========================================================================
    # STAGE 6.5: COMPREHENSIVE EVIDENCE BREAKDOWN
    # ========================================================================
    print("\n" + "="*80)
    print("COMPLETE EVIDENCE BREAKDOWN")
    print("="*80)

    for researcher in researchers:
        lane = researcher.get('lane_id', 'UNKNOWN')
        evidence = researcher.get('evidence', {})

        print(f"\n{'='*80}")
        print(f"{lane} - DETAILED EVIDENCE")
        print(f"{'='*80}")

        for arm_name in ['arm_A', 'arm_B']:
            items = evidence.get(arm_name, [])
            arm_label = "SUPPORT ARM" if arm_name == 'arm_A' else "CHALLENGE ARM"

            print(f"\n{arm_label}: {len(items)} items")
            print("-"*80)

            for idx, item in enumerate(items, 1):
                print(f"\nItem {idx}:")
                print(f"  Title: {item.get('title', 'NO TITLE')}")
                print(f"  URL: {item.get('url', 'NO URL')}")  # Full URL, not truncated
                print(f"  Domain: {item.get('url', '').split('/')[2] if item.get('url') and '/' in item.get('url', '') else 'N/A'}")
                print(f"  Coverage: {item.get('coverage', 'unknown')}")
                print(f"  Stance: {item.get('stance', 'unknown')}")

                # Credibility and tier info
                print(f"\n  CREDIBILITY:")
                print(f"    Score: {item.get('credibility', 0):.3f}")
                print(f"    Tier: {item.get('credibility_tier', 'N/A')}")
                print(f"    Category: {item.get('credibility_category', 'N/A')}")

                # Authority
                print(f"\n  AUTHORITY:")
                print(f"    Score: {item.get('authority', 0):.3f}")

                # Grading breakdown
                finding = item.get('finding', {})
                features = finding.get('features', {})

                print(f"\n  GRADING BREAKDOWN:")

                # P21
                if 'p21' in features:
                    p21 = features['p21']
                    print(f"    P21 (Full Read):")
                    print(f"      Credibility: {p21.get('credibility', 0):.3f}")
                    print(f"      Grade Full: {p21.get('grade_full', 0):.3f}")
                    print(f"      Stance Full: {p21.get('stance_full', 'N/A')}")

                # P23
                if 'p23' in features:
                    p23 = features['p23']
                    print(f"    P23 (Semantic):")
                    print(f"      Item Grade: {p23.get('item_grade', 0):.3f}")
                    print(f"      Stance: {p23.get('stance', 'N/A')}")
                    print(f"      Grade Label: {p23.get('grade_label', 'N/A')}")

                # P24
                if 'p24' in features:
                    p24 = features['p24']
                    print(f"    P24 (Frames):")
                    print(f"      Frame Confidence: {p24.get('frame_confidence', 0):.3f}")
                    frame_matches = p24.get('frame_matches', [])
                    if frame_matches:
                        best_frame = max(frame_matches, key=lambda x: x.get('score', 0))
                        print(f"      Best Frame Score: {best_frame.get('score', 0):.3f}")
                        print(f"      Best Frame Label: {best_frame.get('label', 'N/A')}")

                # Final item grade
                print(f"\n  FINAL ITEM GRADE: {item.get('item_grade', 0):.3f}")

                # Formula breakdown
                if 'p23' in features and 'p24' in features:
                    sem = features['p23'].get('item_grade', 0)
                    frame = features['p24'].get('frame_confidence', 0)
                    auth = item.get('authority', 0)
                    cov_str = item.get('coverage', 'snippet_only')
                    cov = {'full': 1.0, 'partial': 0.7, 'snippet_only': 0.4}.get(cov_str, 0.4)

                    print(f"\n  FORMULA: 0.40×semantic + 0.30×frame + 0.20×authority + 0.10×coverage")
                    print(f"         = 0.40×{sem:.3f} + 0.30×{frame:.3f} + 0.20×{auth:.3f} + 0.10×{cov:.3f}")
                    print(f"         = {0.40*sem:.3f} + {0.30*frame:.3f} + {0.20*auth:.3f} + {0.10*cov:.3f}")
                    print(f"         = {0.40*sem + 0.30*frame + 0.20*auth + 0.10*cov:.3f}")

                print("\n" + "-"*80)

    # ========================================================================
    # STAGE 6.6: VERDICT CALCULATION BREAKDOWN
    # ========================================================================
    print("\n" + "="*80)
    print("VERDICT CALCULATION BREAKDOWN")
    print("="*80)

    arm_strength = verdict.get('arm_strength', {})

    print(f"\nARM STRENGTH:")
    print(f"  Support (raw): {arm_strength.get('support_base', 0):.3f}")
    print(f"  Challenge (raw): {arm_strength.get('challenge_base', 0):.3f}")

    quality_mults = verdict.get('quality_multipliers', {})
    print(f"\nQUALITY MULTIPLIERS:")
    print(f"  Diversity: {quality_mults.get('diversity', 1.0):.3f}")
    print(f"  Consistency: {quality_mults.get('consistency', 1.0):.3f}")
    print(f"  Breadth: {quality_mults.get('breadth', 1.0):.3f}")
    combined = quality_mults.get('diversity', 1.0) * quality_mults.get('consistency', 1.0) * quality_mults.get('breadth', 1.0)
    print(f"  Combined: {combined:.3f}")

    print(f"\nARM STRENGTH (after multipliers):")
    print(f"  Support: {arm_strength.get('support', 0):.3f}")
    print(f"  Challenge: {arm_strength.get('challenge', 0):.3f}")
    print(f"  Balance: {arm_strength.get('balance', 0):.6f}")

    print(f"\nVERDICT LOGIC:")
    threshold = 0.12
    delta = 0.15
    support = arm_strength.get('support', 0)
    challenge = arm_strength.get('challenge', 0)

    print(f"  Insufficient threshold: {threshold}")
    print(f"  Delta threshold: {delta}")
    print(f"  Support arm: {support:.3f} {'>' if support >= threshold else '<'} {threshold}")
    print(f"  Challenge arm: {challenge:.3f} {'>' if challenge >= threshold else '<'} {threshold}")
    print(f"  Difference: {abs(support - challenge):.3f} {'>' if abs(support - challenge) >= delta else '<'} {delta}")

    print(f"\nFINAL VERDICT: {verdict.get('label', 'unknown')}")
    print(f"CONFIDENCE: {verdict.get('confidence', 0):.3f}")

    if verdict.get('summary'):
        print(f"\nSUMMARY: {verdict.get('summary')}")
    else:
        print(f"\nSUMMARY: NOT GENERATED")

    # ========================================================================
    # STAGE 7: GRADING BREAKDOWN
    # ========================================================================
    print_section("STAGE 7: GRADING BREAKDOWN ANALYSIS")

    all_items = []
    for researcher in researchers:
        evidence = researcher.get("evidence", {})
        all_items.extend(evidence.get("arm_A", []))
        all_items.extend(evidence.get("arm_B", []))

    if all_items:
        grades = [item.get('item_grade', 0) for item in all_items]
        stances = [item.get('stance', 'unknown') for item in all_items]

        print(f"Total items: {len(all_items)}")
        print(f"Average grade: {sum(grades)/len(grades):.3f}")
        print(f"Grade range: {min(grades):.3f} - {max(grades):.3f}")

        print(f"\nStance distribution:")
        stance_counts = {}
        for s in stances:
            stance_counts[s] = stance_counts.get(s, 0) + 1
        for stance, count in sorted(stance_counts.items()):
            pct = count / len(all_items) * 100
            print(f"  {stance:20s}: {count:2d} / {len(all_items)} ({pct:.1f}%)")

        # Credibility analysis
        print(f"\nCredibility scores:")
        credibilities = []
        for item in all_items:
            finding = item.get('finding', {})
            features = finding.get('features', {})
            if 'p21' in features:
                cred = features['p21'].get('credibility', 0)
                credibilities.append(cred)

        if credibilities:
            print(f"  Average: {sum(credibilities)/len(credibilities):.3f}")
            print(f"  Range: {min(credibilities):.3f} - {max(credibilities):.3f}")

        # Authority analysis
        print(f"\nAuthority scores:")
        authorities = [item.get('authority', 0) for item in all_items if 'authority' in item]
        if authorities:
            print(f"  Average: {sum(authorities)/len(authorities):.3f}")
            print(f"  Range: {min(authorities):.3f} - {max(authorities):.3f}")

    # ========================================================================
    # STAGE 8: VERIFICATION CHECKS
    # ========================================================================
    print_section("STAGE 8: VERIFICATION CHECKS")

    print("Checking for old code artifacts:")

    # Check queries for old templates
    all_queries = []
    for researcher in researchers:
        plan = researcher.get("plan", {})
        for arm in plan.get("arms", {}).values():
            all_queries.extend(arm.get("queries", []))

    old_templates = [q for q in all_queries if "actual value" in q.lower() or (q.count(' ') == 1 and "verify" in q.lower())]

    if old_templates:
        print("  ❌ OLD template queries detected:")
        for q in old_templates[:5]:
            print(f"    - {q}")
    else:
        print("  ✅ No old template queries detected")

    # Check for semantic queries
    semantic_queries = [q for q in all_queries if len(q.split()) >= 4 and '"' not in q]
    if semantic_queries:
        print(f"  ✅ Semantic queries detected ({len(semantic_queries)} queries)")
        print(f"    Example: {semantic_queries[0]}")

    # Check stance detection method
    entailment_stances = [item.get('stance') for item in all_items if item.get('stance') in ['support', 'challenge', 'contextual_support']]
    if entailment_stances:
        print(f"  ✅ Cross-encoder stances detected ({len(entailment_stances)} items)")

    # Check for missing quote field
    items_with_quote = sum(1 for item in all_items if 'quote' in item)
    items_with_nested_quote = sum(1 for item in all_items
                                   if item.get('finding', {}).get('features', {}).get('p23', {}).get('findings', [])
                                   and item['finding']['features']['p23']['findings'][0].get('quote'))

    print(f"\n  Quote extraction:")
    print(f"    Items with top-level quote: {items_with_quote}/{len(all_items)}")
    print(f"    Items with nested quote: {items_with_nested_quote}/{len(all_items)}")

    if items_with_quote == 0 and items_with_nested_quote > 0:
        print(f"    ❌ Quotes not extracted to top level")
    elif items_with_quote > 0:
        print(f"    ✅ Quotes extracted to top level")

    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)


if __name__ == "__main__":
    claim = "Water boils at 100 degrees Celsius"
    if len(sys.argv) > 1:
        claim = " ".join(sys.argv[1:])

    asyncio.run(diagnose_complete_pipeline(claim))

    # Close output file
    output_file.close()
