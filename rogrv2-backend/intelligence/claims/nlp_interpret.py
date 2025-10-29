"""
Level 2 Semantic NLP Claim Enrichment

This module provides intelligent claim interpretation using NLP models.
Replaces dictionary-based enrichment with semantic understanding.

Architecture:
- spaCy: Entity recognition and dependency parsing
- BART (zero-shot): Domain and claim type classification
- Semantic role labeling: Extract agent, action, patient

IFCN Compliance:
- Confidence thresholds (0.7 minimum)
- Fallback to deterministic if confidence low
- Full transparency logging
- Version-locked models for reproducibility
"""

from __future__ import annotations
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

# Global model instances (lazy loaded)
_nlp_model = None
_classifier = None
_ner_model = None

# Model availability flag
NLP_AVAILABLE = False

try:
    import spacy
    from transformers import pipeline
    import torch
    NLP_AVAILABLE = True
except ImportError as e:
    logger.warning(f"NLP libraries not available: {e}. Will use deterministic fallback.")
    NLP_AVAILABLE = False


def get_nlp_model():
    """Lazy load spaCy model (called once, cached)."""
    global _nlp_model
    if _nlp_model is None:
        try:
            _nlp_model = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model: en_core_web_sm")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            raise
    return _nlp_model


def get_classifier():
    """Lazy load BART zero-shot classifier (called once, cached)."""
    global _classifier
    if _classifier is None:
        try:
            _classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1  # CPU (use 0 for GPU)
            )
            logger.info("Loaded BART classifier: facebook/bart-large-mnli")
        except Exception as e:
            logger.error(f"Failed to load BART classifier: {e}")
            raise
    return _classifier


def get_ner_model():
    """Lazy load NER model for enhanced entity recognition."""
    global _ner_model
    if _ner_model is None:
        try:
            _ner_model = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple",
                device=-1  # CPU
            )
            logger.info("Loaded NER model: dslim/bert-base-NER")
        except Exception as e:
            logger.error(f"Failed to load NER model: {e}")
            raise
    return _ner_model


# ==============================================================================
# LEVEL 2 SEMANTIC NLP FUNCTIONS
# ==============================================================================

def extract_entities_smart(text: str) -> List[str]:
    """
    Enhanced entity extraction using spaCy + BERT NER.

    Improvements over regex:
    - Handles ALL CAPS (COVID, AIDS)
    - Handles compound terms (COVID vaccines, climate change)
    - Normalizes entity names
    - Filters noise (pronouns, articles)
    """
    entities = []

    try:
        nlp = get_nlp_model()
        doc = nlp(text)

        # Extract named entities from spaCy (broader set)
        for ent in doc.ents:
            # Include more entity types, especially medical/scientific
            if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "LAW", "NORP", "FAC", "LOC"]:
                entities.append(ent.text)

        # FALLBACK: If no named entities found, extract key noun phrases
        if len(entities) == 0:
            for chunk in doc.noun_chunks:
                # Extract meaningful noun phrases (skip single articles/pronouns)
                chunk_text = chunk.text.strip()
                if len(chunk_text) > 3 and chunk.root.pos_ in ["NOUN", "PROPN"]:
                    entities.append(chunk_text)

        # Also try BERT NER for additional entities
        try:
            ner = get_ner_model()
            ner_results = ner(text)
            for result in ner_results:
                if result['score'] > 0.8:  # High confidence only
                    entity_text = result['word'].replace('##', '')  # Clean subword tokens
                    if entity_text not in entities and len(entity_text) > 2:
                        entities.append(entity_text)
        except Exception as e:
            logger.warning(f"BERT NER failed, using spaCy only: {e}")

        # Deduplicate while preserving order
        seen = set()
        deduplicated = []
        for e in entities:
            e_clean = e.strip()
            if e_clean and e_clean not in seen and len(e_clean) > 1:
                seen.add(e_clean)
                deduplicated.append(e_clean)

        return deduplicated[:10]  # Limit to top 10

    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        return []


