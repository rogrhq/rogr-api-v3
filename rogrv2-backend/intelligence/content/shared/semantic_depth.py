"""
Phase 9.3: Semantic Depth Enhancement

Detects negation, hedging, and causal relationships.
"""

import re

def detect_negation(text: str) -> bool:
    """
    Detect if statement is negated.

    Returns:
        True if negation present
    """

    negation_patterns = [
        r'\bnot\b', r'\bno\b', r'\bnever\b', r'\bnone\b',
        r'\bneither\b', r'\bdoes not\b', r'\bdoesn\'t\b',
        r'\bdidn\'t\b', r'\bwon\'t\b', r'\bcannot\b',
        r'\bcan\'t\b', r'\bwithout\b', r'\bfail\b',
    ]

    for pattern in negation_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def detect_hedging(text: str) -> dict:
    """
    Detect hedging language that weakens certainty.

    Returns:
        Dict with hedge_present, confidence_penalty, hedge_words
    """

    hedging_patterns = [
        r'\bmay\b', r'\bmight\b', r'\bcould\b', r'\bpossibly\b',
        r'\bperhaps\b', r'\bprobably\b', r'\blikely\b',
        r'\bsuggests\b', r'\bindicates\b', r'\bappears\b',
        r'\bseems\b', r'\bsome evidence\b', r'\btends to\b',
    ]

    hedge_count = 0
    hedge_words = []

    for pattern in hedging_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            hedge_count += len(matches)
            hedge_words.extend(matches)

    # Calculate confidence penalty (0-1, where 1 = full confidence)
    # Each hedge reduces confidence by 10%, min 0.5
    confidence = max(0.5, 1.0 - (hedge_count * 0.1))

    return {
        'hedge_present': hedge_count > 0,
        'hedge_count': hedge_count,
        'confidence_penalty': confidence,
        'hedge_words': hedge_words,
    }


def check_negation_agreement(claim_text: str, evidence_text: str) -> dict:
    """
    Check if negation matches between claim and evidence.

    If claim is negated and evidence is not (or vice versa),
    they have opposite meanings.

    Returns:
        Dict with agreement status
    """

    claim_negated = detect_negation(claim_text)
    evidence_negated = detect_negation(evidence_text)

    agreement = claim_negated == evidence_negated

    return {
        'claim_negated': claim_negated,
        'evidence_negated': evidence_negated,
        'negation_agreement': agreement,
        'semantic_flip': not agreement,  # True if meanings are opposite
    }

