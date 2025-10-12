"""Shared frame structure - extracted from P24 and enhanced for multi-domain"""

from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Frame:
    """
    Semantic frame structure - from P24 lines 23-35, enhanced for multi-domain.

    A frame represents the semantic signature of a claim:
    - Scientific: phenomenon + number + unit + condition
    - Policy: entity + action + number + unit + timeframe
    """
    # Core components (from P24)
    phenomenon: Optional[str] = None  # Scientific: "boiling point", "melting point"
    entity: Optional[str] = None      # Policy: "Austin budget", "GDP"
    action: Optional[str] = None      # increase, decrease, change
    number: Optional[float] = None    # numeric value
    unit: Optional[str] = None        # °C, %, dollars

    # Contextual components (enhanced)
    condition: Optional[str] = None   # sea level, room temperature, fy2024
    timeframe: Optional[str] = None   # 2024, Q1, last year
    direction: Optional[str] = None   # up, down, stable

    # Metadata
    domain: str = "generic"  # scientific, policy, generic
    confidence: float = 1.0

def extract_frame(text, domain="generic"):
    """
    Extract semantic frame from text.
    Based on P24 line 38, enhanced with domain awareness.
    """
    import re
    from intelligence.content.shared.vocabulary import INC_VERBS, DEC_VERBS

    frame = Frame(domain=domain)
    text_lower = text.lower()

    # Extract number
    number_match = re.search(r'(\d+(?:\.\d+)?)', text)
    if number_match:
        frame.number = float(number_match.group(1))

    # Extract unit
    unit_match = re.search(r'(\d+(?:\.\d+)?)\s*([°%$€]|[a-z]+)', text)
    if unit_match:
        frame.unit = unit_match.group(2)

    # Extract action/direction
    for verb in INC_VERBS:
        if verb in text_lower:
            frame.action = 'increase'
            frame.direction = 'up'
            break

    if not frame.action:
        for verb in DEC_VERBS:
            if verb in text_lower:
                frame.action = 'decrease'
                frame.direction = 'down'
                break

    # Domain-specific extraction
    if domain == "scientific":
        # Extract phenomenon (simplified - looks for key scientific terms)
        sci_terms = ['boiling', 'melting', 'freezing', 'temperature', 'pressure']
        for term in sci_terms:
            if term in text_lower:
                frame.phenomenon = term
                break

    elif domain == "policy":
        # Extract entity (simplified - looks for capitalized phrases)
        entity_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
        if entity_match:
            frame.entity = entity_match.group(1)

    return frame

def compare_frames(frame1, frame2):
    """
    Compare two frames for semantic similarity.
    From P24 line 42, returns match type: 'exact', 'partial', 'mismatch'
    """
    matches = []

    # Number match (if both have numbers)
    if frame1.number is not None and frame2.number is not None:
        from intelligence.content.shared.units import values_match
        if values_match(frame1.number, frame2.number):
            matches.append('number')

    # Action/direction match
    if frame1.action and frame2.action:
        if frame1.action == frame2.action:
            matches.append('action')

    # Phenomenon match (scientific)
    if frame1.phenomenon and frame2.phenomenon:
        if frame1.phenomenon == frame2.phenomenon:
            matches.append('phenomenon')

    # Entity match (policy)
    if frame1.entity and frame2.entity:
        if frame1.entity.lower() == frame2.entity.lower():
            matches.append('entity')

    # Condition match
    if frame1.condition and frame2.condition:
        from intelligence.content.shared.conditions import conditions_equivalent
        if conditions_equivalent(frame1.condition, frame2.condition):
            matches.append('condition')

    # Determine match type
    if len(matches) >= 3:
        return 'exact'
    elif len(matches) >= 1:
        return 'partial'
    else:
        return 'mismatch'