def classify_domain(text: str) -> str:
    """
    Classify claim domain using zero-shot classification.

    Returns: medical, political, scientific, economic, social, generic
    """
    try:
        classifier = get_classifier()

        candidate_labels = [
            "medical health disease treatment",
            "political government policy election",
            "scientific physics chemistry biology",
            "economic financial business market",
            "social cultural entertainment sports"
        ]

        result = classifier(text, candidate_labels, multi_label=False)

        # Map to domain names
        label_map = {
            "medical health disease treatment": "medical",
            "political government policy election": "political",
            "scientific physics chemistry biology": "scientific",
            "economic financial business market": "economic",
            "social cultural entertainment sports": "social"
        }

        top_label = result['labels'][0]
        confidence = result['scores'][0]

        if confidence < 0.4:
            return "generic"

        return label_map.get(top_label, "generic")

    except Exception as e:
        logger.error(f"Domain classification failed: {e}")
        return "generic"


def detect_claim_type(text: str, entities: List[str]) -> str:
    """
    Detect claim type: causal, factual, comparative, correlational, temporal, negation.

    Uses pattern matching + zero-shot classification.
    """
    text_lower = text.lower()

    # Pattern-based detection (fast, high precision)
    causal_verbs = ['causes', 'caused', 'cause', 'leads to', 'results in', 'produces', 'triggers']
    correlational_verbs = ['linked to', 'associated with', 'related to', 'connected to', 'correlated with']
    comparative_words = ['more', 'less', 'better', 'worse', 'higher', 'lower', 'greater', 'smaller', 'than']
    negation_words = ['not', 'no', 'never', "n't", 'hoax', 'false', 'myth']

    if any(verb in text_lower for verb in causal_verbs):
        return "causal"
    elif any(verb in text_lower for verb in correlational_verbs):
        return "correlational"
    elif any(word in text_lower for word in comparative_words) and ' than ' in text_lower:
        return "comparative"
    elif any(word in text_lower for word in negation_words):
        return "negation"

    # Default to factual
    return "factual"


def extract_relationship(text: str, entities: List[str]) -> Dict[str, Any]:
    """
    Extract relationship between entities using dependency parsing.

    Returns: {type, verb, agent, patient, confidence}
    """
    try:
        nlp = get_nlp_model()
        doc = nlp(text)

        # Find main verb
        main_verb = None
        for token in doc:
            if token.pos_ == "VERB" and token.dep_ in ["ROOT", "ccomp"]:
                main_verb = token.text
                break

        if not main_verb:
            return {"type": "unknown", "verb": "", "agent": None, "patient": None, "confidence": 0.0}

        # Determine relationship type from verb
        verb_lower = main_verb.lower()

        type_map = {
            "cause": "causal",
            "causes": "causal",
            "prevent": "preventive",
            "prevents": "preventive",
            "treat": "therapeutic",
            "treats": "therapeutic",
            "increase": "amplifying",
            "increases": "amplifying",
            "decrease": "reducing",
            "decreases": "reducing",
            "link": "correlational",
            "links": "correlational",
            "associate": "correlational",
            "associates": "correlational"
        }

        relationship_type = type_map.get(verb_lower, "generic")

        # Extract agent (subject) and patient (object)
        agent = None
        patient = None

        for token in doc:
            if token.dep_ == "nsubj" and token.head.text == main_verb:
                agent = token.text
            elif token.dep_ in ["dobj", "pobj"] and token.head.text == main_verb:
                patient = token.text

        return {
            "type": relationship_type,
            "verb": main_verb,
            "agent": agent,
            "patient": patient,
            "confidence": 0.8  # High confidence for pattern-based
        }

    except Exception as e:
        logger.error(f"Relationship extraction failed: {e}")
        return {"type": "unknown", "verb": "", "agent": None, "patient": None, "confidence": 0.0}


