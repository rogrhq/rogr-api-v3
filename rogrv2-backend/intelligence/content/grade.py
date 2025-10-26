# path: intelligence/content/grade.py
"""
Deterministic grading of a single evidence item against a claim.
Produces a Finding Card: grade (0-10), stance, rationale[], matched_spans[].
No filtering; purely annotative.

KNOWN ISSUE (2025-10): Stance detection uses keyword matching designed for
policy/budget claims. Fails for scientific claims with comparative language.

Example failure:
- Claim: "Water boils at 100°C"
- Evidence: "Water boils at lower temperatures at high altitude"
- Current: Detects "lower" → stance="challenge" ❌
- Should be: Contextual support (explains variation) ✓

PLANNED FIX: Replace with frame-based reasoning:
1. Parse evidence windows for phenomenon, numbers, units, conditions
2. Decision tree: phenomenon match → numeric match → directional cues
3. Claim-type aware adapters (scientific vs policy)
4. Return stance + rationale with anchored findings

See docs/P20_REDESIGN_NEEDED.md for full architectural plan.

FOR NOW: Minimal overwrite bug fix (if→elif). Stance may be incorrect for
scientific claims. Continue testing P21-P25 to isolate other bugs before
implementing full redesign.
"""
from __future__ import annotations
from typing import List, Dict, Any, Tuple
import math
import logging

LOG = logging.getLogger(__name__)

from intelligence.content.extract_facts import (
    extract_fact_view, has_any, jaccard_trigrams,
    claim_entities, claim_numbers, claim_years
)

# Shared utilities for frame-based redesign
from intelligence.content.shared.frames import Frame, extract_frame, compare_frames
from intelligence.content.shared.vocabulary import INC_VERBS, DEC_VERBS
from intelligence.content.shared.paraphrases import paraphrase_match_score
from intelligence.content.shared.conditions import extract_conditions, conditions_equivalent
from intelligence.content.shared.units import values_match
from intelligence.content.shared.text_utils import normalize_text

# Tunable weights (safe, conservative)
W_ENTITY = 2.0
W_NUMBER = 2.0
W_YEAR   = 1.0
W_SIM_HI = 2.0
W_SIM_LO = 1.0
W_STANCE = 1.0
P_MODAL  = 1.0  # penalty for hedged/uncertain

def _modality_penalty(text: str) -> float:
    t = (text or "").lower()
    if any(x in t for x in ("may ", "might ", "could ", "reportedly", "allegedly")):
        return P_MODAL
    return 0.0

def _stance_for_window(text: str, arm: str, claim_text: str = None) -> str:
    """
    Frame-based stance detection with condition awareness.

    Replaces keyword matching with:
    1. Frame extraction (entity, action, quantity, conditions)
    2. Paraphrase detection (rose ↔ increased)
    3. Condition awareness (at sea level vs at altitude)
    """
    if not claim_text:
        # Fallback to old keyword approach if no claim provided
        return _stance_keyword_fallback(text, arm)

    # Extract frames from claim and evidence
    claim_frame = extract_frame(claim_text, domain='policy')
    evidence_frame = extract_frame(text, domain='policy')

    # Extract conditions
    claim_conditions = extract_conditions(claim_text)
    evidence_conditions = extract_conditions(text)

    # Check condition compatibility
    condition_match = False
    condition_conflict = False
    if claim_conditions and evidence_conditions:
        if conditions_equivalent(claim_conditions[0], evidence_conditions[0]):
            condition_match = True
        else:
            condition_conflict = True

    # Compare frames
    frame_comparison = compare_frames(claim_frame, evidence_frame)

    # Check for paraphrases in action words
    paraphrase_score = 0.0
    if claim_frame.action and evidence_frame.action:
        # Check if actions are paraphrases (rose ↔ increased)
        claim_action_text = f"{claim_frame.action} {claim_frame.direction or ''}"
        evidence_action_text = f"{evidence_frame.action} {evidence_frame.direction or ''}"
        paraphrase_score = paraphrase_match_score(claim_action_text, evidence_action_text)

    # Decision logic with frame-based reasoning
    if frame_comparison == 'exact' or paraphrase_score > 0.25:
        # Same frame or strong paraphrase

        # CRITICAL: Check if actions have opposite directions (increased vs decreased)
        # High semantic similarity can occur between antonyms (both budget verbs)
        if claim_frame.direction and evidence_frame.direction:
            if (claim_frame.direction == 'up' and evidence_frame.direction == 'down') or \
               (claim_frame.direction == 'down' and evidence_frame.direction == 'up'):
                return "challenge"  # Opposite directions = contradiction

        if condition_conflict:
            return "contextual_support"  # Same phenomenon, different context
        return "support"

    elif frame_comparison == 'partial':
        # Some frame overlap - check what matches
        has_entity_match = claim_frame.entity and evidence_frame.entity and \
                          claim_frame.entity.lower() == evidence_frame.entity.lower()
        has_number_match = claim_frame.number and evidence_frame.number and \
                          values_match(claim_frame.number, evidence_frame.number, abs_tol=0.5, rel_tol=0.10)

        # If entity + number match, it's support (even if actions differ slightly)
        if has_entity_match and has_number_match:
            if condition_conflict:
                return "contextual_support"
            return "support"

        # Otherwise, check conditions
        if condition_match:
            return "support"
        elif condition_conflict:
            return "contextual_support"

        # Weak paraphrase with some overlap
        if paraphrase_score > 0.2:
            return "support"

        return "mixed"

    elif evidence_frame.action and claim_frame.action:
        # Both have actions, check for contradiction
        if (claim_frame.direction == 'up' and evidence_frame.direction == 'down') or \
           (claim_frame.direction == 'down' and evidence_frame.direction == 'up'):
            return "challenge"

    # Fallback: Check for negation + keyword matching
    t = text.lower()
    neg = any(w in t for w in ("not ", "no ", "false", "incorrect", "deny", "dispute", "refute", "contradict", "debunk"))

    if neg:
        # Negation present - likely challenge or mixed
        if paraphrase_score > 0.2:
            return "challenge"
        return "mixed" if arm.upper() == "A" else "challenge"

    return "unrelated"


