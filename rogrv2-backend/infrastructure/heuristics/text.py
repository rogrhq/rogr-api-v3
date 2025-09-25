import re
from typing import List, Set

_WORD = re.compile(r"[A-Za-z0-9]+", re.UNICODE)
_STOP = {
    "the","a","an","and","or","but","of","to","in","on","for","with","by","at","from",
    "this","that","these","those","has","have","had","was","were","is","are","be","been",
    "as","it","its","their","there","about","over","under","into","out","than","then",
}

def tokens(s: str) -> List[str]:
    return [t.lower() for t in _WORD.findall(s or "") if t and t.lower() not in _STOP]

def token_set(s: str) -> Set[str]:
    return set(tokens(s))

def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b: return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0

def keyword_overlap(a: str, b: str) -> float:
    return jaccard(token_set(a), token_set(b))

def has_negation(s: str) -> bool:
    s = (" " + (s or "").lower() + " ")
    for w in [" not ", " no ", " never ", " without ", " false ", " hoax ", " debunk ", " incorrect ", " misleading "]:
        if w in s: return True
    return False