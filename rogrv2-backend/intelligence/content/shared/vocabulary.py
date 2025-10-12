"""Shared vocabulary - consolidated from P24, extract_facts, P21, P23"""

# From P24 semantic_frames.py lines 74-75
P24_INC_VERBS = {"increase", "rise", "grow", "boost", "surge", "jump", "climb"}
P24_DEC_VERBS = {"decrease", "drop", "fall", "decline", "plunge", "shrink"}

# From extract_facts.py lines 27-28
EXTRACT_FACTS_INC = ("increase", "rising", "growth", "up", "higher", "grew", "climbed")
EXTRACT_FACTS_DEC = ("decrease", "falling", "decline", "down", "lower", "fell", "dropped")

# MERGED - Combine all increase verbs
INC_VERBS = set(P24_INC_VERBS) | set(EXTRACT_FACTS_INC)

# MERGED - Combine all decrease verbs
DEC_VERBS = set(P24_DEC_VERBS) | set(EXTRACT_FACTS_DEC)

# Negation words - consolidated from P21 line 67, P23 line 94, P24 line 83
NEGATION_WORDS = {
    "not", "no", "never", "neither", "nor", "none", "nobody",
    "nothing", "nowhere", "hardly", "scarcely", "barely"
}

# Action families for export
ACTION_VERBS = {
    'increase': INC_VERBS,
    'decrease': DEC_VERBS
}

# Helper function
def is_negation(word):
    """Check if word is a negation"""
    return word.lower() in NEGATION_WORDS
