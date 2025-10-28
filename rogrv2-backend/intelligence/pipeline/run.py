from __future__ import annotations
import sys
from typing import Any, Dict, List, Union, Tuple
from intelligence.score.aggregate import overall_from_claims
from intelligence.ifcn.labels import label_for_score, scale_spec, explanation_from_counts
from intelligence.policy.checks import check_input
from intelligence.gather.pipeline import build_evidence_for_claim
from intelligence.content.fetch_enrichment import enrich_items_with_content
from intelligence.content.grade import attach_finding_to_item
from intelligence.content.fullread import evaluate_full_evidence
from intelligence.content.semantic_read import analyze_item
from intelligence.content.semantic_frames import analyze_frames
from intelligence.content.p25_aggregate import aggregate_verdict
from intelligence.orchestration.dual_lane import run_dual_researchers
from intelligence.planning.diversify import diversify_plan_for_lane
from intelligence.telemetry.collect import LaneTelemetry, generate_manifest
from intelligence.consensus.dual_lane import compute_consensus
# FIX-7: Edge case handlers (ADDED)
from intelligence.calibration.edge_cases import (
    detect_ambiguous_claim,
    detect_breaking_news,
    handle_conflicting_experts
)

def _to_json_primitive(x: Any) -> Any:
    """
    Deeply coerce nested structures into JSON-safe primitives.
    - dict -> dict(str -> primitive)
    - list/tuple -> list(primitive)
    - bool/int/float/str/None -> as-is
    Everything else -> str(x)
    """
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            ks = str(k)
            out[ks] = _to_json_primitive(v)
        return out
    if isinstance(x, (list, tuple)):
        return [_to_json_primitive(i) for i in x]
    # fallback
    return str(x)

async def run_single_lane_enrichment(
    claim_text: str,
    plan: Dict[str, Any],
    lane_id: str,
    telemetry: Any,
    claim_entities: list = None,
    claim_numbers: list = None,
    claim_classification: dict = None
) -> Dict[str, Any]:
    """
    Run full P19-P25 enrichment for one researcher lane.

    Args:
        claim_text: Claim being fact-checked
        plan: Diversified search plan
        lane_id: "R1" or "R2"
        telemetry: Telemetry tracker

    Returns:
        {"verdict": {...}, "evidence": {...}}
    """
    # Gather evidence (includes P19 counter-frames)
    evidence = await build_evidence_for_claim(claim_text, plan, claim_entities, claim_numbers, max_per_arm=5)

    # Track provider calls
    for arm_key in ("arm_A", "arm_B"):
        for item in evidence.get(arm_key, []):
            provider = item.get("provider")
            if provider:
                telemetry.record_provider_call(provider)

    # P22: Content enrichment
    fetch_cache = {}
    for arm_key in ("arm_A", "arm_B"):
        items = evidence.get(arm_key, [])
        if items:
            items, fetch_cache = await enrich_items_with_content(items, fetch_cache)
            evidence[arm_key] = items

    # P20-P25: Item enrichment
    for arm_key, arm_label in [("arm_A", "A"), ("arm_B", "B")]:
        for item in evidence.get(arm_key, []):
            # P20
            try:
                attach_finding_to_item(claim_text, arm_label, item)
            except Exception as e:
                print(f"❌ ERROR in attach_finding_to_item (P20 grading): {e}", file=sys.stderr)
                print(f"   Claim: {claim_text[:50]}...", file=sys.stderr)
                print(f"   Item: {item.get('title', 'NO TITLE')[:50]}", file=sys.stderr)
                import traceback
                traceback.print_exc()

    # FIX-5: Intelligent stance filtering to preserve adversarial design
    # Each arm should prioritize aligned evidence but maintain minimum threshold
    # This happens AFTER P23 assigns stances, BEFORE aggregation

    pre_filter_arm_a_count = len(evidence.get("arm_A", []))
    pre_filter_arm_b_count = len(evidence.get("arm_B", []))

    # Arm A mission: Find support evidence
    # Keep support and neutral, filter only strong contradictions
    arm_a_filtered = [
        item for item in evidence.get("arm_A", [])
        if item.get("stance", "unrelated").lower() in ["support", "neutral"]
    ]

    # Safety check: Keep minimum 3 items per arm
    # If filtering is too aggressive, keep highest-graded items
    if len(arm_a_filtered) < 3 and len(evidence.get("arm_A", [])) >= 3:
        # Keep original set sorted by item_grade
        arm_a_sorted = sorted(evidence.get("arm_A", []),
                             key=lambda x: x.get("item_grade", 0),
                             reverse=True)
        evidence["arm_A"] = arm_a_sorted[:max(3, len(arm_a_filtered))]
        print(f"[Stance Filter] Arm A: Filtering too aggressive, keeping top {len(evidence['arm_A'])} by grade", file=sys.stderr)
    else:
        evidence["arm_A"] = arm_a_filtered

    # Arm B mission: Find challenge evidence
    # Keep challenge/refute and neutral, filter only strong support
    arm_b_filtered = [
        item for item in evidence.get("arm_B", [])
        if item.get("stance", "unrelated").lower() in ["challenge", "refute", "neutral"]
    ]

    # Safety check: Keep minimum 3 items per arm
    if len(arm_b_filtered) < 3 and len(evidence.get("arm_B", [])) >= 3:
        # Keep original set sorted by item_grade
        arm_b_sorted = sorted(evidence.get("arm_B", []),
                             key=lambda x: x.get("item_grade", 0),
                             reverse=True)
        evidence["arm_B"] = arm_b_sorted[:max(3, len(arm_b_filtered))]
        print(f"[Stance Filter] Arm B: Filtering too aggressive, keeping top {len(evidence['arm_B'])} by grade", file=sys.stderr)
    else:
        evidence["arm_B"] = arm_b_filtered

    # Log filtering results
    post_filter_arm_a_count = len(evidence["arm_A"])
    post_filter_arm_b_count = len(evidence["arm_B"])

    if pre_filter_arm_a_count > post_filter_arm_a_count:
        filtered_a = pre_filter_arm_a_count - post_filter_arm_a_count
        print(f"[Stance Filter] Arm A: Removed {filtered_a} misaligned items ({pre_filter_arm_a_count} → {post_filter_arm_a_count})", file=sys.stderr)

    if pre_filter_arm_b_count > post_filter_arm_b_count:
        filtered_b = pre_filter_arm_b_count - post_filter_arm_b_count
        print(f"[Stance Filter] Arm B: Removed {filtered_b} misaligned items ({pre_filter_arm_b_count} → {post_filter_arm_b_count})", file=sys.stderr)

    # Note: Minimum 3 items per arm ensures sufficient evidence for verdict
    # If an arm has <3 after filtering, we keep highest-quality original items

    # P25: Aggregate
    try:
        verdict = aggregate_verdict(
            claim_text,
            evidence.get("arm_A", []),
            evidence.get("arm_B", []),
            claim_numbers,  # Pass through from function parameter (added in TASK 1.2)
            delta=0.15
        )
    except:
        verdict = {"label": "insufficient", "confidence": 0.0}

    return {"verdict": verdict, "evidence": evidence}

