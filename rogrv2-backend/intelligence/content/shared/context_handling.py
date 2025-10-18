"""
Phase 9.2: Temporal & Geographic Context Handling

Handles date-based relevance and geographic scope matching.
"""

from datetime import datetime
import re

def extract_publication_date(content: str, url: str = '') -> datetime:
    """
    Extract publication date from content or URL.

    Tries multiple strategies:
    1. Common date patterns in content
    2. Date in URL path
    3. Returns None if not found
    """

    # Strategy 1: Look for dates in content
    date_patterns = [
        r'Published:\s*(\w+\s+\d{1,2},\s+\d{4})',  # Published: January 15, 2023
        r'(\w+\s+\d{1,2},\s+\d{4})',                # January 15, 2023
        r'(\d{4}-\d{2}-\d{2})',                     # 2023-01-15 (ISO format)
        r'(\d{1,2}/\d{1,2}/\d{4})',                 # 01/15/2023
    ]

    for pattern in date_patterns:
        match = re.search(pattern, content)
        if match:
            date_str = match.group(1)
            try:
                # Try parsing (simplified - would need proper date parsing)
                # This is a placeholder
                return datetime.now()  # Would parse actual date
            except:
                continue

    # Strategy 2: Look in URL (e.g., /2023/01/15/article)
    url_date_pattern = r'/(\d{4})/(\d{2})/(\d{2})/'
    match = re.search(url_date_pattern, url)
    if match:
        year, month, day = match.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except:
            pass

    return None  # Could not determine date


def calculate_temporal_weight(item_date: datetime, claim_type: str,
                              current_date: datetime = None) -> float:
    """
    Weight evidence by publication date based on claim type.

    Claim types handle currency differently:
    - SIMPLE_FACTUAL/SCIENTIFIC: Date doesn't matter much (facts don't change)
    - HISTORICAL: Prefer contemporary sources
    - COMPLEX_FACTUAL/POLICY: Recent data important

    Returns:
        Temporal weight 0-1 (1.0 = perfect currency)
    """

    if item_date is None:
        return 0.8  # Unknown date, slight penalty

    current_date = current_date or datetime.now()
    age_days = (current_date - item_date).days

    # Age in years
    age_years = age_days / 365

    if claim_type in ['SIMPLE_FACTUAL', 'SCIENTIFIC']:
        # Unchanging facts: date doesn't matter much
        if age_years < 5:
            return 1.0
        elif age_years < 10:
            return 0.95
        else:
            return 0.90

    elif claim_type == 'HISTORICAL':
        # Historical claims: prefer contemporary sources
        # (Would need claim year to calculate properly)
        # Placeholder: slight preference for older = more contemporary
        if age_years < 5:
            return 0.90  # Recent analysis
        else:
            return 1.0   # Could be contemporary

    elif claim_type in ['COMPLEX_FACTUAL', 'POLICY']:
        # Current data important
        if age_years < 1:
            return 1.0   # Very recent
        elif age_years < 2:
            return 0.90
        elif age_years < 5:
            return 0.75
        else:
            return 0.60  # Outdated

    return 0.8  # Default


def extract_geographic_scope(text: str) -> list:
    """
    Extract geographic context from text.

    Returns:
        List of locations mentioned (or ['Global'] if none/worldwide)
    """

    locations = []

    # Common location patterns
    patterns = {
        'USA': r'\b(United States|USA|U\.S\.|America|US)\b',
        'UK': r'\b(United Kingdom|UK|U\.K\.|Britain|British)\b',
        'China': r'\bChina\b',
        'Europe': r'\bEurope\b',
        'Global': r'\b(world|global|worldwide|international)\b',
    }

    text_lower = text.lower()

    for location, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            locations.append(location)

    return locations if locations else ['Global']  # Default global


def check_geographic_match(claim_scope: list, item_scope: list) -> float:
    """
    Check if geographic scopes match.

    Returns:
        Match score 0-1 (1.0 = perfect match)
    """

    # Global matches everything
    if 'Global' in claim_scope or 'Global' in item_scope:
        return 1.0

    # Check overlap
    overlap = set(claim_scope) & set(item_scope)

    if overlap:
        return 1.0  # Has overlap

    # No overlap
    return 0.7  # Penalty for geographic mismatch

