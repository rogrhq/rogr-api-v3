# ARCHITECT ANSWERS - SESSION 3 (Complete)

**Date:** 2025-09-29
**Source:** User provided complete answers to all 43 validation questions
**Context:** These answers were provided before the reframing - they were meant to validate the ADR

---

## PART A: BLOCKING QUESTIONS (B1-B4)

### B1: ASYNC MIGRATION PLAN (6 questions)

**B1-1) Current orchestrator signature (run.py)**

Today (baseline):
```python
def run_preview(text: str, test_mode: bool = True, debug: bool = False) -> Dict[str, Any]
```
- Parameters observed in use: text (str), test_mode (bool), debug (bool).
- It builds a single claim object internally (MVP), executes P1–P13 deterministically, returns the trust capsule payload.

**B1-2) Which functions become async?**

Phase 1 (minimal risk):
- Make ONLY the top-level orchestrator async to be compatible with future async gather, but keep internal P1–P13 calls synchronous.
- Async boundary is at I/O: evidence gathering (future S2P14).

Phase 2 (optional, later):
- If any heavy CPU steps are introduced (e.g., OCR/ASR/HTML parsing), wrap them via run_in_executor rather than converting guardrails to async.

Net: P1–P13 packet functions remain sync. Only orchestrator and live gather are async.

**B1-3) How do P9–P13 calls work with async?**

They remain synchronous, called in strict sequence after evidence selection. No wrapping in async needed; we explicitly await only the live gather step. This preserves deterministic order and removes race conditions.

**B1-4) Before/After code examples**

BEFORE (sync orchestrator):
```python
def run_preview(text: str, test_mode: bool = True, debug: bool = False):
    claim = _build_single_claim(text)                # P1 (MVP)
    plans = build_search_plans(claim)                # strategy
    if test_mode:
        evidence = _fixture_evidence()               # deterministic
    else:
        # (not wired in baseline)
        evidence = {"arm_A": [], "arm_B": []}
    ranked = rank_select(evidence)                   # P3 (may be empty)
    normed  = normalize(ranked)                      # P4
    stance  = compute_stance(normed, claim)          # P5
    cred    = score_credibility(normed)              # P11
    div_ok  = guardrail_diversity(normed)            # P9
    bal_ok  = guardrail_balance(stance)              # P10
    contr   = contradictions(stance)                 # P13
    score   = compute_overall_score(stance, cred, div_ok, bal_ok, contr)  # P6
    label   = map_ifcn_label(score, contr)           # P7 (+Mixed override)
    return assemble_capsule(claim, evidence, score, label, stance, cred, div_ok, bal_ok, contr)
```

AFTER (async boundary for live gather only):
```python
async def run_preview(text: str, test_mode: bool = True, debug: bool = False):
    claim = _build_single_claim(text)                          # P1
    plans = build_search_plans(claim)                          # strategy

    if test_mode:
        evidence = _fixture_evidence()                         # deterministic
    else:
        # Only this step is async (S2P14 to be implemented)
        evidence = await build_evidence_for_claim_async(
            claim_text=claim["text"], plan=plans,
            max_per_arm=3, live=True, ai_assist=False
        )

    ranked  = rank_select(evidence)                            # P3 (sync)
    normed  = normalize(ranked)                                # P4 (sync)
    stance  = compute_stance(normed, claim)                    # P5 (sync)
    cred    = score_credibility(normed)                        # P11 (sync)
    div_ok  = guardrail_diversity(normed)                      # P9 (sync)
    bal_ok  = guardrail_balance(stance)                        # P10 (sync)
    contr   = contradictions(stance)                           # P13 (sync)
    score   = compute_overall_score(stance, cred, div_ok, bal_ok, contr)  # P6
    label   = map_ifcn_label(score, contr)                     # P7
    return assemble_capsule(...)
```

**B1-5) Dependency graph (what runs in parallel vs sequential)**

Parallel: only external I/O in live gather (fan-out to providers). That happens inside build_evidence_for_claim_async using asyncio.gather.

Sequential (deterministic): normalization → ranking → stance → diversity → balance → credibility → contradictions → scoring → labeling.

Determinism is preserved because post-gather steps run in fixed order on fixed inputs.

**B1-6) FastAPI integration / compatibility**

FastAPI endpoints already support async def. We change the handler to await run_preview if run_preview becomes async. API request/response schema stays identical → no client breakage. API versioning not required for this change (no contract changes).

---

### B2: ROLLBACK MECHANISM (4 questions)

**B2-7) Feature flag for async vs sync**

Yes. Add PIPELINE_ASYNC=true|false (default: false).

