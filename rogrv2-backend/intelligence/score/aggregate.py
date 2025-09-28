from __future__ import annotations
from typing import Dict, List
from .labeling import map_score_to_label

def overall_from_claims(claims: List[Dict]) -> Dict:
    """
    Overall = robust mean of per-claim numeric grades (trim 10% each side if many).
    """
    if not claims:
        return {"score": 50, "label": "Mixed"}
    vals = sorted(int(c.get("verdict",{}).get("claim_grade_numeric", 50)) for c in claims)
    n = len(vals)
    if n >= 10:
        k = max(1, n//10)
        vals = vals[k:-k]
    s = int(round(sum(vals)/len(vals)))
    return {"score": s, "label": map_score_to_label(s)}