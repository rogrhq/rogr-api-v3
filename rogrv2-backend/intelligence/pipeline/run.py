from __future__ import annotations
from typing import Any, Dict, List

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

    # 4) assemble response (always includes methodology.strategy.plan)
    response = {
        "overall": {"score": 50, "label": "Mixed"},
        "claims": [
            {
                **claim,
                "evidence": {
                    "arm_A": evidence_bundle.get("A", {}).get("candidates", []),
                    "arm_B": evidence_bundle.get("B", {}).get("candidates", []),
                },
            }
        ],
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
            "consensus": evidence_bundle.get("consensus", {"overlap_ratio":0.0,"conflict_score":0.0,"stability":1.0}),
            "ranking": {
                "version": "s2p3-lex+type+rec",
                "explain": "Score = 0.55*lexical + 0.30*type_prior + 0.15*recency (bounded). Type prior uses source *type*, not specific sites.",
            },
            "stance": {
                "version": "s2p5",
                "signals": ["negation/refute cues", "support cues", "adversative tokens", "numeric/trend comparison"],
                "notes": "Heuristic-only, deterministic; no domain hardcoding; IFCN-friendly transparency"
            }
        },
    }
    return response