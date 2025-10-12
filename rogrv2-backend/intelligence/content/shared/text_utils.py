"""Shared text processing utilities - consolidated from P21, P23, P24"""

import re

# Simple functions (for backward compatibility)
def normalize_text(text):
    """Normalize text for comparison - from P21 fullread.py line 53"""
    return text.lower().strip()

def tokenize(text):
    """Tokenize text into words - from P23 semantic_read.py line 89"""
    return text.lower().split()

def clean_text(text):
    """Remove extra whitespace - from P24 semantic_frames.py line 112"""
    return re.sub(r'\s+', ' ', text).strip()

def _norm(text):
    """Legacy normalization function - kept for backward compatibility"""
    return normalize_text(text)

# Advanced functions from P23 (sophisticated normalization and tokenization)

# Regex patterns for sophisticated normalization
_APOS = re.compile(r"['׳`´]")
_PUNCT = re.compile(r"[^a-z0-9\s]")
_WS = re.compile(r"\s+")

# Stop words for tokenization
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "will", "with"
}

def normalize_text_advanced(text: str) -> str:
    """Advanced normalization from P23 - handles apostrophes, punctuation"""
    s = (text or "").lower()
    s = _APOS.sub("'", s)
    s = s.replace("'s", " ")
    s = _PUNCT.sub(" ", s)
    s = _WS.sub(" ", s).strip()
    return s

def tokenize_advanced(text: str) -> list:
    """Advanced tokenization from P23 - removes stop words"""
    tokens = normalize_text_advanced(text).split()
    return [t for t in tokens if t and t not in STOP_WORDS]

def trigrams(tokens: list) -> list:
    """Create trigram tuples from token list"""
    if len(tokens) < 3:
        return []
    return [(tokens[i], tokens[i+1], tokens[i+2]) for i in range(len(tokens) - 2)]

def jaccard_similarity(set1, set2) -> float:
    """Jaccard similarity between two sets"""
    if not set1 or not set2:
        return 0.0
    s1 = set(set1) if not isinstance(set1, set) else set1
    s2 = set(set2) if not isinstance(set2, set) else set2
    intersection = len(s1 & s2)
    union = len(s1 | s2)
    return intersection / union if union > 0 else 0.0
