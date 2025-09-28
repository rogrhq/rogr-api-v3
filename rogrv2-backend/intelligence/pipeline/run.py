from __future__ import annotations
from typing import Any, Dict, List, Union, Tuple
from intelligence.score.aggregate import overall_from_claims
from intelligence.ifcn.labels import label_for_score, scale_spec, explanation_from_counts
from intelligence.policy.checks import check_input

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
    # Policy annotation (non-blocking)
    _policy = check_input(text)

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

    # S2P11: In deterministic test_mode, pipelines may return empty arms.
    # To validate credibility scoring consistently, seed minimal synthetic evidence.
    # These items are clearly marked and only injected when test_mode=True AND arms are empty.
    try:
        if test_mode:
            for c in claims:
                ev = c.get("evidence") or {}
                armA = ev.get("arm_A") or []
                armB = ev.get("arm_B") or []
                if not armA:
                    armA = [{
                        "url": "https://example.gov/budget/austin-2024",
                        "title": "Austin FY2024 budget overview",
                        "snippet": "Official overview of the City of Austin fiscal year 2024 budget and key percentage changes.",
                        "source_type": "government",
                        "age_days": 2,
                        "meta": {"seeded_for_test": True}
                    }]
                if not armB:
                    armB = [{
                        "url": "https://news.example.com/austin/2024-budget",
                        "title": "Report: Austin passes 2024 budget",
                        "snippet": "News coverage discussing the 2024 budget decision, context, and reactions from local stakeholders.",
                        "source_type": "news",
                        "age_days": 120,
                        "meta": {"seeded_for_test": True}
                    }]
                ev["arm_A"] = armA
                ev["arm_B"] = armB
                c["evidence"] = ev
    except Exception:
        # Do not fail preview if seeding encounters an edge case
        pass

    # --- IFCN compliance additions ---
    overall_result = overall_from_claims(claims)
    overall_score = overall_result.get("score", 50)
    overall_label = label_for_score(overall_score)

    # Ensure each claim contains verdict with IFCN label + explanation
    claims_out = []
    for c in claims:
        v = c.get("verdict") or {}
        v_score = int(v.get("score", v.get("claim_grade_numeric", overall_score)))
        v_label = label_for_score(v_score)
        # Build minimal deterministic explanation using stance counts and top-ranked titles
        ev = c.get("evidence") or {}
        # Collect stance counts across arms if present
        support = 0; refute = 0; neutral = 0
        titles_publishers: List[Tuple[str,str]] = []
        for arm_key in ("arm_A","arm_B","arm_brave","arm_bing","arm_google"):
            items = (ev.get(arm_key) or [])
            for it in items:
                stance = (it.get("stance") or "").lower()
                if stance == "support": support += 1
                elif stance == "refute": refute += 1
                else: neutral += 1
                title = (it.get("title") or "")[:120]
                publisher = (it.get("publisher") or "")[:80]
                if title or publisher:
                    titles_publishers.append((title, publisher))
        counts = {"support": support, "refute": refute, "neutral": neutral}
        explanation = explanation_from_counts(c.get("text",""), counts, titles_publishers)
        v["score"] = v_score
        v["label"] = v_label
        v["explanation"] = explanation
        c["verdict"] = v

        # Add stance balance guardrail counts (non-failing; best-effort)
        try:
            from intelligence.stance.balance import summarize_balance
            ev = c.get("evidence", {})
            armA = ev.get("arm_A") or []
            armB = ev.get("arm_B") or []
            balance = summarize_balance(armA, armB)
            # place under evidence.guardrails.balance
            guards = ev.get("guardrails") or {}
            guards["balance"] = balance
            ev["guardrails"] = guards
            c["evidence"] = ev
        except Exception:
            # Do not fail preview if balance computation has issues
            pass

        # Add deterministic credibility scores per evidence item + rollups
        try:
            from intelligence.cred.score import score_item
            ev = c.get("evidence", {})
            armA = ev.get("arm_A") or []
            armB = ev.get("arm_B") or []
            def _score_arm(items):
                total = 0
                out = []
                for it in items:
                    try:
                        sc, det = score_item(it)
                        it2 = dict(it)
                        meta = it2.get("meta") or {}
                        meta["credibility"] = {"score": sc, "details": det}
                        it2["meta"] = meta
                        out.append(it2)
                        total += sc
                    except Exception:
                        out.append(it)
                avg = int(round(total / len(out))) if out else 0
                return out, avg
            armA_scored, avgA = _score_arm(armA)
            armB_scored, avgB = _score_arm(armB)
            ev["arm_A"] = armA_scored
            ev["arm_B"] = armB_scored
            guards = ev.get("guardrails") or {}
            guards["credibility"] = {"avg": {"A": avgA, "B": avgB, "all": int(round((avgA+avgB)/2))}}
            ev["guardrails"] = guards
            c["evidence"] = ev
        except Exception:
            pass

        claims_out.append(c)

    # S2P9 hotfix: if no claims were extracted (edge in some modes), emit a minimal fallback claim
    if not claims_out:
        # Ensure evidence/guardrails objects exist even if empty
        _guardrails = (evidence_bundle or {}).get("guardrails") or {
            "A": {"kept": 0, "dropped": 0, "domains": {}, "types": {}, "parameters": {"max_per_domain": 1, "min_total": 2, "prefer_types": [], "version": "s2p9-1"}},
            "B": {"kept": 0, "dropped": 0, "domains": {}, "types": {}, "parameters": {"max_per_domain": 1, "min_total": 2, "prefer_types": [], "version": "s2p9-1"}},
            "version": "s2p9-1",
        }
        claims_out = [{
            "text": text,
            "tier": "primary",
            "entities": [],
            "numbers": {"percents": []},
            "cues": {"has_comparison": False},
            "scope": {"year": None},
            "kind_hint": None,
            "evidence": {
                "arm_A": [],
                "arm_B": [],
                "guardrails": _guardrails,
            },
            "verdict": {"score": 50, "label": "Mixed"},
        }]

    # Expose a short note that stance balance counts were computed
    methodology_final = {
        "version": "S2P7-1",
        "ifcn": {
            "version": "S2P7-1",
            "label_scale": scale_spec(),
        },
        "notes": "Deterministic pipeline with A/B arms; no domain hardcoding; quality and stance aggregated.",
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
        },
        "policy": _policy
    }

    try:
        guards = any(c.get("evidence", {}).get("guardrails", {}) or {} for c in claims_out)
        if guards:
            methodology_final.setdefault("guardrails", {})
            if any(c.get("evidence", {}).get("guardrails", {}).get("balance") for c in claims_out):
                methodology_final["guardrails"]["balance"] = "per-arm pro/con/neutral counts computed"
            if any(c.get("evidence", {}).get("guardrails", {}).get("credibility") for c in claims_out):
                methodology_final["guardrails"]["credibility"] = "per-item deterministic credibility scored; per-arm and overall averages reported"
    except Exception:
        pass

    response = _to_json_primitive({
        "overall": {"score": overall_score, "label": overall_label},
        "claims": claims_out,
        "methodology": methodology_final,
    })
    return response