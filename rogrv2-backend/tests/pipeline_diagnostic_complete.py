#!/usr/bin/env python3
"""
COMPREHENSIVE PRODUCTION PIPELINE DIAGNOSTIC TEST
==================================================

This is the SINGLE SOURCE OF TRUTH test for the ROGR pipeline.

Purpose:
- Tests real production pipeline end-to-end (no mocking)
- Outputs comprehensive diagnostic information with timestamps
- Shows where issues occur in the pipeline
- Produces beautiful end-user formatted output
- Creates timestamped output files for historical tracking

Output Location: Refactor 5/PIPELINE COMPLETE TEST RUNS/
File Format: pipeline_diag_full_run_YYYYMMDD_HHMMSS.txt (CST)

Usage:
    python tests/pipeline_diagnostic_complete.py [claim_text]

    # If no claim provided, uses default test claim
    python tests/pipeline_diagnostic_complete.py
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from dotenv import load_dotenv
load_dotenv(override=True)

import asyncio
import sys
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import pytz

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TimestampedLogger:
    """Logger that timestamps every output line"""

    def __init__(self, output_file):
        self.output_file = output_file
        self.start_time = datetime.now()
        self.cst = pytz.timezone('America/Chicago')

    def log(self, message: str, indent: int = 0):
        """Log a message with CST timestamp"""
        timestamp = datetime.now(self.cst).strftime("%H:%M:%S.%f")[:-3]
        indent_str = "  " * indent
        line = f"[{timestamp}] {indent_str}{message}"
        print(line)
        self.output_file.write(line + "\n")
        self.output_file.flush()

    def section(self, title: str):
        """Log a section header"""
        self.log("=" * 80)
        self.log(title)
        self.log("=" * 80)

    def subsection(self, title: str):
        """Log a subsection header"""
        self.log("-" * 80)
        self.log(title)
        self.log("-" * 80)

    def elapsed(self) -> float:
        """Get elapsed time since start in seconds"""
        return (datetime.now() - self.start_time).total_seconds()


async def run_diagnostic(claim_text: str, logger: TimestampedLogger):
    """Run comprehensive pipeline diagnostic"""

    logger.section("COMPREHENSIVE PRODUCTION PIPELINE DIAGNOSTIC")
    logger.log(f"Test Claim: {claim_text}")
    logger.log("")
    logger.log(">>> PIPELINE EXECUTION START")
    logger.log("")

    # Import pipeline components
    logger.subsection("Phase 0: Importing Pipeline Components")
    start_import = logger.elapsed()

    from intelligence.pipeline.run import run_preview
    from intelligence.analyze.enrich import enrich_claim_obj

    logger.log(f"Imports completed in {logger.elapsed() - start_import:.3f}s", indent=1)
    logger.log("")

    # Phase 1: Claim Enrichment
    logger.subsection("Phase 1: Claim Enrichment")
    start_enrich = logger.elapsed()

    claim = {"id": "test-1", "text": claim_text, "tier": "primary"}
    enriched = enrich_claim_obj(claim)

    enrich_duration = logger.elapsed() - start_enrich
    logger.log(f"Enrichment completed in {enrich_duration:.3f}s", indent=1)
    logger.log("")
    logger.log("Enrichment Results:", indent=1)
    logger.log(f"• Concept: '{enriched.get('concept', '')}'", indent=2)
    logger.log(f"• Dimension: '{enriched.get('dimension', 'unknown')}'", indent=2)
    logger.log(f"• Entities: {enriched.get('entities', [])}", indent=2)
    logger.log(f"• Numbers: {enriched.get('numbers', {})}", indent=2)
    logger.log(f"• Cues: {enriched.get('cues', {})}", indent=2)
    logger.log(f"• Kind: {enriched.get('kind_hint', 'unknown')}", indent=2)

    # Check enrichment quality
    has_concept = bool(enriched.get('concept', ''))
    has_dimension = enriched.get('dimension', 'unknown') != 'unknown'
    has_entities = bool(enriched.get('entities', []))

    logger.log("")
    logger.log("Enrichment Quality Assessment:", indent=1)
    logger.log(f"• Concept populated: {'✓' if has_concept else '✗'}", indent=2)
    logger.log(f"• Dimension detected: {'✓' if has_dimension else '✗'}", indent=2)
    logger.log(f"• Entities extracted: {'✓' if has_entities else '✗'}", indent=2)

    if not (has_concept or has_entities):
        logger.log("")
        logger.log("⚠️  WARNING: Enrichment may be insufficient for query differentiation", indent=1)
        logger.log("   Query generation may fall back to base claim text only", indent=1)

    logger.log("")

    # Phase 2: Full Pipeline Execution
    logger.subsection("Phase 2: Full Pipeline Execution")
    start_pipeline = logger.elapsed()

    logger.log("Executing run_preview()...", indent=1)
    result = await run_preview(claim_text)

    pipeline_duration = logger.elapsed() - start_pipeline
    logger.log(f"Pipeline execution completed in {pipeline_duration:.3f}s", indent=1)
    logger.log("")

    # Phase 3: Result Analysis
    logger.subsection("Phase 3: Result Structure Analysis")

    logger.log("Top-level keys:", indent=1)
    for key in result.keys():
        logger.log(f"• {key}", indent=2)

    logger.log("")

    # Get claim result
    claims = result.get("claims", [])
    if not claims:
        logger.log("ERROR: No claims in result", indent=1)
        return result

    claim_result = claims[0]

    logger.log("Claim result keys:", indent=1)
    for key in claim_result.keys():
        logger.log(f"• {key}", indent=2)

    logger.log("")

    # Phase 4: Verdict Analysis
    logger.subsection("Phase 4: Verdict Information")

    verdict = claim_result.get("verdict", {})
    logger.log(f"Label: {verdict.get('label', 'unknown')}", indent=1)
    logger.log(f"Confidence: {verdict.get('confidence', 0.0):.3f}", indent=1)
    logger.log("")

    # Phase 5: Evidence Analysis
    logger.subsection("Phase 5: Evidence Analysis")

    evidence = claim_result.get("evidence", {})
    arm_a_items = evidence.get("arm_A", [])
    arm_b_items = evidence.get("arm_B", [])

    logger.log(f"Arm A (Support-Seeking): {len(arm_a_items)} items", indent=1)
    logger.log(f"Arm B (Challenge-Seeking): {len(arm_b_items)} items", indent=1)
    logger.log(f"Total evidence items: {len(arm_a_items) + len(arm_b_items)}", indent=1)
    logger.log("")

    # Arm A Evidence
    if arm_a_items:
        logger.log("Arm A Evidence Details:", indent=1)
        for i, item in enumerate(arm_a_items[:5], 1):  # Show first 5
            logger.log(f"Item {i}:", indent=2)
            logger.log(f"• URL: {item.get('url', 'N/A')}", indent=3)
            logger.log(f"• Domain: {item.get('domain', 'N/A')}", indent=3)
            logger.log(f"• Authority: {item.get('authority', 0.0):.3f}", indent=3)
            logger.log(f"• Semantic Score: {item.get('semantic_score', 0.0):.3f}", indent=3)
            logger.log(f"• Frame Score: {item.get('frame_score', 0.0):.3f}", indent=3)
            logger.log(f"• Item Grade: {item.get('item_grade', 0.0):.3f}", indent=3)
            logger.log(f"• Stance: {item.get('stance', 'unknown')}", indent=3)
            logger.log(f"• Credibility: {item.get('credibility', 0.0):.3f} (Tier {item.get('credibility_tier', 'N/A')})", indent=3)
            logger.log("")

    logger.log("")

    # Arm B Evidence
    if arm_b_items:
        logger.log("Arm B Evidence Details:", indent=1)
        for i, item in enumerate(arm_b_items[:5], 1):  # Show first 5
            logger.log(f"Item {i}:", indent=2)
            logger.log(f"• URL: {item.get('url', 'N/A')}", indent=3)
            logger.log(f"• Domain: {item.get('domain', 'N/A')}", indent=3)
            logger.log(f"• Authority: {item.get('authority', 0.0):.3f}", indent=3)
            logger.log(f"• Semantic Score: {item.get('semantic_score', 0.0):.3f}", indent=3)
            logger.log(f"• Frame Score: {item.get('frame_score', 0.0):.3f}", indent=3)
            logger.log(f"• Item Grade: {item.get('item_grade', 0.0):.3f}", indent=3)
            logger.log(f"• Stance: {item.get('stance', 'unknown')}", indent=3)
            logger.log(f"• Credibility: {item.get('credibility', 0.0):.3f} (Tier {item.get('credibility_tier', 'N/A')})", indent=3)
            logger.log("")

    logger.log("")

    # Phase 6: Aggregation Analysis
    logger.subsection("Phase 6: Aggregation Metrics")

    arm_a_agg = claim_result.get("arm_A_aggregation", {})
    arm_b_agg = claim_result.get("arm_B_aggregation", {})

    if arm_a_agg:
        logger.log("Arm A Aggregation:", indent=1)
        logger.log(f"• Base Strength: {arm_a_agg.get('base_strength', 0.0):.3f}", indent=2)
        logger.log(f"• Final Strength: {arm_a_agg.get('strength', 0.0):.3f}", indent=2)
        logger.log(f"• Item Count: {arm_a_agg.get('count', 0)}", indent=2)

        multipliers = arm_a_agg.get('multipliers', {})
        if multipliers:
            logger.log(f"• Diversity: {multipliers.get('diversity', 0.0):.3f}", indent=2)
            logger.log(f"• Consistency: {multipliers.get('consistency', 0.0):.3f}", indent=2)
            logger.log(f"• Breadth: {multipliers.get('breadth', 0.0):.3f}", indent=2)
    else:
        logger.log("Arm A Aggregation: Not available", indent=1)

    logger.log("")

    if arm_b_agg:
        logger.log("Arm B Aggregation:", indent=1)
        logger.log(f"• Base Strength: {arm_b_agg.get('base_strength', 0.0):.3f}", indent=2)
        logger.log(f"• Final Strength: {arm_b_agg.get('strength', 0.0):.3f}", indent=2)
        logger.log(f"• Item Count: {arm_b_agg.get('count', 0)}", indent=2)

        multipliers = arm_b_agg.get('multipliers', {})
        if multipliers:
            logger.log(f"• Diversity: {multipliers.get('diversity', 0.0):.3f}", indent=2)
            logger.log(f"• Consistency: {multipliers.get('consistency', 0.0):.3f}", indent=2)
            logger.log(f"• Breadth: {multipliers.get('breadth', 0.0):.3f}", indent=2)
    else:
        logger.log("Arm B Aggregation: Not available", indent=1)

    logger.log("")

    # Phase 7: Consensus Analysis
    logger.subsection("Phase 7: Consensus Logic")

    consensus = claim_result.get("consensus", {})
    if consensus:
        logger.log(f"Consensus Label: {consensus.get('label', 'N/A')}", indent=1)
        logger.log(f"Consensus Confidence: {consensus.get('confidence', 0.0):.3f}", indent=1)

        arm_strengths = consensus.get('arm_strength', {})
        if arm_strengths:
            logger.log(f"Support Strength: {arm_strengths.get('support', 0.0):.3f}", indent=1)
            logger.log(f"Challenge Strength: {arm_strengths.get('challenge', 0.0):.3f}", indent=1)
            logger.log(f"Balance: {arm_strengths.get('balance', 0.0):.3f}", indent=1)

    logger.log("")

    # Phase 8: Researcher Analysis
    logger.subsection("Phase 8: Dual Researcher System")

    researchers = claim_result.get("researchers", [])
    logger.log(f"Number of researchers: {len(researchers)}", indent=1)

    for i, researcher in enumerate(researchers, 1):
        logger.log(f"Researcher {i} ({researcher.get('lane', 'unknown')}):", indent=1)
        logger.log(f"• Verdict: {researcher.get('verdict', 'N/A')}", indent=2)
        logger.log(f"• Confidence: {researcher.get('confidence', 0.0):.3f}", indent=2)
        logger.log(f"• Evidence Count: {researcher.get('evidence_count', 0)}", indent=2)

    logger.log("")

    # Timing Summary
    total_time = logger.elapsed()
    logger.log(f"<<< PIPELINE EXECUTION END (duration: {total_time:.3f}s)")
    logger.log("")

    return result


def format_authority_stars(authority: float) -> str:
    """Convert authority score to star rating"""
    stars = int(authority * 5)
    return "⭐" * stars if stars > 0 else "☆"


def format_end_user_output(claim_text: str, result: Dict[str, Any], total_time: float, logger: TimestampedLogger):
    """Format beautiful end-user output"""

    # Beautiful separator
    logger.log("")
    logger.log("╔" + "═" * 78 + "╗")
    logger.log("║" + " " * 78 + "║")
    logger.log("║" + " " * 20 + "END USER OUTPUT - ROGR VERDICT" + " " * 27 + "║")
    logger.log("║" + " " * 78 + "║")
    logger.log("╚" + "═" * 78 + "╝")
    logger.log("")

    # Get claim result
    claims = result.get("claims", [])
    if not claims:
        logger.log("ERROR: No result available")
        return

    claim_result = claims[0]
    verdict = claim_result.get("verdict", {})
    evidence = claim_result.get("evidence", {})
    consensus = claim_result.get("consensus", {})

    # Verdict header
    label = verdict.get("label", "UNKNOWN").upper()
    confidence = verdict.get("confidence", 0.0) * 100

    logger.log(f"Verdict: {label}")
    logger.log(f"Confidence: {confidence:.0f}%")
    logger.log("")
    logger.log(f"Claim: \"{claim_text}\"")
    logger.log("")

    # Summary
    summary = claim_result.get("summary", "")
    if summary:
        logger.log("Summary:")
        # Word wrap summary at 76 characters
        words = summary.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 <= 76:
                line += word + " "
            else:
                logger.log(line.strip())
                line = word + " "
        if line:
            logger.log(line.strip())
    else:
        logger.log("Summary: Not available")

    logger.log("")

    # Supporting Evidence (Arm A)
    arm_a_items = evidence.get("arm_A", [])
    if arm_a_items:
        logger.log(f"✓ SUPPORTING EVIDENCE ({len(arm_a_items)} sources)")
        logger.log("")

        for i, item in enumerate(arm_a_items, 1):
            url = item.get("url", "N/A")
            title = item.get("title", "Untitled")
            domain = item.get("domain", "unknown")
            authority = item.get("authority", 0.0)
            item_grade = item.get("item_grade", 0.0)
            credibility = item.get("credibility", 0.0)
            credibility_category = item.get("credibility_category", "unknown")
            quote = item.get("quote", "")

            # Format grade as percentage
            grade_pct = int(item_grade * 100)

            # Authority stars
            stars = format_authority_stars(authority)

            logger.log(f"{i}. {title} ({domain})")
            logger.log(f"   Grade: {grade_pct}/100 | Authority: {credibility_category.title()} ({stars})")

            if quote:
                # Truncate quote to reasonable length
                if len(quote) > 200:
                    quote = quote[:197] + "..."
                logger.log(f"   \"{quote}\"")

            logger.log(f"   [Read full article: {url}]")
            logger.log("")

    # Important Context (Arm B)
    arm_b_items = evidence.get("arm_B", [])
    if arm_b_items:
        logger.log(f"⚠️  IMPORTANT CONTEXT ({len(arm_b_items)} sources)")
        logger.log("")

        for i, item in enumerate(arm_b_items, 1):
            url = item.get("url", "N/A")
            title = item.get("title", "Untitled")
            domain = item.get("domain", "unknown")
            authority = item.get("authority", 0.0)
            item_grade = item.get("item_grade", 0.0)
            credibility_category = item.get("credibility_category", "unknown")
            quote = item.get("quote", "")

            grade_pct = int(item_grade * 100)
            stars = format_authority_stars(authority)

            logger.log(f"{i}. {title} ({domain})")
            logger.log(f"   Grade: {grade_pct}/100 | Authority: {credibility_category.title()} ({stars})")

            if quote:
                if len(quote) > 200:
                    quote = quote[:197] + "..."
                logger.log(f"   \"{quote}\"")

            logger.log(f"   [Read full article: {url}]")
            logger.log("")

    # Research Quality Metrics
    logger.log("Research Quality:")

    # Calculate unique domains
    all_items = arm_a_items + arm_b_items
    unique_domains = len(set(item.get("domain", "") for item in all_items))

    # Calculate average authority
    if all_items:
        avg_authority = sum(item.get("authority", 0.0) for item in all_items) / len(all_items)
        avg_authority_pct = int(avg_authority * 100)
    else:
        avg_authority_pct = 0

    # Get quality multipliers
    arm_strength = consensus.get("arm_strength", {})
    quality_multipliers = consensus.get("quality_multipliers", {})

    logger.log(f"  • Source Diversity: {unique_domains} unique authoritative domains")
    logger.log(f"  • Source Authority: {avg_authority_pct}% average")

    if quality_multipliers:
        consistency = quality_multipliers.get("consistency", 0.0)
        logger.log(f"  • Evidence Consistency: {int(consistency * 100)}% agreement")

    # Researcher agreement
    researchers = claim_result.get("researchers", [])
    if len(researchers) >= 2:
        r1_verdict = researchers[0].get("verdict", "")
        r2_verdict = researchers[1].get("verdict", "")
        if r1_verdict == r2_verdict:
            logger.log(f"  • Two independent researchers agreed")
        else:
            logger.log(f"  • Researchers had differing conclusions")

    logger.log("")

    # Processing stats
    logger.log(f"Processing Time: {total_time:.1f} seconds")

    # Count total candidates processed
    run_manifest = result.get("run_manifest", {})
    total_candidates = 0
    for researcher in run_manifest.get("researchers", []):
        for arm in researcher.get("arms", []):
            total_candidates += arm.get("raw_count", 0)

    logger.log(f"Evidence Items Analyzed: {total_candidates} candidates → {len(all_items)} selected")

    logger.log("")
    logger.log("─" * 80)


def main():
    """Main entry point"""

    # Get claim from command line or use default
    if len(sys.argv) > 1:
        claim_text = " ".join(sys.argv[1:])
    else:
        claim_text = "Water boils at 100 degrees Celsius"

    # Create output directory
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Refactor 5",
        "PIPELINE COMPLETE TEST RUNS"
    )
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename with CST timestamp
    cst = pytz.timezone('America/Chicago')
    timestamp = datetime.now(cst).strftime("%Y%m%d_%H%M%S")
    filename = f"pipeline_diag_full_run_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)

    # Open output file
    with open(filepath, "w", encoding="utf-8") as f:
        logger = TimestampedLogger(f)

        # Run diagnostic
        try:
            result = asyncio.run(run_diagnostic(claim_text, logger))

            # Format end-user output
            total_time = logger.elapsed()
            format_end_user_output(claim_text, result, total_time, logger)

            logger.log("")
            logger.log(f"Test completed successfully!")
            logger.log(f"Output saved to: {filepath}")

        except Exception as e:
            logger.log("")
            logger.log(f"ERROR: Test failed with exception:")
            logger.log(f"{type(e).__name__}: {str(e)}")
            import traceback
            logger.log("")
            logger.log("Traceback:")
            for line in traceback.format_exc().split("\n"):
                logger.log(line)
            sys.exit(1)

    print(f"\nOutput saved to: {filepath}")


if __name__ == "__main__":
    main()