def _stance_keyword_fallback(text: str, arm: str) -> str:
    """Fallback to old keyword approach when frame extraction unavailable"""
    t = (text or "").lower()
    is_inc = any(w in t for w in ("increase","increased","up","rise","grew","growth","higher"))
    is_dec = any(w in t for w in ("decrease","decreased","down","lower","reduced","reduction"))
    neg = any(w in t for w in ("not ","no ","false","incorrect","deny","dispute","refute","contradict","debunk"))

    stance = "unrelated"
    if is_inc and not neg:
        stance = "support"
    elif (is_dec and not neg) or (neg and is_inc):
        stance = "challenge"
    if is_inc and neg and arm.upper()=="A":
        stance = "mixed"
    return stance

def build_finding(claim_text: str, arm: str, content_text: str, snippet_text: str = "", precomputed_window: str = "", precomputed_sim: float = -1.0) -> Dict[str, Any]:
    """
    Build a finding for one evidence item.
    - Uses precomputed window/similarity if provided; otherwise selects best window.
    """
    # Window selection
    window = precomputed_window or snippet_text or ""
    sim = precomputed_sim
    if not window:
        from intelligence.content.extract_facts import best_window_for_text
        window, sim = best_window_for_text(claim_text, content_text or "", win=4)
        # Fix: If window still empty (short content), use snippet or content directly
        if not window:
            window = snippet_text or content_text or ""
    if sim is None or sim < 0:
        sim = jaccard_trigrams(claim_text, window)

    # Signals
    ents = claim_entities(claim_text)
    nums = claim_numbers(claim_text)
    yrs  = claim_years(claim_text)

    has_ent = has_any(window, ents)
    has_num = has_any(window, nums)
    has_yr  = has_any(window, yrs)

    # Stance & modality
    stance = _stance_for_window(window, arm, claim_text=claim_text)
    penalty = _modality_penalty(window)

    # Score
    score = 0.0
    rationale: List[str] = []
    if has_ent:
        score += W_ENTITY; rationale.append("entity matched")
    if has_num:
        score += W_NUMBER; rationale.append("number matched")
    if has_yr:
        score += W_YEAR; rationale.append("year matched")

    if sim >= 0.35:
        score += W_SIM_HI; rationale.append(f"similarity high ({sim:.2f})")
    elif sim >= 0.25:
        score += W_SIM_LO; rationale.append(f"similarity moderate ({sim:.2f})")

    if arm.upper()=="A" and stance=="support":
        score += W_STANCE; rationale.append("stance supports claim")
    if arm.upper()=="B" and stance=="challenge":
        score += W_STANCE; rationale.append("stance challenges claim")

    if penalty > 0:
        score -= penalty; rationale.append("modality hedged")

    score = max(0.0, score)
    # normalize to 0..10 (max theoretical ~8); scale gently
    grade = round(min(score, 8.0)  / 8.0, 3)

    finding = {
        "grade": grade,
        "stance": stance,
        "matched_spans": [window][:1] if window else [],
        "rationale": rationale,
        "similarity": round(sim, 3),
        "signals": {
            "entity": bool(has_ent),
            "number": bool(has_num),
            "year": bool(has_yr),
        }
    }
    return finding

