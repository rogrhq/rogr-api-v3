from __future__ import annotations
from typing import Dict, Any, Tuple, List
import re

_NEG_WORDS = {"not","no","never","false","untrue","refute","refuted","debunk","debunked","incorrect","wrong"}
_SUPPORT_WORDS = {"confirm","confirmed","supports","supporting","corroborate","corroborated","verify","verified","true","accurate"}
_REFUTE_MARKERS = {"hoax","myth","misleading","contradict","contradicts","contradiction"}
_ADVERSATIVE = {"however","but","although","though","nevertheless","nonetheless","yet","despite"}

_NUM_RE = re.compile(r"([-+]?\d+(?:\.\d+)?)\s*%")
_INC_WORDS = {"increase","increased","rises","rose","up","higher","growth","grew"}
_DEC_WORDS = {"decrease","decreased","drops","dropped","down","lower","decline","declined","cut","reduced"}

def _extract_percents(text: str) -> List[float]:
    return [float(m.group(1)) for m in _NUM_RE.finditer(text or "")]

def _has_any(text: str, vocab: set[str]) -> bool:
    t = (text or "").lower()
    return any(w in t for w in vocab)

def _trend(text: str) -> str | None:
    t = (text or "").lower()
    if any(w in t for w in _INC_WORDS): return "up"
    if any(w in t for w in _DEC_WORDS): return "down"
    return None

def _compare_numbers(claim: str, evidence: str) -> Tuple[bool, bool]:
    """Return (numbers_present, likely_conflict). Conflict if both have % and far apart (>= 3pp) or opposite trend words."""
    cp = _extract_percents(claim)
    ep = _extract_percents(evidence)
    if not cp or not ep:
        # still consider trend words
        ct, et = _trend(claim), _trend(evidence)
        if ct and et and ct != et:
            return False, True
        return False, False
    c, e = cp[0], ep[0]
    # conflict if >= 3 percentage-points apart or opposite trends
    pp_diff = abs(c - e) >= 3.0
    ct, et = _trend(claim), _trend(evidence)
    opp_trend = (ct and et and ct != et)
    return True, bool(pp_diff or opp_trend)

def assess_stance(claim_text: str, item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Heuristic stance assessment.
    Returns fields:
      - stance: 'support'|'refute'|'neutral'
      - stance_score: int (0-100) confidence style scalar
      - contradiction_flags: List[str] (e.g., ['negation','numeric_conflict','adversative'])
      - notes: short machine note for transparency
    """
    title = (item.get("title") or "")
    snippet = (item.get("snippet") or "")
    text = f"{title}. {snippet}".strip()

    flags: List[str] = []
    score = 50  # start neutral

    # Negation/refute cues
    if _has_any(text, _NEG_WORDS | _REFUTE_MARKERS):
        flags.append("negation_or_refute")
        score -= 20

    # Adversative cue (suggests contrast/contradiction context)
    if _has_any(text, _ADVERSATIVE):
        flags.append("adversative")
        score -= 5

    # Support cues
    if _has_any(text, _SUPPORT_WORDS):
        flags.append("support_cue")
        score += 20

    # Numeric/trend comparison
    has_nums, numeric_conflict = _compare_numbers(claim_text, text)
    if has_nums:
        flags.append("numbers_present")
    if numeric_conflict:
        flags.append("numeric_conflict")
        score -= 25
    else:
        # small nudge toward support if numbers present & no conflict
        if has_nums:
            score += 10

    # Clamp
    score = max(0, min(100, score))

    # Stance decision bands
    if score >= 65:
        stance = "support"
    elif score <= 35:
        stance = "refute"
    else:
        stance = "neutral"

    note_bits = []
    if "numeric_conflict" in flags: note_bits.append("percent values or trends disagree")
    if "negation_or_refute" in flags: note_bits.append("negation/refutation cues detected")
    if "support_cue" in flags: note_bits.append("support/verification cues detected")
    if "adversative" in flags: note_bits.append("contrastive language present")

    return {
        "stance": stance,
        "stance_score": score,
        "contradiction_flags": flags,
        "notes": "; ".join(note_bits) or "no strong cues"
    }