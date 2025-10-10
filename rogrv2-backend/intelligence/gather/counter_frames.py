from typing import List, Dict, Tuple, Set, Any
import re


def generate_counter_frame_queries(claim_text: str, original_queries: List[str]) -> List[Tuple[str, str]]:
    """
    Generate 5 types of counter-frame queries for the challenge arm (Arm B).

    Args:
        claim_text: The claim to generate counter-frames for
        original_queries: Original queries (not currently used but kept for API compatibility)

    Returns:
        List of (frame_name, query_string) tuples
    """
    # Extract anchors from claim
    anchors = _extract_anchors(claim_text)

    # Frame types to generate
    frame_types = [
        "numeric_dispute",
        "denominator_shift",
        "timing_change",
        "authority_conflict",
        "methodology"
    ]

    # Build queries for each frame type
    queries = []
    for frame_type in frame_types:
        query = _build_frame_query(frame_type, claim_text, anchors)
        queries.append((frame_type, query))

    return queries


def _extract_anchors(claim_text: str) -> Dict[str, List[str]]:
    """
    Extract key elements from claim.

    Args:
        claim_text: The claim text to extract from

    Returns:
        Dictionary with entities, numbers, years, and keywords
    """
    # Extract entities (capitalized words)
    entities = re.findall(r'\b[A-Z][a-z]+\b', claim_text)

    # Extract numbers (including percentages)
    numbers = re.findall(r'\b\d+\.?\d*%?\b', claim_text)

    # Extract years (4-digit years starting with 19 or 20)
    years = re.findall(r'\b(?:19|20)\d{2}\b', claim_text)

    # Extract keywords (lowercase, 4+ chars, no common stopwords)
    stopwords = {'that', 'this', 'with', 'from', 'have', 'been', 'were', 'said', 'about', 'than', 'into', 'over', 'they', 'them', 'their', 'what', 'when', 'where', 'which', 'while', 'would', 'could', 'should'}
    words = re.findall(r'\b[a-z]{4,}\b', claim_text.lower())
    keywords = [w for w in words if w not in stopwords]

    return {
        "entities": entities,
        "numbers": numbers,
        "years": years,
        "keywords": keywords
    }


def _build_frame_query(frame_type: str, claim_text: str, anchors: Dict) -> str:
    """
    Build query for specific frame type.

    Args:
        frame_type: Type of counter-frame
        claim_text: Original claim text
        anchors: Extracted anchors from claim

    Returns:
        Formatted query string
    """
    # Templates for each frame type
    templates = {
        "numeric_dispute": "{entity} {number} audit revised actual figure",
        "denominator_shift": "{entity} total baseline context general fund",
        "timing_change": "{entity} {year} rescinded changed amended revised",
        "authority_conflict": "{entity} official statement comptroller minutes",
        "methodology": "{entity} methodology calculation how measured"
    }

    # Get template for this frame type
    template = templates.get(frame_type, "{entity} {number}")

    # Get first entity (or first word from claim as fallback)
    entity = anchors['entities'][0] if anchors['entities'] else claim_text.split()[0]

    # Get first number
    number = anchors['numbers'][0] if anchors['numbers'] else ""

    # Get first year
    year = anchors['years'][0] if anchors['years'] else ""

    # Replace placeholders
    query = template.replace("{entity}", entity)
    query = query.replace("{number}", number)
    query = query.replace("{year}", year)

    # Clean up extra spaces
    query = re.sub(r'\s+', ' ', query).strip()

    return query


def compute_coverage_metrics(candidates: List[Dict], queries: List[str], providers_used: Set[str]) -> Dict[str, Any]:
    """
    Compute coverage statistics.

    Args:
        candidates: List of candidate results
        queries: List of queries issued
        providers_used: Set of provider names used

    Returns:
        Dictionary with coverage metrics
    """
    return {
        "frames_attempted": 5,  # Always 5 frame types
        "providers_used": len(providers_used),
        "queries_issued": len(queries),
        "candidates_fetched": len(candidates)
    }


def reorder_by_anchor_score(candidates: List[Dict], claim_text: str) -> List[Dict]:
    """
    Reorder candidates by anchor match score.

    Args:
        candidates: List of candidate items
        claim_text: Original claim text

    Returns:
        Reordered list (all candidates, sorted by relevance)
    """
    # Extract anchors from claim
    anchors = _extract_anchors(claim_text)

    # Combine all anchors into a single list for matching
    all_anchors = (
        anchors['entities'] +
        anchors['numbers'] +
        anchors['years'] +
        anchors['keywords']
    )

    # Convert to lowercase for case-insensitive matching
    all_anchors_lower = [a.lower() for a in all_anchors]

    # Score each candidate
    scored_candidates = []
    for candidate in candidates:
        # Get text fields to search
        snippet = candidate.get('snippet', '').lower()
        title = candidate.get('title', '').lower()
        combined_text = snippet + ' ' + title

        # Count anchor matches
        score = sum(1 for anchor in all_anchors_lower if anchor in combined_text)

        scored_candidates.append((score, candidate))

    # Sort by score (highest first)
    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    # Return just the candidates (without scores)
    return [candidate for score, candidate in scored_candidates]


if __name__ == "__main__":
    # Test query generation
    claim = "Austin budget increased 8% in 2024"
    queries = generate_counter_frame_queries(claim, ["Austin budget"])

    print(f"Generated {len(queries)} counter-frame queries:")
    for frame, query in queries:
        print(f"  {frame}: {query}")

    assert len(queries) == 5, f"Expected 5 queries, got {len(queries)}"
    frame_names = [f for f, q in queries]
    assert "numeric_dispute" in frame_names
    assert "denominator_shift" in frame_names

    # Test coverage metrics
    candidates = [
        {'provider': 'google'},
        {'provider': 'brave'},
        {'provider': 'google'}
    ]
    coverage = compute_coverage_metrics(candidates, ["q1", "q2"], {"google", "brave"})
    print(f"\nCoverage: {coverage}")
    assert coverage['providers_used'] == 2
    assert coverage['queries_issued'] == 2
    assert coverage['candidates_fetched'] == 3

    # Test anchor extraction
    anchors = _extract_anchors(claim)
    print(f"\nAnchors: {anchors}")
    assert "Austin" in anchors['entities']
    assert any('8' in n for n in anchors['numbers'])

    print("\n✓ PASS: All tests")