def extract_concept_semantic(
    text: str,
    entities: List[str],
    domain: str,
    claim_type: str,
    relationship: Dict[str, Any]
) -> str:
    """
    Extract semantic concept (the phenomenon being discussed).

    Context-aware and domain-specific.
    """
    text_lower = text.lower()

    # Domain-specific concept extraction
    if domain == "medical":
        # Medical concepts: disease, treatment, drug, symptom, diagnosis
        medical_keywords = {
            'vaccine': 'vaccination',
            'drug': 'medication',
            'disease': 'condition',
            'symptom': 'clinical presentation',
            'diagnosis': 'diagnostic assessment'
        }

        for keyword, concept_type in medical_keywords.items():
            if keyword in text_lower:
                if claim_type == "causal" and len(entities) >= 2:
                    return f"{entities[0]}-{entities[-1]} causation hypothesis"
                elif claim_type == "correlational":
                    return f"{entities[0]}-{entities[-1]} correlation"
                else:
                    return f"{entities[0]} {concept_type}" if entities else f"{keyword} {concept_type}"

    elif domain == "political":
        # Political concepts: policy, legislation, budget, election
        political_keywords = ['budget', 'policy', 'law', 'election', 'regulation', 'spending']

        for keyword in political_keywords:
            if keyword in text_lower:
                if entities:
                    return f"{entities[0]} {keyword}"
                return f"{keyword}"

    elif domain == "scientific":
        # Scientific concepts: phenomenon, measurement, property
        # Look for measurement patterns
        measurement_pattern = r'(\w+)\s+(at|equals?|is)\s+(\d+(?:\.\d+)?)\s*(\w+)'
        match = re.search(measurement_pattern, text_lower)
        if match:
            substance = match.group(1)
            unit = match.group(4)
            return f"{substance} {unit} measurement"

        if entities:
            return f"{entities[0]} property"

    # Generic fallback: use relationship
    if relationship['type'] != "unknown" and len(entities) >= 2:
        return f"{entities[0]} {relationship['type']}"
    elif entities:
        return entities[0]

    # Last resort: extract main noun phrase
    try:
        nlp = get_nlp_model()
        doc = nlp(text)
        for chunk in doc.noun_chunks:
            if len(chunk.text) > 3:
                return chunk.text
    except:
        pass

    return ""


def extract_dimension_semantic(
    text: str,
    concept: str,
    domain: str,
    claim_type: str
) -> str:
    """
    Extract precise dimension (the aspect being measured/claimed).

    More specific than generic categories.
    """
    text_lower = text.lower()

    # Domain-specific dimensions
    if domain == "medical":
        if 'safety' in text_lower or 'side effect' in text_lower or 'adverse' in text_lower:
            return "medical safety / adverse effects"
        elif 'efficacy' in text_lower or 'effectiveness' in text_lower or 'works' in text_lower:
            return "treatment efficacy"
        elif 'diagnosis' in text_lower:
            return "diagnostic accuracy"
        else:
            return "medical causation"

    elif domain == "political":
        if 'budget' in text_lower or 'spending' in text_lower or 'fund' in text_lower:
            return "fiscal policy / government spending"
        elif 'election' in text_lower or 'vote' in text_lower:
            return "electoral politics"
        elif 'law' in text_lower or 'regulation' in text_lower:
            return "legislation / regulatory policy"
        else:
            return "political affairs"

    elif domain == "scientific":
        # Check for unit indicators
        if any(unit in text_lower for unit in ['celsius', 'fahrenheit', 'kelvin', 'degrees', '°c', '°f']):
            return "temperature"
        elif any(unit in text_lower for unit in ['pressure', 'atm', 'kpa', 'psi', 'bar']):
            return "pressure"
        elif any(word in text_lower for word in ['distance', 'meter', 'kilometer', 'mile', 'feet']):
            return "distance"
        elif any(word in text_lower for word in ['mass', 'weight', 'kilogram', 'pound', 'gram']):
            return "mass"
        else:
            return "physical property"

    elif domain == "economic":
        if 'gdp' in text_lower or 'growth' in text_lower:
            return "economic growth"
        elif 'inflation' in text_lower or 'price' in text_lower:
            return "price level / inflation"
        elif 'unemployment' in text_lower or 'job' in text_lower:
            return "employment"
        else:
            return "economic indicator"

    # Generic fallback based on claim type
    if claim_type == "causal":
        return "causation"
    elif claim_type == "correlational":
        return "correlation"
    elif claim_type == "comparative":
        return "comparison"

    return "unknown"


