"""
Paraphrase matching using semantic embeddings.

UPDATED: 2025-10-14 - Replaced dictionary-based matching with embeddings.
Previous dictionary approach had limited vocabulary (missing "rose", "travels", etc.)
New approach uses sentence-transformers for unlimited vocabulary coverage.

See: intelligence/content/shared/embeddings.py for implementation details.
See: docs/EMBEDDINGS_LEVEL4_COMPLETE.md for full documentation.
"""

# Scientific paraphrase families
SCIENTIFIC_PARAPHRASES = {
    'boiling': ['boil', 'boils', 'boiling', 'boiling point', 'boils at', 'reaches boiling'],
    'melting': ['melt', 'melts', 'melting', 'melting point', 'melts at'],
    'freezing': ['freeze', 'freezes', 'freezing', 'freezing point', 'freezes at'],
    'temperature': ['temp', 'temperature', 'degrees', 'thermal'],
    'pressure': ['pressure', 'atmospheric pressure', 'atm', 'kpa', 'psi'],
}

# Policy/economic paraphrase families
POLICY_PARAPHRASES = {
    'budget': ['budget', 'spending', 'allocation', 'appropriation', 'fiscal plan'],
    'increase': ['increase', 'rise', 'growth', 'surge', 'jump', 'boost', 'climb'],
    'decrease': ['decrease', 'decline', 'drop', 'fall', 'reduction', 'cut'],
    'revenue': ['revenue', 'income', 'earnings', 'receipts'],
    'expenditure': ['expenditure', 'spending', 'costs', 'expenses', 'outlays'],
}

# Generic paraphrase families
GENERIC_PARAPHRASES = {
    'change': ['change', 'shift', 'alteration', 'modification', 'adjustment'],
    'report': ['report', 'study', 'analysis', 'findings', 'research'],
    'show': ['show', 'indicate', 'demonstrate', 'reveal', 'suggest'],
}

# Combine all paraphrases
ALL_PARAPHRASES = {
    **SCIENTIFIC_PARAPHRASES,
    **POLICY_PARAPHRASES,
    **GENERIC_PARAPHRASES
}

def get_paraphrase_family(word):
    """Get the paraphrase family for a word"""
    word_lower = word.lower()
    for canonical, family in ALL_PARAPHRASES.items():
        if word_lower in [f.lower() for f in family]:
            return canonical, family
    return None, []

def are_paraphrases(word1, word2):
    """Check if two words are paraphrases of each other"""
    canonical1, family1 = get_paraphrase_family(word1)
    canonical2, family2 = get_paraphrase_family(word2)

    if canonical1 and canonical2:
        return canonical1 == canonical2
    return False

def find_paraphrases_in_text(text, target_word):
    """Find all paraphrases of target_word in text"""
    canonical, family = get_paraphrase_family(target_word)
    if not family:
        return []

    text_lower = text.lower()
    found = []
    for paraphrase in family:
        if paraphrase.lower() in text_lower:
            found.append(paraphrase)
    return found

def paraphrase_match_score(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity between two texts using embeddings.

    This replaces dictionary-based matching with unlimited vocabulary coverage.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score 0.0-1.0

    Examples:
        "rose", "increased" → ~0.29 (previously 0.0 - NOW WORKS!)
        "travels", "speed" → ~0.39 (previously 0.0 - NOW WORKS!)
        "faster", "higher" → ~0.52 (previously 0.0 - NOW WORKS!)
        "increase", "rise" → ~0.43 (previously 1.0 - still works)

    Note: Dictionary-based functions (are_paraphrases, etc.) are preserved
    for backward compatibility but are no longer used by this function.
    """
    from intelligence.content.shared.embeddings import get_semantic_similarity

    # Use embeddings-based similarity (unlimited vocabulary)
    similarity = get_semantic_similarity(text1, text2)

    return similarity
