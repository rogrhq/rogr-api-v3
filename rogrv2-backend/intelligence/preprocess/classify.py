"""
Phase 8.2: Claim Classification System

Classifies claims to set appropriate verification strategies.
"""

def classify_claim(claim_text: str, entities: list = None, numbers: list = None) -> dict:
    """
    Classify claim into category.

    Categories:
    - SIMPLE_FACTUAL: Basic facts (highly verifiable)
    - COMPLEX_FACTUAL: Statistics, multi-part (verifiable)
    - HISTORICAL: Past events (verifiable with records)
    - SCIENTIFIC: Scientific facts (verifiable with studies)
    - POLICY: Laws, regulations (partially verifiable)
    - OPINION: Subjective (unverifiable)
    - PREDICTION: Future events (unverifiable)

    Returns:
        Dict with classification and confidence thresholds
    """
    import re

    claim_lower = claim_text.lower()

    # Opinion markers
    opinion_markers = [
        'should', 'ought', 'must', 'better', 'worse', 'good', 'bad',
        'right', 'wrong', 'best', 'worst', 'I think', 'in my opinion',
        'believe', 'feel',
    ]

    # Prediction markers
    prediction_markers = [
        'will', 'going to', 'predict', 'forecast', 'expect', 'likely',
        'probably', 'may', 'might', 'could',
    ]

    # Historical markers
    historical_markers = [
        r'\d{4}',  # Years
        'was', 'were', 'happened', 'occurred', 'began', 'ended',
        'ago', 'past', 'history', 'historical',
    ]

    # Scientific markers
    scientific_markers = [
        'study', 'research', 'experiment', 'evidence', 'data',
        'molecular', 'chemical', 'biological', 'physics', 'theory',
        'hypothesis', 'scientific',
    ]

    # Check for opinion
    if any(marker in claim_lower for marker in opinion_markers):
        return {
            'category': 'OPINION',
            'verifiability': 'UNVERIFIABLE',
            'confidence_thresholds': {
                'min_confidence': 0.95,  # Very high bar (probably shouldn't verify)
            },
            'note': 'Subjective claim - opinion or value judgment',
        }

    # Check for prediction
    if any(marker in claim_lower for marker in prediction_markers):
        # Check if it's about future
        future_markers = ['next', 'future', '2025', '2026', '2027', '2028', '2029', '2030']
        if any(marker in claim_lower for marker in future_markers):
            return {
                'category': 'PREDICTION',
                'verifiability': 'UNVERIFIABLE',
                'confidence_thresholds': {
                    'min_confidence': 0.95,
                },
                'note': 'Future prediction - cannot verify',
            }

    # Check for scientific
    if any(marker in claim_lower for marker in scientific_markers):
        return {
            'category': 'SCIENTIFIC',
            'verifiability': 'HIGHLY_VERIFIABLE',
            'confidence_thresholds': {
                'min_confidence': 0.70,
                'mixed_threshold': 0.15,
            },
            'note': 'Scientific claim - verify with studies',
        }

    # Check for historical
    if any(re.search(marker, claim_lower) for marker in historical_markers):
        return {
            'category': 'HISTORICAL',
            'verifiability': 'HIGHLY_VERIFIABLE',
            'confidence_thresholds': {
                'min_confidence': 0.70,
                'mixed_threshold': 0.15,
            },
            'note': 'Historical claim - verify with records',
        }

    # Check for complex (has numbers/statistics)
    if numbers and len(numbers) > 0:
        return {
            'category': 'COMPLEX_FACTUAL',
            'verifiability': 'HIGHLY_VERIFIABLE',
            'confidence_thresholds': {
                'min_confidence': 0.70,
                'mixed_threshold': 0.15,
            },
            'note': 'Statistical claim - verify with data',
        }

    # Default: Simple factual
    return {
        'category': 'SIMPLE_FACTUAL',
        'verifiability': 'HIGHLY_VERIFIABLE',
        'confidence_thresholds': {
            'min_confidence': 0.65,
            'mixed_threshold': 0.15,
        },
        'note': 'Simple factual claim',
    }