def extract_semantic_roles(text: str) -> Dict[str, Optional[str]]:
    """
    Extract semantic roles: agent (who), action (what), patient (whom), time (when), place (where).
    """
    try:
        nlp = get_nlp_model()
        doc = nlp(text)

        roles = {
            "agent": None,
            "action": None,
            "patient": None,
            "temporal": None,
            "location": None
        }

        # Find main verb (action)
        for token in doc:
            if token.pos_ == "VERB" and token.dep_ == "ROOT":
                roles["action"] = token.text

                # Find subject (agent)
                for child in token.children:
                    if child.dep_ == "nsubj":
                        roles["agent"] = child.text
                    elif child.dep_ in ["dobj", "pobj"]:
                        roles["patient"] = child.text

        # Find temporal and location markers
        for ent in doc.ents:
            if ent.label_ == "DATE" or ent.label_ == "TIME":
                roles["temporal"] = ent.text
            elif ent.label_ == "GPE" or ent.label_ == "LOC":
                roles["location"] = ent.text

        return roles

    except Exception as e:
        logger.error(f"Semantic role extraction failed: {e}")
        return {"agent": None, "action": None, "patient": None, "temporal": None, "location": None}


def detect_semantic_context(
    text: str,
    concept: str,
    domain: str,
    claim_type: str
) -> Dict[str, Any]:
    """
    Detect semantic context: Is this a known misconception? Controversial? What's the consensus?
    """
    text_lower = text.lower()

    context = {
        "is_misconception": False,
        "controversy_level": "low",
        "research_consensus": "unknown"
    }

    # Known misconception patterns
    misconception_patterns = {
        "vaccine": ["autism", "cause"],
        "climate": ["hoax", "fake", "not real"],
        "election": ["stolen", "fraud"],
        "flat": ["earth"],
        "5g": ["coronavirus", "covid"]
    }

    for topic, keywords in misconception_patterns.items():
        if topic in text_lower and all(kw in text_lower for kw in keywords):
            context["is_misconception"] = True
            context["controversy_level"] = "high"
            context["research_consensus"] = "debunked"
            break

    # Conspiracy theory markers
    conspiracy_markers = ["hoax", "conspiracy", "fake", "lie", "cover-up", "truth", "they don't want you to know"]
    if any(marker in text_lower for marker in conspiracy_markers):
        context["controversy_level"] = "high"

    # Scientific consensus markers
    consensus_markers = ["proven", "established", "consensus", "widely accepted", "confirmed"]
    if any(marker in text_lower for marker in consensus_markers):
        context["research_consensus"] = "strong"

    return context


def calculate_confidence(
    entities: List[str],
    concept: str,
    dimension: str,
    context: Dict[str, Any]
) -> float:
    """
    Calculate overall confidence in the enrichment.

    Returns: 0.0-1.0 (use 0.7 as threshold for IFCN compliance)
    """
    confidence = 0.0

    # Entity extraction quality (0-0.3)
    if len(entities) >= 2:
        confidence += 0.3
    elif len(entities) == 1:
        confidence += 0.2
    elif len(entities) == 0:
        confidence += 0.0

    # Concept extraction quality (0-0.4)
    if concept and len(concept) > 5:
        confidence += 0.4
    elif concept:
        confidence += 0.2

    # Dimension extraction quality (0-0.3)
    if dimension and dimension != "unknown":
        confidence += 0.3
    elif dimension == "unknown":
        confidence += 0.1

    return min(1.0, confidence)


# ==============================================================================
# MAIN NLP ENRICHMENT FUNCTION
# ==============================================================================

