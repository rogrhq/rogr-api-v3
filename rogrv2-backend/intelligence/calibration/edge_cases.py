"""
Phase 10.2: Edge Case Handlers

Handles special cases that break normal verification logic.
"""

import re

def detect_ambiguous_claim(claim_text: str, entities: list, numbers: list) -> dict:
    """
    Detect claims that are inherently ambiguous.

    Ambiguity markers:
    - Vague quantifiers (many, most, some, few)
    - Missing context
    - Incomplete comparisons

    Returns:
        Dict with ambiguous flag and reason
    """

    # Vague quantifiers
    vague_terms = ['many', 'most', 'some', 'few', 'often', 'rarely',
                  'usually', 'sometimes', 'generally', 'typically']

    if any(term in claim_text.lower() for term in vague_terms):
        return {
            'ambiguous': True,
            'reason': 'vague_quantifier',
            'recommendation': 'Request more specific claim',
        }

    # Missing anchors (no entities or numbers)
    if not entities and not numbers:
        return {
            'ambiguous': True,
            'reason': 'no_anchors',
            'recommendation': 'Claim lacks specific entities or numbers',
        }

    # Incomplete comparison ("more" without "than")
    if 'more' in claim_text.lower() and 'than' not in claim_text.lower():
        return {
            'ambiguous': True,
            'reason': 'incomplete_comparison',
            'recommendation': 'Comparison lacks baseline',
        }

    return {'ambiguous': False}


def handle_conflicting_experts(arm_a_items: list, arm_b_items: list) -> dict:
    """
    Handle cases where high-authority sources disagree.

    If both arms have 2+ high-authority sources (>0.85), this is
    genuine expert disagreement, not a fact-checkable claim.

    Returns:
        Dict with conflict status and verdict
    """

    # Count high-authority sources per arm
    arm_a_experts = [i for i in arm_a_items
                    if i.get('source_reliability', {}).get('score', 0) > 0.85]
    arm_b_experts = [i for i in arm_b_items
                    if i.get('source_reliability', {}).get('score', 0) > 0.85]

    if len(arm_a_experts) >= 2 and len(arm_b_experts) >= 2:
        # Genuine expert disagreement
        return {
            'conflicting_experts': True,
            'verdict': {
                'label': 'mixed',
                'confidence': 0.75,  # High confidence in "mixed"
                'rationale': 'High-quality sources disagree - genuine scientific/expert debate',
            },
        }

    return {'conflicting_experts': False}


def detect_breaking_news(evidence_items: list) -> dict:
    """
    Detect if this is breaking/emerging news (situation evolving).

    If 80%+ of evidence is <7 days old, situation may be fluid.

    Returns:
        Dict with breaking_news flag
    """
    from datetime import datetime, timedelta

    if not evidence_items:
        return {'breaking_news': False}

    # Check publication dates (would need actual date extraction)
    # Placeholder logic
    recent_count = 0
    total_with_dates = 0

    for item in evidence_items:
        # In real implementation, would extract and compare dates
        # For now, placeholder
        pass

    # If we had real dates, would check:
    # recent_count = items published < 7 days ago
    # if recent_count / total_with_dates >= 0.8: breaking news

    return {
        'breaking_news': False,  # Placeholder
        'note': 'Date extraction needed for full implementation',
    }

