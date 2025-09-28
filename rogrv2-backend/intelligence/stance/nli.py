from __future__ import annotations
import os
from typing import Literal

Stance = Literal["support","refute","neutral"]

# Feature flags (default off for AI calls)
USE_NLI = os.getenv("USE_NLI", "0") in ("1","true","True","yes","YES")

def simple_lexical_nli(premise: str, hypothesis: str) -> Stance:
    """
    Deterministic, cheap fallback:
    - If hypothesis negated and premise unnegated, lean 'refute'
    - If premise contains hypothesis key phrase, lean 'support'
    - Otherwise 'neutral'
    """
    p = (premise or "").lower()
    h = (hypothesis or "").lower()
    # crude negation cues
    neg_tokens = {" not ", " no ", "n't ", " never ", " false ", " hoax "}
    if any(tok in h for tok in neg_tokens) and not any(tok in p for tok in neg_tokens):
        return "refute"
    # overlap cue
    k = " ".join([w for w in h.split() if len(w) > 4])[:60]
    if k and k in p:
        return "support"
    return "neutral"

def infer_stance(premise: str, hypothesis: str) -> Stance:
    """
    Placeholder to toggle AI providers later.
    For now always use deterministic fallback to keep tests hermetic.
    """
    return simple_lexical_nli(premise, hypothesis)