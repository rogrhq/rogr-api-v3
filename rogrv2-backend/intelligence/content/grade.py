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
    grade = round(min(score, 8.0) * (10.0/8.0), 2)

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
    finding = build_finding(claim_text, arm, content_text=content, snippet_text=snippet, precomputed_window=pre, precomputed_sim=pre_sim)
    # annotate the item
    item["grade"] = finding["grade"]
    item["stance"] = finding["stance"]
    item["finding"] = finding
    return item
