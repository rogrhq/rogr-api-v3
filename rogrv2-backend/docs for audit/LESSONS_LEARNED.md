# LESSONS_LEARNED

This document captures insights from the recent implementation and stabilization work. It contains observations only—no prescriptions or new code.

---

## 1) Why monkey patches were chosen (what problem they were solving)

- **Rapid instrumentation without refactors:** Monkey patches provided a way to observe, log, or alter behavior at specific choke points (e.g., `run_preview`, `online.run_plan`) without changing many call sites.
- **Unstable or ambiguous contracts:** With multiple modules exchanging `Dict[str, Any]`, wrapping functions allowed us to adapt to shape differences temporarily while discovering the de facto contracts.
- **Import-order accessibility:** Wrappers made it possible to insert diagnostics and enforcement before downstream code executed, especially where explicit dependency wiring didn’t exist yet.
- **Live-path verification:** Patches enabled running the live pipeline end-to-end to collect telemetry when the canonical production path was not yet consistently exercised by tests.
- **Feature gating without routing changes:** Some packets needed to add logic across modules (e.g., coverage, semantic aligns) without rearchitecting the API; wrapping let those features be introduced incrementally.

> Cost recognized: the approach obscured execution flow, created dependency on import order, and made behavior harder to reason about—useful for discovery, harmful for long-term clarity.

---

## 2) Critical integration points for Day 1 (minimum viable, live path)

- **Single production entry:** `/analyses/preview` must call `intelligence.pipeline.run.run_preview` directly (no alternate paths).
- **Claim intake contract:** Request body `{"text": <str>, "test_mode": false}` must be honored and validated; empty strings should not silently pass.
- **Planner → Gatherer boundary:** Planner yields `{"arms": {"A": {...}, "B": {...}}}` with query lists; gatherer consumes exactly that dict shape.
- **Provider keys & policy:** Search providers (Google/Brave/Bing) require valid keys and a single query-shaping function applied consistently.
- **Evidence item minimum fields:** Each item should provide `url`, `title`, `snippet`, `provider`, plus ranking and credibility scores (`rank_score`, `credibility_score`).
- **Content ingestion:** Where content is fetched, use `content_chars` and `content_excerpt` fields; clearly mark fetch status.
- **Deterministic semantics present:** Items that have content produce anchored quotes with offsets and stance signals for traceability.
- **Verdict envelope:** Top-level `verdict` includes `label` and `confidence`; no silent failures.
- **Diagnostics isolation:** Logging/diagnostics must never contaminate request/response bodies (stdout vs stderr separation).

---

## 3) Wiring order (practical dependency sequence)

1. **API → Pipeline:** `main.py` router → `run_preview` (single entry point).
2. **Claim extraction/enrichment:** `extract_claims` → enrichment to supply planner-required fields (entities/numbers/cues/scope).
3. **Planning:** `strategy.plan_v2.build_search_plans_v2` → returns `{"arms": {"A": {...}, "B": {...}}}`.
4. **Gathering:** `gather.pipeline.build_evidence_for_claim` → delegates to `gather.online.run_plan` with unified query policy and provider clients.
5. **Normalization & dedupe:** `gather.normalize` produces a stable evidence item shape.
6. **Ranking & credibility:** `rank.select` assigns `rank_score` and `credibility_score` deterministically.
7. **Guardrails:** Balance/consistency/credibility summaries recorded for transparency.
8. **Content fetch (where applicable):** Ingestion fills `content_chars` and `content_excerpt` for items that allow it.
9. **Deterministic semantics:** Aligns content to claim; emits anchored quotes, stance, and item-level semantic scores.
10. **Aggregation & verdict:** Per-arm summaries → dual-lane (if enabled) → consensus → top-level verdict and confidence.
11. **API marshal:** Response shaped with `overall`, `claims[]`, `methodology`, preserving canonical keys.

> Each step depends on the previous step producing the expected contract shape; ambiguity or drift at one boundary propagates downstream.

---

## 4) What works vs what doesn’t (current understanding)

### Works
- **End-to-end live invocation** from `/analyses/preview` reaching the pipeline.
- **Planner structure (v2)** emitting dict-based arms (`A`/`B`) where enabled.
- **Provider access** (when keys present and query policy is consistent) for Brave/Google.
- **Normalization & basic ranking**: Items carry minimal fields post-gather (url/title/snippet/provider).
- **Coverage fields** recorded when content fetch succeeds (`content_chars`, `content_excerpt`).
- **Deterministic semantic alignment** can emit anchored quotes/offsets on content-bearing items.
- **Top-level verdict envelope** with `label` and `confidence` populated.

### Doesn’t (or is inconsistent)
- **Contract uniformity:** Multiple alternate evidence shapes are still handled defensively in places.
- **Elimination of wrappers:** Some behaviors relied on import-time wrapping; explicit composition is not universal yet.
- **Provider query consistency:** Quotation handling and token preservation have been a source of off-topic/empty results when not uniformly applied.
- **Score completeness:** `rank_score`/`credibility_score` sometimes remain `null` when stages aren’t invoked or inputs are missing.
- **Diagnostics isolation:** Prior runs mixed diagnostic stdout into request JSON if environment and tooling weren’t isolated.

---

## 5) Critical dependencies between modules (observed)

- **`run_preview` ↔ claim enrichment:** Planner expects fields (e.g., numbers, cues) that plain extraction doesn’t produce; enrichment must precede planning.
- **`plan_v2` ↔ `gather.online`:** Strict expectation of `{"arms": {"A": {...}, "B": {...}}}` with query lists per arm.
- **`gather.online` ↔ provider clients:** Requires valid keys and a centralized query policy (quote/percent normalization) to avoid provider rejections and off-topic results.
- **`gather.normalize` ↔ `rank.select`:** Ranking assumes certain fields exist on items post-normalization.
- **`content ingestion` ↔ `semantic alignment`:** Alignment requires text presence (`content_excerpt`/full text); without it, only snippet-level signals exist.
- **`dual-lane orchestration` ↔ `consensus`:** Lane metadata must persist across gather and reduction or consensus loses needed context.
- **`diagnostics` ↔ API I/O:** Logging must be isolated from request/response streams to prevent JSON contamination.

---

*Prepared for internal knowledge transfer; describes current understanding of the implemented system without prescribing changes.*
