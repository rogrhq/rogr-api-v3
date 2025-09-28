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

    # 3) assemble response (always includes methodology.strategy.plan)
    response = {
        "overall": {"score": 50, "label": "Mixed"},
        "claims": [claim],
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
        },
    }
    return response