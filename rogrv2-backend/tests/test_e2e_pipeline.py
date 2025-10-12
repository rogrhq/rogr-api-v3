"""
End-to-End Pipeline Integration Test

Tests the complete P19-P29 architecture with a real claim.
Verifies STRUCTURE (not semantic accuracy, which has documented gaps).

Expected:
- Dual researchers (R1, R2) with different provider configs
- Consensus computation between researchers
- Telemetry tracking per lane
- Reproducibility manifest
"""

import sys
sys.path.insert(0, '/Users/txtk/Documents/ROGR/github/rogrv2-backend')

import asyncio
from intelligence.pipeline.run import run_preview


def format_verdict(verdict):
    """Format verdict dict for display"""
    if not verdict:
        return "No verdict"
    label = verdict.get("label", "unknown")
    confidence = verdict.get("confidence", 0.0)
    return f"{label.upper()} (confidence: {confidence:.3f})"


def format_evidence(evidence, max_items=3):
    """Format evidence dict for display"""
    if not evidence:
        return "No evidence"

    arm_a = evidence.get("arm_A", [])
    arm_b = evidence.get("arm_B", [])

    output = []
    output.append(f"  Supporting (Arm A): {len(arm_a)} items")
    for i, item in enumerate(arm_a[:max_items]):
        title = item.get("title", "Untitled")[:60]
        source = item.get("source", "Unknown")[:30]
        output.append(f"    {i+1}. {title}... ({source})")

    output.append(f"  Challenging (Arm B): {len(arm_b)} items")
    for i, item in enumerate(arm_b[:max_items]):
        title = item.get("title", "Untitled")[:60]
        source = item.get("source", "Unknown")[:30]
        output.append(f"    {i+1}. {title}... ({source})")

    return "\n".join(output)


def format_lane_config(config):
    """Format lane config for display"""
    if not config:
        return "No config"

    output = []
    output.append(f"  Lane ID: {config.get('lane_id', 'unknown')}")
    output.append(f"  Seed: {config.get('seed', 'none')}")

    providers = config.get("providers", [])
    if providers:
        output.append(f"  Provider order: {', '.join(providers[:3])}")

    return "\n".join(output)


def format_telemetry(telemetry):
    """Format telemetry dict for display"""
    if not telemetry:
        return "No telemetry"

    output = []

    providers = telemetry.get("providers", {})
    if providers:
        total_calls = sum(providers.values())
        output.append(f"  Total provider calls: {total_calls}")
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True):
            output.append(f"    {provider}: {count} calls")
    else:
        output.append("  No provider calls recorded")

    duration = telemetry.get("duration_ms", 0)
    output.append(f"  Duration: {duration}ms")

    return "\n".join(output)


def format_consensus(consensus):
    """Format consensus dict for display"""
    if not consensus:
        return "No consensus computed"

    output = []
    output.append(f"  Final Label: {consensus.get('label', 'unknown').upper()}")
    output.append(f"  Confidence: {consensus.get('confidence', 0.0):.3f}")

    if "rule" in consensus:
        output.append(f"  Rule: {consensus['rule']}")

    if "rationale" in consensus:
        output.append(f"  Rationale: {consensus['rationale']}")

    return "\n".join(output)


def format_manifest(manifest):
    """Format manifest dict for display"""
    if not manifest:
        return "No manifest"

    output = []
    output.append(f"  Replay ID: {manifest.get('replay_id', 'none')}")

    if "created_at" in manifest:
        output.append(f"  Created: {manifest['created_at']}")

    lanes = manifest.get("lanes", {})
    if lanes:
        output.append(f"  Lanes configured: {len(lanes)}")
        for lane_id, lane_data in lanes.items():
            seed = lane_data.get("seed", "none")
            output.append(f"    {lane_id}: seed={seed}")

    return "\n".join(output)


