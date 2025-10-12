"""Shared entity extraction - consolidated from P23 and P24"""

import re

# Entity patterns - from P23 lines 58-65 and P24 lines 48-52
ENTITY_PATTERNS = {
    'organization': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Corp|LLC|Ltd|Company|Association|Department|Agency))',
    'person': r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
    'location': r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:City|County|State|Country|District)))\b',
    'date': r'\b(\d{4}|\d{1,2}/\d{1,2}/\d{2,4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b',
    'money': r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|thousand)?',
    'percentage': r'(\d+(?:\.\d+)?)\s*%',
}

def extract_entities(text):
    """
    Extract entities from text using pattern matching.
    Consolidated from P23 line 67 and P24 line 55.

    Returns dict of entity_type -> list of matches
    """
    entities = {}
    for entity_type, pattern in ENTITY_PATTERNS.items():
        # Use IGNORECASE for most patterns, but NOT for organization (needs proper capitalization)
        flags = 0 if entity_type == 'organization' else re.IGNORECASE
        matches = re.findall(pattern, text, flags)
        if matches:
            entities[entity_type] = matches
    return entities

def extract_entities_by_type(text, entity_type):
    """Extract specific entity type - from P23 line 74"""
    pattern = ENTITY_PATTERNS.get(entity_type)
    if not pattern:
        return []
    # Use IGNORECASE for most patterns, but NOT for organization (needs proper capitalization)
    flags = 0 if entity_type == 'organization' else re.IGNORECASE
    return re.findall(pattern, text, flags)

def entity_overlap(entities1, entities2):
    """
    Check if two entity sets have overlap.
    From P23 line 78 - used for identity matching.
    """
    for etype in entities1:
        if etype in entities2:
            set1 = set(entities1[etype])
            set2 = set(entities2[etype])
            if set1 & set2:  # intersection
                return True
    return False
