from typing import Dict, List, Tuple

_QW = {"A":3.0,"B":2.5,"C":2.0,"D":1.0,"E":0.5,"F":0.0}

def claim_score(evidence: List[Dict]) -> Tuple[int, str, str]:
    """
    Returns: (numeric_0_100, label, explanation)
      80-100 True
      65-79  Mostly True
      45-64  Mixed
      25-44  Mostly False
       0-24  False
    """
    if not evidence:
        return 50, "Mixed", "No qualifying evidence; defaulting to Mixed."

    support = 0.0
    refute  = 0.0
    used = 0.0
    for e in evidence:
        w = _QW.get(e.get("quality_letter","F"), 0.0) * float(max(0.0, min(1.0, e.get("confidence", 0.0))))
        if e.get("stance") == "support":
            support += w
        elif e.get("stance") == "refute":
            refute += w
        used += w

    raw = 0.0 if used == 0.0 else (support - refute) / max(1e-6, (support + refute))
    score = int(round((raw + 1.0) * 50.0))  # map -1..1 → 0..100

    if score >= 80: label = "True"
    elif score >= 65: label = "Mostly True"
    elif score >= 45: label = "Mixed"
    elif score >= 25: label = "Mostly False"
    else: label = "False"

    expl = f"Support={support:.2f}, Refute={refute:.2f}, Raw={raw:.2f}, Score={score}"
    return score, label, expl

def overall_score(claims: List[Dict]) -> Tuple[int, str]:
    if not claims:
        return 50, "Mixed"
    w_map = {"primary":3, "secondary":2, "tertiary":1}
    total_w = 0
    acc = 0.0
    for c in claims:
        w = w_map.get(c.get("tier","tertiary"),1)
        acc += w * int(c.get("score",50))
        total_w += w
    s = int(round(acc / max(1, total_w)))
    if s >= 80: lbl = "True"
    elif s >= 65: lbl = "Mostly True"
    elif s >= 45: lbl = "Mixed"
    elif s >= 25: lbl = "Mostly False"
    else: lbl = "False"
    return s, lbl