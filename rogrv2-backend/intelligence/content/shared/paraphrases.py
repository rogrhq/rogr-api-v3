"""Paraphrase and synonym matching - NEW module (gap identified in inventory)"""

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

def paraphrase_match_score(text1, text2):
    """
    Compute paraphrase match score between two texts.
    Returns: 0.0 (no match) to 1.0 (all words have paraphrases)
    """
    from intelligence.content.shared.text_utils import tokenize_advanced

    tokens1 = tokenize_advanced(text1)
    tokens2 = tokenize_advanced(text2)

    matches = 0
    for t1 in tokens1:
        for t2 in tokens2:
            if are_paraphrases(t1, t2):
                matches += 1
                break

    if not tokens1:
        return 0.0

    return matches / len(tokens1)
