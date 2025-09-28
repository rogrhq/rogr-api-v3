from __future__ import annotations
import os
import re
from typing import Dict, Any, List

_PRONOUNS = re.compile(r"\b(he|she|they|it|this|that|these|those)\b", re.I)

def _max_chars() -> int:
    try:
        return max(256, int(os.getenv("POLICY_MAX_CHARS", "2000")))
    except Exception:
        return 2000

def _min_chars() -> int:
    try:
        return max(1, int(os.getenv("POLICY_MIN_CHARS", "8")))
    except Exception:
        return 8

def _rough_tokens(text: str) -> int:
    # cheap token proxy
    return len(re.findall(r"\w+", text or ""))

def check_input(text: str) -> Dict[str, Any]:
    text = text or ""
    maxc = _max_chars()
    minc = _min_chars()
    L = len(text)
    min_ok = L >= minc
    max_ok = L <= maxc
    ambiguous: List[str] = []
    # naive ambiguity: pronouns without obvious named entities (uppercase words) nearby
    if _PRONOUNS.search(text) and not re.search(r"\b[A-Z][a-z]{2,}\b", text):
        ambiguous.append("pronoun_without_entity")

    return {
        "min_length_ok": bool(min_ok),
        "max_length_ok": bool(max_ok),
        "length": L,
        "rough_tokens": _rough_tokens(text),
        "ambiguity_flags": ambiguous,
        "safe_to_process": bool(min_ok and max_ok),
        "max_chars_limit": maxc,
        "min_chars_limit": minc,
        "version": "s2p8-1",
    }