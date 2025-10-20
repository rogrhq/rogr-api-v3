from typing import Dict, Any
# Phase 6: Evidence quality comparison (ADDED)
from intelligence.consensus.build import compare_evidence_quality, resolve_disagreement, synthesize_evidence


def compute_consensus(r1_verdict: Dict[str, Any], r2_verdict: Dict[str, Any],
                     r1_evidence: Dict[str, Any] = None, r2_evidence: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Combine two researcher verdicts into consensus.

    Args:
        r1_verdict: {"label": str, "confidence": float, "arm_strength": {...}}
        r2_verdict: {"label": str, "confidence": float, "arm_strength": {...}}

    Returns:
        {
            "label": str,
            "confidence": float,
            "rationale": {
                "rule": str,
                "support_mean": float,
                "challenge_mean": float,
                "delta": float,
                "base_conf": float,
                "bonus_or_penalty": float
            },
            "agreement": {
                "r1_label": str,
                "r2_label": str,
                "r1_conf": float,
                "r2_conf": float,
                "delta_balance": float
            }
        }
    """
    # Extract labels and confidences
    r1_label = r1_verdict.get("label", "insufficient")
    r2_label = r2_verdict.get("label", "insufficient")
    r1_conf = r1_verdict.get("confidence", 0.0)
    r2_conf = r2_verdict.get("confidence", 0.0)

    # Extract arm strengths
    r1_arm = r1_verdict.get("arm_strength", {})
    r2_arm = r2_verdict.get("arm_strength", {})

    # Build agreement info
    agreement = {
        "r1_label": r1_label,
        "r2_label": r2_label,
        "r1_conf": r1_conf,
        "r2_conf": r2_conf,
        "delta_balance": r1_arm.get("balance", 0) - r2_arm.get("balance", 0)
    }

    # Phase 6: Synthesize evidence from both researchers (ADDED)
    if r1_evidence and r2_evidence:
        r1_items_a = r1_evidence.get("arm_A", [])
        r1_items_b = r1_evidence.get("arm_B", [])
        r2_items_a = r2_evidence.get("arm_A", [])
        r2_items_b = r2_evidence.get("arm_B", [])
        consensus_evidence = synthesize_evidence(r1_items_a, r1_items_b, r2_items_a, r2_items_b)
    else:
        # Fallback: combine arms from both researchers
        consensus_evidence = {
            "arm_A": (r1_evidence.get("arm_A", []) if r1_evidence else []) +
                    (r2_evidence.get("arm_A", []) if r2_evidence else []),
            "arm_B": (r1_evidence.get("arm_B", []) if r1_evidence else []) +
                    (r2_evidence.get("arm_B", []) if r2_evidence else [])
        }

    # Disagreement logic with evidence quality
    if r1_label == r2_label:
        # Agreement: check evidence quality for bonus
        if r1_evidence and r2_evidence:
            r1_items_a = r1_evidence.get("arm_A", [])
            r1_items_b = r1_evidence.get("arm_B", [])
            r2_items_a = r2_evidence.get("arm_A", [])
            r2_items_b = r2_evidence.get("arm_B", [])
            quality_comparison = compare_evidence_quality(r1_items_a, r1_items_b, r2_items_a, r2_items_b)
            # Higher quality evidence = higher confidence boost
            avg_quality = (quality_comparison['r1']['overall'] + quality_comparison['r2']['overall']) / 2
            quality_boost = avg_quality * 0.10  # Scale to 0-0.10 bonus
            bonus = 0.10 + quality_boost  # Total: 0.10-0.20
        else:
            bonus = 0.10

        base_conf = max(r1_conf, r2_conf)
        final_conf = min(base_conf + bonus, 0.95)

        support_mean = (r1_arm.get("support", 0) + r2_arm.get("support", 0)) / 2
        challenge_mean = (r1_arm.get("challenge", 0) + r2_arm.get("challenge", 0)) / 2

        return {
            "label": r1_label,
            "confidence": final_conf,
            "rationale": {
                "rule": "agree_same_label",
                "support_mean": support_mean,
                "challenge_mean": challenge_mean,
                "delta": abs(support_mean - challenge_mean),
                "base_conf": base_conf,
                "bonus_or_penalty": bonus
            },
            "agreement": agreement
        }
    else:
        # Disagreement: resolve by evidence quality (Phase 6)
        if r1_evidence and r2_evidence:
            r1_items_a = r1_evidence.get("arm_A", [])
            r1_items_b = r1_evidence.get("arm_B", [])
            r2_items_a = r2_evidence.get("arm_A", [])
            r2_items_b = r2_evidence.get("arm_B", [])
            quality_comparison = compare_evidence_quality(r1_items_a, r1_items_b, r2_items_a, r2_items_b)
            resolution = resolve_disagreement(r1_verdict, r2_verdict, quality_comparison)

            # Use confidence directly from resolution (not as adjustment)
            label = resolution["label"]
            final_conf = resolution["confidence"]

            support_mean = (r1_arm.get("support", 0) + r2_arm.get("support", 0)) / 2
            challenge_mean = (r1_arm.get("challenge", 0) + r2_arm.get("challenge", 0)) / 2
            delta = abs(support_mean - challenge_mean)
            base_conf = max(r1_conf, r2_conf)

            return {
                "label": label,
                "confidence": final_conf,
                "rationale": {
                    "rule": "disagree_evidence_quality",
                    "support_mean": support_mean,
                    "challenge_mean": challenge_mean,
                    "delta": delta,
                    "base_conf": base_conf,
                    "bonus_or_penalty": final_conf - base_conf  # Store actual adjustment for transparency
                },
                "agreement": agreement
            }

        # Fallback: original logic if no evidence
        support_mean = (r1_arm.get("support", 0) + r2_arm.get("support", 0)) / 2
        challenge_mean = (r1_arm.get("challenge", 0) + r2_arm.get("challenge", 0)) / 2
        delta = abs(support_mean - challenge_mean)
        base_conf = max(r1_conf, r2_conf)

        if delta >= 0.20:
            # Fallback: clear gap, pick stronger side
            label = "supports" if support_mean > challenge_mean else "challenges"
            penalty = -0.05
        else:
            # Fallback: too close, mixed
            label = "mixed"
            penalty = -0.10

        final_conf = max(base_conf + penalty, 0.0)

        return {
            "label": label,
            "confidence": final_conf,
            "rationale": {
                "rule": "disagree_fallback",
                "support_mean": support_mean,
                "challenge_mean": challenge_mean,
                "delta": delta,
                "base_conf": base_conf,
            "bonus_or_penalty": penalty
        },
        "agreement": agreement
    }


if __name__ == "__main__":
    # Test agreement
    r1 = {"label": "supports", "confidence": 0.7, "arm_strength": {"support": 0.8, "challenge": 0.2, "balance": 0.6}}
    r2 = {"label": "supports", "confidence": 0.75, "arm_strength": {"support": 0.85, "challenge": 0.15, "balance": 0.7}}

    result = compute_consensus(r1, r2)
    print(f"Agreement: {result['label']}, conf={result['confidence']:.2f}, rule={result['rationale']['rule']}")
    assert result['label'] == 'supports'
    assert result['confidence'] > 0.75

    # Test disagreement
    r1 = {"label": "supports", "confidence": 0.65, "arm_strength": {"support": 0.75, "challenge": 0.25, "balance": 0.5}}
    r2 = {"label": "challenges", "confidence": 0.60, "arm_strength": {"support": 0.30, "challenge": 0.70, "balance": -0.4}}

    result = compute_consensus(r1, r2)
    print(f"Disagreement: {result['label']}, conf={result['confidence']:.2f}, rule={result['rationale']['rule']}")

    # Test mixed
    r1 = {"label": "supports", "confidence": 0.55, "arm_strength": {"support": 0.55, "challenge": 0.45, "balance": 0.1}}
    r2 = {"label": "challenges", "confidence": 0.52, "arm_strength": {"support": 0.48, "challenge": 0.52, "balance": -0.04}}

    result = compute_consensus(r1, r2)
    print(f"Mixed: {result['label']}, conf={result['confidence']:.2f}")
    assert result['label'] == 'mixed'

    print("✓ PASS")
