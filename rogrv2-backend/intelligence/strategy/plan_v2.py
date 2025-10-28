from __future__ import annotations
from typing import Dict, List, Any, Union
import re
_DOMAIN_RE = re.compile(r"""(?ix)
    (?:^|[\s'"\]])            # start or space
    (?:site:|inurl:)?       # common operators we forbid too
    [\w-]+(?:\.[\w-]+)+     # looks like a.domain.tld
""")

def _uniq(seq: List[str]) -> List[str]:
    seen = set(); out=[]
    for s in seq:
        k = s.strip()
        if not k:
            continue
        if k.lower() in seen:
            continue
        seen.add(k.lower()); out.append(k)
    return out

def _norm_words(s: str) -> List[str]:
    return [w for w in re.split(r"[^\w%]+", s) if w]

def _percent_terms(numbers: Dict[str, Any]) -> List[str]:
    """
    Extract percentage terms from enrichment data.

    Handles both float values (8.0) and string formats ("8%").
    Converts floats to proper percentage strings to prevent domain filter issues.
    """
    out: List[str] = []
    if not numbers:
        return out

    for p in numbers.get("percents", []) or []:
        # Handle both float (8.0) and string ("8%") formats
        if isinstance(p, (int, float)):
            # Convert float to percent string
            # Use int() if it's a whole number (8.0 → 8%), else keep decimal (8.5 → 8.5%)
            val = int(p) if p == int(p) else p
            out.append(f"{val}%")
            out.append(f"{val} percent")
        else:
            # String format (already has %)
            s = str(p)
            out.append(s)
            # normalize "8%" -> "8 percent"
            m = re.match(r"^(\d+(?:\.\d+)?)%$", s)
            if m:
                out.append(f"{m.group(1)} percent")

    return out