If false → orchestrator remains sync and (if live requested) raises clear "live gather not available" error.

When true → orchestrator is async and will await live gather.

**B2-8) Phased migration**

Phase 1: Async orchestrator + provider probes; keep test_mode path unchanged.
Tests: all P1–P13 deterministic tests pass; preview endpoint returns unchanged outputs in test_mode.

Phase 2: Implement build_evidence_for_claim_async (S2P14) and wire to orchestrator under PIPELINE_ASYNC=true and test_mode=false (feature-flagged).
Tests: live happy-paths with keys; simulate zero/partial results; ensure guardrail behavior unchanged.

Phase 3: Enable AI-assist (another flag PIPELINE_AI_ASSIST=true) keeping deterministic verification (no fabricated evidence).
Tests: OFF vs ON regression harness (see B4).

**B2-9) Rollback steps**

Code: Toggle PIPELINE_ASYNC=false (instant revert to sync behavior).

Git: Tag each phase (e.g., s2p14_phase1, s2p14_phase2). To rollback, checkout previous tag and deploy.

DB: No schema changes for async itself; no migration rollback needed.

**B2-10) Success criteria per phase**

Phase 1: 100% of existing P1–P13 tests green; latency unchanged in test_mode; API schema unchanged.

Phase 2: ≥80% of typical claims yield ≥1 item/arm with valid keys; no silent fallbacks; clear error messages on provider failures; post-gather metrics match P1–P13 expectations.

Phase 3: OFF vs ON regression harness shows measurable quality lift (e.g., +10–15 points on "explanation completeness" or increased contradiction surfacing) with bounded cost; no unverifiable passages.

---

### B3: S3 NUMERIC/TEMPORAL MODULES (3 questions)

**B3-11) Why out of scope?**

They were deferred only to keep P14 live gather focused. They are NOT low value; they are high-leverage accuracy modules.

**B3-12) Should S3 be added now?**

Yes. Add as S3 (two sub-modules):
- intelligence/analyze/numeric.py: normalize and compare numbers (percentages, absolute counts, ratios), with tolerance windows (e.g., ±3pp for percentages; ±5% for absolutes unless domain-specific rules apply).
- intelligence/analyze/time.py: year/date extraction, stale-data checks, temporal alignment (claim year vs evidence year).

Effort: ~150–220 LOC, ~1 workday including tests.

Impact: boosts stance precision and reduces false support/refute.

**B3-13) Where to integrate?**

After P4 normalize and before P5 stance, as enrichment the stance can consume:
normed → S3 numeric/time enrich → P5: compute stance using enriched signals.

Alternatively label as P14A if you prefer to keep numbering contiguous with live gather, but functionally it sits between P4 and P5.

---

### B4: S6 REGRESSION HARNESS (3 questions)

**B4-14) Why was it out of scope?**

It was omitted earlier due to time pressure; that was a mistake. We need it to quantify changes and justify AI spend.

**B4-15) Should S6 be added before AI integration?**

Yes. Add now. Minimal set:
- scripts/dev_regress.sh — runs a batch of claims with modes OFF (no-AI) vs ON (AI), live gather identical otherwise.
- scripts/report_capsules.py — compares capsules (evidence count, contradiction signals, explanation length/passages present) and outputs a CSV/HTML summary.

**B4-16) If not S6, what else?**

Manual testing is insufficient. If S6 cannot be added, at least add a JSON diff tool and a small curated suite of 30–50 claims. But the harness is strongly recommended.

---

## PART C: IMPORTANT QUESTIONS (I5-I12)

### I5: P12 FUNCTIONALITY MISMATCH (2 questions)

**I5-17) Is ADR's P12 description correct?**

No. Reality: P12 currently computes cross-arm agreement (token overlap, shared domains, exact URL matches) via intelligence/consistency/agreement.py.

**I5-18) Should ADR be updated?**

Yes. Update ADR to reflect P12 = cross-arm agreement.

If a "guardrail consolidation" summary is desired, implement that as a small aggregation step inside run.py (no new packet number) that collects P9/P10/P11/P12 outcomes into methodology.guardrails.

---

### I6: FILE PATH CORRECTIONS (1 question)

**I6-19) Correct paths:**

- Stance heuristics: intelligence/analyze/stance.py (not intelligence/stance/heuristics.py)
- IFCN labels: intelligence/ifcn/labels.py (not scoring/labels.py)
- Guardrails:
  - Domain diversity (P9): intelligence/policy/guardrails.py (function: check_domain_diversity or similar)
  - Stance balance (P10): intelligence/stance/balance.py
- Strategy plan implementation actually used: intelligence/strategy/plan_v2.py (not plan.py)

---

