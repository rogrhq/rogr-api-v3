from typing import Dict, Any


def compute_consensus(r1_verdict: Dict[str, Any], r2_verdict: Dict[str, Any]) -> Dict[str, Any]:
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

    # Agreement case
    if r1_label == r2_label:
        base_conf = max(r1_conf, r2_conf)
        bonus = 0.10
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

    # Disagreement case
    support_mean = (r1_arm.get("support", 0) + r2_arm.get("support", 0)) / 2
    challenge_mean = (r1_arm.get("challenge", 0) + r2_arm.get("challenge", 0)) / 2
    delta = abs(support_mean - challenge_mean)

    base_conf = max(r1_conf, r2_conf)

    # Clear gap - pick stronger side
    if delta >= 0.20:
        label = "supports" if support_mean > challenge_mean else "challenges"
        penalty = -0.05
        final_conf = max(base_conf + penalty, 0.0)

        return {
            "label": label,
            "confidence": final_conf,
            "rationale": {
                "rule": "disagree_gap_select",
                "support_mean": support_mean,
                "challenge_mean": challenge_mean,
                "delta": delta,
                "base_conf": base_conf,
                "bonus_or_penalty": penalty
            },
            "agreement": agreement
        }

    # Too close - mixed
    penalty = -0.10
    final_conf = max(base_conf + penalty, 0.0)

    return {
        "label": "mixed",
        "confidence": final_conf,
        "rationale": {
            "rule": "disagree_mixed",
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
