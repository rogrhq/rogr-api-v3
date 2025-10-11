"""
P19 (LIVE): Non-existence aware counter-frames + coverage for arm_B.

This module monkey-patches intelligence.gather.online.run_plan to:
- Add deterministic counter-frame, anchor-based challenge queries for arm_B.
- Track per-arm coverage: frames_attempted, providers_used, queries_issued, candidates_fetched.
- Preserve original return shape; only adds 'coverage_by_arm' and reorders candidates in-arm by tiny anchor score.
Idempotent: safe to import multiple times.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import re

try:
    from intelligence.gather import online  # existing module we are wrapping
except Exception as e:
    raise RuntimeError(f"P19 wrapper: cannot import intelligence.gather.online: {e}")

if getattr(online, "_ROGR_P19_INSTALLED", False):
    # Already wrapped
    pass
else:
    setattr(online, "_ROGR_P19_INSTALLED", True)

    _WORD = re.compile(r"[A-Za-z0-9%]+")
    _PERCENT_WORDS = {
        "0":"zero","1":"one","2":"two","3":"three","4":"four","5":"five",
        "6":"six","7":"seven","8":"eight","9":"nine","10":"ten"
    }

    def _digits_to_words_percent(s: str) -> List[str]:
        outs: List[str] = []
        m = re.match(r"^(\d+)%$", s)
        if m:
            n = m.group(1)
            w = _PERCENT_WORDS.get(n)
            outs.append(f"{n}%")
            if w:
                outs.append(f"{w} percent")
            return outs
        m = re.match(r"^(\d+)$", s)
        if m:
            n = m.group(1)
            w = _PERCENT_WORDS.get(n)
            outs.append(n)
            if w:
                outs.append(w)
        return outs or [s]

    def _extract_anchors_from_claim(claim: str) -> Dict[str, List[str]]:
        claim = claim or ""
        tokens = _WORD.findall(claim)
        proper = [t for t in tokens if len(t) > 2 and t[0].isupper()]
        aliases: List[str] = []
        for p in proper:
            aliases.append(p)
            aliases.append(f"City of {p}")
            aliases.append(f"{p} City Council")
        nums: List[str] = []
        for t in tokens:
            if t.isdigit() or t.endswith("%"):
                nums.extend(_digits_to_words_percent(t))
        topic = []
        for head in ("budget","spending","appropriation","tax","levy","expenditure"):
            if re.search(rf"\b{head}\b", claim, flags=re.I):
                topic = [head]
                break
        # de-dup but preserve order
        seen = set()
        def dd(xs: List[str]) -> List[str]:
            out=[]
            for x in xs:
                if x and x not in seen:
                    seen.add(x); out.append(x)
            return out
        return {"entities": dd(aliases), "numbers": dd(nums), "topic": dd(topic)}

    _COUNTER_FRAMES: List[Tuple[str,List[str]]] = [
        ("numeric_dispute", ["audit","revised","update","estimate","figure","inflation","adjusted"]),
        ("denominator_shift", ["general fund","all funds","enterprise fund","capital","operating"]),
        ("timing_change", ["rescinded","repealed","rollback","amendment","later","subsequent","FY","fiscal year"]),
        ("authority_conflict", ["minutes","agenda","auditor","comptroller","controller","clerk","hearing"]),
        ("methodology", ["methodology","classification","reclassification","baseline","nominal","real terms"]),
    ]

    def _compose_anchor_clause(anchors: Dict[str,List[str]]) -> str:
        parts: List[str] = []
        for key in ("entities","numbers","topic"):
            vals = anchors.get(key) or []
            if vals:
                group = " OR ".join(f"\"{v}\"" if " " in v else v for v in vals[:3])
                parts.append(f"({group})")
        return " AND ".join(parts) if parts else ""

    def _build_b_queries(claim: str, orig_queries: List[str]) -> List[Tuple[str,str]]:
        anchors = _extract_anchors_from_claim(claim or " ".join(orig_queries))
        anchor_clause = _compose_anchor_clause(anchors)
        qpairs: List[Tuple[str,str]] = []
        if not anchor_clause:
            base = (claim or " ".join(orig_queries)).strip()
            ops = ["fact check","dispute","refute","contradict","correction","revised"]
            for op in ops:
                qpairs.append(("fallback", f"{base} {op}"))
            return qpairs[:3]
        for fname, ops in _COUNTER_FRAMES:
            op_clause = " OR ".join(f"\"{o}\"" if " " in o else o for o in ops[:4])
            q = f"{anchor_clause} AND ({op_clause})"
            qpairs.append((fname, q))
        return qpairs

    def _anchor_score(title: str, snippet: str, claim: str) -> int:
        hay = f"{title} {snippet}".lower()
        anchors = _extract_anchors_from_claim(claim)
        score = 0
        if any(a.lower() in hay for a in anchors.get("entities") or []): score += 1
        if any(a.lower() in hay for a in anchors.get("numbers") or []): score += 1
        if any(a.lower() in hay for a in anchors.get("topic") or []): score += 1
        return score

    def _init_cov() -> Dict[str,Any]:
        return {
            "frames_attempted": 0,
            "providers_used": 0,
            "queries_issued": 0,
            "candidates_fetched": 0,
            "_providers": set(),  # internal; collapsed to count later
        }

    _ORIG_RUN_PLAN = getattr(online, "run_plan", None)

    async def _p19_run_plan(plan: Dict[str,Any], max_per_query: int = 2, *args: Any, **kwargs: Any) -> Dict[str,Any]:  # type: ignore[override]
        """Wrap original run_plan: add arm_B frame queries and per-arm coverage."""
        if _ORIG_RUN_PLAN is None:
            return {"candidates": [], "coverage_by_arm": {}}

        # shallow copy, normalize arms
        plan = dict(plan or {})
        arms = plan.get("arms")
        claim_text = (plan.get("claim") or {}).get("text") if isinstance(plan.get("claim"), dict) else None

        if isinstance(arms, dict):
            arm_defs = list(arms.values())
        else:
            arm_defs = [a for a in (arms or []) if isinstance(a, dict)]

        aug_arms: List[Dict[str,Any]] = []
        coverage_by_arm: Dict[str,Dict[str,Any]] = {}
        for a in arm_defs:
            name = a.get("name") or a.get("arm") or ""
            intent = (a.get("intent") or "").lower()
            queries = list(a.get("queries") or [])
            cov = _init_cov()
            if intent in ("challenge","contradict","refute") or str(name).upper().startswith("B"):
                base_claim = (claim_text or " ".join(queries)) if queries else (claim_text or "")
                bq = _build_b_queries(base_claim, queries)
                cov["frames_attempted"] = len(bq)
                for _, q in bq[:3]:
                    queries.append(q)
            a2 = dict(a); a2["queries"] = queries
            aug_arms.append(a2)
            coverage_by_arm[str(name) or ""] = cov
        plan["arms"] = aug_arms

        res = await _ORIG_RUN_PLAN(plan, max_per_query=max_per_query, *args, **kwargs)
        cands: List[Dict[str,Any]] = list((res or {}).get("candidates") or [])

        # provider usage & candidate counts
        for c in cands:
            arm = str(c.get("arm") or "")
            prov = (c.get("provider") or "").lower()
            if arm in coverage_by_arm:
                coverage_by_arm[arm]["candidates_fetched"] += 1
                if prov:
                    coverage_by_arm[arm]["_providers"].add(prov)

        # queries_issued: prefer res.queries_by_arm if present; else approximate from aug_arms
        try:
            q_by_arm = (res or {}).get("queries_by_arm") or {}
            for arm, qs in q_by_arm.items():
                if arm in coverage_by_arm:
                    coverage_by_arm[arm]["queries_issued"] = len(qs or [])
        except Exception:
            pass
        for a in aug_arms:
            name = str(a.get("name") or a.get("arm") or "")
            if name in coverage_by_arm and coverage_by_arm[name]["queries_issued"] == 0:
                coverage_by_arm[name]["queries_issued"] = len(a.get("queries") or 0)

        # collapse provider sets to counts
        for arm, cov in coverage_by_arm.items():
            providers = cov.pop("_providers", set())
            cov["providers_used"] = len(providers)

        # attach coverage; preserve all original keys
        out = dict(res or {})
        out["coverage_by_arm"] = coverage_by_arm

        # Stable in-arm ordering by tiny anchor score (non-filtering)
        if claim_text and cands:
            def _score_item(it: Dict[str,Any]) -> int:
                return _anchor_score(it.get("title",""), it.get("snippet",""), claim_text)
            grouped: Dict[str,List[Dict[str,Any]]] = {}
            for it in cands:
                grouped.setdefault(str(it.get("arm") or ""), []).append(it)
            ordered: List[Dict[str,Any]] = []
            for _, lst in grouped.items():
                lst_sorted = sorted(lst, key=_score_item, reverse=True)
                ordered.extend(lst_sorted)
            out["candidates"] = ordered
        return out

    # install wrapper
    setattr(online, "run_plan", _p19_run_plan)
