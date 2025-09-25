from typing import Dict, Tuple
from infrastructure.heuristics.text import keyword_overlap, has_negation

def stance_for(claim_text: str, source: Dict) -> Tuple[str, float]:
    """
    Returns (stance_label, confidence 0..1)
    Labels: 'support' | 'refute' | 'neutral'
    """
    title = source.get("title","")
    snippet = source.get("snippet","")
    text = f"{title}. {snippet}".strip()
    kw_sim = keyword_overlap(claim_text, text)  # 0..1
    neg = has_negation(text)
    # Simple deterministic rules
    if kw_sim >= 0.35 and not neg:
        return "support", min(1.0, 0.50 + kw_sim/2)
    if kw_sim >= 0.25 and neg:
        return "refute", min(1.0, 0.50 + kw_sim/2)
    if neg and kw_sim >= 0.15:
        return "refute", 0.55
    if kw_sim >= 0.15:
        return "support", 0.50
    return "neutral", 0.30