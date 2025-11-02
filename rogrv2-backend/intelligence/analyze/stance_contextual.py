"""
intelligence/analyze/stance_contextual.py

REFACTOR 7: Contextual Stance Detection
Created: Week 1
Spec: See REFACTOR_7_IMPLEMENTATION_SPEC.md

⚠️ IMPLEMENTATION RULES FOR THIS FILE ⚠️
1. This file is NEW - created for Refactor 7
2. MUST delegate to existing stance.py:assess_stance()
3. MUST preserve all base return fields
4. MUST only ADD optional 'context_analysis' field
5. MUST NOT modify existing stance labels/scores

DEPENDENCIES:
- intelligence.analyze.stance.assess_stance() (existing - UNCHANGED)

INTEGRATION:
- NOT integrated into pipeline yet (as of Week 1)
- Feature-flagged when integrated into pipeline (Week 4)

TESTING:
- Unit tests: tests/test_stance_contextual.py
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def assess_stance_with_context(claim_text: str, item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced stance assessment with contextual understanding.

    This function wraps the existing assess_stance() and adds optional
    contextual analysis without modifying base stance behavior.

    Args:
        claim_text: The claim being fact-checked
        item: Evidence item dict with title, snippet, content

    Returns:
        {
            # Base fields from stance.py (PRESERVED EXACTLY)
            "stance": str,  # "supports", "challenges", "neutral"
            "stance_score": float,
            "contradiction_flags": List,
            "notes": str,

            # Optional enhancement (ONLY if context detected)
            "context_analysis": {
                "is_contextual": bool,
                "has_conditions": bool,
                "detected_conditions": List[str]
            }
        }
    """
    try:
        # Step 1: DELEGATE to existing function (preserves all base behavior)
        from intelligence.analyze.stance import assess_stance

        base_stance = assess_stance(claim_text, item)

        # Step 2: Extract content for analysis
        content = item.get('content', '') or item.get('snippet', '')

        if not content:
            # No content to analyze, return base stance unchanged
            return base_stance

        # Step 3: Detect contextual patterns
        context_analysis = _detect_contextual_patterns(content, claim_text)

        # Step 4: Add optional field ONLY if context detected
        if context_analysis.get('is_contextual', False):
            base_stance['context_analysis'] = context_analysis
            logger.debug(f"Context detected in evidence: {context_analysis}")

        # Return enhanced dict (base + optional context)
        return base_stance

    except Exception as e:
        # ERROR HANDLING: If contextual analysis fails, return base stance
        # This ensures graceful degradation - existing behavior preserved
        logger.error(f"Contextual stance analysis failed: {e}", exc_info=True)
        try:
            from intelligence.analyze.stance import assess_stance
            return assess_stance(claim_text, item)  # Fallback to base
        except:
            # Ultimate fallback if even base stance fails
            return {
                "stance": "neutral",
                "stance_score": 0.5,
                "contradiction_flags": [],
                "notes": "Error in stance analysis"
            }


def _detect_contextual_patterns(text: str, claim_text: str) -> Dict[str, Any]:
    """
    Detect contextual qualifiers and variation patterns.

    Uses extract_conditions_from_text from contextual_variation.py.

    Returns:
        {
            "is_contextual": bool,
            "has_conditions": bool,
            "detected_conditions": List[str],
            "has_variation_language": bool
        }
    """
    try:
        from intelligence.content.contextual_variation import (
            extract_conditions_from_text,
            detect_variation_language
        )

        # Extract conditions
        conditions = extract_conditions_from_text(text)

        # Check for variation language
        has_variation = detect_variation_language([{"content": text}], claim_text)

        # Build context analysis
        is_contextual = len(conditions) > 0 or has_variation

        return {
            "is_contextual": is_contextual,
            "has_conditions": len(conditions) > 0,
            "detected_conditions": [c.get('condition', '') for c in conditions if c.get('condition')],
            "has_variation_language": has_variation
        }

    except Exception as e:
        logger.error(f"Contextual pattern detection failed: {e}", exc_info=True)
        return {
            "is_contextual": False,
            "has_conditions": False,
            "detected_conditions": [],
            "has_variation_language": False
        }
