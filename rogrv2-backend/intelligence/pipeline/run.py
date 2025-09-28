from typing import Dict, List, Tuple, Optional
import asyncio
from intelligence.claims.extract import extract_claims
from intelligence.strategy.plan import build_search_plans
from intelligence.gather.pipeline import build_evidence_for_claim
from intelligence.consensus.aggregate import consensus_metrics
from typing import Dict, Any, List
from intelligence.score.scoring import claim_score, overall_score
from intelligence.gather.online import run as live_run
from infrastructure.audit.log import start as audit_start, event as audit_event, finalize_capsule, provider_set_from_env
from intelligence.analyze.counterclaim import generate_counterclaims

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

def run_preview(text: str, test_mode: bool = False) -> Dict[str, Any]:
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
    claims: List[Dict[str, Any]] = extract_claims(text or "") or []
    # Guarantee IDs/tier fields even if extractor returns plain text items
    for i, c in enumerate(claims):
        if not isinstance(c, dict):
            claims[i] = {"id": f"c{i+1}", "text": str(c), "tier": "primary"}
        else:
            c.setdefault("id", f"c{i+1}")
            c.setdefault("tier", "primary")

    plans_by_claim: Dict[str, Any] = {}
    try:
        plans_by_claim = build_search_plans(claims, test_mode=test_mode) or {}
    except Exception as e:
        # Don't abort preview; continue with empty plans
        plans_by_claim = {}

    enriched: List[Dict[str, Any]] = []
    for c in claims:
        cid = c.get("id")
        plan = plans_by_claim.get(cid) if isinstance(plans_by_claim, dict) else None
        try:
            ec = build_evidence_for_claim(c, plan, test_mode=test_mode) or {}
        except Exception:
            ec = {"id": cid, "text": c.get("text",""), "tier": c.get("tier","primary"), "evidence": [], "verdict": {"score": 50, "label": "Mixed"}}
        # Minimal shape
        if "verdict" not in ec:
            ec["verdict"] = {"score": 50, "label": "Mixed"}
        if "evidence" not in ec:
            ec["evidence"] = []
        enriched.append(ec)

    try:
        from intelligence.consensus.overall import overall_from_claims
        overall = overall_from_claims(enriched) or {"score": 50, "label": "Mixed"}
    except Exception:
        overall = {"score": 50, "label": "Mixed"}
    return {"overall": overall, "claims": enriched}