### I7: P9–P13 INTEGRATION IN NEW ASYNC ORCHESTRATOR (3 questions)

**I7-20) Where called?**

Exactly after evidence gathering → normalization → (S3 numeric/time enrichment) → ranking.

Then P5 stance, followed by P9/P10/P11/P12/P13, then P6 score and P7 label.

**I7-21) Signature changes?**

No. Keep P9–P13 sync signatures and current input shapes (lists of evidence items with provider, url, source_type, age_days, etc.).

Only requirement: ensure age_days is filled by gather/normalize for P11 recency bonus.

**I7-22) Parameter preservation?**

Yes. Preserve P9's max_per_domain=1, min_total=2 (configurable via constants/env).

P10 stance balance thresholds: add 0.4-0.6 balance range.

For P11 quality letters, apply thresholds: A≥85, B≥75, C≥65, D≥55, E≥45, F<45.

---

### I8: P13 MODIFICATION SCOPE (2 questions)

**I8-23) Must P13 consume P5 outputs?**

Recommended but not strictly required. Current P13 uses a quick negation proxy; consuming P5's richer stance annotations yields better precision and consistency.

**I8-24) Migration plan & compatibility**

Add an optional parameter to P13 (e.g., use_p5_stance: bool=False). When true, P13 consumes stance fields from P5 on each evidence item. Maintain existing inputs for backward compatibility.

Rationale: Safe, staged adoption.

Action: Update ADR with dual-mode plan and success metrics (e.g., fewer false contradictions on validation set).

---

### I9: PERFORMANCE TARGET AUTHORITY (2 questions)

**I9-25) Which performance targets are authoritative?**

Use the more conservative targets from the Q&A: Test 700 ms (P50) / 1.5 s (P95); Live 3–6 s; Live+AI 6–12 s.

Rationale: Realistic production budgets reduce fire drills and timeouts under load.

**I9-26) Update ADR sections?**

Yes. Rev ADR to reflect conservative budgets; add a table of per-stage SLOs.

---

### I10: MULTI-CLAIM TIMELINE (2 questions)

**I10-27) Effort estimate for multi-claim**

~2–3 days engineering (net): P1 claim extraction adapter, looped orchestration, per-claim parallelization manager, result merging, tests.

Rationale: Requires careful memory and rate-limit handling; more than a trivial loop.

**I10-28) Scope for S2P15?**

Out of scope for S2P15; target a follow-on packet (S2P16).

Rationale: Stabilize evidence and guardrails first.

Action: Document roadmap and preconditions (P14 stable, provider keys validated, regression harness in place).

---

### I11: AI MODEL SELECTION (3 questions)

**I11-29) Which Claude model?**

Default: Claude Sonnet 4.* for balance of cost/quality; allow override to Opus for premium runs; Haiku for low-cost drafts.

Rationale: Sonnet hits the best cost-quality sweet spot for retrieval-augmented reasoning and explanation.

Action: Config keys:
- ANTHROPIC_MODEL_ASSIST=claude-sonnet-4-20250514 (default)
- ANTHROPIC_MODEL_EXPLAIN=claude-sonnet-4-20250514
- Allow CLI/env override.

**I11-30) Token budgets**

Defaults:
- Query refinement: 1.5k in / 300 out
- Passage triage: 2k in / 300 out
- Contradiction surfacing: 2k in / 300 out
- Explanation draft: 4k in / 700 out

Rationale: Keeps costs bounded; fits typical context sizes from top-k results.

Action: Expose budgets in config; log prompt/response tokens for monitoring.

**I11-31) Caching strategy**

Cache prompts and normalized provider results keyed by (claim_hash, provider, query_hash). TTL 24h for search results; 6h for AI prompts.

Rationale: Reduces cost and latency under repeated claims.

Action: Implement simple SQLite/Redis cache layer; include "X-Cache: HIT|MISS" in debug output.

---

### I12: PROVIDER CONFIGURATION (3 questions)

**I12-32) Env var names**

- GOOGLE_CSE_API_KEY, GOOGLE_CSE_ENGINE_ID
- BRAVE_API_KEY
- BING_API_KEY (optional)

Rationale: Matches current usage.

Action: Document in README and .env.sample; add startup validator that lists which providers are active.

**I12-33) Provider priorities**

Priority order: Brave → Google CSE → Bing (optional). Interleave results to improve diversity.

Rationale: Empirically, Brave+Google coverage is strong; mixing avoids single-provider bias.

Action: Configurable priority in config/providers.yaml, with round-robin interleave at selection time.

**I12-34) Fallback/rotation strategy**

