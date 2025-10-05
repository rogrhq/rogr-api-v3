"""
Deterministic full-read evaluator (no AI).

Exports:
    evaluate_full_evidence(claim_text: str, item: dict) -> dict
Attaches fields to item:
    - grade_full: float (0..10)
    - stance_full: str in {"support","challenge","mixed","unrelated"}
    - signals_full: dict (explainable features)
    - credibility: float in [0,1]
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple
import re
import math
from urllib.parse import urlparse

_WORD = re.compile(r"[a-z0-9]+")
_APOS = re.compile(r"['׳`´]")
_PUNCT = re.compile(r"[^a-z0-9\s]")
_PERCENT = re.compile(r"(?:(\d{1,3})(?:\.\d+)?)\s?%|\b(\d{1,2})\s?(?:percent|per\s?cent)\b", re.I)
_YEAR = re.compile(r"\b(19[5-9]\d|20[0-4]\d|2050)\b")
_NEG = re.compile(r"\b(no|not|never|without|lacks|declined|denied|false|incorrect|inaccurate|misleading)\b", re.I)
_SUPPORT = re.compile(r"\b(confirms?|supports?|corroborates?|shows|finds|indicates)\b", re.I)
_CHALLENGE = re.compile(r"\b(disputes?|contradicts?|refutes?|debunks?|casts\s+doubt|challenges?)\b", re.I)
_AUTHZ_WORDS = re.compile(r"\b(report|press\s+release|statement|dataset|methodology|audit|budget)\b", re.I)

def _norm(s: str) -> str:
    s = (s or "").lower()
    s = _APOS.sub("'", s)
    s = s.replace("'s", " ")
    s = _PUNCT.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _tokens(s: str) -> List[str]:
    return _WORD.findall(_norm(s))

def _ngrams(tokens: List[str], n: int) -> List[Tuple[str,...]]:
    return [tuple(tokens[i:i+n]) for i in range(0, max(0, len(tokens)-n+1))]

def _jaccard(a: List[Tuple[str,...]], b: List[Tuple[str,...]]) -> float:
    if not a or not b:
        return 0.0
    A = set(a)
    B = set(b)
    inter = len(A & B)
    union = len(A | B)
    return float(inter) / float(union or 1)

def _window_sentences(text: str, win: int = 4, max_sents: int = 80) -> List[List[str]]:
    # naive sentence split; keep small to be fast
    raw = re.split(r"(?<=[\.\?\!])\s+", text or "")
    sents = [s.strip() for s in raw if s.strip()]
    sents = sents[:max_sents]
    out: List[List[str]] = []
    for i in range(0, max(0, len(sents)-win+1)):
        out.append(sents[i:i+win])
    return out

def _stance_for_chunk(txt: str) -> str:
    sup = bool(_SUPPORT.search(txt))
    ch = bool(_CHALLENGE.search(txt))
    if sup and ch:
        return "mixed"
    if ch:
        return "challenge"
    if sup:
        return "support"
    return "unrelated"

def _percent_hits(claim: str, text: str) -> Tuple[bool, bool]:
    """(any_percent_in_claim, any_close_match_in_text)"""
    claim_nums = []
    for m in _PERCENT.finditer(claim):
        v = m.group(1) or m.group(2)
        if v:
            try:
                claim_nums.append(float(v))
            except Exception:
                pass
    tnums = []
    for m in _PERCENT.finditer(text):
        v = m.group(1) or m.group(2)
        if v:
            try:
                tnums.append(float(v))
            except Exception:
                pass
    if not claim_nums:
        return (False, False)
    # close if within 0.5 absolute or within 10% relative tolerance
    close = any(
        abs(t - c) <= 0.5 or (abs(t - c) / max(0.5, c)) <= 0.10
        for c in claim_nums for t in tnums
    )
    return (True, close)

def _year_hit(claim: str, text: str) -> bool:
    cy = {m.group(0) for m in _YEAR.finditer(claim)}
    ty = {m.group(0) for m in _YEAR.finditer(text)}
    return bool(cy & ty)

def _entity_overlap(claim: str, text: str) -> float:
    ct = set(_tokens(claim))
    tt = set(_tokens(text))
    if not ct or not tt:
        return 0.0
    inter = len(ct & tt)
    return inter / float(len(ct))

def _credibility_from(url: str, text: str) -> float:
    """
    Structural-only credibility in [0,1], no whitelists:
      + HTTPS scheme
      + TLD .gov/.edu bonus
      + presence of authz words in body (report/press release/statement/dataset/methodology/audit/budget)
    """
    score = 0.0
    try:
        p = urlparse(url or "")
        if p.scheme == "https":
            score += 0.15
        host = (p.hostname or "").lower()
        if host.endswith(".gov") or host.endswith(".edu"):
            score += 0.25
    except Exception:
        pass
    if _AUTHZ_WORDS.search(text or ""):
        score += 0.15
    return max(0.0, min(1.0, score))

def evaluate_full_evidence(claim_text: str, item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic deeper read on best available text. Returns mutated item.
    """
    read = item.get("content") or item.get("content_excerpt") or item.get("snippet") or ""
    # clamp read budget
    if len(read) > 12000:
        read = read[:12000]

    claim = claim_text or item.get("claim_text") or ""
    if not read.strip():
        # no text -> neutral low grade
        item["grade_full"] = float(item.get("grade") or 0.0)
        item["stance_full"] = item.get("finding", {}).get("stance") or "unrelated"
        item["signals_full"] = {"reason": "no_text"}
        item["credibility"] = _credibility_from(item.get("url") or "", "")
        return item

    # slide windows, compute best window by combined signal score
    best = {"score": -1.0, "stance": "unrelated", "jacc": 0.0, "neg": False,
            "entity_overlap": 0.0, "pct_any": False, "pct_close": False, "year_hit": False}
    claim_tri = _ngrams(_tokens(claim), 3)
    for chunk in _window_sentences(read, win=4, max_sents=80):
        txt = " ".join(chunk)
        tri = _ngrams(_tokens(txt), 3)
        j = _jaccard(claim_tri, tri)
        stance = _stance_for_chunk(txt)
        neg = bool(_NEG.search(txt))
        ent = _entity_overlap(claim, txt)
        pct_any, pct_close = _percent_hits(claim, txt)
        yh = _year_hit(claim, txt)
        # weighted score for window
        score = 0.0
        score += 2.0 * (1.0 if pct_close else 0.0) + 0.8 * (1.0 if pct_any else 0.0)
        score += 1.2 * (1.0 if yh else 0.0)
        score += 2.0 * min(ent, 1.0)
        score += 3.0 * j  # tri-gram paraphrase
        if stance in ("support", "challenge"):
            score += 0.8
        if score > best["score"]:
            best = {"score": score, "stance": stance, "jacc": j, "neg": neg,
                    "entity_overlap": ent, "pct_any": pct_any, "pct_close": pct_close, "year_hit": yh}

    # Map window score to 0..10 grade_full
    base = max(0.0, best["score"])
    # squashing to 0..10 with diminishing returns
    grade_full = 10.0 * (1.0 - math.exp(-base / 6.0))
    # stance normalization: if neg + challenge -> slightly stronger challenge; if neg + support -> reduce
    stance_full = best["stance"]
    if best["neg"] and stance_full == "challenge":
        grade_full = min(10.0, grade_full + 0.5)
    if best["neg"] and stance_full == "support":
        grade_full = max(0.0, grade_full - 0.5)

    item["grade_full"] = round(grade_full, 2)
    item["stance_full"] = stance_full
    item["signals_full"] = {
        "jaccard3": round(best["jacc"], 3),
        "entity_overlap": round(best["entity_overlap"], 3),
        "percent_any": bool(best["pct_any"]),
        "percent_close": bool(best["pct_close"]),
        "year_hit": bool(best["year_hit"]),
        "negation": bool(best["neg"]),
    }
    item["credibility"] = round(_credibility_from(item.get("url") or "", read), 3)
    return item
