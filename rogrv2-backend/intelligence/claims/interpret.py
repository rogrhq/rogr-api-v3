from __future__ import annotations
import re
from typing import Dict, List, Any, Tuple
from intelligence.content.shared.text_utils import tokenize_advanced as _tokens

# Very lightweight deterministic interpreters (no external NLP deps)
_WORD = re.compile(r"[A-Za-z][A-Za-z\-\']+")
_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_PERCENT = re.compile(r"\b(-?\d+(?:\.\d+)?)\s*%")
_NUMBER_UNIT = re.compile(r"\b(-?\d+(?:\.\d+)?)\s*(million|billion|k|thousand|percent|%)\b", re.I)
# crude entity-ish: sequences of Capitalized Words (excluding start-of-sentence artifacts when possible)
_ENTITY = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b")
# negation and comparison cues
_NEG_CUES = {"not","no","never","none","n't"}
_COMP_CUES = {"more","less","increase","decrease","higher","lower","rise","fell","fewer","greater","smaller","above","below","exceed","drop","up","down"}
_ATTRIB_CUES = {"claims","said","according","reported","announced","stated","told","alleged"}

def _entities(s: str) -> List[str]:
    ents: List[str] = []
    for m in _ENTITY.finditer(s):
        val = m.group(1)
        # Heuristics: skip pronouns / articles
        if val in {"The","A","An"}:
            continue
        if len(val) < 3:
            continue
        ents.append(val)
    # dedupe preserving order
    seen=set(); out=[]
    for e in ents:
        if e not in seen:
            seen.add(e); out.append(e)
    return out

def _numbers(s: str) -> Dict[str, Any]:
    percents = [float(p) for p in _PERCENT.findall(s)]
    year_matches = [int(y.group(0)) for y in _YEAR.finditer(s)]
    num_units: List[Tuple[float,str]] = []
    for m in _NUMBER_UNIT.finditer(s):
        v = float(m.group(1))
        u = m.group(2).lower()
        num_units.append((v,u))
    return {"percents": percents, "years": year_matches, "number_units": num_units}

def _cues(tokens: List[str]) -> Dict[str, Any]:
    neg = any(t in _NEG_CUES for t in tokens)
    comp = any(t in _COMP_CUES for t in tokens)
    attrib = any(t in _ATTRIB_CUES for t in tokens)
    return {"has_negation": neg, "has_comparison": comp, "has_attribution": attrib}

def parse_claim(text: str) -> Dict[str, Any]:
    """
    Deterministic enrichment for a claim string:
    - entities: rough proper-noun detection
    - numbers: percents, year hints, number+unit pairs
    - cues: negation/comparison/attribution flags
    - scope guess: geographic/time hints
    """
    s = (text or "").strip()
    toks = _tokens(s)
    ents = _entities(s)
    nums = _numbers(s)
    cues = _cues(toks)

    # scope guesses (very light)
    scope: Dict[str, Any] = {}
    if nums["years"]:
        scope["year_hint"] = nums["years"][0]
    # geo guess: first entity that looks like a place-ish name (cheap heuristic)
    for e in ents:
        if e in {"US","U.S.","USA","United States","Europe"} or len(e.split()) in (1,2):
            scope["geo_hint"] = e
            break

    parsed = {
        "text": s,
        "entities": ents,
        "numbers": nums,
        "cues": cues,
        "scope": scope,
        "kind_hint": "comparative" if cues["has_comparison"] else "attribution" if cues["has_attribution"] else "statement",
    }

    # Extract concept (phenomenon being discussed)
    concept_info = extract_concept(s, parsed)
    parsed["concept"] = concept_info["concept"]
    parsed["dimension"] = concept_info["dimension"]

    return parsed


