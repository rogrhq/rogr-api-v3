from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Tuple

from intelligence.gather import online
from intelligence.gather.normalize import normalize_candidates
from intelligence.rank.select import rank_candidates
from intelligence.analyze.stance import assess_stance
from intelligence.policy.guardrails import apply_guardrails_to_arms
from intelligence.consensus.metrics import compute_overlap_conflict
from intelligence.score.labeling import score_from_evidence, map_score_to_label
from intelligence.util import diag


def _canonical_arm_label(arm_def: Dict[str, Any], idx: int) -> str:
    """
    Map arbitrary arm names/intents to canonical labels 'A' or 'B'.
    Priority:
      1) name startswith 'A' or 'B' (case-insensitive)
      2) intent == 'support' -> 'A'; intent == 'challenge' -> 'B'
      3) index: 0 -> 'A', 1 -> 'B'
    """
    name = str(arm_def.get("name") or "").strip()
    intent = str(arm_def.get("intent") or "").strip().lower()
    if name.upper().startswith("A"):
        return "A"
    if name.upper().startswith("B"):
        return "B"
    if intent in ("support", "agree", "for"):
        return "A"
    if intent in ("challenge", "refute", "against"):
        return "B"
    return "A" if idx == 0 else "B"


async def _exec_plan_for_arm(full_plan: Dict[str, Any], arm_def: Dict[str, Any], arm_label: str, *, max_per_query: int) -> List[Dict[str, Any]]:
    """
    Run the provider plan for a single arm (LIVE), then stamp every candidate with canonical arm label.
    Async-only: awaits online.run_plan; NO asyncio.run / run_until_complete (safe in FastAPI event loop).
    """
    sub_plan: Dict[str, Any] = {**full_plan}
    sub_plan["arms"] = [arm_def]

    res = await online.run_plan(sub_plan, max_per_query=max_per_query)
    raw = (res or {}).get("candidates") or []
    out: List[Dict[str, Any]] = []
    for c in raw:
        if isinstance(c, dict):
            if "arm" not in c or not c.get("arm"):
                c = {**c, "arm": arm_label}
            else:
                # normalize arm value to canonical 'A'/'B' when possible
                v = str(c.get("arm") or "").upper()
                if v.startswith("A"):
                    c = {**c, "arm": "A"}
                elif v.startswith("B"):
                    c = {**c, "arm": "B"}
                else:
                    c = {**c, "arm": arm_label}
            out.append(c)
    return out


def _group_by_arm(cands: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split candidates into lists where c['arm'] == 'A' or 'B'."""
    a: List[Dict[str, Any]] = []
    b: List[Dict[str, Any]] = []
    for c in cands or []:
        arm = str(c.get("arm") or "").upper()
        if arm == "A":
            a.append(c)
        elif arm == "B":
            b.append(c)
    return a, b


def _extract_arm_defs(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Accept both list-form and dict-form arms from v2 planner.
    Returns a list of arm dicts with a populated 'name' field.
    Preferred order: A, B, then remaining keys in insertion order.
    """
    arms = plan.get("arms") or []
    out: List[Dict[str, Any]] = []
    if isinstance(arms, dict):
        ordered: List[str] = []
        for k in ("A", "B", "a", "b"):
            if k in arms:
                ordered.append(k)
        for k in arms.keys():
            if k not in ordered:
                ordered.append(k)
        for k in ordered:
            v = arms.get(k)
            if isinstance(v, dict):
                arm = {**v}
                if not arm.get("name"):
                    arm["name"] = str(k)
                out.append(arm)
    elif isinstance(arms, list):
        out = [a for a in arms if isinstance(a, dict)]
    return out


async def build_evidence_for_claim(*, claim_text: str, plan: Dict[str, Any], max_per_arm: int = 3) -> Dict[str, Any]:
    """
    LIVE evidence pipeline with explicit arm tagging at source (no mocks, no fallbacks).
      1) Execute plan per arm (A, B) and stamp every candidate with canonical arm label.
      2) Normalize & rank within each arm.
      3) Enrich stance metadata.
      4) Apply guardrails (balance/diversity caps, min totals).
      5) Compute cross-arm consensus.
      6) Produce verdict (numeric & label) from evidence.
    """
    # 1) Execute per arm and tag at source
    arm_defs = _extract_arm_defs(plan)
    labeled_cands: List[Dict[str, Any]] = []
    for idx, arm_def in enumerate(arm_defs):
        label = _canonical_arm_label(arm_def, idx)
        labeled_cands.extend(await _exec_plan_for_arm(plan, arm_def, label, max_per_query=2))

    # 2) Group by explicit arm, then normalize & rank
    armA_raw, armB_raw = _group_by_arm(labeled_cands)
    armA_norm = normalize_candidates(armA_raw)
    armB_norm = normalize_candidates(armB_raw)
    if diag.enabled():
        diag.log("gather_counts_pre_rank", armA=len(armA_norm), armB=len(armB_norm))

    ranked_A = rank_candidates(claim_text=claim_text, query=claim_text, candidates=armA_norm, top_k=max_per_arm)
    ranked_B = rank_candidates(claim_text=claim_text, query=claim_text, candidates=armB_norm, top_k=max_per_arm)

    # 3) Stance enrichment
    enr_A = [{**it, **assess_stance(claim_text, it)} for it in ranked_A]
    enr_B = [{**it, **assess_stance(claim_text, it)} for it in ranked_B]

    bundle = {"A": {"intent": "support", "candidates": enr_A}, "B": {"intent": "challenge", "candidates": enr_B}}

    # 4) Guardrails (function may return (bundle, report) or mutate in place)
    gr = apply_guardrails_to_arms(bundle)
    if isinstance(gr, tuple) and len(gr) == 2:
        guarded, report = gr
        guarded["guardrails"] = report
    else:
        guarded = gr
        if "guardrails" not in guarded:
            guarded["guardrails"] = {"status": "applied"}

    # 5) Cross-arm consensus
    a = guarded["A"]["candidates"]
    b = guarded["B"]["candidates"]
    if diag.enabled():
        diag.log("gather_counts_post_guardrails", armA=len(a), armB=len(b))
    guarded["consensus"] = compute_overlap_conflict(a, b)

    # 6) Verdict from evidence
    flat = [*a, *b]
    sv = score_from_evidence(flat)
    score_num = int(sv.get("claim_grade_numeric", 50))
    guarded["verdict"] = {
        "claim_grade_numeric": score_num,
        "label": map_score_to_label(score_num),
        "evidence_grade_letter": sv.get("evidence_grade_letter", "F"),
        "rationale": "Per-arm live gather with explicit arm tags; ranked, guarded, and scored.",
    }
    # Expose Day-1 contract keys expected by API/tests
    guarded["arm_A"] = a
    guarded["arm_B"] = b
    return guarded