def attach_finding_to_item(claim_text: str, arm: str, item: Dict[str, Any]) -> Dict[str, Any]:
    content = item.get("content") or item.get("content_excerpt") or ""
    snippet = item.get("snippet") or ""
    # prefer any upstream best-match window if present
    pre = ""
    pre_sim = -1.0
    for m in item.get("matches") or []:
        # take the highest score match if present
        pre = m.get("sentence") or m.get("text") or pre
        try:
            pre_sim = float(m.get("score", -1.0))
        except Exception:
            pass
        break
    finding = build_finding_v2(claim_text, arm, item)
    # annotate the item
    item["item_grade"] = finding["item_grade"]
    item["authority"] = finding.get("features", {}).get("authority", {}).get("score", 0.5)
    item["stance"] = finding.get("features", {}).get("p23", {}).get("stance", "unrelated")
    item["credibility"] = finding.get("features", {}).get("p21", {}).get("credibility", 0.5)
    item["credibility_tier"] = finding.get("features", {}).get("p21", {}).get("credibility_tier", 4)
    item["credibility_category"] = finding.get("features", {}).get("p21", {}).get("credibility_category", "unknown")
    item["finding"] = finding
    return item


# ============================================================================
# PHASE 1.2a: NEW ORCHESTRATOR FUNCTIONS (ADDED)
# ============================================================================



def fuse_module_grades(features: dict, evidence_item: dict) -> float:
    """
    Fuse P21, P23, P24 features into single item_grade (0-1).

    Weighting:
    - 40% semantic similarity (P23)
    - 30% frame matching (P24)
    - 20% credibility (P21)
    - 10% coverage quality
    """

    # Check for failed fetch status - skip scoring
    fetch_status = evidence_item.get('fetch_status')
    if fetch_status == 'failed':
        url = evidence_item.get('url', 'unknown')
        LOG.warning(f"⏭️  Skipping failed fetch item: {url}")
        return 0.0

    # Extract components
    # P23: Semantic similarity
    if features.get('p23_available'):
        semantic_score = features['p23'].get('item_grade', 0.0)
    else:
        semantic_score = 0.0

    # P24: Frame matching
    if features.get('p24_available'):
        frame_score = features['p24'].get('frame_confidence', 0.0)
    else:
        frame_score = 0.0

    # P21: Credibility (for authority calculation)
    if features.get('p21_available'):
        credibility = features['p21'].get('credibility', 0.5)
    else:
        credibility = 0.5

    # PHASE 3.2: Calculate authority from domain + credibility
    url = evidence_item.get('url', '')
    authority = calculate_authority_score(url, credibility)

    # Coverage: full > partial > snippet_only
    coverage = evidence_item.get('coverage', 'snippet_only')
    if coverage == 'full':
        coverage_weight = 1.0
    elif coverage == 'partial':
        coverage_weight = 0.7
    else:  # snippet_only
        coverage_weight = 0.4

    # Fuse with weights (PHASE 3.2: using authority instead of credibility)
    item_grade = (
        0.40 * semantic_score +
        0.30 * frame_score +
        0.20 * authority +       # NEW: Domain-aware authority
        0.10 * coverage_weight
    )

    # Ensure 0-1 range
    item_grade = max(0.0, min(1.0, item_grade))

    # Round to 3 decimals
    item_grade = round(item_grade, 3)

    return item_grade

