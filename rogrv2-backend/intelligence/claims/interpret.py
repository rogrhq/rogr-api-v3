from __future__ import annotations
import re
from typing import Dict, List, Any, Tuple

# Very lightweight deterministic interpreters (no external NLP deps)
_WORD = re.compile(r"[A-Za-z][A-Za-z\-\']+")
_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_PERCENT = re.compile(r"\b(-?\d+(?:\.\d+)?)\s*%")
_NUMBER_UNIT = re.compile(r"\b(-?\d+(?:\.\d+)?)\s*(million|billion|k|thousand|percent|%)\b", re.I)
# crude entity-ish: sequences of Capitalized Words (excluding start-of-sentence artifacts when possible)
_ENTITY = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b")
# negation and comparison cues
_NEG_CUES = {"not","no","never","none","n't"}
_COMP_CUES = {"more","less","increase","decrease","higher","lower","rise","fell","fewer","greater","smaller","above","below","exceed","drop","up","down"}
_ATTRIB_CUES = {"claims","said","according","reported","announced","stated","told","alleged"}

def _tokens(s: str) -> List[str]:
    return [m.group(0).lower() for m in _WORD.finditer(s)]

def _entities(s: str) -> List[str]:
    ents: List[str] = []
    for m in _ENTITY.finditer(s):
        val = m.group(1)
        # Heuristics: skip pronouns / articles
        if val in {"The","A","An"}:
            continue
        if len(val) < 3:
            continue
        ents.append(val)
    # dedupe preserving order
    seen=set(); out=[]
    for e in ents:
        if e not in seen:
            seen.add(e); out.append(e)
    return out

def _numbers(s: str) -> Dict[str, Any]:
    percents = [float(p) for p in _PERCENT.findall(s)]
    year_matches = [int(y.group(0)) for y in _YEAR.finditer(s)]
    num_units: List[Tuple[float,str]] = []
    for m in _NUMBER_UNIT.finditer(s):
        v = float(m.group(1))
        u = m.group(2).lower()
        num_units.append((v,u))
    return {"percents": percents, "years": year_matches, "number_units": num_units}

def _cues(tokens: List[str]) -> Dict[str, Any]:
    neg = any(t in _NEG_CUES for t in tokens)
    comp = any(t in _COMP_CUES for t in tokens)
    attrib = any(t in _ATTRIB_CUES for t in tokens)
    return {"has_negation": neg, "has_comparison": comp, "has_attribution": attrib}

def parse_claim(text: str) -> Dict[str, Any]:
    """
    Deterministic enrichment for a claim string:
    - entities: rough proper-noun detection
    - numbers: percents, year hints, number+unit pairs
    - cues: negation/comparison/attribution flags
    - scope guess: geographic/time hints
    """
    s = (text or "").strip()
    toks = _tokens(s)
    ents = _entities(s)
    nums = _numbers(s)
    cues = _cues(toks)

    # scope guesses (very light)
    scope: Dict[str, Any] = {}
    if nums["years"]:
        scope["year_hint"] = nums["years"][0]
    # geo guess: first entity that looks like a place-ish name (cheap heuristic)
    for e in ents:
        if e in {"US","U.S.","USA","United States","Europe"} or len(e.split()) in (1,2):
            scope["geo_hint"] = e
            break

    return {
        "text": s,
        "entities": ents,
        "numbers": nums,
        "cues": cues,
        "scope": scope,
        "kind_hint": "comparative" if cues["has_comparison"] else "attribution" if cues["has_attribution"] else "statement",
    }