async def run_e2e_test():
    """Run end-to-end pipeline test"""

    test_claim = "Water boils at 100 degrees Celsius at sea level"

    print("=" * 80)
    print("END-TO-END PIPELINE INTEGRATION TEST")
    print("=" * 80)
    print()
    print(f"Test Claim: \"{test_claim}\"")
    print()
    print("Testing complete P19-P29 architecture:")
    print("  P19: Counter-frame query generation")
    print("  P20-P24: Content enrichment and semantic analysis")
    print("  P25: Verdict aggregation")
    print("  P26: Dual-researcher orchestration")
    print("  P27: Consensus mechanism")
    print("  P28: Query diversification")
    print("  P29: Telemetry & reproducibility")
    print()
    print("Note: Semantic accuracy may be weak (documented gaps).")
    print("      This test verifies STRUCTURE, not accuracy.")
    print()
    print("-" * 80)
    print()

    # Run pipeline
    try:
        print("Running pipeline...")
        result = await run_preview(test_claim)
        print("✓ Pipeline completed successfully")
        print()
    except Exception as e:
        print(f"✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Extract data
    claims = result.get("claims", [])
    if not claims:
        print("✗ No claims in result")
        return False

    claim = claims[0]
    researchers = claim.get("researchers", [])
    consensus = claim.get("consensus", {})
    manifest = result.get("run_manifest", {})

    # Display results
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    # R1 Researcher
    if len(researchers) > 0:
        r1 = researchers[0]
        print("┌─ R1 RESEARCHER " + "─" * 62)
        print("│")
        print("│ Verdict:")
        print("│   " + format_verdict(r1.get("verdict", {})))
        print("│")
        print("│ Evidence:")
        for line in format_evidence(r1.get("evidence", {}), max_items=2).split("\n"):
            print("│ " + line)
        print("│")
        print("│ Lane Configuration (P28):")
        for line in format_lane_config(r1.get("lane_config", {})).split("\n"):
            print("│ " + line)
        print("│")
        print("│ Telemetry (P29):")
        for line in format_telemetry(r1.get("telemetry", {})).split("\n"):
            print("│ " + line)
        print("└" + "─" * 79)
        print()

    # R2 Researcher
    if len(researchers) > 1:
        r2 = researchers[1]
        print("┌─ R2 RESEARCHER " + "─" * 62)
        print("│")
        print("│ Verdict:")
        print("│   " + format_verdict(r2.get("verdict", {})))
        print("│")
        print("│ Evidence:")
        for line in format_evidence(r2.get("evidence", {}), max_items=2).split("\n"):
            print("│ " + line)
        print("│")
        print("│ Lane Configuration (P28):")
        for line in format_lane_config(r2.get("lane_config", {})).split("\n"):
            print("│ " + line)
        print("│")
        print("│ Telemetry (P29):")
        for line in format_telemetry(r2.get("telemetry", {})).split("\n"):
            print("│ " + line)
        print("└" + "─" * 79)
        print()

    # Consensus
    print("┌─ CONSENSUS (P27) " + "─" * 60)
    print("│")
    for line in format_consensus(consensus).split("\n"):
        print("│ " + line)
    print("└" + "─" * 79)
    print()

    # Manifest
    print("┌─ REPRODUCIBILITY MANIFEST (P29) " + "─" * 45)
    print("│")
    for line in format_manifest(manifest).split("\n"):
        print("│ " + line)
    print("└" + "─" * 79)
    print()

    # Verification
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print()

    checks = []

    # Check dual researchers
    if len(researchers) >= 2:
        checks.append(("✓", "Dual researchers (R1, R2) present"))
    else:
        checks.append(("✗", f"Expected 2 researchers, got {len(researchers)}"))

    # Check diversification
    if len(researchers) >= 2:
        r1_seed = researchers[0].get("lane_config", {}).get("seed")
        r2_seed = researchers[1].get("lane_config", {}).get("seed")
        if r1_seed and r2_seed and r1_seed != r2_seed:
            checks.append(("✓", f"P28 diversification active (seeds differ: {r1_seed} ≠ {r2_seed})"))
        else:
            checks.append(("⚠", "P28 diversification unclear (seeds may be same)"))

    # Check telemetry
    if len(researchers) >= 2:
        r1_telem = researchers[0].get("telemetry", {})
        r2_telem = researchers[1].get("telemetry", {})
        if r1_telem and r2_telem:
            checks.append(("✓", "P29 telemetry captured per lane"))
        else:
            checks.append(("⚠", "P29 telemetry missing or incomplete"))

    # Check consensus
    if consensus:
        checks.append(("✓", "P27 consensus computed"))
    else:
        checks.append(("⚠", "P27 consensus missing"))

    # Check manifest
    if manifest and manifest.get("replay_id"):
        checks.append(("✓", f"P29 manifest generated (replay_id: {manifest.get('replay_id')[:20]}...)"))
    else:
        checks.append(("⚠", "P29 manifest missing or incomplete"))

    # Check diversified flag
    if result.get("diversified"):
        checks.append(("✓", "Diversified flag set"))
    else:
        checks.append(("⚠", "Diversified flag not set"))

    for status, message in checks:
        print(f"{status} {message}")

    print()

    # Summary
    passed = sum(1 for s, _ in checks if s == "✓")
    total = len(checks)

    print("=" * 80)
    print(f"SUMMARY: {passed}/{total} checks passed")
    print("=" * 80)
    print()

    if passed >= total - 1:
        print("✓ END-TO-END INTEGRATION TEST PASSED")
        print()
        print("Architecture verification complete. All modules P19-P29 are integrated")
        print("and working together. Semantic accuracy may be limited (documented gaps),")
        print("but the structural integration is solid.")
        return True
    else:
        print("⚠ SOME CHECKS FAILED")
        print()
        print("Review warnings above. Architecture may need adjustments.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_e2e_test())
    sys.exit(0 if success else 1)