Try all active providers in parallel with per-provider budgets; require at least 1 provider to return ≥N items (e.g., N=2). If a provider fails (timeout/429), degrade gracefully; mark provider status in telemetry; optionally retry once with exponential backoff.

Rationale: Improves resiliency; avoids single points of failure.

Action: Implement provider health tracker; expose stats in /health/providers.

---

## PART D: CLARIFICATION QUESTIONS (C13-C17)

### C13: PASSAGE VS SNIPPET TERMINOLOGY (2 questions)

**C13-35) What does "passage" mean?**

In current code, "snippet" is the short provider summary; "passage" refers to a longer extract from fetched HTML (paragraph-level) — not yet implemented broadly.

Rationale: Prevents confusion between search snippets and on-page text.

Action: Update ADR to use:
- snippet: provider short text
- passage: paragraph extracted from page fetch

S2 passage extraction is a future enhancement; out of scope for S2P15 unless explicitly added.

**C13-36) Is passage extraction in scope?**

Not for S2P15 by default; stick to snippets + URLs. If added, estimate ~1–2 days for a basic HTML paragraph extractor with boilerplate stripping and quote-context alignment.

Rationale: Avoid expanding scope while stabilizing live evidence.

Action: Note as S2P17 candidate.

---

### C14: DATABASE MIGRATION PLAN (2 questions)

**C14-37) Current DB state?**

Minimal tables in MVP (users, tokens, maybe analyses). ADR enumerates 13 conceptual tables required for full provenance and audit. Many may not exist yet.

Rationale: Past focus was on pipeline logic, not persistence breadth.

Action: Add Alembic migrations to create missing tables incrementally (claims, evidence_items, guardrail_signals, scores, snapshots, provider_calls, etc.). Provide a migration script and a rollback plan.

**C14-38) Migration scripts?**

Use Alembic; include a baseline migration and subsequent steps per new table. Provide a "seed" script for local dev.

Rationale: Standard practice and safer than ad-hoc SQL.

Action: Add /migrations with versioned scripts; document commands in README.

---

### C15: TEST FIXTURES LOCATION (1 question)

**C15-39) Exact path?**

Use tests/fixtures/ with:
- tests/fixtures/synthetic_evidence.py
- tests/data/ for JSON payloads and HTML snapshots

Rationale: Conventional layout and clear separation.

Action: Move any synthetic evidence seeding out of run.py into tests/fixtures to keep production code clean.

---

### C16: DEPLOYMENT STRATEGY (1 question)

**C16-40) Transition from test to live**

Feature flag via .env (PIPELINE_MODE=off|lite|on) and per-request override for admins. Gradual rollout: 10% → 25% → 50% → 100% users. A/B test optional.

Rationale: Control risk and monitor metrics.

Action: Add middleware that stamps the active mode into responses; add Prometheus counters per mode.

---

### C17: EDGE CASE EXPECTED BEHAVIOR (3 questions)

**C17-41) All providers rate limit (429)**

Return partial results if any; otherwise return 503 "upstream providers unavailable" with request_id. Apply exponential backoff once per provider in-session and fail fast afterward; suggest retry-after in response.

Rationale: Honest error signaling with graceful retry logic.

Action: Implement per-provider retry (1x) and bubble clear error when none succeed.

**C17-42) Contradictions = 100%**

Label "Mixed/Conflicting Evidence." Provide explanation and show distribution chart. Do not force a binary verdict; score reflects disagreement (e.g., 40–60).

Rationale: Transparency over false certainty.

Action: Add explicit label band for "Mixed/Conflicting" and surface top contradictory items in capsule.

**C17-43) All credibility scores = 0**

Label "Unverifiable/Low-Credibility Evidence." Return with guidance to refine claim or sources; do not generate AI hallucinated support.

Rationale: Avoids unsafe conclusions.

Action: Enforce floor behavior in P6 scoring and IFCN labels; add UX copy in result for next steps.

---

## SUMMARY

**Total Questions Answered:** 43
- Blocking (B1-B4): 16 questions
- Important (I5-I12): 18 questions
- Clarification (C13-C17): 9 questions

**Key Decisions:**
1. S3 and S6 are IN SCOPE (not out of scope)
2. Async migration is minimal (only orchestrator, P9-P13 stay sync)
3. Rollback via PIPELINE_ASYNC feature flag (default: false)
4. P12 description in ADR is wrong (should be "cross-arm agreement")
5. File paths all corrected
6. Performance targets: conservative (700ms test, 3-6s live, 6-12s AI)

**NOTE:** These answers were provided to validate the ADR approach. However, Session 3 code inspection revealed the ADR may be solving the wrong problem (proposing to build features that already exist).

---

**END OF ARCHITECT ANSWERS**