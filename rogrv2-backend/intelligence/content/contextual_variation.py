"""
intelligence/content/contextual_variation.py

REFACTOR 7: Contextual Variation Detection
Created: Week 1
Spec: See REFACTOR_7_IMPLEMENTATION_SPEC.md (v1.5 - NLP-based)

⚠️ IMPLEMENTATION RULES FOR THIS FILE ⚠️
1. This file is NEW - created for Refactor 7
2. Pure analysis module - NO modifications to items
3. Detects patterns ACROSS multiple evidence items
4. Returns structured metadata only
5. **CRITICAL:** Uses NLP dependency parsing (NOT hardcoded regex patterns)

DEPENDENCIES:
- intelligence.claims.nlp_interpret.get_nlp_model (Refactor 6)
- spacy (already installed from Refactor 6)

INTEGRATION:
- Used by contextual_mapping.py (Week 1)
- Feature-flagged when integrated (Week 4)

TESTING:
- Unit tests: tests/test_contextual_variation.py
"""

from typing import List, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


def detect_context_dependency_from_evidence(
    items: List[Dict[str, Any]],
    claim_text: str
) -> Dict[str, Any]:
    """
    Analyze evidence items to detect contextual variation.

    Args:
        items: List of evidence items (all arms combined)
        claim_text: Original claim being checked

    Returns:
        {
            "is_context_dependent": bool,
            "confidence": float (0-1),
            "contextual_factors": List[str],
            "variation_detected": bool,
            "sources_agree_on_variation": bool,
            "detected_conditions": List[str]
        }
    """
    try:
        if not items:
            return {
                "is_context_dependent": False,
                "confidence": 0.0,
                "contextual_factors": [],
                "variation_detected": False,
                "sources_agree_on_variation": False,
                "detected_conditions": []
            }

        # Extract conditions from all items
        all_conditions = []
        items_with_conditions = 0

        for item in items:
            content = item.get('content', '') or item.get('snippet', '')
            if content:
                conditions = extract_conditions_from_text(content)
                if conditions:
                    all_conditions.extend(conditions)
                    items_with_conditions += 1

        # Detect if variation is explained by conditions
        has_variation = detect_variation_language(items, claim_text)

        # Context dependency criteria from spec (line 791-811):
        # >= 1 item mentions conditions + variation language detected
        is_context_dependent = (items_with_conditions >= 1) and has_variation

        confidence = min(items_with_conditions / max(len(items), 1), 1.0)

        # Extract unique contextual factors
        unique_factors = list(set([c.get('type', 'unknown') for c in all_conditions]))
        unique_conditions = list(set([c.get('condition', '') for c in all_conditions if c.get('condition')]))

        return {
            "is_context_dependent": is_context_dependent,
            "confidence": confidence,
            "contextual_factors": unique_factors,
            "variation_detected": has_variation,
            "sources_agree_on_variation": is_context_dependent,
            "detected_conditions": unique_conditions
        }

    except Exception as e:
        logger.error(f"Context dependency detection failed: {e}", exc_info=True)
        return {
            "is_context_dependent": False,
            "confidence": 0.0,
            "contextual_factors": [],
            "variation_detected": False,
            "sources_agree_on_variation": False,
            "detected_conditions": []
        }


def extract_conditions_from_text(text: str) -> List[Dict[str, str]]:
    """
    Extract conditional qualifiers using spaCy NLP (NOT hardcoded regex).

    Uses dependency parsing + entity recognition per spec (lines 1768-1854).

    Returns:
        List of condition dictionaries with type, preposition, object, condition
    """
    try:
        from intelligence.claims.nlp_interpret import get_nlp_model

        nlp = get_nlp_model()
        doc = nlp(text)
        conditions = []

        # Strategy 1: Prepositional phrases with entities (at/in/on/under + location/quantity)
        for chunk in doc.noun_chunks:
            if chunk.root.dep_ == "pobj":  # Object of preposition
                prep = chunk.root.head
                if prep.pos_ == "ADP":  # Preposition
                    cond_type = _classify_condition_type(chunk)
                    condition = {
                        "type": cond_type,
                        "preposition": prep.text,
                        "object": chunk.text,
                        "condition": f"{prep.text} {chunk.text}"
                    }
                    conditions.append(condition)

        # Strategy 2: Conditional clauses (when/if/unless)
        for token in doc:
            if token.dep_ == "mark" and token.lemma_ in ["when", "if", "unless", "while", "as"]:
                head = token.head
                if head.dep_ == "advcl":  # Adverbial clause
                    conditions.append({
                        "type": "conditional",
                        "marker": token.text,
                        "condition": " ".join([t.text for t in head.subtree])
                    })

        # Strategy 3: Causal relationships (due to/because of)
        for token in doc:
            if token.lemma_ in ["due", "because"]:
                conditions.append({
                    "type": "causal",
                    "marker": token.text,
                    "condition": " ".join([t.text for t in token.subtree])
                })

        # Strategy 4: Modal hedging (may/can/typically)
        for token in doc:
            if token.pos_ == "VERB":
                for child in token.children:
                    if child.dep_ == "aux" and child.tag_ == "MD":  # Modal auxiliary
                        conditions.append({
                            "type": "hedging",
                            "modal": child.text,
                            "context": token.text
                        })

        return conditions

    except Exception as e:
        logger.error(f"Condition extraction failed: {e}", exc_info=True)
        return []


def _classify_condition_type(noun_chunk) -> str:
    """Classify condition type based on entity recognition (spec lines 1841-1854)."""
    # Use spaCy NER to classify - NO HARDCODED PATTERNS
    if noun_chunk.root.ent_type_ in ["GPE", "LOC", "FAC"]:
        return "spatial"
    elif noun_chunk.root.ent_type_ in ["QUANTITY", "CARDINAL"]:
        return "quantitative"
    elif noun_chunk.root.ent_type_ in ["DATE", "TIME"]:
        return "temporal"
    elif noun_chunk.root.ent_type_ in ["PERSON", "NORP"]:
        return "demographic"
    else:
        return "circumstantial"


def detect_variation_language(items: List[Dict[str, Any]], claim_text: str) -> bool:
    """
    Detect if text contains variation language using NLP (NOT keyword matching).

    Looks for patterns like "varies with", "depends on", "due to", etc.
    """
    try:
        variation_patterns = [
            r'\b(varies?|varying|variation)\b',
            r'\b(depends?|depending)\b',
            r'\bdue to\b',
            r'\bbecause of\b',
            r'\baffected by\b',
            r'\binfluenced by\b',
            r'\bdifferent\b.*\bconditions?\b',
            r'\bunder\b.*\bconditions?\b',
            r'\bmay\b.*\bdiffer\b',
            r'\bcan\b.*\bvary\b'
        ]

        for item in items:
            content = (item.get('content', '') or item.get('snippet', '')).lower()
            for pattern in variation_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True

        return False

    except Exception as e:
        logger.error(f"Variation language detection failed: {e}", exc_info=True)
        return False