# NOTE: preview handler calls run_preview() (async), updated for async pipeline
async def run_preview(text: str, test_mode: bool = False) -> Dict[str, Any]:
    """Run preview with dual researchers."""

    # Create claim
    claim = {"id": "c-0", "text": text.strip(), "tier": "primary"}

    # Enrich claim with parsed entities/numbers/cues
    from intelligence.analyze.enrich import enrich_claim_obj
    claim = enrich_claim_obj(claim)

    # Add claim_type detection
    from intelligence.claims.interpret import detect_claim_type
    claim["claim_type"] = detect_claim_type(claim)

    # Phase 8: Classify claim (ADDED)
    from intelligence.preprocess.classify import classify_claim
    classification = classify_claim(
        claim_text=text,
        entities=claim.get("entities", []),
        numbers=claim.get("numbers", [])
    )
    claim["classification"] = classification

    # Early exit for unverifiable claims
    if classification.get("verifiability") == "UNVERIFIABLE":
        # Generate summary for unverifiable claim
        summary = explanation_from_counts(
            text.strip(),
            {"support": 0, "refute": 0, "neutral": 0},
            []
        )

        # Return early with insufficient verdict
        return {
            "claims": [{
                "id": "c-0",
                "text": text.strip(),
                "tier": "primary",
                "classification": classification,
                "verdict": {
                    "label": "insufficient",
                    "confidence": 0.0,
                    "rationale": classification.get("note", "Unverifiable claim type")
                },
                "evidence": {},
                "researchers": [],
                "summary": summary
            }],
            "run_manifest": {},
            "diversified": False,
            "overall": {"score": 50, "label": "Mixed"}
        }

    # Build base search plan
    from intelligence.strategy.plan_v2 import build_search_plans_v2
    base_plan = build_search_plans_v2(claim)

    # Extract claim data for pipeline functions
    claim_entities = claim.get("entities", [])

    # Convert numbers dict to list of {"value": ...} dicts (bug fix for TASK 2.1)
    numbers_dict = claim.get("numbers", {})
    claim_numbers = []
    if isinstance(numbers_dict, dict):
        # Add percents
        for percent in numbers_dict.get('percents', []):
            claim_numbers.append({"value": percent})
        # Add years
        for year in numbers_dict.get('years', []):
            claim_numbers.append({"value": year})
        # Add number_units (tuples of (value, unit))
        for num_unit in numbers_dict.get('number_units', []):
            if isinstance(num_unit, (list, tuple)) and len(num_unit) >= 2:
                claim_numbers.append({"value": num_unit[0], "unit": num_unit[1]})
            elif isinstance(num_unit, (list, tuple)) and len(num_unit) == 1:
                claim_numbers.append({"value": num_unit[0]})
            else:
                # Fallback if structure is different
                claim_numbers.append({"value": num_unit})
    elif isinstance(numbers_dict, list):
        # Already a list
        claim_numbers = numbers_dict
    else:
        claim_numbers = []
    # Extract claim classification (from TASK 1.1)
    claim_classification = claim.get("classification", None)

    # Run dual researchers (P26)
    dual_result = await run_dual_researchers(
        claim_text=text,
        base_plan=base_plan,
        enrichment_pipeline=lambda claim_text, plan, lane_id, telemetry:
            run_single_lane_enrichment(claim_text, plan, lane_id, telemetry, claim_entities, claim_numbers, claim_classification),
        diversify_fn=diversify_plan_for_lane,
        telemetry_class=LaneTelemetry
    )

    # Extract researchers
    researchers = dual_result.get("researchers", [])

    # Build aggregation metadata from researchers' verdicts (FIX-4)
    # Note: Design spec describes compute_aggregation() function which doesn't exist.
    # Actual implementation uses aggregate_verdict() which computes same data.
    # This extracts and reformats for diagnostic transparency.
    aggregation_metadata = {}
    if len(researchers) >= 2:
        r1_verdict = researchers[0].get("verdict", {})
        r2_verdict = researchers[1].get("verdict", {})
        r1_evidence = researchers[0].get("evidence", {})
        r2_evidence = researchers[1].get("evidence", {})

        # Extract arm strengths from verdicts (averaged across R1 and R2)
        r1_arm_strength = r1_verdict.get("arm_strength", {})
        r2_arm_strength = r2_verdict.get("arm_strength", {})

        arm_a_strength = (r1_arm_strength.get("support", 0) + r2_arm_strength.get("support", 0)) / 2
        arm_b_strength = (r1_arm_strength.get("challenge", 0) + r2_arm_strength.get("challenge", 0)) / 2
        arm_a_base = (r1_arm_strength.get("support_base", 0) + r2_arm_strength.get("support_base", 0)) / 2
        arm_b_base = (r1_arm_strength.get("challenge_base", 0) + r2_arm_strength.get("challenge_base", 0)) / 2

        # Extract quality multipliers (averaged across R1 and R2)
        r1_multipliers = r1_verdict.get("quality_multipliers", {})
        r2_multipliers = r2_verdict.get("quality_multipliers", {})

        avg_diversity = (r1_multipliers.get("diversity", 1.0) + r2_multipliers.get("diversity", 1.0)) / 2
        avg_consistency = (r1_multipliers.get("consistency", 1.0) + r2_multipliers.get("consistency", 1.0)) / 2
        avg_breadth = (r1_multipliers.get("breadth", 1.0) + r2_multipliers.get("breadth", 1.0)) / 2

        # Compute per-arm average item grades
        arm_a_items = r1_evidence.get("arm_A", []) + r2_evidence.get("arm_A", [])
        arm_b_items = r1_evidence.get("arm_B", []) + r2_evidence.get("arm_B", [])

        arm_a_grades = [item.get("item_grade", 0) for item in arm_a_items if item.get("item_grade", 0) > 0]
        arm_b_grades = [item.get("item_grade", 0) for item in arm_b_items if item.get("item_grade", 0) > 0]

        avg_grade_a = sum(arm_a_grades) / len(arm_a_grades) if arm_a_grades else 0.0
        avg_grade_b = sum(arm_b_grades) / len(arm_b_grades) if arm_b_grades else 0.0

        # Compute per-arm domain diversity
        from intelligence.content.fullread import _extract_base_domain

        def compute_domain_diversity(items):
            """Calculate unique domains / total items for one arm"""
            domains = []
            for item in items:
                url = item.get('url', '')
                if url:
                    domain = _extract_base_domain(url)
                    if domain:
                        domains.append(domain)
            if not domains:
                return 0.0
            unique = len(set(domains))
            total = len(domains)
            return unique / total

        arm_a_domain_diversity = compute_domain_diversity(arm_a_items)
        arm_b_domain_diversity = compute_domain_diversity(arm_b_items)

        # Build aggregation structures matching diagnostic expectations
        # Enhancement: Include individual R1/R2 values for full transparency
        aggregation_metadata = {
            "arm_A_aggregation": {
                "arm_strength": float(arm_a_strength),              # AVERAGED (consensus uses this)
                "r1_arm_strength": float(r1_arm_strength.get("support", 0)),  # R1's individual value
                "r2_arm_strength": float(r2_arm_strength.get("support", 0)),  # R2's individual value
                "base_strength": float(arm_a_base),
                "r1_base_strength": float(r1_arm_strength.get("support_base", 0)),
                "r2_base_strength": float(r2_arm_strength.get("support_base", 0)),
                "avg_grade": float(avg_grade_a),
                "domain_diversity": float(arm_a_domain_diversity),
                "consistency": float(avg_consistency),     # Global multiplier
                "breadth": float(avg_breadth),            # Global multiplier
                "diversity": float(avg_diversity)          # Global multiplier (for transparency)
            },
            "arm_B_aggregation": {
                "arm_strength": float(arm_b_strength),              # AVERAGED (consensus uses this)
                "r1_arm_strength": float(r1_arm_strength.get("challenge", 0)),  # R1's individual value
                "r2_arm_strength": float(r2_arm_strength.get("challenge", 0)),  # R2's individual value
                "base_strength": float(arm_b_base),
                "r1_base_strength": float(r1_arm_strength.get("challenge_base", 0)),
                "r2_base_strength": float(r2_arm_strength.get("challenge_base", 0)),
                "avg_grade": float(avg_grade_b),
                "domain_diversity": float(arm_b_domain_diversity),
                "consistency": float(avg_consistency),     # Global multiplier
                "breadth": float(avg_breadth),            # Global multiplier
                "diversity": float(avg_diversity)          # Global multiplier (for transparency)
            }
        }

    # Compute consensus (P27)
    if len(researchers) >= 2:
        r1_verdict = researchers[0].get("verdict", {})
        r2_verdict = researchers[1].get("verdict", {})
        r1_evidence = researchers[0].get("evidence", {})
        r2_evidence = researchers[1].get("evidence", {})
        consensus = compute_consensus(r1_verdict, r2_verdict, r1_evidence, r2_evidence)
    else:
        consensus = dual_result.get("verdict", {})

    # Phase 10: Confidence calibration (ADDED)
    from intelligence.calibration.confidence import calibrate_confidence, apply_confidence_thresholds

    # Extract quality metrics from researchers
    if len(researchers) >= 2:
        r1_evidence = researchers[0].get("evidence", {})
        r2_evidence = researchers[1].get("evidence", {})

        # Extract credibility scores from items
        # NOTE: Items don't have "authority_score" attribute (verified in DATA_STRUCTURE_VERIFICATION.md)
        # Instead, use "credibility" which exists on all items from P21
        arm_a_items = r1_evidence.get("arm_A", []) + r2_evidence.get("arm_A", [])
        arm_b_items = r1_evidence.get("arm_B", []) + r2_evidence.get("arm_B", [])

        # Use credibility scores (authority_score doesn't exist on items)
        arm_a_authorities = [item.get("credibility", 0.5) for item in arm_a_items]
        arm_b_authorities = [item.get("credibility", 0.5) for item in arm_b_items]

        # Calculate arm quality
        arm_a_quality = {
            "overall": (r1_verdict.get("arm_strength", {}).get("support", 0) +
                       r2_verdict.get("arm_strength", {}).get("support", 0)) / 2,
            "avg_authority": sum(arm_a_authorities) / len(arm_a_authorities) if arm_a_authorities else 0.5
        }
        arm_b_quality = {
            "overall": (r1_verdict.get("arm_strength", {}).get("challenge", 0) +
                       r2_verdict.get("arm_strength", {}).get("challenge", 0)) / 2,
            "avg_authority": sum(arm_b_authorities) / len(arm_b_authorities) if arm_b_authorities else 0.5
        }

        # FIX-7: Edge case detection (ADDED)
        # Check for ambiguous claims
        ambiguous_result = detect_ambiguous_claim(text, claim_entities, claim_numbers)

        # Check for breaking news
        all_evidence_items = arm_a_items + arm_b_items
        breaking_news_result = detect_breaking_news(all_evidence_items)

        # Check for conflicting experts
        conflict_result = handle_conflicting_experts(arm_a_items, arm_b_items)

        # Calibrate confidence
        claim_classification = claim.get("classification", {
            "verifiability": "HIGHLY_VERIFIABLE",
            "confidence_thresholds": {"min_confidence": 0.65, "mixed_threshold": 0.15}
        })

        raw_confidence = consensus.get("confidence", 0.0)
        calibrated_confidence = calibrate_confidence(
            raw_confidence,
            claim_classification,
            arm_a_quality,
            arm_b_quality
        )

        # Handle calibration failure (below minimum)
        if calibrated_confidence is None:
            consensus["label"] = "insufficient"
            consensus["confidence"] = raw_confidence
            consensus["calibration_note"] = "Below minimum confidence threshold"
        else:
            # Apply thresholds
            arm_balance = abs(arm_a_quality["overall"] - arm_b_quality["overall"])
            final_verdict = apply_confidence_thresholds(
                consensus["label"],
                calibrated_confidence,
                arm_balance,
                claim_classification
            )

            # Update consensus
            consensus["label"] = final_verdict["label"]
            consensus["confidence"] = final_verdict["confidence"]
            consensus["calibration_note"] = final_verdict["rationale"]

            # FIX-7: Apply edge case adjustments (ADDED)
            edge_case_notes = []

            # If ambiguous, reduce confidence
            if ambiguous_result.get("ambiguous"):
                consensus["confidence"] = consensus["confidence"] * 0.85
                edge_case_notes.append(f"Ambiguous: {ambiguous_result.get('reason')}")

            # If breaking news, reduce confidence
            if breaking_news_result.get("breaking_news"):
                consensus["confidence"] = consensus["confidence"] * 0.90
                edge_case_notes.append("Breaking news: situation may be evolving")

            # If conflicting experts, override verdict
            if conflict_result.get("is_expert_conflict"):
                consensus["label"] = "mixed"
                consensus["confidence"] = 0.75
                edge_case_notes.append("High-quality sources disagree")

            # Add notes if any edge cases detected
            if edge_case_notes:
                existing_note = consensus.get("calibration_note", "")
                consensus["calibration_note"] = existing_note + " | Edge cases: " + "; ".join(edge_case_notes)

    # Generate manifest (P29)
    if len(researchers) >= 2:
        r1_config = researchers[0].get("lane_config", {})
        r2_config = researchers[1].get("lane_config", {})
        manifest = generate_manifest(text, r1_config, r2_config)
    else:
        manifest = {"replay_id": "error", "lanes": {}}

    # Generate summary from evidence
    evidence = dual_result.get("evidence", {})
    arm_a = evidence.get("arm_A", [])
    arm_b = evidence.get("arm_B", [])

    # Count by stance
    support_count = sum(1 for item in arm_a if item.get("stance") == "support")
    refute_count = sum(1 for item in arm_b if item.get("stance") == "refute")
    all_items = arm_a + arm_b
    neutral_count = sum(1 for item in all_items if item.get("stance") in ["neutral", "unrelated"])

    # Get top 3 sources by credibility
    sorted_items = sorted(all_items, key=lambda x: x.get("credibility", 0), reverse=True)[:3]
    top_sources = [(item.get("title", "Unknown"), item.get("domain", "unknown")) for item in sorted_items]

    # Generate summary
    summary = explanation_from_counts(
        text.strip(),
        {"support": support_count, "refute": refute_count, "neutral": neutral_count},
        top_sources
    )

    # Build response
    claim_obj = {
        "id": "c-0",
        "text": text.strip(),
        "tier": "primary",
        "verdict": dual_result.get("verdict", {}),
        "evidence": dual_result.get("evidence", {}),
        "researchers": researchers,
        "consensus": consensus,  # NEW
        "summary": summary,
        **aggregation_metadata  # FIX-4: Unpack arm_A_aggregation and arm_B_aggregation
    }

    # Compute overall verdict from consensus
    overall_score = int(consensus.get("confidence", 0.5) * 100)
    overall_label = label_for_score(overall_score)

    return {
        "claims": [claim_obj],
        "run_manifest": manifest,  # NEW
        "diversified": True,
        "overall": {"score": overall_score, "label": overall_label}
    }