from __future__ import annotations
from typing import Dict, List

# Letter → weight (quality proxy)
LETTER_W = {"A": 1.00, "B": 0.85, "C": 0.65, "D": 0.45, "E": 0.25, "F": 0.10}

def _avg_letter(letters: List[str]) -> str:
    if not letters: return "F"
    vals = [LETTER_W.get(x.upper(), 0.10) for x in letters if isinstance(x, str) and x]
    if not vals: return "F"
    m = sum(vals)/len(vals)
    # invert map by nearest
    by_diff = sorted(LETTER_W.items(), key=lambda kv: abs(kv[1]-m))
    return by_diff[0][0]

def map_score_to_label(score: int) -> str:
    """
    IFCN-style readability bands:
      90–100: True
      75–89 : Mostly True
      55–74 : Mixed
      35–54 : Mostly False
      0–34  : False
    """
    s = max(0, min(100, int(score)))
    if s >= 90: return "True"
    if s >= 75: return "Mostly True"
    if s >= 55: return "Mixed"
    if s >= 35: return "Mostly False"
    return "False"

def score_from_evidence(evidence_items: List[Dict]) -> Dict:
    """
    Convert per-evidence stances + quality into a numeric claim score and aggregate evidence grade.
    Evidence item shape (expected minimal fields):
      {
        "stance": "support"|"refute"|"neutral",
        "quality_letter": "A".."F",
        "relevance_score": int (0..100)
      }
    """
    if not evidence_items:
        return {"claim_grade_numeric": 50, "evidence_grade_letter": "F"}

    support = 0.0
    refute = 0.0
    letters: List[str] = []

    for ev in evidence_items:
        stance = (ev.get("stance") or "neutral").lower()
        q = (ev.get("quality_letter") or "F").upper()
        rel = int(ev.get("relevance_score") or 0)
        w = LETTER_W.get(q, 0.10) * (rel/100.0)
        letters.append(q)
        if stance == "support":
            support += w
        elif stance == "refute":
            refute  += w
        # neutral contributes nothing

    # Normalize to 0..100 with a margin for uncertainty:
    # base 50, +/- scaled by net evidence weight (cap at 0.5)
    net = max(-0.5, min(0.5, (support - refute)))
    score = int(round(50 + net * 100))
    return {"claim_grade_numeric": max(0, min(100, score)),
            "evidence_grade_letter": _avg_letter(letters)}