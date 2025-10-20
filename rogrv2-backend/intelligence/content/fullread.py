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

# Shared advanced text processing utilities
from intelligence.content.shared.text_utils import normalize_text_advanced as _norm, tokenize_advanced as _tokens
from intelligence.content.shared.paraphrases import paraphrase_match_score
from intelligence.content.shared.conditions import extract_conditions, conditions_equivalent
from intelligence.content.shared.units import values_match
from intelligence.content.shared.frames import extract_frame, compare_frames
# Phase 9.2: Temporal/geographic context (ADDED)
from intelligence.content.shared.context_handling import (
    extract_publication_date,
    calculate_temporal_weight,
    extract_geographic_scope,
    check_geographic_match
)

# Regex patterns for specific matching
_PERCENT = re.compile(r"(?:(\d{1,3})(?:\.\d+)?)\s?%|\b(\d{1,2})\s?(?:percent|per\s?cent)\b", re.I)
_YEAR = re.compile(r"\b(19[5-9]\d|20[0-4]\d|2050)\b")
_NEG = re.compile(r"\b(no|not|never|without|lacks|declined|denied|false|incorrect|inaccurate|misleading)\b", re.I)
_SUPPORT = re.compile(r"\b(confirms?|supports?|corroborates?|shows|finds|indicates)\b", re.I)
_CHALLENGE = re.compile(r"\b(disputes?|contradicts?|refutes?|debunks?|casts\s+doubt|challenges?)\b", re.I)
_AUTHZ_WORDS = re.compile(r"\b(report|press\s+release|statement|dataset|methodology|audit|budget)\b", re.I)

# Local _norm() and _tokens() removed - now using shared advanced versions from text_utils
# Stop words, apostrophe handling, and possessive removal handled by normalize_text_advanced()
# See intelligence/content/shared/text_utils.py for implementation

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

    # Handle short evidence: create at least one window
    if len(sents) < win:
        # Use all available sentences as one window
        return [sents] if sents else []
    else:
        # Normal sliding window
        out: List[List[str]] = []
        for i in range(len(sents) - win + 1):
            out.append(sents[i:i+win])
        return out

def _frame_based_stance(claim_text: str, evidence_text: str) -> str:
    """
    Determine stance using frame-based reasoning.
    Returns: 'support', 'challenge', 'mixed', or 'unrelated' (if inconclusive)
    """
    # Extract frames
    try:
        claim_frame = extract_frame(claim_text, domain='policy')
        evidence_frame = extract_frame(evidence_text, domain='policy')

        # If frames are incomplete, return 'unrelated' (fall back to keyword method)
        if not claim_frame or not evidence_frame:
            return "unrelated"

        # Compare frames
        frame_result = compare_frames(claim_frame, evidence_frame)

        # Map frame comparison to stance
        if frame_result == 'exact' or frame_result == 'partial':
            return 'support'
        elif frame_result == 'contradiction':
            return 'challenge'
        else:
            return "unrelated"  # Inconclusive, fall back to keywords
    except Exception:
        # If frame extraction fails, fall back to keyword method
        return "unrelated"

def _stance_for_chunk(claim_text: str, txt: str) -> str:
    """
    Determine stance for a window of evidence.
    Uses frame-based detection first, falls back to keywords.
    """
    # Try frame-based detection first (NEW)
    frame_stance = _frame_based_stance(claim_text, txt)
    if frame_stance != "unrelated":
        return frame_stance

    # Fall back to existing keyword-based detection (PRESERVED)
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
    # Use shared tolerance matching
    close = any(
        values_match(t, c, abs_tol=0.5, rel_tol=0.10)
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

def evaluate_full_evidence(claim_text: str, item: Dict[str, Any], claim_classification: dict = None) -> Dict[str, Any]:
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
        stance = _stance_for_chunk(claim, txt)
        neg = bool(_NEG.search(txt))
        ent = _entity_overlap(claim, txt)
        pct_any, pct_close = _percent_hits(claim, txt)
        yh = _year_hit(claim, txt)
        # Condition awareness
        claim_conditions = extract_conditions(claim)
        window_conditions = extract_conditions(txt)
        cond_match = False
        cond_mismatch = False
        if claim_conditions and window_conditions:
            # Check if any conditions match
            for cc in claim_conditions:
                for wc in window_conditions:
                    if conditions_equivalent(cc, wc):
                        cond_match = True
                        break
                if cond_match:
                    break
            # If we have conditions but no match, it's a mismatch
            if not cond_match:
                cond_mismatch = True
        # weighted score for window
        score = 0.0
        score += 2.0 * (1.0 if pct_close else 0.0) + 0.8 * (1.0 if pct_any else 0.0)
        score += 1.2 * (1.0 if yh else 0.0)
        score += 2.0 * min(ent, 1.0)
        score += 3.0 * j  # tri-gram paraphrase
        # Real paraphrase matching (not just n-grams)
        para_score = paraphrase_match_score(claim, txt)
        if para_score > 0.3:  # Threshold for meaningful paraphrase match
            score += 0.6 * para_score  # Add paraphrase signal
        # Apply condition awareness to score
        if cond_match:
            score += 0.4  # Matching conditions boost score
        elif cond_mismatch:
            score -= 0.3  # Mismatched conditions reduce score
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

    # Phase 9.2: Apply temporal/geographic context (ADDED)
    pub_date = extract_publication_date(item.get('content', ''), item.get('url', ''))
    item_scope = extract_geographic_scope(item.get('content', ''))
    claim_scope = extract_geographic_scope(claim_text)

    # Get claim category (default to SIMPLE_FACTUAL if not provided)
    claim_category = 'SIMPLE_FACTUAL'
    if claim_classification:
        claim_category = claim_classification.get('category', 'SIMPLE_FACTUAL')

    # Calculate weights
    temporal_weight = calculate_temporal_weight(pub_date, claim_category)
    geographic_weight = check_geographic_match(claim_scope, item_scope)

    # Apply to credibility (use credibility, not authority_score which doesn't exist on items)
    if 'credibility' in item:
        item['credibility'] = item['credibility'] * temporal_weight * geographic_weight
        item['context_weights'] = {
            'temporal': temporal_weight,
            'geographic': geographic_weight
        }

    return item
