"""
intelligence/content/contextual_mapping.py

REFACTOR 7: IFCN Label Mapping with Contextual Awareness
Created: Week 1
Spec: See REFACTOR_7_IMPLEMENTATION_SPEC.md

⚠️ IMPLEMENTATION RULES FOR THIS FILE ⚠️
1. This file is NEW - created for Refactor 7
2. Does NOT modify input verdict
3. Returns NEW dict with IFCN labels + contextual enhancements
4. Pure mapping layer (delegates to contextual_variation.py)
5. Must always include IFCN-compliant label

DEPENDENCIES:
- intelligence.content.contextual_variation (new - Week 1)

INTEGRATION:
- Feature-flagged when integrated (Week 4)

TESTING:
- Unit tests: tests/test_contextual_mapping.py
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# IFCN Label Confidence Thresholds (spec lines 2032-2034)
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.70
CONFIDENCE_LOW = 0.50


def map_to_ifcn_label(
    verdict_label: str,
    confidence: float,
    context_dependent: bool = False
) -> str:
    """
    Map internal verdict to IFCN-compliant label.

    Per spec (lines 2036-2095):
    - SUPPORTS + high conf (>=0.85) + NOT context-dependent → TRUE
    - SUPPORTS + high conf (>=0.85) + context-dependent → MOSTLY TRUE
    - SUPPORTS + medium conf (>=0.70) → MOSTLY TRUE
    - SUPPORTS + low conf (>=0.50) → HALF TRUE
    - CHALLENGES + high conf (>=0.85) → FALSE
    - CHALLENGES + medium conf (>=0.70) → MOSTLY FALSE
    - CHALLENGES + low conf (>=0.50) → HALF TRUE
    - MIXED → HALF TRUE
    - INSUFFICIENT → UNSUPPORTED

    Args:
        verdict_label: Internal verdict ("supports", "challenges", "mixed", "insufficient")
        confidence: Confidence score (0.0-1.0)
        context_dependent: Whether claim is context-dependent

    Returns:
        IFCN-compliant label string
    """
    verdict_lower = verdict_label.lower()

    if verdict_lower == "supports":
        if confidence >= CONFIDENCE_HIGH and not context_dependent:
            return "TRUE"
        elif confidence >= CONFIDENCE_HIGH:
            return "MOSTLY TRUE"  # Context-dependent caps at MOSTLY TRUE
        elif confidence >= CONFIDENCE_MEDIUM:
            return "MOSTLY TRUE"
        elif confidence >= CONFIDENCE_LOW:
            return "HALF TRUE"
        else:
            return "UNSUPPORTED"

    elif verdict_lower == "challenges":
        if confidence >= CONFIDENCE_HIGH:
            return "FALSE"
        elif confidence >= CONFIDENCE_MEDIUM:
            return "MOSTLY FALSE"
        elif confidence >= CONFIDENCE_LOW:
            return "HALF TRUE"
        else:
            return "UNSUPPORTED"

    elif verdict_lower == "mixed":
        return "HALF TRUE"

    else:  # insufficient or unknown
        return "UNSUPPORTED"


def map_verdict_to_ifcn_contextual(
    verdict: Dict[str, Any],
    claim_text: str,
    all_items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Enhanced IFCN mapping with contextual awareness.

    Args:
        verdict: Output from aggregate_verdict() (unchanged)
        claim_text: Original claim
        all_items: All evidence items (for context detection)

    Returns:
        {
            **verdict,  # Preserve all original fields
            "ifcn_label": str,  # ALWAYS present
            "contextual_status": {...},  # OPTIONAL - only if context detected
        }
    """
    try:
        from intelligence.content.contextual_variation import detect_context_dependency_from_evidence

        # Detect context dependency
        context_status = detect_context_dependency_from_evidence(all_items, claim_text)

        # Map to IFCN label
        verdict_label = verdict.get('label', 'insufficient')
        confidence = verdict.get('confidence', 0.0)
        is_context_dependent = context_status.get('is_context_dependent', False)

        ifcn_label = map_to_ifcn_label(verdict_label, confidence, is_context_dependent)

        # Build result preserving all original fields
        result = {
            **verdict,  # Preserve everything from original verdict
            "ifcn_label": ifcn_label
        }

        # Add contextual status only if context detected
        if is_context_dependent:
            result["contextual_status"] = {
                "is_context_dependent": True,
                "completeness": "INCOMPLETE",
                "missing_factors": context_status.get('contextual_factors', []),
                "detected_conditions": context_status.get('detected_conditions', []),
                "confidence": context_status.get('confidence', 0.0)
            }

        return result

    except Exception as e:
        logger.error(f"Contextual IFCN mapping failed: {e}", exc_info=True)
        # Fallback: return original verdict with basic IFCN label
        return {
            **verdict,
            "ifcn_label": map_to_ifcn_label(
                verdict.get('label', 'insufficient'),
                verdict.get('confidence', 0.0),
                False
            )
        }
