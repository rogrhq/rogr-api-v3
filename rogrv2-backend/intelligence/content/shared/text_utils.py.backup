"""Shared text processing utilities - consolidated from P21, P23, P24"""

def normalize_text(text):
    """Normalize text for comparison - from P21 fullread.py line 53"""
    return text.lower().strip()

def tokenize(text):
    """Tokenize text into words - from P23 semantic_read.py line 89"""
    return text.lower().split()

def clean_text(text):
    """Remove extra whitespace - from P24 semantic_frames.py line 112"""
    import re
    return re.sub(r'\s+', ' ', text).strip()

def _norm(text):
    """Legacy normalization function - kept for backward compatibility"""
    return normalize_text(text)
