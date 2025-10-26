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
import sys
from typing import Any, Dict, List, Tuple
import re
import math
from urllib.parse import urlparse
import tldextract
import logging

LOG = logging.getLogger(__name__)

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
# FIX-4: Numeric precision for P21 (ADDED)
from intelligence.content.shared.numeric_precision import extract_and_match_numbers

# Regex patterns for specific matching
_PERCENT = re.compile(r"(?:(\d{1,3})(?:\.\d+)?)\s?%|\b(\d{1,2})\s?(?:percent|per\s?cent)\b", re.I)
_YEAR = re.compile(r"\b(19[5-9]\d|20[0-4]\d|2050)\b")
_NEG = re.compile(r"\b(no|not|never|without|lacks|declined|denied|false|incorrect|inaccurate|misleading)\b", re.I)
_SUPPORT = re.compile(r"\b(confirms?|supports?|corroborates?|shows|finds|indicates)\b", re.I)
_CHALLENGE = re.compile(r"\b(disputes?|contradicts?|refutes?|debunks?|casts\s+doubt|challenges?)\b", re.I)
# ============================================================================
# TIER-BASED CREDIBILITY MODEL (IFCN-COMPLIANT)
# ============================================================================
# Professional fact-checkers use tiered source evaluation.
# This model provides transparent, defensible credibility scoring.
#
# IFCN Compliance:
# - Transparent methodology (documented tiers)
# - Non-partisan selection (based on editorial standards)
# - Small curated whitelist (10 domains, publicly documented)
# - Regular review process
#
# Version: 1.0
# Last updated: 2025-10-21
# ============================================================================

# Established sources whitelist - IFCN compliant
# Selection criteria (ALL must be met):
# 1. Established: 10+ years operation
# 2. Editorial standards: Review/correction process
# 3. Track record: No systematic misinformation
# 4. Recognized expertise: Cited by institutions
# 5. Non-partisan: Not politically affiliated
#
# Format: domain: (tier, score, category)

_ESTABLISHED_REFERENCES = {
    # Science & Academic Publishing (Tier 1)
    'nature.com': (1, 0.85, 'peer-reviewed journal'),
    'science.org': (1, 0.85, 'peer-reviewed journal'),
    'pnas.org': (1, 0.90, 'peer-reviewed journal'),

    # Medical & Health (Tier 1-2)
    'mayoclinic.org': (2, 0.75, 'medical institution'),
    'who.int': (1, 0.90, 'international health org'),

    # Technical & Standards (Tier 2)
    'engineeringtoolbox.com': (2, 0.65, 'technical reference'),
    'iso.org': (2, 0.70, 'standards organization'),

    # Reference & Education (Tier 2-3)
    'britannica.com': (2, 0.70, 'encyclopedia'),
    'khanacademy.org': (2, 0.70, 'educational non-profit'),
    'wikipedia.org': (3, 0.55, 'collaborative reference'),
}

# Expanded authoritative keywords for tier detection
_AUTHZ_WORDS = re.compile(
    r"\b(report|press\s+release|statement|dataset|methodology|audit|budget|"
    r"study|research|analysis|explanation|definition|formula|equation|"
    r"properties|characteristics|data|measurement|findings|results|"
    r"peer[\s-]reviewed|published|journal|abstract)\b",
    re.I
)

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

def _extract_base_domain(url: str) -> str:
    """
    Extract base domain from URL for whitelist matching.

    This function removes subdomains (www., en., m., mobile., etc.) and
    returns only the base domain + TLD, properly handling compound TLDs.

    Examples:
        "https://en.wikipedia.org/..." → "wikipedia.org"
        "https://m.wikipedia.org/..." → "wikipedia.org"
        "https://www.bbc.co.uk/..." → "bbc.co.uk"
        "https://news.bbc.co.uk/..." → "bbc.co.uk"

    Args:
        url: Full URL

    Returns:
        Base domain (e.g., "wikipedia.org")
    """
    try:
        # Use tldextract to handle compound TLDs
        extracted = tldextract.extract(url)

        # Combine domain + suffix (TLD)
        base_domain = f"{extracted.domain}.{extracted.suffix}"

        return base_domain.lower()

    except Exception as e:
        LOG.warning(f"Failed to extract base domain from {url}: {e}")

        # Fallback: simple parsing
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.netloc.lower()

            # Remove port if present
            if ':' in host:
                host = host.split(':')[0]

            # Simple subdomain removal (www. only)
            if host.startswith('www.'):
                host = host[4:]

            return host

        except Exception:
            return ""

def _credibility_from(url: str, text: str) -> Tuple[int, float, str]:
    """Calculate credibility tier and score from URL/content."""

    # Extract base domain for whitelist matching
    base_domain = _extract_base_domain(url)

    if not base_domain:
        LOG.warning(f"Could not extract domain from URL: {url}")
        return (4, 0.30, 'unknown')

    # Check whitelist using BASE DOMAIN
    if base_domain in _ESTABLISHED_REFERENCES:
        tier, score, category = _ESTABLISHED_REFERENCES[base_domain]
        LOG.debug(f"Whitelist match: {url} → {base_domain} → Tier {tier} ({category})")
        return (tier, score, category)

    # .gov domains
    if base_domain.endswith('.gov'):
        return (1, 0.85, 'government')

    # .edu domains
    if base_domain.endswith('.edu'):
        return (2, 0.65, 'education')

    # Peer-reviewed patterns in URL
    if 'journal' in url.lower() or 'peer' in url.lower() or 'doi.org' in base_domain:
        return (1, 0.85, 'peer-reviewed')

    # Default
    return (4, 0.30, 'unknown')


def _credibility_score_only(url: str, text: str) -> float:
    """
    Legacy wrapper that returns only score (for backward compatibility).
    Use _credibility_from() for full tier information.
    """
    _, score, _ = _credibility_from(url, text)
    return score

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
        tier, credibility, category = _credibility_from(item.get("url") or "", "")
        item["credibility"] = credibility
        item["credibility_tier"] = tier
        item["credibility_category"] = category
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
        # FIX-4: Numeric precision check (ADDED)
        num_match = extract_and_match_numbers(claim, txt)
        has_number_match = bool(num_match.get("matches"))
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
        # FIX-4: Boost for precise number match (ADDED)
        if has_number_match:
            score += 0.5
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
    tier, credibility, category = _credibility_from(item.get("url") or "", read)
    item["credibility"] = round(credibility, 3)
    item["credibility_tier"] = tier
    item["credibility_category"] = category

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
