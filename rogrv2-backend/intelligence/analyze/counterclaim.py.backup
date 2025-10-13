from __future__ import annotations
from typing import List, Dict
import re

# very light normalizer
_WS = re.compile(r"\s+")
def _norm(s: str) -> str:
    return _WS.sub(" ", s.strip())

def generate_counterclaims(claim_text: str) -> List[Dict[str, str]]:
    """
    Produce small, deterministic counter-claims that a journalist would probe.
    Rules:
    - invert direction/magnitude if a % or increase/decrease is present
    - request scope/time/place precision
    - propose alternative causal explanation
    """
    t = _norm(claim_text)
    out: List[Dict[str, str]] = []

    # 1) Magnitude inversion (if % present)
    if "%" in t or re.search(r"\b(increase|decrease|rise|fall|drop|up|down)\b", t, re.I):
        out.append({
            "text": f"Reported change is mis-stated; the underlying dataset shows a different magnitude or direction.",
            "rationale": "Invert/verify direction & magnitude; check base period and comp (YoY vs MoM)."
        })

    # 2) Scope/time/place precision
    out.append({
        "text": "Claim over-generalizes; the statement applies to a subset (time window, geography, department) not the whole.",
        "rationale": "Enforce scope precision: who/where/when; look for definitions, exclusions, footnotes."
    })

    # 3) Alternative cause
    out.append({
        "text": "Observed change is confounded by external factors (policy timing, accounting changes, one-off items).",
        "rationale": "Causality caution; correlate with contemporaneous events and reporting lags."
    })

    return out