# path: intelligence/content/extract_facts.py
"""
Deterministic utilities for extracting comparable facts from free text and claims.

Outputs are intentionally simple so they are auditable:
- entities: canonicalized surface forms from the claim (and simple aliases)
- numbers: percents and integers with tolerant representations (8% / "eight percent" / 0.08)
- years: 4-digit numbers likely to represent years (and FY markers)
- scope and predicate hints via lightweight pattern families
"""
from __future__ import annotations
from typing import List, Dict, Any, Tuple, Iterable
import re

# Shared advanced text processing utilities
from intelligence.content.shared.text_utils import tokenize_advanced as tokenize

_WORD = re.compile(r"[A-Za-z0-9%]+")
_APOS = re.compile(r"['׳`´]")
_NONWORD = re.compile(r"[^a-z0-9\s]")
_WS = re.compile(r"\s+")
_YEAR = re.compile(r"\b(20\d{2}|19\d{2})\b")
_FY = re.compile(r"\bFY\s?(20\d{2}|19\d{2})\b", re.I)
_PERCENT = re.compile(r"\b(\d{1,3})\s?%\b")
_NUMBER_WORDS = {
    "0":"zero","1":"one","2":"two","3":"three","4":"four","5":"five",
    "6":"six","7":"seven","8":"eight","9":"nine","10":"ten"
}
SCOPE_WORDS = ("general fund","all funds","enterprise fund","capital","operating","city budget","budget")
PRED_INCREASE = ("increase","increased","rising","rise","grew","growth","up","higher")
PRED_DECREASE = ("decrease","decreased","decline","down","lower","reduced","reduction")
NEGATORS = ("not","no","false","incorrect","deny","denied","dispute","disputed","refute","refuted","contradict","contradicted","debunk")

def _clean(s: str) -> str:
    s = (s or "").lower()
    s = _APOS.sub("'", s)
    s = _NONWORD.sub(" ", s)
    s = _WS.sub(" ", s).strip()
    return s

# Local tokenize() removed - now using shared tokenize_advanced from text_utils
# See intelligence/content/shared/text_utils.py for implementation

def percent_forms(n: str) -> List[str]:
    forms = [f"{n}%"]
    w = NUMBER_WORDS.get(n)
    if w:
        forms.append(f"{w} percent")
    return forms

# public constants
NUMBER_WORDS = _NUMBER_WORDS

def claim_entities(claim: str) -> List[str]:
    # entities as capitalized tokens + simple city council/city of aliases
    ents: List[str] = []
    for t in tokenize(claim):
        if len(t) > 2 and t[0].isupper():
            ents.extend([t, f"City of {t}", f"{t} City Council"])
    # dedupe preserving order
    seen=set(); out=[]
    for e in ents:
        if e not in seen:
            seen.add(e); out.append(e)
    return out[:6]

def claim_numbers(claim: str) -> List[str]:
    nums: List[str] = []
    for m in _PERCENT.finditer(claim or ""):
        n = m.group(1)
        nums.extend(percent_forms(n))
    # also add bare integers from the claim (e.g., "8")
    for t in tokenize(claim):
        if t.isdigit():
            nums.append(t)
            w = NUMBER_WORDS.get(t)
            if w: nums.append(f"{w} percent")
    # dedupe
    seen=set(); out=[]
    for x in nums:
        if x not in seen:
            seen.add(x); out.append(x)
    return out[:6]

def claim_years(claim: str) -> List[str]:
    yrs = [m.group(1) for m in _YEAR.finditer(claim or "")]
    fys = [m.group(1) for m in _FY.finditer(claim or "")]
    # dedupe
    seen=set(); out=[]
    for y in yrs + fys:
        if y not in seen:
            seen.add(y); out.append(y)
    return out[:4]

def has_any(hay: str, needles: Iterable[str]) -> bool:
    H = _clean(hay)
    return any(_clean(n) in H for n in needles if n)

def predicate_hint(text: str) -> str:
    T = _clean(text)
    if any(w in T for w in PRED_INCREASE):
        return "increase"
    if any(w in T for w in PRED_DECREASE):
        return "decrease"
    return "other"

def stance_hint(text: str) -> str:
    T = _clean(text)
    neg = any(w in T for w in NEGATORS)
    inc = any(w in T for w in PRED_INCREASE)
    dec = any(w in T for w in PRED_DECREASE)
    if neg and (inc or dec):
        return "challenge"
    if inc:
        return "support"  # default bias towards support for increase-like phrasing
    if dec:
        return "challenge"
    return "unrelated"

def jaccard_trigrams(a: str, b: str) -> float:
    def trigs(s: str) -> set[str]:
        s = _clean(s)
        return {s[i:i+3] for i in range(len(s)-2)} if len(s) >= 3 else set()
    A, B = trigs(a), trigs(b)
    if not A or not B:
        return 0.0
    return len(A & B) / float(len(A | B))

def best_window_for_text(claim: str, text: str, win: int = 4) -> Tuple[str, float]:
    """Return (window_text, jaccard) using a naive sliding window if no alignment matches are provided."""
    sents = re.split(r"(?<=[\.\!\?])\s+", text or "")[:80]
    best = ("", 0.0)
    for i in range(0, max(0, len(sents) - win + 1)):
        w = " ".join(sents[i:i+win])
        j = jaccard_trigrams(claim, w)
        if j > best[1]:
            best = (w, j)
    return best

def scope_hint(text: str) -> str:
    T = text.lower()
    for s in SCOPE_WORDS:
        if s in T:
            return s
    return ""

def extract_fact_view(claim: str, text: str) -> Dict[str, Any]:
    """Produce a minimal comparable view from the evidence text."""
    ents = claim_entities(claim)
    nums = claim_numbers(claim)
    yrs  = claim_years(claim)
    scope = scope_hint(text)
    pred  = predicate_hint(text)
    return {
        "entities": ents,
        "numbers": nums,
        "years": yrs,
        "scope": scope,
        "predicate": pred,
    }
