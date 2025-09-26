from typing import Dict, List
from intelligence.gather.normalize import normalize_candidates
from intelligence.analyze.stance import stance_for
from intelligence.analyze.quality import assess_quality

def build_evidence_for_claim(claim_text: str, candidates: List[Dict]) -> List[Dict]:
    """
    Input: claim_text, provider candidates [{url,title,snippet}]
    Output: evidence list [{source:{...}, stance, confidence, quality_letter}]
    """
    sources = normalize_candidates(candidates)
    evidence: List[Dict] = []
    for s in sources:
        stance, conf = stance_for(claim_text, s)
        # attach claim_text so quality can compute overlap features
        ql = assess_quality({"source": s, "claim_text": claim_text})
        evidence.append({
            "source": s,
            "stance": stance,
            "confidence": round(float(conf), 3),
            "quality_letter": ql,
        })
    return evidence