def extract_concept(claim_text: str, parsed: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract the phenomenon/concept from claim.

    Returns: {"concept": str, "dimension": str}

    Examples:
    - "Water boils at 100°C" → {"concept": "water boiling point", "dimension": "temperature"}
    - "Ice melts at 0°C" → {"concept": "ice melting point", "dimension": "temperature"}
    """
    text_lower = claim_text.lower()
    entities = parsed.get('entities', [])
    entity = entities[0].lower() if entities else ""

    # Verb → phenomenon mapping
    verb_to_phenomenon = {
        'boils': 'boiling point',
        'boiling': 'boiling point',
        'freezes': 'freezing point',
        'melts': 'melting point',
        'melting': 'melting point',
        'reacts': 'reaction',
        'moves': 'movement',
        'expands': 'expansion'
    }

    # Check for phenomenon verbs
    concept = None
    for verb, phenomenon in verb_to_phenomenon.items():
        if verb in text_lower:
            concept = f"{entity} {phenomenon}"
            break

    # Detect dimension from text (temperature units, pressure indicators)
    dimension = None
    if any(unit in text_lower for unit in ['celsius', 'fahrenheit', 'kelvin', 'degrees', '°c', '°f']):
        dimension = "temperature"
    elif any(unit in text_lower for unit in ['pressure', 'atm', 'kpa', 'psi', 'bar']):
        dimension = "pressure"
    elif any(word in text_lower for word in ['distance', 'meter', 'kilometer', 'mile', 'feet']):
        dimension = "distance"
    elif any(word in text_lower for word in ['mass', 'weight', 'kilogram', 'pound', 'gram']):
        dimension = "mass"

    # Fallbacks
    if not concept and dimension:
        concept = f"{entity} {dimension}"
    elif not concept and entity:
        # Try to find verb+s pattern (finds "boils", "melts")
        import re
        verb_match = re.search(r'\b(\w+)s\b', text_lower)
        if verb_match:
            verb = verb_match.group(1)
            concept = f"{entity} {verb}ing"

    if not concept:
        # Last resort: use entity alone
        concept = entity

    return {
        "concept": concept or "",
        "dimension": dimension or "unknown"
    }


def detect_claim_type(claim: Dict[str, Any]) -> str:
    """
    Detect claim type for P19 counter-frame template selection.
    Returns: "scientific" | "policy_econ" | "generic"

    Uses parsed fields from claim enrichment to classify claim domain.
    """
    text = claim.get("text", "").lower()

    # Scientific indicators
    scientific_units = {
        # Temperature
        "celsius", "fahrenheit", "kelvin", "degrees",
        # Distance/length
        "meter", "meters", "kilometer", "kilometers", "mile", "miles", "feet", "inches",
        # Mass/weight
        "gram", "grams", "kilogram", "kilograms", "pound", "pounds", "ounce", "ounces",
        # Energy
        "joule", "joules", "calorie", "calories", "watt", "watts",
        # Time (scientific context)
        "nanosecond", "microsecond", "millisecond",
        # Other scientific
        "mole", "moles", "pascal", "pascals", "hertz", "volt", "volts", "ampere", "amperes"
    }

    scientific_keywords = {
        "boils", "boiling", "melts", "melting", "freezes", "freezing",
        "chemical", "physics", "biology", "chemistry", "molecule", "molecules",
        "atom", "atoms", "element", "elements", "compound", "compounds",
        "reaction", "formula", "equation", "theory", "hypothesis",
        "gravity", "velocity", "acceleration", "force", "energy", "mass",
        "temperature", "pressure", "volume", "density"
    }

    # Policy/economic indicators
    policy_econ_keywords = {
        # Budget/financial
        "budget", "spending", "revenue", "tax", "taxes", "fund", "funding", "grant", "grants",
        "appropriation", "appropriations", "fiscal", "financial", "deficit", "surplus",
        "allocation", "allocations", "expenditure", "expenditures",
        # Policy/government
        "policy", "law", "regulation", "regulations", "bill", "amendment", "legislation",
        "congress", "senate", "house", "government", "federal", "state", "municipal",
        "council", "committee", "department", "agency",
        # Economic
        "gdp", "inflation", "unemployment", "economy", "economic", "recession",
        "growth rate", "interest rate", "market", "stock", "bond", "currency"
    }

    # Check for scientific indicators
    scientific_score = 0
    for unit in scientific_units:
        if unit in text:
            scientific_score += 2  # Units are strong signals
    for keyword in scientific_keywords:
        if keyword in text:
            scientific_score += 1

    # Check for policy/economic indicators
    policy_econ_score = 0
    for keyword in policy_econ_keywords:
        if keyword in text:
            policy_econ_score += 1

    # Check for budget + percentage combination (strong policy/econ signal)
    nums = claim.get("numbers", {})
    if nums and nums.get("percents"):
        if any(kw in text for kw in ["budget", "spending", "revenue", "tax", "fund"]):
            policy_econ_score += 3

    # Decision logic
    if scientific_score >= 2:
        return "scientific"
    elif policy_econ_score >= 2:
        return "policy_econ"
    else:
        return "generic"


# ==============================================================================
# HYBRID NLP + DETERMINISTIC ENRICHMENT (Level 2 Semantic NLP)
# ==============================================================================

def parse_claim_hybrid(text: str) -> Dict[str, Any]:
    """
    NLP-only enrichment: Use Level 2 Semantic NLP for all claims.

    REFACTOR 6 CHANGE (2025-10-29): Removed deterministic-first priority.
    Rationale: Fail-fast approach reveals NLP issues immediately, prevents silent
    degradation to 10% coverage. Every claim validates NLP quality.

    Previous strategy (deterministic-first):
    1. Try deterministic (fast, 10% coverage)
    2. If succeeded, return (NLP never tested on simple cases)
    3. If failed, try NLP (only gets hard cases)
    Problem: NLP failures masked, never validated on known-good claims

    NEW strategy (NLP-only):
    1. Try NLP (85% expected coverage)
    2. If fails or low confidence, fail visibly with clear error
    3. Deterministic kept for emergency rollback only (commented out)
    Benefit: All claims test NLP, failures detected immediately

    See: REFACTOR-6-PROGRESS-LOG.md Stage 4 - Investigation 1

    Returns: Same schema as parse_claim() for compatibility
    """
    import logging
    logger = logging.getLogger(__name__)

    # REFACTOR 6: Deterministic-first logic commented out (2025-10-29)
    # Keep code available for emergency rollback if NLP fails catastrophically
    #
    # # OLD Step 1: Try deterministic first
    # logger.debug(f"Hybrid enrichment: trying deterministic for '{text[:50]}...'")
    # deterministic_result = parse_claim(text)
    #
    # # OLD Step 2: Check if deterministic succeeded
    # if deterministic_result.get("concept") and len(deterministic_result["concept"]) > 3:
    #     logger.info(f"Deterministic enrichment succeeded: concept='{deterministic_result['concept']}'")
    #     deterministic_result["enrichment_method"] = "deterministic"
    #     deterministic_result["confidence"] = 0.95  # High confidence for pattern-based
    #     return deterministic_result

    # NEW: NLP-only enrichment
    logger.info(f"NLP enrichment for '{text[:50]}...'")

    try:
        from intelligence.claims.nlp_interpret import parse_claim_nlp, NLP_AVAILABLE

        if not NLP_AVAILABLE:
            # CRITICAL ERROR: NLP not available
            logger.error("NLP libraries not available - CRITICAL: Install dependencies!")
            raise RuntimeError(
                "NLP enrichment unavailable. Install required packages: "
                "spacy, transformers, torch. "
                "See intelligence/claims/nlp_interpret.py for details."
            )

        # Try NLP enrichment
        nlp_result = parse_claim_nlp(text)

        # Check NLP confidence
        nlp_confidence = nlp_result.get("confidence", 0.0)

        if nlp_confidence < 0.7:
            # Low confidence but still return result - let pipeline decide
            logger.warning(
                f"NLP confidence low ({nlp_confidence:.2f}) for '{text[:50]}...' "
                f"concept='{nlp_result.get('concept', 'EMPTY')}'"
            )
            nlp_result["enrichment_method"] = "nlp_low_confidence"
            return nlp_result

        # NLP succeeded with high confidence
        logger.info(
            f"NLP enrichment succeeded: concept='{nlp_result['concept']}', "
            f"confidence={nlp_confidence:.2f}"
        )
        nlp_result["enrichment_method"] = "nlp"
        return nlp_result

    except ImportError as e:
        # CRITICAL ERROR: Missing dependencies
        logger.error(f"NLP import failed: {e}")
        raise RuntimeError(
            f"Failed to import NLP modules: {e}. "
            "Install required packages: spacy, transformers, torch"
        )

    except Exception as e:
        # NLP processing error - fail visibly
        logger.error(f"NLP enrichment failed: {e}", exc_info=True)
        raise RuntimeError(
            f"NLP enrichment failed for '{text[:50]}...': {e}. "
            "This is a critical failure - check NLP models and configuration."
        )