def _time_terms(scope: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    if not scope:
        return out
    year = scope.get("year")
    if year:
        out.append(str(year))
    # could add month/quarter in later packets
    return out

def _entity_terms(entities: Union[List[str], List[Dict[str, Any]]]) -> List[str]:
    """
    Extract entity terms, handling both string list and dict list formats.

    Args:
        entities: List[str] (canonical) or List[Dict] with "name" key (legacy)

    Returns:
        List of entity name strings
    """
    if not entities:
        return []

    result = []
    for e in entities:
        if isinstance(e, str):
            # Canonical format: List[str]
            result.append(e)
        elif isinstance(e, dict) and "name" in e:
            # Legacy format: List[Dict] with "name" key
            name = (e.get("name") or "").strip()
            if name:
                result.append(name)
        # Ignore anything else (malformed input)

    return result

def _comparison_terms(cues: Dict[str, Any]) -> List[str]:
    if not cues:
        return []
    terms = []
    if bool(cues.get("has_comparison")):
        # neutral comparison lexicon, no domains
        terms.extend(["increase", "decrease", "change", "rise", "fall", "trend", "growth", "decline"])
        terms.extend(["year over year", "yoy", "compared to", "versus"])
    return terms

def _challenge_terms(kind_hint: str) -> List[str]:
    # neutral "challenge" lexicon (no domain bias)
    return ["dispute", "counterclaim", "contradict", "refute", "debunk", "controversy", "criticism", "fact check"]

def _support_terms(kind_hint: str) -> List[str]:
    return ["report", "press release", "official", "statement", "dataset", "document", "methodology"]

def _head_clause(text: str) -> str:
    # keep a short quoted clause to anchor semantics
    t = text.strip()
    if len(t) > 140:
        t = t[:140]
    return f"\"{t}\""

def build_search_plans_v2(claim: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input: claim dict with enrichment keys from S2 Packet 1.
    Output: normalized plan with two arms (A support-seeking, B challenge-seeking).
    """
    text = claim.get("text") or ""
    entities = _entity_terms(claim.get("entities") or [])
    percents = _percent_terms(claim.get("numbers") or {})
    time = _time_terms(claim.get("scope") or {})
    comps = _comparison_terms(claim.get("cues") or {})
    kind = claim.get("kind_hint") or ""

    head = _head_clause(text)

    common_pool = _uniq(entities + percents + time + comps + _norm_words(kind))
    # Arm A: Support-seeking
    a_queries: List[str] = []
    a_queries.append(" ".join(_uniq([head] + common_pool + _support_terms(kind))))
    if entities:
        a_queries.append(" ".join(_uniq([entities[0]] + percents + time + ["official statistics"])))
    if percents:
        a_queries.append(" ".join(_uniq([head] + percents + ["explainer"])))
    # Arm B: Challenge-seeking
    b_queries: List[str] = []
    b_queries.append(" ".join(_uniq([head] + common_pool + _challenge_terms(kind))))
    if entities:
        b_queries.append(" ".join(_uniq([entities[0]] + percents + time + ["dispute"])))
    b_queries.append(" ".join(_uniq(_challenge_terms(kind) + percents + time)))

    # prune empties, drop any query that contains a domain or site operator
    def _clean(queries: List[str]) -> List[str]:
        out = []
        for q in queries:
            q = q.strip()
            if not q:
                continue
            if _DOMAIN_RE.search(q):
                continue
            out.append(q)
        return out
    a_queries = _clean(a_queries)
    b_queries = _clean(b_queries)

    plan = {
        "version": "v2",
        "arms": {
            "A": {"intent": "support", "queries": a_queries[:5]},
            "B": {"intent": "challenge", "queries": b_queries[:5]},
        },
        "meta": {
            "claim_id": claim.get("id", "unknown"),
            "claim_type": claim.get("claim_type", "generic"),
            "concept": claim.get("concept", ""),
            "dimension": claim.get("dimension", "unknown")
        }
    }

    # Add claim data for diversify_plan_for_lane()
    plan["claim"] = {
        "text": claim.get("text", ""),
        "entities": claim.get("entities", []),
        "numbers": claim.get("numbers", [])
    }

    return plan

# ============================================================================
# PHASE 5.1: QUERY STRATEGY DIFFERENTIATION (ADDED)
# ============================================================================

# OLD IMPLEMENTATION - REPLACED 2025-10-20
# Kept for reference, remove after validation period
"""
def generate_queries_r1(claim_text: str, entities: list, numbers: list, arm: str) -> list:
    '''
    R1 (Precision) query strategy - quoted, anchored, exact.

    Characteristics:
    - Uses exact quotes
    - Anchors on specific entities + numbers
    - Conservative counter-frames
    - Aims for high precision (fewer results, high relevance)

    Args:
        claim_text: The claim
        entities: Extracted entities
        numbers: Extracted numbers
        arm: 'A' (support) or 'B' (challenge)

    Returns:
        List of query strings (3-5 queries)
    '''
    queries = []

    # Query 1: Exact claim (quoted)
    queries.append(f'"{claim_text}"')

    # Query 2: Entity + number combinations (quoted)
    if entities and numbers:
        for entity in entities[:2]:  # Top 2 entities
            for number in numbers[:2]:  # Top 2 numbers
                entity_str = entity if isinstance(entity, str) else entity.get('name', '')
                num_val = number.get('value', '') if isinstance(number, dict) else str(number)
                queries.append(f'"{entity_str}" {num_val}')

    # Query 3: Conservative counter-frame (if arm B)
    if arm == 'B' and entities:
        entity_str = entities[0] if isinstance(entities[0], str) else entities[0].get('name', '')
        queries.append(f'"{entity_str}" actual value')
        queries.append(f'"{entity_str}" verify')

    return queries[:5]  # Max 5 queries


def generate_queries_r2(claim_text: str, entities: list, numbers: list, arm: str) -> list:
    '''
    R2 (Recall) query strategy - paraphrased, exploratory, broad.

    Characteristics:
    - No quotes (natural language)
    - Paraphrased versions
    - Broader synonyms
    - Aggressive counter-frames
    - Aims for high recall (more results, cast wide net)

    Args:
        claim_text: The claim
        entities: Extracted entities
        numbers: Extracted numbers
        arm: 'A' (support) or 'B' (challenge)

    Returns:
        List of query strings (5-8 queries)
    '''
    queries = []

    # Query 1: Natural language (no quotes)
    queries.append(claim_text)

    # Query 2: Paraphrased (simple rewording)
    # TODO: Add actual paraphrase generation
    # For now, extract key terms
    if entities:
        entity_str = entities[0] if isinstance(entities[0], str) else entities[0].get('name', '')
        queries.append(f"{entity_str} data statistics")
        queries.append(f"{entity_str} report analysis")

    # Query 3: Broader exploratory terms
    if entities and numbers:
        entity_str = entities[0] if isinstance(entities[0], str) else entities[0].get('name', '')
        queries.append(f"{entity_str} trends changes")

    # Query 4: Aggressive counter-frames (if arm B)
    if arm == 'B' and entities:
        entity_str = entities[0] if isinstance(entities[0], str) else entities[0].get('name', '')
        queries.append(f"{entity_str} variation exceptions")
        queries.append(f"{entity_str} different conditions")
        queries.append(f"{entity_str} context factors")

    return queries[:8]  # Max 8 queries
"""


# ============================================================================
# SEMANTIC QUERY GENERATION (Replaces broken Phase 5 templates)
# ============================================================================

def _generate_semantic_queries_internal(
    claim: Dict[str, Any],
    arm: str,
    strategy: str,
    base_plan: Dict[str, Any] = None
) -> List[str]:
    """
    Generate semantic queries using compositional building + bi-encoder validation.

    Uses enrichment data (concept, dimension, entities, numbers) to build
    semantically meaningful queries, then validates with bi-encoder.

    Args:
        claim: Full enriched claim dict with text, entities, numbers
        arm: "A" (support) or "B" (challenge)
        strategy: "r1" (precision) or "r2" (recall)
        base_plan: Base plan with meta.concept and meta.dimension

    Returns:
        List of 3-8 high-quality query strings

    Raises:
        Exception: If bi-encoder fails or critical data missing
    """
    from intelligence.content.shared.embeddings import get_embeddings
    import logging

    logger = logging.getLogger(__name__)

    # Extract semantic components
    text = claim.get("text", "").strip()
    if not text:
        raise ValueError("Claim text is empty")

    concept = claim.get("concept", "")
    dimension = claim.get("dimension", "")
    entities = claim.get("entities", [])
    numbers = claim.get("numbers", {})

    # Extract concept/dimension from base_plan if not in claim
    if base_plan and not concept:
        concept = base_plan.get("meta", {}).get("concept", "")
    if base_plan and not dimension:
        dimension = base_plan.get("meta", {}).get("dimension", "")

    # Extract numeric values with units
    values = []
    for num_unit in numbers.get("number_units", []):
        if isinstance(num_unit, (list, tuple)) and len(num_unit) >= 2:
            values.append(f"{num_unit[0]} {num_unit[1]}")

    # Build query candidates with ARM-SPECIFIC logic (NO shared queries)
    candidates = []

    if arm == "A":
        # ========================================================================
        # ARM A: SUPPORT QUERIES - seeking confirmation and authoritative evidence
        # Strategy: Target textbooks, standards, peer-reviewed sources with precise values
        # ========================================================================
        logger.debug(f"Generating ARM A (support) queries for: {text}")

        # Always include the full claim text
        candidates.append(text)

        # TIER 1: Exact Value + Authority Source Queries
        # Target academic and reference materials with specific values
        if values and entities:
            entity = entities[0] if isinstance(entities[0], str) else entities[0].get('name', '')
            if entity:
                # Educational sources with exact values
                candidates.append(f'"{values[0]}" {entity} textbook')
                candidates.append(f'"{values[0]}" {entity} chemistry handbook')
                candidates.append(f'{entity} {values[0]} scientific reference')

                # Standards organizations
                candidates.append(f'{entity} {values[0]} standard definition')
                candidates.append(f'official {entity} {values[0]} specification')

        # TIER 2: Concept + Dimension with Domain Expertise
        # Target domain experts and educational materials
        if concept and dimension:
            candidates.append(f'{concept} {dimension} peer reviewed')
            candidates.append(f'{concept} {dimension} established science')
            candidates.append(f'{concept} {dimension} university')
            candidates.append(f'{concept} {dimension} handbook')
        elif concept:
            candidates.append(f'{concept} peer reviewed')

        # TIER 3: Quantitative Precision Queries
        # Include alternative unit representations for scientific precision
        if values and concept:
            candidates.append(f'{concept} exactly {values[0]}')
            candidates.append(f'{concept} measured {values[0]}')

            # Temperature conversion for celsius/fahrenheit
            if values[0] and any(unit in str(values[0]).lower() for unit in ['celsius', 'fahrenheit']):
                try:
                    num_str = ''.join(c for c in str(values[0]) if c.isdigit() or c == '.')
                    if num_str:
                        value_num = float(num_str)
                        if 'celsius' in str(values[0]).lower():
                            kelvin = value_num + 273.15
                            candidates.append(f'{concept} {kelvin} kelvin')
                except (ValueError, AttributeError):
                    pass

        # TIER 4: Research Evidence Queries
        # Target primary research and experimental data
        if concept:
            candidates.append(f'{concept} experimental measurement')
            candidates.append(f'{concept} published study')
            candidates.append(f'{concept} research findings')

        # TIER 5: Authority Domain Queries
        # Explicitly target high-credibility domains
        if concept and dimension:
            candidates.append(f'{concept} {dimension} .edu')
            candidates.append(f'{concept} {dimension} .gov')
            candidates.append(f'{concept} {dimension} scientific consensus')

    elif arm == "B":
        # ========================================================================
        # ARM B: CHALLENGE QUERIES - seeking context, limitations, and exceptions
        # Strategy: Target conditions, edge cases, variability factors, contextual dependencies
        # ========================================================================
        logger.debug(f"Generating ARM B (challenge) queries for: {text}")

        # Always include the full claim text
        candidates.append(text)

        # TIER 1: Context-Dependency Queries
        # Explicitly seek conditional and contextual information (AVOID exact value mentions)
        if concept and dimension:
            candidates.append(f'{concept} pressure altitude effects')
            candidates.append(f'{dimension} varies environmental conditions')
            candidates.append(f'{concept} different elevations')
            candidates.append(f'{dimension} atmospheric pressure relationship')
            if entities:
                entity = entities[0] if isinstance(entities[0], str) else entities[0].get('name', '')
                candidates.append(f'{entity} {concept} varying pressures')

        # TIER 2: Exception-Seeking Queries
        # Target specific counter-examples and edge cases (focus on variations, not values)
        if concept:
            candidates.append(f'non-standard conditions {concept}')
            candidates.append(f'{concept} exceptional cases')
            candidates.append(f'{concept} real world variations')
            candidates.append(f'factors affecting {concept}')

            if dimension:
                candidates.append(f'{dimension} variability')

        # TIER 3: Variability Factor Queries
        # Seek factors that cause deviation from claimed value
        if concept and dimension:
            candidates.append(f'{concept} {dimension} factors affecting')
            candidates.append(f'{concept} {dimension} environmental effects')
            candidates.append(f'{concept} {dimension} measurement conditions')
            candidates.append(f'{concept} {dimension} depends on purity')

        # TIER 4: Comparative/Nuance Queries
        # Find discussions of complexity and context-dependency (avoid exact value)
        if concept:
            candidates.append(f'{concept} complexity contextual factors')
            candidates.append(f'{concept} simplified vs actual')
            candidates.append(f'{concept} depends on multiple variables')

        # TIER 5: Scientific Nuance Queries
        # Target advanced discussions of factors and variables
        if concept:
            candidates.append(f'{concept} variables influence')
            candidates.append(f'{concept} factors determine')
            candidates.append(f'{concept} conditions required')

        # TIER 6: Domain-Specific Challenge Patterns
        # Specialized patterns based on claim type
        if concept:
            concept_lower = concept.lower()

            # Physical phase transitions (pressure/purity dependent)
            if any(x in concept_lower for x in ["boiling", "melting", "freezing", "phase"]):
                candidates.append(f'{concept} pressure dependence')
                candidates.append(f'{concept} altitude effect')
                candidates.append(f'{concept} phase diagram')
                candidates.append(f'{concept} impurities effect')
                if dimension:
                    candidates.append(f'{concept} {dimension} atmospheric pressure')

            # Medical/biological (individual variability)
            elif any(x in concept_lower for x in ["dosage", "drug", "medicine", "treatment"]):
                candidates.append(f'{concept} individual variation')
                candidates.append(f'{concept} patient factors')
                candidates.append(f'{concept} contraindications')
                candidates.append(f'{concept} side effects')

            # Statistical claims (methodology dependent)
            elif any(x in concept_lower for x in ["rate", "percentage", "statistics", "population"]):
                candidates.append(f'{concept} methodology differences')
                candidates.append(f'{concept} sampling bias')
                candidates.append(f'{concept} demographic factors')
                candidates.append(f'{concept} regional variation')

            # Chemical reactions (conditions matter)
            elif any(x in concept_lower for x in ["reaction", "chemical", "catalyst"]):
                candidates.append(f'{concept} reaction conditions')
                candidates.append(f'{concept} temperature dependence')
                candidates.append(f'{concept} catalyst effects')

        # TIER 7: Entity + Contextual Queries
        if entities and concept:
            entity = entities[0] if isinstance(entities[0], str) else entities[0].get('name', '')
            if entity:
                candidates.append(f'{entity} {concept} context dependent')
                candidates.append(f'{entity} {concept} varying conditions')

    else:
        # Fallback for unknown arm (should not happen, but handle gracefully)
        logger.warning(f"Unknown arm '{arm}', generating generic queries")
        candidates.append(text)
        if concept:
            candidates.append(concept)
        if concept and dimension:
            candidates.append(f"{concept} {dimension}")

    # 6. Validate with bi-encoder
    emb = get_embeddings()  # Let this fail if embeddings not available

    scored_queries = []
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate or candidate == '""':
            continue

        # Score semantic similarity to original claim
        similarity = emb.get_semantic_similarity(text, candidate)
        scored_queries.append((candidate, similarity))

    # Sort by similarity (highest first)
    scored_queries.sort(key=lambda x: x[1], reverse=True)

    # Filter: Keep queries with similarity > 0.4
    filtered = [(q, s) for q, s in scored_queries if s >= 0.4]

    if not filtered:
        # If nothing passed threshold, this indicates a problem
        logger.error(f"No queries passed similarity threshold for claim: {text}")
        raise ValueError("Query generation failed: no valid candidates")

    # Return top-N based on strategy
    # R1 (precision): fewer queries
    # R2 (recall): more queries
    top_n = 5 if strategy == "r1" else 8

    result = [q for q, s in filtered[:top_n]]

    logger.info(f"✅ Generated {len(result)} {strategy} queries for arm {arm}")
    logger.debug(f"   Top query similarity: {filtered[0][1]:.3f}")
    logger.debug(f"   Queries: {result[:3]}...")  # Log first 3 queries for verification

    return result


def generate_queries_r1(
    claim: Dict[str, Any],
    arm: str,
    base_plan: Dict[str, Any] = None
) -> list:
    """
    R1 (Precision) query strategy - semantic queries with high similarity threshold.

    Replaces broken Phase 5 template-based implementation.

    Args:
        claim: Enriched claim dict
        arm: "A" (support) or "B" (challenge)
        base_plan: Base plan with meta fields

    Returns:
        List of 3-5 high-quality query strings
    """
    return _generate_semantic_queries_internal(claim, arm, "r1", base_plan)


def generate_queries_r2(
    claim: Dict[str, Any],
    arm: str,
    base_plan: Dict[str, Any] = None
) -> list:
    """
    R2 (Recall) query strategy - semantic queries with broader exploration.

    Replaces broken Phase 5 template-based implementation.

    Args:
        claim: Enriched claim dict
        arm: "A" (support) or "B" (challenge)
        base_plan: Base plan with meta fields

    Returns:
        List of 5-8 high-quality query strings
    """
    return _generate_semantic_queries_internal(claim, arm, "r2", base_plan)

