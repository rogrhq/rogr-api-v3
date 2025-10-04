from __future__ import annotations
from typing import List, Dict, Any, Tuple
import re

__all__ = [
    "align_claim_to_text",
    "extract_claim_pieces",
    "split_sentences",
]

_SENT_SPLIT = re.compile(r"(?<=[\.!?])\s+")
_WORD = re.compile(r"[A-Za-z][A-Za-z\-']+")
_YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")
_PERCENT_IN_CLAIM = re.compile(r"(\d+(?:\.\d+)?)\s*%|(\d+)\s*percent", re.IGNORECASE)

INCREASE = re.compile(r"\b(increase|increased|raises?|raised|rise|rose|grow|grew|growth)\b", re.IGNORECASE)
DECREASE = re.compile(r"\b(decrease|decreased|cut|cuts|reduction|reduced|decline|fell|drop|dropped)\b", re.IGNORECASE)
NEG = re.compile(r"\b(no|not|did\s+not|does\s+not|never|without|deny|denies|false)\b", re.IGNORECASE)


def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    parts = _SENT_SPLIT.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def extract_claim_pieces(claim: str) -> Dict[str, Any]:
    claim_l = (claim or "").strip()
    # entities: capitalized tokens in claim
    entities: List[str] = []
    for m in _WORD.finditer(claim_l):
        w = m.group(0)
        if w[:1].isupper():
            entities.append(w.lower())
    entities = list(dict.fromkeys(entities))  # dedupe preserve order
    # percent number
    pct_num: str | None = None
    m = _PERCENT_IN_CLAIM.search(claim_l)
    if m:
        pct_num = (m.group(1) or m.group(2) or "").split(".")[0]
    years = [y for y in _YEAR.findall(claim_l)]
    return {"entities": entities, "percent": pct_num, "years": years}


def _percent_hit(sentence: str, num: str | None) -> bool:
    if not num:
        return False
    s = sentence.lower()
    return (f"{num}%" in s) or (re.search(rf"\b{re.escape(num)}\s*percent\b", s) is not None)


def _entity_hit(sentence: str, entities: List[str]) -> bool:
    s = sentence.lower()
    return any((f" {e} " in f" {s} ") for e in entities[:4])  # first few entities only


def _year_hit(sentence: str, years: List[str]) -> bool:
    if not years:
        return False
    s = sentence
    return any((y in s) for y in years)


def _stance_for_sentence(sentence: str) -> str:
    # very small heuristic: increase + not/negation -> challenge; decrease verbs -> challenge; increase -> support
    sent = sentence
    inc = INCREASE.search(sent) is not None
    dec = DECREASE.search(sent) is not None
    neg = NEG.search(sent) is not None
    if dec:
        return "challenge"
    if inc and neg:
        return "challenge"
    if inc and not neg:
        return "support"
    return "unrelated"


def align_claim_to_text(claim: str, text: str) -> Dict[str, Any]:
    pieces = extract_claim_pieces(claim)
    entities = pieces.get("entities") or []
    pct = pieces.get("percent")
    years = pieces.get("years") or []
    matches: List[Dict[str, Any]] = []
    entity_hit = False
    number_hit = False
    year_hit = False
    best_score = 0.0
    best_stance = "unrelated"
    for sent in split_sentences(text):
        fields: List[str] = []
        eh = _entity_hit(sent, entities)
        nh = _percent_hit(sent, pct)
        yh = _year_hit(sent, years)
        if eh:
            fields.append("entity")
        if nh:
            fields.append("number")
        if yh:
            fields.append("year")
        if fields:
            stance = _stance_for_sentence(sent)
            score = 0.5 + 0.25 * min(2, len(fields))  # 0.75 or 1.0 for 2+ fields
            matches.append({"sentence": sent, "fields": fields, "stance": stance, "score": score})
            entity_hit = entity_hit or eh
            number_hit = number_hit or nh
            year_hit = year_hit or yh
            if score > best_score:
                best_score = score
                best_stance = stance
    return {
        "entity_hit": bool(entity_hit),
        "number_hit": bool(number_hit),
        "year_hit": bool(year_hit),
        "matches": matches,
        "content_score": float(best_score),
        "item_stance": best_stance,
    }
