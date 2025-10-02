# ARCHITECT ANSWERS - Q1-Q6 (Evidence & Orchestration Clarifications)

**Date:** 2025-09-29
**Context:** These are answers to 6 critical questions identified during Session 3 codebase assessment
**Source:** User provided these answers after Session 3 analysis

---

## Q1: Evidence Gathering Status
**Question:** Is pipeline.py line 33 early-return a bug or intentional test mode?

**Answer:**
The early return is an **intentional test-mode shim** that got left in the default path. It short-circuits the pipeline to return a skeleton result for CI sanity checks.

Because that guard is evaluated before the live path, the later live-gathering block (lines 50–68) is **unreachable** in the current control flow.

**Why:**
During S2 unit work we needed a quick "make the API respond deterministically even if live providers aren't wired" path. The flag check was accidentally made too broad (e.g., `if not FORCE_LIVE` or equivalent), so it triggers even when you expect live mode.

This is the same reason you saw "overall: Mixed, arms: 0/0" even with live flags—execution never reached the real evidence branch.

**Action:**
1. Flip the gate: make the early-return happen **only** when `test_mode is True AND FORCE_LIVE is False`. In all other cases, proceed to live.
2. Move the shim into a small function (e.g., `_return_skeleton_result()`) and call it only from test paths.
3. Add an explicit runtime log line at decision point: `Mode decision: test={test_mode} force_live={FORCE_LIVE} → path={shim|live}`.
4. Add a unit test asserting that `test_mode=False` + valid keys **never** takes the shim path.

---

## Q2: Duplicate Functions in normalize.py
**Question:** Why two normalize_candidates() functions? Bug or intentional?

**Answer:**
It's a **refactor collision**, not intentional. One version implements domain capping + URL fingerprints; the other adds near-duplicate (title-similarity) pruning. They were meant to be **merged** into a single pipeline step.

**Why:**
We developed dedupe in phases: first canonicalization/fingerprints, later title similarity (e.g., normalized Levenshtein/Jaccard). Both landed in the same file without consolidation, and the later import sites inconsistently call one or the other.

**Action:**
1. Merge into one `normalize_candidates()` with this order:
   a) canonicalize URL + hash fingerprint
   b) per-domain cap (e.g., max 2)
   c) title-similarity near-duplicate pruning
   d) attach `provider`, `arm`, `age_days` if available
2. Add a single unit test file `tests/normalize_test.py` covering caps & similarity.
3. Remove the duplicate function; update all imports to the unified entry point.

---

## Q3: Multi-Claim Extraction
**Question:** Is single-claim mode temporary or permanent? Wire up P1 extraction now or defer?

**Answer:**
Single-claim mode is **temporary MVP** to keep S2 stable while we finished guardrails.

We should **defer multi-claim wiring until P14 live path is stable** (providers + ranking + guardrails in place). Then implement multi-claim as S2P16.

**Why:**
Multi-claim introduces concurrency, rate limiting, and merging complexity. Adding it while evidence gather is unstable multiplies failure modes.

The roadmap was: stabilize single-claim end-to-end → then parallelize across multiple claims.

**Action:**
1. Keep single-claim orchestrator in S2P15.
2. Create a ticket for S2P16: loop over P1-extracted claims, per-claim orchestration (bounded concurrency), and capsule merging.

---

## Q4: P1 Number/Cue Detection
**Question:** interpret.py is implemented; why isn't it being called?

**Answer:**
The orchestrator currently **bypasses** P1 interpret for the MVP path and treats the entire input as the single claim text. The interpret step wasn't **wired** into `run_preview()`.

**Why:**
During guardrail buildout we hardwired a single claim object for determinism and postponed the P1 integration to avoid expanding surface area.

That left interpret's useful cues (numbers, entities, dates) unused in query planning and validation.

**Action:**
1. In `run_preview`, call the P1 interpret function early:
   `parsed = p1_interpret(text)` → select the "primary" claim (index 0) for MVP
2. Pass `parsed.cues` into search-plan builder (e.g., entity, numbers, "8%", year "2024").
3. Add a regression test asserting that "8% / 2024" propagate into A/B queries.

---

## Q5: Test Mode Behavior
**Question:** What should test_mode actually do? Default is False but live gathering doesn't work anyway.

**Answer:**

**test_mode=True should:**
- a) disable all network calls,
- b) optionally seed small synthetic evidence fixtures for guardrail tests,
- c) return quickly (<700 ms) with stable, predictable outputs.

**test_mode=False should:**
- a) run live providers when keys are present OR fail clearly with a structured 503 if providers unavailable (no silent shim),
- b) never inject synthetic evidence.

**Why:**
Clear separation avoids "half-live" confusion. A deterministic mode aids CI; a live mode must be all-real or clearly degraded with an error and guidance.

**Action:**
1. Tie early-return shim **only** to `test_mode=True`.
2. When `test_mode=False` and providers are down, return `{error: "providers_unavailable", status:503,…}` rather than a fake success.
3. Add a startup `/health/providers` and a preflight endpoint to show which providers are active.

---

## Q6: Architect's Awareness of online.py
**Question:** Does the architect know online.py exists and is functional? Why does ADR propose "building from scratch"?

**Answer:**
Yes—online.py exists and works for Brave/Google CSE fetch + normalization skeleton. The ADR's "from scratch" language is **misleading**; the intent was "consolidate and harden existing code paths," not literally discard them.

**Why:**
We saw instability from interleaving shims and partial refactors (duplicate normalize, unreachable branches). The ADR aimed to **re-center a clean, async-safe path**, but wording implied replacement instead of consolidation.

**Action:**
1. Update ADR wording: "Consolidate online.py providers and unify normalization; do NOT re-invent them."
2. Keep online.py as the provider layer; call it from orchestrator after fixing the test-mode gate and normalization merge.
3. Add provider telemetry (per-provider success/timeout/429 counts) to guide future tuning.

---

## Closing Notes
The fastest route to "real evidence shows up" is:
- (a) fix the test/live gate in pipeline/run.py,
- (b) merge the duplicate normalization,
- (c) wire P1 interpret cues into plan,
- (d) ensure live mode fails loudly when providers are unusable.

After that, we can safely add async orchestration and multi-claim.

---

**END OF ARCHITECT Q1-Q6 ANSWERS**
