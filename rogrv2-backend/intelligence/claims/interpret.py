from __future__ import annotations
from typing import Dict, Any, List, Optional
import re

_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_PCT  = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_STOP = {"The","A","An","In","On","At","Of","For","To","By","And","Or","But","If","Then","With","From","This","That"}

def interpret(text: str) -> Dict[str, Any]:
    s = (text or "").strip()

    year: Optional[str] = None
    m = _YEAR.search(s)
    if m: year = m.group(0)

    pct: Optional[str] = None
    m2 = _PCT.search(s)
    if m2: pct = m2.group(1)

    ents: List[str] = []
    # very light entity heuristic: keep capitalized tokens not in STOP
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-']{1,}", s)
    seen_l = set()
    for t in tokens:
        if t[0].isupper() and t not in _STOP:
            tl = t.lower()
            if tl not in seen_l:
                ents.append(t)
                seen_l.add(tl)

    # predicate/object hinting (super light verbs/nouns)
    predicate_hint = None
    if re.search(r"\b(increase|increased|raises?|raised|approve[sd]?)\b", s, re.I):
        predicate_hint = "increase_or_approve"

    object_hint = None
    if re.search(r"\b(budget|appropriation|spend|spending)\b", s, re.I):
        object_hint = "budget"

    return {
        "text": s,
        "entities": ents,
        "year": year,
        "percent": pct,
        "predicate_hint": predicate_hint,
        "object_hint": object_hint,
    }