def build_finding_v2(claim_text: str, arm: str, evidence_item: dict) -> dict:
    """
    NEW orchestrated grading - calls P21, P23, P24 and fuses results.

    This replaces the old build_finding() which did its own analysis.
    Now P20 acts as orchestrator, calling other modules as helpers.

    Args:
        claim_text: The claim being fact-checked
        arm: 'A' (support) or 'B' (challenge)
        evidence_item: Evidence item dict with 'content', 'url', etc.

    Returns:
        Dict with combined features and single item_grade (0-1)
    """
    from intelligence.content.fullread import evaluate_full_evidence
    from intelligence.content.semantic_read import analyze_item
    from intelligence.content.semantic_frames import analyze_frames

    # Initialize feature collectors
    features = {
        'p21_available': False,
        'p23_available': False,
        'p24_available': False,
    }

    # P21: Full-text analysis
    try:
        # P21 modifies item in place, returns updated item
        p21_result = evaluate_full_evidence(claim_text, evidence_item.copy())
        features['p21'] = {
            'grade_full': p21_result.get('grade_full', 0.0),
            'stance_full': p21_result.get('stance_full', 'unrelated'),
            'credibility': p21_result.get('credibility', 0.5),
            'credibility_tier': p21_result.get('credibility_tier', 4),
            'credibility_category': p21_result.get('credibility_category', 'unknown'),
            'signals_full': p21_result.get('signals_full', {}),
        }
        features['p21_available'] = True
    except Exception as e:
        features['p21'] = {'error': str(e)}

    # P23: Semantic analysis
    try:
        # P23 modifies item in place, returns updated item
        p23_result = analyze_item(claim_text, evidence_item.copy(), window=3)
        p23_findings = p23_result.get('findings', [])
        features['p23'] = {
            'item_grade': p23_result.get('item_grade', 0.0),
            'findings': p23_findings,
            'grade_label': p23_result.get('grade_label', 'low'),
            'stance': p23_findings[0].get('stance', 'unrelated') if p23_findings else 'unrelated',
        }
        features['p23_available'] = True
    except Exception as e:
        features['p23'] = {'error': str(e)}

    # P24: Frame analysis
    try:
        content = evidence_item.get('content', evidence_item.get('snippet', ''))
        p24_result = analyze_frames(claim_text, content, window=3, max_windows=500)
        features['p24'] = {
            'frame_matches': p24_result.get('frame_matches', []),
            'frame_confidence': p24_result.get('frame_confidence', 0.0),
            'item_frame': p24_result.get('item_frame', {}),
        }
        features['p24_available'] = True
    except Exception as e:
        features['p24'] = {'error': str(e)}

    # Temporary: Just return features (fusion in step 1.2e)
    # For now, use P23's grade as primary (it's most tested)
    item_grade = fuse_module_grades(features, evidence_item)

    # Store authority score for transparency and downstream use
    credibility = features.get('p21', {}).get('credibility', 0.5) if features.get('p21_available') else 0.5
    url = evidence_item.get('url', '')
    authority = calculate_authority_score(url, credibility)

    features['authority'] = {
        'score': authority,
        'credibility': credibility,
        'domain': url,
    }

    return {
        'item_grade': item_grade,
        'features': features,
        'orchestrated': True,  # Flag that this used new system
    }



# ============================================================================
# PHASE 3.1: AUTHORITY SCORING SYSTEM (ADDED)
# ============================================================================

def calculate_authority_score(url: str, credibility: float = 0.5) -> float:
    """Calculate authority score from domain and credibility."""
    from intelligence.content.fullread import _extract_base_domain

    # Use shared base domain extraction (fixes subdomain bug)
    domain = _extract_base_domain(url)

    # Domain-specific scores (most authoritative first)
    DOMAIN_SCORES = {
        # US Government
        'nih.gov': 1.0,
        'cdc.gov': 1.0,
        'census.gov': 0.98,
        'nasa.gov': 0.98,
        'usgs.gov': 0.97,
        'noaa.gov': 0.97,
        'fda.gov': 0.98,
        'epa.gov': 0.97,

        # International Organizations
        'who.int': 0.95,
        'un.org': 0.92,
        'worldbank.org': 0.90,

        # Peer-reviewed Journals
        'nature.com': 0.95,
        'science.org': 0.95,
        'sciencedirect.com': 0.90,
        'cell.com': 0.93,
        'nejm.org': 0.95,
        'thelancet.com': 0.94,
        'plos.org': 0.85,

        # News - Tier 1 (wire services)
        'apnews.com': 0.85,
        'reuters.com': 0.85,
        'bloomberg.com': 0.82,

        # News - Tier 2 (major newspapers)
        'nytimes.com': 0.75,
        'washingtonpost.com': 0.75,
        'wsj.com': 0.75,
        'bbc.com': 0.82,
        'bbc.co.uk': 0.82,
        'npr.org': 0.80,
        'theguardian.com': 0.72,

        # Encyclopedias
        'britannica.com': 0.80,
        'wikipedia.org': 0.70,  # Lower due to editability

        # Fact-checkers
        'snopes.com': 0.90,
        'factcheck.org': 0.92,
        'politifact.com': 0.88,
    }

    # Check DOMAIN_SCORES
    if domain in DOMAIN_SCORES:
        domain_score = DOMAIN_SCORES[domain]
    elif domain.endswith('.gov'):
        domain_score = 0.95
    elif domain.endswith('.edu'):
        domain_score = 0.85
    elif domain.endswith('.org'):
        domain_score = 0.60
    else:
        domain_score = 0.50

    # Calculate authority
    authority = 0.6 * domain_score + 0.4 * credibility
    return round(authority, 2)

