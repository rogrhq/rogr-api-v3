from typing import Dict, List, Tuple, Optional
from intelligence.claims.extract import extract_claims
from intelligence.strategy.plan import build_search_plans
from intelligence.gather.pipeline import build_evidence_for_claim
from intelligence.consensus.aggregate import consensus_metrics
from intelligence.score.scoring import claim_score, overall_score

def _synth_candidates(claim_text: str, arm: str) -> List[Dict]:
    base_kw = " ".join(claim_text.split()[:6])
    if arm == "A":
        return [
            {"url":"https://city.gov/reports/bridge-2027-plan","title":"City issues 2027 bridge plan","snippet":f"{base_kw} official report outlines costs and timeline 2027 with financial details."},
            {"url":"https://localnews.example/bridge-costs","title":"Bridge costs rise due to steel","snippet":"Steel prices increased; estimates adjusted; timeline remains on track for 2027 according to officials."},
            {"url":"https://opinion.example/blog-bridge","title":"Opinion: concerns remain","snippet":"Some residents are worried; details unclear; no figures given."},
        ]
    else:
        return [
            {"url":"https://watchgroup.example/bridge-oversight","title":"Watch group flags issues","snippet":"Report suggests the 2027 claim may be optimistic; not confirmed by independent audit."},
            {"url":"https://transport.db/stats","title":"Traffic statistics 2020-2024","snippet":f"Data shows traffic doubled since 2020 in corridor; numbers compiled annually 2021 2022 2023."},
            {"url":"https://forum.example/thread","title":"Community thread","snippet":"People discuss the bridge; mixed views; uncertain details."},
        ]

def run_preview(text: str, *, test_mode: bool = True) -> Dict:
    """
    Returns dict:
    {
      'claims': [
        {
          'text','tier','priority',
          'strategies': {'A': [...], 'B': [...]},
          'evidence': {'A': [...], 'B': [...]},     # each evidence has quality_letter (A..F), stance, etc.
          'consensus': {...},
          'score_numeric': int,                     # 0..100
          'label': 'True|Mostly True|Mixed|Mostly False|False',
          'explanation': str
        }, ...
      ],
      'overall': {'score': int, 'label': str}
    }
    """
    claims = extract_claims(text or "")
    plans = build_search_plans(claims)

    # group plans by claim text + arm
    by_claim: Dict[str, Dict[str, List[str]]] = {}
    for p in plans:
        ctext = p["claim_text"]
        by_claim.setdefault(ctext, {})[p["arm"]] = p["queries"]

    results: List[Dict] = []
    for c in claims:
        strategies = by_claim.get(c.text, {})
        # Build evidence for both arms.
        if test_mode:
            candA = _synth_candidates(c.text, "A")
            candB = _synth_candidates(c.text, "B")
        else:
            # In v1 we stay offline/deterministic by default; network providers will be wired later.
            candA = _synth_candidates(c.text, "A")
            candB = _synth_candidates(c.text, "B")

        armA = build_evidence_for_claim(c.text, candA)
        armB = build_evidence_for_claim(c.text, candB)
        cons = consensus_metrics(armA, armB)

        # Score using all evidence (A+B)
        score, label, expl = claim_score(armA + armB)

        results.append({
            "text": c.text,
            "tier": c.tier.value,
            "priority": c.priority,
            "strategies": strategies,
            "evidence": {"A": armA, "B": armB},
            "consensus": cons,
            "score_numeric": score,
            "label": label,
            "explanation": expl
        })

    # overall (tier-weighted)
    overall_num, overall_lbl = overall_score([{"tier": r["tier"], "score": r["score_numeric"]} for r in results])
    return {"claims": results, "overall": {"score": overall_num, "label": overall_lbl}}