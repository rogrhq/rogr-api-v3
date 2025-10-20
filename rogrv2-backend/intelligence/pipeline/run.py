from __future__ import annotations
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
    claim_numbers: list = None
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
            except:
                pass

            # P21
            if item.get("content"):
                try:
                    evaluate_full_evidence(claim_text, item)
                except:
                    pass

            # P23
            if item.get("content"):
                try:
                    # Set threshold based on lane (R1=Skeptic strict, R2=Explorer lenient)
                    stance_threshold = 0.70 if lane_id == "R1" else 0.50
                    analyze_item(claim_text, item, window=3, stance_threshold=stance_threshold)
                except:
                    pass

            # P24
            content = item.get("content") or ""
            if content:
                try:
                    frames = analyze_frames(claim_text, content, window=3)
                    item.update(frames)
                except:
                    pass

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
                "researchers": []
            }],
            "run_manifest": {},
            "diversified": False
        }

    # Build base search plan
    from intelligence.strategy.plan_v2 import build_search_plans_v2
    base_plan = build_search_plans_v2(claim)

    # Extract claim data for pipeline functions
    claim_entities = claim.get("entities", [])
    claim_numbers = claim.get("numbers", [])

    # Run dual researchers (P26)
    dual_result = await run_dual_researchers(
        claim_text=text,
        base_plan=base_plan,
        enrichment_pipeline=lambda claim_text, plan, lane_id, telemetry:
            run_single_lane_enrichment(claim_text, plan, lane_id, telemetry, claim_entities, claim_numbers),
        diversify_fn=diversify_plan_for_lane,
        telemetry_class=LaneTelemetry
    )

    # Extract researchers
    researchers = dual_result.get("researchers", [])

    # Compute consensus (P27)
    if len(researchers) >= 2:
        r1_verdict = researchers[0].get("verdict", {})
        r2_verdict = researchers[1].get("verdict", {})
        consensus = compute_consensus(r1_verdict, r2_verdict)
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

    # Generate manifest (P29)
    if len(researchers) >= 2:
        r1_config = researchers[0].get("lane_config", {})
        r2_config = researchers[1].get("lane_config", {})
        manifest = generate_manifest(text, r1_config, r2_config)
    else:
        manifest = {"replay_id": "error", "lanes": {}}

    # Build response
    claim_obj = {
        "id": "c-0",
        "text": text.strip(),
        "tier": "primary",
        "verdict": dual_result.get("verdict", {}),
        "evidence": dual_result.get("evidence", {}),
        "researchers": researchers,
        "consensus": consensus  # NEW
    }

    return {
        "claims": [claim_obj],
        "run_manifest": manifest,  # NEW
        "diversified": True
    }