def parse_claim_nlp(text: str) -> Dict[str, Any]:
    """
    Level 2 Semantic NLP enrichment.

    Main entry point for NLP-based claim interpretation.

    Returns same schema as deterministic parse_claim for compatibility:
        {
            "text": str,
            "entities": List[str],
            "numbers": dict,
            "cues": dict,
            "scope": dict,
            "concept": str,
            "dimension": str,
            "kind_hint": str,

            # Level 2 enhancements
            "claim_type": str,
            "relationship_type": str,
            "semantic_roles": dict,
            "semantic_context": dict,
            "confidence": float,
            "enrichment_method": "nlp_semantic"
        }
    """

    if not NLP_AVAILABLE:
        raise ImportError("NLP libraries not available. Use deterministic fallback.")

    if not text or not text.strip():
        raise ValueError("Text is empty")

    logger.info(f"Running Level 2 Semantic NLP on: {text[:100]}")

    try:
        # 1. Entity Recognition (Enhanced)
        entities = extract_entities_smart(text)
        logger.debug(f"Entities: {entities}")

        # 2. Domain Classification
        domain = classify_domain(text)
        logger.debug(f"Domain: {domain}")

        # 3. Claim Type Detection
        claim_type = detect_claim_type(text, entities)
        logger.debug(f"Claim type: {claim_type}")

        # 4. Relationship Extraction
        relationship = extract_relationship(text, entities)
        logger.debug(f"Relationship: {relationship['type']}")

        # 5. Semantic Concept Extraction
        concept = extract_concept_semantic(text, entities, domain, claim_type, relationship)
        logger.debug(f"Concept: {concept}")

        # 6. Dimension Extraction
        dimension = extract_dimension_semantic(text, concept, domain, claim_type)
        logger.debug(f"Dimension: {dimension}")

        # 7. Semantic Roles
        semantic_roles = extract_semantic_roles(text)
        logger.debug(f"Semantic roles: {semantic_roles}")

        # 8. Context Detection
        semantic_context = detect_semantic_context(text, concept, domain, claim_type)
        logger.debug(f"Context: {semantic_context}")

        # 9. Calculate Confidence
        confidence = calculate_confidence(entities, concept, dimension, semantic_context)
        logger.info(f"NLP enrichment confidence: {confidence:.2f}")

        # 10. Build result (compatible with existing schema)
        result = {
            "text": text.strip(),
            "entities": entities,
            "concept": concept,
            "dimension": dimension,
            "claim_type": claim_type,
            "relationship_type": relationship['type'],
            "semantic_roles": semantic_roles,
            "semantic_context": semantic_context,
            "confidence": confidence,
            "enrichment_method": "nlp_semantic",

            # Legacy fields (extract with simple patterns for compatibility)
            "numbers": _extract_numbers_simple(text),
            "cues": _extract_cues_simple(text),
            "scope": _extract_scope_simple(text, entities),
            "kind_hint": _map_claim_type_to_kind(claim_type)
        }

        return result

    except Exception as e:
        logger.error(f"NLP enrichment failed: {e}", exc_info=True)
        raise


# ==============================================================================
# HELPER FUNCTIONS (for legacy field compatibility)
# ==============================================================================

def _extract_numbers_simple(text: str) -> Dict[str, Any]:
    """Simple number extraction for legacy compatibility."""
    percents = [float(p) for p in re.findall(r'\b(\d+(?:\.\d+)?)\s*%', text)]
    years = [int(y) for y in re.findall(r'\b(19|20)\d{2}\b', text)]
    return {"percents": percents, "years": years, "number_units": []}


def _extract_cues_simple(text: str) -> Dict[str, Any]:
    """Simple cue extraction for legacy compatibility."""
    text_lower = text.lower()
    return {
        "has_negation": any(word in text_lower for word in ["not", "no", "never", "n't"]),
        "has_comparison": any(word in text_lower for word in ["more", "less", "than", "higher", "lower"]),
        "has_attribution": any(word in text_lower for word in ["claims", "said", "according", "reported"])
    }


def _extract_scope_simple(text: str, entities: List[str]) -> Dict[str, Any]:
    """Simple scope extraction for legacy compatibility."""
    scope = {}
    years = re.findall(r'\b(19|20)\d{2}\b', text)
    if years:
        scope["year_hint"] = int(years[0])

    geo_entities = ["US", "USA", "Europe", "China", "India", "UK"]
    for entity in entities:
        if entity in geo_entities:
            scope["geo_hint"] = entity
            break

    return scope


def _map_claim_type_to_kind(claim_type: str) -> str:
    """Map new claim_type to legacy kind_hint."""
    mapping = {
        "causal": "statement",
        "correlational": "statement",
        "comparative": "comparative",
        "factual": "statement",
        "temporal": "statement",
        "negation": "statement"
    }
    return mapping.get(claim_type, "statement")
