from __future__ import annotations
from typing import Any, Dict, List, Union
from intelligence.score.aggregate import overall_from_claims

def _to_json_primitive(x: Any) -> Any:
    """
    Deeply coerce nested structures into JSON-safe primitives.
    - dict -> dict(str -> primitive)
    - list/tuple -> list(primitive)
    - bool/int/float/str/None -> as-is
    Everything else -> str(x)
    """
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            ks = str(k)
            out[ks] = _to_json_primitive(v)
        return out
    if isinstance(x, (list, tuple)):
        return [_to_json_primitive(i) for i in x]
    # fallback
    return str(x)

# NOTE: preview handler calls run_preview() (sync), so keep this non-async
def run_preview(text: str, test_mode: bool = False) -> Dict[str, Any]:
    """
    Build a minimal claim, plan strategy, and return stable JSON with methodology.
    This function MUST NOT raise on planner availability; it must always return a valid shape.
    """
    # 1) make a single claim object (MVP)
    claim: Dict[str, Any] = {
        "id": "c-0",
        "text": (text or "").strip(),
        "tier": "primary",
        "evidence": [],
        "verdict": {"score": 50, "label": "Mixed"},
    }

    # 2) strategy planning (v2 if present; otherwise v1; otherwise empty)
    _planner_v2 = False
    plans: Dict[str, Any] = {"version": "v0", "arms": {
        "A": {"intent": "support", "queries": []},
        "B": {"intent": "challenge", "queries": []},
    }}
    try:
        # Prefer v2 planner if available
        from intelligence.strategy.plan_v2 import build_search_plans_v2  # type: ignore
        plans = build_search_plans_v2(claim) or plans
        _planner_v2 = True
    except Exception:
        # Fallback to v1 if present
        try:
            from intelligence.strategy.plan import build_search_plans  # type: ignore
            plans = build_search_plans(claim) or plans
        except Exception:
            # Keep default `plans`
            pass

    # 3) Optionally gather + rank deterministic evidence (lightweight)
    evidence_bundle = {"A": {"candidates":[]}, "B":{"candidates":[]}}
    try:
        from intelligence.gather.pipeline import build_evidence_for_claim
        evidence_bundle = build_evidence_for_claim(claim_text=claim["text"], plan=plans, max_per_arm=3)
    except Exception:
        evidence_bundle = {"A": {"candidates":[]}, "B":{"candidates":[]}}

    # 4) Attach per-claim evidence + verdict
    claims = []
    claim_ev = evidence_bundle or {}

    # Build evidence; provider may return None or alternate shapes.
    arm_A: List[Any] = []
    arm_B: List[Any] = []
    verdict: Dict[str, Any] = {}

    if isinstance(claim_ev, dict):
        # Preferred shape: {"arm_A": [...], "arm_B": [...], "verdict": {...}}
        if isinstance(claim_ev.get("arm_A"), list):
            arm_A = claim_ev.get("arm_A") or []
        if isinstance(claim_ev.get("arm_B"), list):
            arm_B = claim_ev.get("arm_B") or []
        if isinstance(claim_ev.get("verdict"), dict):
            verdict = claim_ev.get("verdict") or {}

        # Alternate shape: {"A": {"candidates":[...]}, "B": {"candidates":[...]}}
        if not arm_A and isinstance(claim_ev.get("A"), dict):
            arm_A = (claim_ev["A"].get("candidates") or []) if isinstance(claim_ev["A"].get("candidates"), list) else []
        if not arm_B and isinstance(claim_ev.get("B"), dict):
            arm_B = (claim_ev["B"].get("candidates") or []) if isinstance(claim_ev["B"].get("candidates"), list) else []

    # Defaults if still empty
    if not isinstance(verdict, dict) or not verdict:
        verdict = {
            "claim_grade_numeric": 50,
            "label": "Mixed",
            "evidence_grade_letter": "F",
            "rationale": "n/a",
        }

    claims = [
        {
            **claim,
            "evidence": {
                "arm_A": _to_json_primitive(arm_A),
                "arm_B": _to_json_primitive(arm_B),
            },
            "verdict": _to_json_primitive(verdict)
        }
    ]

    response = _to_json_primitive({
        "overall": overall_from_claims(claims),
        "claims": claims,
        "methodology": {
            "version": "mvp-1",
            "strategy": {
                "planner": "v2" if _planner_v2 else "v1",
                "plan": plans,
                "guardrails": {
                    "no_domain_tokens_in_queries": True,
                    "per_domain_diversity_per_rank_bin": True,
                    "provider_interleave": True,
                },
            },
            "consensus": claim_ev.get("consensus", {"overlap_ratio":0.0,"conflict_score":0.0,"stability":1.0}),
            "ranking": {
                "version": "s2p3-lex+type+rec",
                "explain": "Score = 0.55*lexical + 0.30*type_prior + 0.15*recency (bounded). Type prior uses source *type*, not specific sites.",
            },
            "stance": {
                "version": "s2p5",
                "signals": ["negation/refute cues", "support cues", "adversative tokens", "numeric/trend comparison"],
                "notes": "Heuristic-only, deterministic; no domain hardcoding; IFCN-friendly transparency"
            },
            "scoring": {
                "per_claim": "Weighted by stance (support/refute), quality letter (A..F), and relevance.",
                "overall":   "Robust mean of claim grades; mapped to label bands.",
                "bands":     {"True": "90-100","Mostly True":"75-89","Mixed":"55-74","Mostly False":"35-54","False":"0-34"}
            }
        },
    })
    return response