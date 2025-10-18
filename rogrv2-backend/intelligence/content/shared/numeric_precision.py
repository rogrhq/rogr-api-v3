"""
Phase 9.1: Numeric Precision Handling

Smart number matching with contextual precision.
"""

def match_number_with_precision(claim_number: float, evidence_number: float,
                                claim_precision: int = None) -> dict:
    """
    Check if evidence number matches claim number within precision bounds.

    Precision levels:
    - Integer (8): ±0.5 (matches 7.5-8.5)
    - 1 decimal (8.0): ±0.05 (matches 7.95-8.05)
    - 2 decimals (8.00): ±0.005 (matches 7.995-8.005)

    Args:
        claim_number: Number from claim
        evidence_number: Number from evidence
        claim_precision: Decimal places in original claim (None = auto-detect)

    Returns:
        Dict with match status and details
    """

    # Auto-detect precision if not provided
    if claim_precision is None:
        claim_str = str(claim_number)
        if '.' in claim_str:
            claim_precision = len(claim_str.split('.')[1])
        else:
            claim_precision = 0

    # Set tolerance based on precision
    if claim_precision == 0:
        # Integer precision
        tolerance = 0.5
        tolerance_pct = 0.05  # 5%
    elif claim_precision == 1:
        tolerance = 0.05
        tolerance_pct = 0.01  # 1%
    elif claim_precision == 2:
        tolerance = 0.005
        tolerance_pct = 0.001  # 0.1%
    else:
        # 3+ decimals: very precise
        tolerance = 0.0005
        tolerance_pct = 0.0001  # 0.01%

    # Calculate absolute difference
    abs_diff = abs(claim_number - evidence_number)

    # Calculate percentage difference (if claim is non-zero)
    if claim_number != 0:
        pct_diff = abs_diff / abs(claim_number)
    else:
        pct_diff = 0 if evidence_number == 0 else 1.0

    # Match if within tolerance (use stricter of absolute or percentage)
    match = abs_diff <= tolerance or pct_diff <= tolerance_pct

    return {
        'match': match,
        'abs_diff': round(abs_diff, 4),
        'pct_diff': round(pct_diff, 4),
        'tolerance': tolerance,
        'precision_level': claim_precision,
        'match_type': 'exact' if abs_diff == 0 else 'close' if match else 'mismatch',
    }


def extract_and_match_numbers(claim_text: str, evidence_text: str) -> dict:
    """
    Extract numbers from both texts and find matches.

    Returns:
        Dict with matched_numbers, unmatched_claim_numbers, etc.
    """
    import re

    def extract_numbers_with_precision(text):
        """Extract numbers preserving precision"""
        # Pattern for numbers with optional decimals and units
        pattern = r'\b(\d+\.?\d*)\s*(%|percent|million|billion|thousand)?\b'
        matches = re.findall(pattern, text, re.IGNORECASE)

        numbers = []
        for num_str, unit in matches:
            try:
                value = float(num_str)

                # Determine precision
                if '.' in num_str:
                    precision = len(num_str.split('.')[1])
                else:
                    precision = 0

                numbers.append({
                    'value': value,
                    'precision': precision,
                    'unit': unit.lower() if unit else None,
                    'original': num_str,
                })
            except ValueError:
                continue

        return numbers

    claim_numbers = extract_numbers_with_precision(claim_text)
    evidence_numbers = extract_numbers_with_precision(evidence_text)

    # Match claim numbers to evidence numbers
    matched = []
    unmatched_claim = []

    for claim_num in claim_numbers:
        best_match = None
        best_match_score = 0.0

        for evidence_num in evidence_numbers:
            # Check if units match (if present)
            if claim_num['unit'] and evidence_num['unit']:
                if claim_num['unit'] != evidence_num['unit']:
                    continue  # Different units, skip

            # Check precision match
            match_result = match_number_with_precision(
                claim_num['value'],
                evidence_num['value'],
                claim_num['precision']
            )

            if match_result['match']:
                # Calculate match score (closer = better)
                score = 1.0 - match_result['pct_diff']
                if score > best_match_score:
                    best_match = evidence_num
                    best_match_score = score
                    claim_num['match_result'] = match_result

        if best_match:
            matched.append({
                'claim': claim_num,
                'evidence': best_match,
                'score': best_match_score,
            })
        else:
            unmatched_claim.append(claim_num)

    return {
        'matched_count': len(matched),
        'unmatched_claim_count': len(unmatched_claim),
        'matched_numbers': matched,
        'unmatched_claim_numbers': unmatched_claim,
        'match_rate': len(matched) / len(claim_numbers) if claim_numbers else 0.0,
    }

