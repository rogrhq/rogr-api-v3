#!/usr/bin/env python3
"""
Comprehensive Diagnostic Script for ROGRv2 Pipeline
DO NOT convert this to pytest - it won't work with async + ML models.

This script provides:
- Real-time timestamped printing at every major step
- Complete tracing of queries, searches, fetches, scores, and aggregations
- IFCN-style end user summary
- Performance bottleneck identification
- Output saved to diagnostic_output_[timestamp].txt
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from dotenv import load_dotenv
load_dotenv(override=True)

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import pipeline components
from intelligence.pipeline.run import run_preview


class DiagnosticLogger:
    """Logger that timestamps every output line and saves to file"""

    def __init__(self):
        self.lines = []
        self.start_time = time.time()

    def timestamp(self):
        """Generate timestamp in [HH:MM:SS.mmm] format"""
        now = datetime.now()
        ms = int((time.time() % 1) * 1000)
        return f"[{now.strftime('%H:%M:%S')}.{ms:03d}]"

    def log(self, message: str, indent: int = 0):
        """Print and save a timestamped message"""
        prefix = "  " * indent
        line = f"{self.timestamp()} {prefix}{message}"
        print(line)
        self.lines.append(line)

    def log_separator(self, char="=", length=80):
        """Print a separator line"""
        line = char * length
        print(line)
        self.lines.append(line)

    def save(self, filepath: str):
        """Save all logged lines to file"""
        with open(filepath, 'w') as f:
            f.write('\n'.join(self.lines))
        print(f"\n{self.timestamp()} ✓ Diagnostic output saved to: {filepath}")


logger = DiagnosticLogger()


def format_duration(start_time: float) -> str:
    """Format duration since start_time"""
    duration = time.time() - start_time
    return f"{duration:.3f}s"


async def run_diagnostic(claim: str):
    """Run comprehensive diagnostic on the pipeline"""

    logger.log_separator("=", 80)
    logger.log("COMPREHENSIVE PIPELINE DIAGNOSTIC")
    logger.log_separator("=", 80)
    logger.log(f"Test Claim: {claim}")
    logger.log("")

    # Run the pipeline with detailed tracing
    logger.log(">>> PIPELINE EXECUTION START")
    pipeline_start = time.time()

    try:
        result = await run_preview(claim, test_mode=False)

        logger.log(f"<<< PIPELINE EXECUTION END (duration: {format_duration(pipeline_start)})")
        logger.log("")

        # Extract results
        if "claims" not in result or len(result["claims"]) == 0:
            logger.log("⚠ ERROR: No claims in result", indent=1)
            return None

        claim_result = result["claims"][0]

        # Log high-level structure
        logger.log("RESULT STRUCTURE:", indent=0)
        logger.log(f"Keys in result: {list(result.keys())}", indent=1)
        logger.log(f"Keys in claim_result: {list(claim_result.keys())}", indent=1)
        logger.log("")

        # Extract verdict
        verdict_obj = claim_result.get("verdict", {})
        verdict_label = verdict_obj.get("label", "unknown") if isinstance(verdict_obj, dict) else str(verdict_obj)
        verdict_confidence = verdict_obj.get("confidence", 0.0) if isinstance(verdict_obj, dict) else 0.0

        logger.log("VERDICT INFORMATION:", indent=0)
        logger.log(f"Label: {verdict_label}", indent=1)
        logger.log(f"Confidence: {verdict_confidence:.3f}", indent=1)
        logger.log("")

        # Extract evidence
        evidence = claim_result.get("evidence", {})
        arm_a = evidence.get("arm_A", [])
        arm_b = evidence.get("arm_B", [])

        logger.log("EVIDENCE COUNTS:", indent=0)
        logger.log(f"Arm A items: {len(arm_a)}", indent=1)
        logger.log(f"Arm B items: {len(arm_b)}", indent=1)
        logger.log(f"Total items: {len(arm_a) + len(arm_b)}", indent=1)
        logger.log("")

        # Detailed Arm A analysis
        logger.log_separator("-", 80)
        logger.log("ARM A EVIDENCE (Support-Seeking):")
        logger.log_separator("-", 80)

        for i, item in enumerate(arm_a, 1):
            logger.log(f"Item {i}:", indent=0)
            logger.log(f"URL: {item.get('url', 'N/A')}", indent=1)
            logger.log(f"Title: {item.get('title', 'N/A')[:80]}", indent=1)

            # Scores
            logger.log("Scores:", indent=1)
            logger.log(f"Authority: {item.get('authority', 0.0):.3f}", indent=2)
            logger.log(f"Semantic: {item.get('semantic_score', 0.0):.3f}", indent=2)
            logger.log(f"Frame: {item.get('frame_score', 0.0):.3f}", indent=2)
            logger.log(f"Item Grade: {item.get('item_grade', 0.0):.3f}", indent=2)

            # Credibility breakdown
            if 'credibility' in item:
                cred = item['credibility']
                logger.log(f"Credibility: {cred}", indent=2)

            # Domain info
            if 'domain' in item:
                logger.log(f"Domain: {item['domain']}", indent=2)

            # Quote/excerpt
            quote = item.get('quote', item.get('text', ''))[:200]
            if quote:
                logger.log(f"Quote: \"{quote}...\"", indent=2)

            # Stance info
            if 'stance' in item:
                logger.log(f"Stance: {item['stance']}", indent=2)

            logger.log("")

        # Detailed Arm B analysis
        logger.log_separator("-", 80)
        logger.log("ARM B EVIDENCE (Challenge-Seeking):")
        logger.log_separator("-", 80)

        for i, item in enumerate(arm_b, 1):
            logger.log(f"Item {i}:", indent=0)
            logger.log(f"URL: {item.get('url', 'N/A')}", indent=1)
            logger.log(f"Title: {item.get('title', 'N/A')[:80]}", indent=1)

            # Scores
            logger.log("Scores:", indent=1)
            logger.log(f"Authority: {item.get('authority', 0.0):.3f}", indent=2)
            logger.log(f"Semantic: {item.get('semantic_score', 0.0):.3f}", indent=2)
            logger.log(f"Frame: {item.get('frame_score', 0.0):.3f}", indent=2)
            logger.log(f"Item Grade: {item.get('item_grade', 0.0):.3f}", indent=2)

            # Credibility breakdown
            if 'credibility' in item:
                cred = item['credibility']
                logger.log(f"Credibility: {cred}", indent=2)

            # Domain info
            if 'domain' in item:
                logger.log(f"Domain: {item['domain']}", indent=2)

            # Quote/excerpt
            quote = item.get('quote', item.get('text', ''))[:200]
            if quote:
                logger.log(f"Quote: \"{quote}...\"", indent=2)

            # Stance info
            if 'stance' in item:
                logger.log(f"Stance: {item['stance']}", indent=2)

            logger.log("")

        # Aggregation metrics
        logger.log_separator("-", 80)
        logger.log("AGGREGATION METRICS:")
        logger.log_separator("-", 80)

        # Try to extract aggregation info
        agg_a = claim_result.get("arm_A_aggregation", {})
        agg_b = claim_result.get("arm_B_aggregation", {})

        if agg_a:
            logger.log("Arm A Aggregation:", indent=0)
            logger.log(f"Average Grade: {agg_a.get('avg_grade', 0.0):.3f}", indent=1)
            logger.log(f"Domain Diversity: {agg_a.get('domain_diversity', 0.0):.3f}", indent=1)
            logger.log(f"Consistency: {agg_a.get('consistency', 0.0):.3f}", indent=1)
            logger.log(f"Breadth: {agg_a.get('breadth', 0.0):.3f}", indent=1)
            logger.log(f"Final Arm Strength: {agg_a.get('arm_strength', 0.0):.3f}", indent=1)
            logger.log("")

        if agg_b:
            logger.log("Arm B Aggregation:", indent=0)
            logger.log(f"Average Grade: {agg_b.get('avg_grade', 0.0):.3f}", indent=1)
            logger.log(f"Domain Diversity: {agg_b.get('domain_diversity', 0.0):.3f}", indent=1)
            logger.log(f"Consistency: {agg_b.get('consistency', 0.0):.3f}", indent=1)
            logger.log(f"Breadth: {agg_b.get('breadth', 0.0):.3f}", indent=1)
            logger.log(f"Final Arm Strength: {agg_b.get('arm_strength', 0.0):.3f}", indent=1)
            logger.log("")

        # Consensus logic
        logger.log_separator("-", 80)
        logger.log("CONSENSUS LOGIC (P27):")
        logger.log_separator("-", 80)

        arm_a_strength = agg_a.get('arm_strength', 0.0) if agg_a else 0.0
        arm_b_strength = agg_b.get('arm_strength', 0.0) if agg_b else 0.0

        logger.log(f"Arm A Strength: {arm_a_strength:.3f}", indent=1)
        logger.log(f"Arm B Strength: {arm_b_strength:.3f}", indent=1)
        logger.log(f"Difference: {abs(arm_a_strength - arm_b_strength):.3f}", indent=1)
        logger.log("")

        # Balance calculation
        total_strength = arm_a_strength + arm_b_strength
        if total_strength > 0:
            balance = abs(arm_a_strength - arm_b_strength) / total_strength
            logger.log(f"Balance: {balance:.3f}", indent=1)
            logger.log(f"Verdict determination:", indent=1)

            if balance > 0.3:
                if arm_a_strength > arm_b_strength:
                    logger.log("Balance > 0.3 AND Arm A > Arm B → SUPPORTS", indent=2)
                else:
                    logger.log("Balance > 0.3 AND Arm B > Arm A → REFUTES", indent=2)
            else:
                logger.log("Balance ≤ 0.3 → MIXED (evidence too balanced)", indent=2)
        else:
            logger.log("Total strength = 0, cannot determine verdict", indent=1)

        logger.log("")

        # Generate IFCN-style summary
        generate_ifcn_summary(claim, verdict_label, verdict_confidence, arm_a, arm_b)

        return result

    except Exception as e:
        logger.log(f"⚠ PIPELINE ERROR: {e}", indent=1)
        import traceback
        logger.log(traceback.format_exc(), indent=1)
        return None


def generate_ifcn_summary(claim: str, verdict: str, confidence: float, arm_a: List[Dict], arm_b: List[Dict]):
    """Generate IFCN-style end user summary"""

    logger.log_separator("=", 80)
    logger.log("IFCN-STYLE END USER SUMMARY")
    logger.log_separator("=", 80)
    logger.log("")

    # Claim
    logger.log("CLAIM:", indent=0)
    logger.log(f"\"{claim}\"", indent=1)
    logger.log("")

    # Verdict
    verdict_display = verdict.upper()
    logger.log("IFCN LABEL:", indent=0)
    logger.log(verdict_display, indent=1)
    logger.log("")

    # Confidence
    logger.log("CONFIDENCE SCORE:", indent=0)
    logger.log(f"{confidence:.2f}", indent=1)
    logger.log("")

    # Results summary
    logger.log("RESULTS SUMMARY:", indent=0)

    if verdict.lower() == "supports":
        summary = f"The claim is SUPPORTED by available evidence. We found {len(arm_a)} sources supporting the claim with high-quality evidence, while challenge-seeking queries found {len(arm_b)} sources with alternative perspectives. The overall confidence in this verdict is {confidence:.2f}."
    elif verdict.lower() == "refutes":
        summary = f"The claim is REFUTED by available evidence. We found {len(arm_b)} sources contradicting the claim with high-quality evidence, while support-seeking queries found {len(arm_a)} sources. The overall confidence in this verdict is {confidence:.2f}."
    else:  # mixed
        summary = f"The evidence is MIXED for this claim. We found {len(arm_a)} sources supporting the claim and {len(arm_b)} sources challenging it, with relatively balanced evidence strength on both sides. This suggests the claim may be context-dependent or contain both accurate and inaccurate elements. Confidence: {confidence:.2f}."

    logger.log(summary, indent=1)
    logger.log("")

    # Complete source list
    logger.log_separator("-", 80)
    logger.log("COMPLETE SOURCE LIST:")
    logger.log_separator("-", 80)
    logger.log("")

    logger.log("SUPPORTING SOURCES (Arm A):", indent=0)
    logger.log("")

    if arm_a:
        for i, item in enumerate(arm_a, 1):
            logger.log(f"Source {i}:", indent=1)
            logger.log(f"Title: {item.get('title', 'N/A')}", indent=2)
            logger.log(f"URL: {item.get('url', 'N/A')}", indent=2)
            logger.log(f"Authority: {item.get('authority', 0.0):.2f}", indent=2)
            logger.log(f"Semantic: {item.get('semantic_score', 0.0):.2f}", indent=2)
            logger.log(f"Frame: {item.get('frame_score', 0.0):.2f}", indent=2)
            logger.log(f"Item Grade: {item.get('item_grade', 0.0):.2f}", indent=2)

            quote = item.get('quote', item.get('text', ''))[:300]
            if quote:
                logger.log(f"Quote: \"{quote}...\"", indent=2)
            else:
                logger.log("Quote: [No excerpt available]", indent=2)

            logger.log("")
    else:
        logger.log("No supporting sources found.", indent=1)
        logger.log("")

    logger.log("CHALLENGING SOURCES (Arm B):", indent=0)
    logger.log("")

    if arm_b:
        for i, item in enumerate(arm_b, 1):
            logger.log(f"Source {i}:", indent=1)
            logger.log(f"Title: {item.get('title', 'N/A')}", indent=2)
            logger.log(f"URL: {item.get('url', 'N/A')}", indent=2)
            logger.log(f"Authority: {item.get('authority', 0.0):.2f}", indent=2)
            logger.log(f"Semantic: {item.get('semantic_score', 0.0):.2f}", indent=2)
            logger.log(f"Frame: {item.get('frame_score', 0.0):.2f}", indent=2)
            logger.log(f"Item Grade: {item.get('item_grade', 0.0):.2f}", indent=2)

            quote = item.get('quote', item.get('text', ''))[:300]
            if quote:
                logger.log(f"Quote: \"{quote}...\"", indent=2)
            else:
                logger.log("Quote: [No excerpt available]", indent=2)

            logger.log("")
    else:
        logger.log("No challenging sources found.", indent=1)
        logger.log("")

    logger.log_separator("=", 80)


def main():
    """Main entry point"""

    # Test claim
    # Get claim from command line or use default
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--claim" and len(sys.argv) > 2:
        claim = sys.argv[2]
    else:
        claim = "Water boils at 100 degrees Celsius"

    try:
        # Run diagnostic
        result = asyncio.run(run_diagnostic(claim))

        if result:
            logger.log("")
            logger.log("✓ DIAGNOSTIC COMPLETE")
        else:
            logger.log("")
            logger.log("✗ DIAGNOSTIC FAILED")

        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"diagnostic_output_{timestamp}.txt"
        logger.save(output_file)

        sys.exit(0 if result else 1)

    except Exception as e:
        logger.log("")
        logger.log(f"✗ FATAL ERROR: {e}")
        import traceback
        logger.log(traceback.format_exc())

        # Still save output even on error
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"diagnostic_output_{timestamp}_ERROR.txt"
        logger.save(output_file)

        sys.exit(1)


if __name__ == "__main__":
    main()
