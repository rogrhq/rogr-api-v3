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
    Hybrid enrichment: Try deterministic first, fallback to NLP if enrichment fails.

    This is the PRODUCTION entry point that guarantees zero regressions.

    Strategy:
    1. Try deterministic (fast, proven, works for 10% of claims)
    2. If enrichment succeeded (concept populated), return it
    3. If enrichment failed (concept empty), try NLP
    4. If NLP confidence < 0.7, return deterministic (IFCN compliance)
    5. Otherwise, return NLP enrichment

    Returns: Same schema as parse_claim() for compatibility
    """
    import logging
    logger = logging.getLogger(__name__)

    # Step 1: Try deterministic first
    logger.debug(f"Hybrid enrichment: trying deterministic for '{text[:50]}...'")
    deterministic_result = parse_claim(text)

    # Step 2: Check if deterministic succeeded
    if deterministic_result.get("concept") and len(deterministic_result["concept"]) > 3:
        logger.info(f"Deterministic enrichment succeeded: concept='{deterministic_result['concept']}'")
        deterministic_result["enrichment_method"] = "deterministic"
        deterministic_result["confidence"] = 0.95  # High confidence for pattern-based
        return deterministic_result

    # Step 3: Deterministic failed, try NLP
    logger.info("Deterministic enrichment failed (empty concept), trying NLP...")

    try:
        from intelligence.claims.nlp_interpret import parse_claim_nlp, NLP_AVAILABLE

        if not NLP_AVAILABLE:
            logger.warning("NLP libraries not available, using deterministic fallback")
            deterministic_result["enrichment_method"] = "deterministic_fallback"
            deterministic_result["confidence"] = 0.5
            return deterministic_result

        # Try NLP enrichment
        nlp_result = parse_claim_nlp(text)

        # Step 4: Check NLP confidence
        nlp_confidence = nlp_result.get("confidence", 0.0)

        if nlp_confidence < 0.7:
            logger.warning(f"NLP confidence too low ({nlp_confidence:.2f}), using deterministic fallback")
            deterministic_result["enrichment_method"] = "deterministic_fallback"
            deterministic_result["confidence"] = nlp_confidence
            deterministic_result["nlp_attempted"] = True
            return deterministic_result

        # Step 5: NLP succeeded with high confidence
        logger.info(f"NLP enrichment succeeded: concept='{nlp_result['concept']}', confidence={nlp_confidence:.2f}")
        return nlp_result

    except ImportError as e:
        logger.warning(f"NLP import failed: {e}, using deterministic fallback")
        deterministic_result["enrichment_method"] = "deterministic_fallback"
        deterministic_result["confidence"] = 0.5
        return deterministic_result

    except Exception as e:
        logger.error(f"NLP enrichment failed with error: {e}, using deterministic fallback", exc_info=True)
        deterministic_result["enrichment_method"] = "deterministic_fallback"
        deterministic_result["confidence"] = 0.3
        deterministic_result["nlp_error"] = str(e)
        return deterministic_result