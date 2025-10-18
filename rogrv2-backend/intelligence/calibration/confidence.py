"""
Phase 10.1: Confidence Calibration

Ensures confidence scores correlate with accuracy.
"""

def calibrate_confidence(raw_confidence: float, claim_classification: dict,
                        arm_a_quality: dict, arm_b_quality: dict) -> float:
    """
    Calibrate confidence to ensure reliability.

    Adjustments:
    - Claim verifiability (boost for simple facts, reduce for complex)
    - Evidence quality (boost for high authority, reduce for low)
    - Arm balance (reduce if close, boost if clear winner)

    Returns:
        Calibrated confidence 0-1 (or None if below minimum)
    """

    # Start with raw confidence
    calibrated = raw_confidence

    # Adjustment 1: Claim verifiability
    verifiability = claim_classification.get('verifiability', 'HIGHLY_VERIFIABLE')

    if verifiability == 'HIGHLY_VERIFIABLE':
        # Simple facts: slight boost
        calibrated = min(1.0, calibrated * 1.05)
    elif verifiability == 'PARTIALLY_VERIFIABLE':
        # Complex: reduce confidence
        calibrated = calibrated * 0.90
    elif verifiability == 'UNVERIFIABLE':
        # Cannot verify
        return None  # Insufficient evidence

    # Adjustment 2: Evidence quality
    avg_reliability = (
        arm_a_quality.get('avg_authority', 0.5) +
        arm_b_quality.get('avg_authority', 0.5)
    ) / 2

    if avg_reliability < 0.70:
        # Low-quality sources: reduce confidence significantly
        calibrated = calibrated * 0.85
    elif avg_reliability > 0.90:
        # High-quality sources: boost confidence
        calibrated = min(1.0, calibrated * 1.08)

    # Adjustment 3: Arm balance
    arm_a_strength = arm_a_quality.get('overall', 0.0)
    arm_b_strength = arm_b_quality.get('overall', 0.0)
    arm_balance = abs(arm_a_strength - arm_b_strength)

    if arm_balance < 0.10:
        # Very close: reduce confidence significantly
        calibrated = calibrated * 0.80
    elif arm_balance > 0.30:
        # Clear winner: boost confidence
        calibrated = min(1.0, calibrated * 1.10)

    # Apply conservative floor
    min_confidence = claim_classification.get('confidence_thresholds', {}).get('min_confidence', 0.65)

    if calibrated < min_confidence:
        return None  # Below minimum

    return round(calibrated, 3)


def apply_confidence_thresholds(verdict_label: str, confidence: float,
                                arm_balance: float, claim_classification: dict) -> dict:
    """
    Apply strict thresholds. Default to 'mixed' or 'insufficient' when uncertain.

    Conservative approach:
    - Below minimum → insufficient
    - Close arms → mixed
    - Not confident enough for definitive verdict → mixed

    Returns:
        Dict with final label, confidence, rationale
    """

    min_conf = claim_classification.get('confidence_thresholds', {}).get('min_confidence', 0.65)
    mixed_threshold = claim_classification.get('confidence_thresholds', {}).get('mixed_threshold', 0.15)

    # Check 1: Below minimum
    if confidence < min_conf:
        return {
            'label': 'insufficient',
            'confidence': confidence,
            'rationale': f'Confidence {confidence:.2f} below minimum {min_conf:.2f}',
        }

    # Check 2: Arms too close
    if arm_balance < mixed_threshold:
        return {
            'label': 'mixed',
            'confidence': confidence * 0.90,  # Penalty for ambiguity
            'rationale': f'Arm balance {arm_balance:.2f} too close (threshold {mixed_threshold:.2f})',
        }

    # Check 3: Definitive verdicts need high confidence
    if verdict_label in ['supports', 'challenges']:
        if confidence < 0.85:
            # Not confident enough for definitive
            return {
                'label': 'mixed',
                'confidence': confidence * 0.92,
                'rationale': 'Confidence insufficient for definitive verdict',
            }

    # Passed all checks
    return {
        'label': verdict_label,
        'confidence': confidence,
        'rationale': 'Confidence meets all thresholds',
    }

