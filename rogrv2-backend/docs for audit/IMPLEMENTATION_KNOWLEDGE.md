# IMPLEMENTATION_KNOWLEDGE.md
_Last updated: 2025-10-07T21:28:12Z_

> Scope: This document summarizes **what exists today** in the restored **P29 state** of the backend, how it integrates, challenges encountered, what works vs. what does not, and critical module dependencies. It does **not** propose fixes or new code.

---

## 1) Module Catalog — One‑Sentence Purpose Each

### Pipeline & Orchestration
- **`intelligence/pipeline/run.py`** — Top‑level preview orchestrator that drives claim extraction, planning, gather, ranking, content read, semantic analysis, aggregation, and verdict assembly.
- **`intelligence/gather/pipeline.py`** — Coordinates provider calls for each arm of the search plan and returns raw candidate items per arm.
- **`intelligence/strategy/plan_v2.py`** — Builds a two‑arm search plan (support/challenge) with intent and query lists from an enriched claim.
- **`intelligence/rank/select.py`** — Scores and orders gathered candidates based on lexical relevance, type priors, and rough recency signals.
- **`intelligence/stance/verdict.py`** — Aggregates per‑item signals into per‑arm strengths and an overall label+confidence verdict.

### Gathering & Query Policy
- **`intelligence/gather/online.py`** — Provider adapter that executes provider queries (Google/Brave/Bing as configured) and normalizes result fields.
- **`intelligence/gather/normalize.py`** — De‑duplicates, normalizes shapes/fields of raw provider results, and assigns per‑arm ranks.
- **`intelligence/gather/query_compactor.py`** — Shapes outgoing queries to preserve core tokens while avoiding API‑blocking syntax (e.g., brittle quoting).

### Content & Semantics
- **`intelligence/content/align.py`** — Deterministic semantic reader that scans text in sliding windows to emit anchored quotes, offsets, stance, and a content score for each item.
- **`intelligence/content/p22_ingest.py`** — Adds full‑text ingestion into the live flow and annotates items with coverage fields (`content_chars`, `content_excerpt`, `content_status`).
- **`intelligence/content/p23_semantic.py`** — Applies alignment over available text to produce per‑item findings (`matches`) and an `item_grade`/label.
- **`intelligence/content/p24_semantic_frames.py`** — Extracts simple frames (entity/action/quantity/year/scope) and computes entail/contradict matches against the claim frame.
- **`intelligence/content/p25_aggregate.py`** — Aggregates item‑level semantic signals into arm strengths used by the verdict stage.

### Multi‑Lane & Consensus
- **`intelligence/content/p26_dual_orchestrator.py`** — Runs two independent researchers (lanes) end‑to‑end and returns lane‑scoped outputs alongside a top‑level preview result.
- **`intelligence/content/p27_consensus_reducer.py`** — Produces a consensus label+confidence by combining the two lanes’ verdicts and agreement heuristics.
- **`intelligence/content/p28_diversify.py`** — Diversifies provider order and other small knobs per lane to encourage evidence variety without changing core logic.
- **`intelligence/content/p29_diversify_controls.py`** — Exposes/records diversification settings and telemetry for lane runs (provider order, timeouts, seeds).

### Diagnostics & Scripts
- **`sitecustomize.py`** — Historically loaded some packet wrappers/diagnostics at interpreter start (in P29 state, present but usage should be minimal for live path).
- **`scripts/run_full_pipeline_diagnostic.sh`** — One‑command script that starts the API if needed, registers, runs `/analyses/preview` live, and writes a human‑readable run summary.
- **`scripts/packet_test_*.sh` / `scripts/packet_test_p2x*.sh`** — Packet‑scoped smoke tests that exercise specific stages and emit structured diagnostics.

> Note: Some additional helper modules and tests exist; the list above focuses on the modules involved in the live P29 pipeline.

---

## 2) Integration Approach Attempted — What & Why

- **Single HTTP entrypoint:** `/analyses/preview` calls `intelligence.pipeline.run.run_preview()` as the primary orchestrator to keep the production path centralized.
- **Two‑arm planning:** A support arm (“A”) and a challenge arm (“B”) are generated from the same claim to surface corroborating and challenging evidence in parallel.
- **Provider abstraction:** `online.py` encapsulates provider specifics (query execution, field normalization) so upstream logic remains provider‑agnostic.
- **Deterministic semantics first:** `align.py` performs non‑AI, reproducible semantic matching (quotes+offsets, stance) before any AI assistance to ensure transparency.
- **Progressive enrichment:** After ranking, items are enriched with text coverage (P22), then read semantically (P23/P24), then aggregated (P25) into arm strengths and final verdict.
- **Dual lanes + consensus:** P26–P27 run the full pipeline twice with small diversification controls (P28/P29) to reduce single‑path bias and enable consensus reasoning.
- **Diagnostics on demand:** Scripts produce a file‑based run manifest and summaries (counts, top items, label/confidence) for auditability.

---

## 3) Challenges Encountered (observed; descriptive only)

- **Contract drift:** Modules exchange untyped dicts, so key presence/shape varies by caller, requiring many defensive `.get()` calls and ad‑hoc shape checks.
- **Wrapper side‑effects (historical):** Packet wrappers (P20–P29) modified behavior via import‑time monkey‑patching; diagnosing order‑dependent effects was difficult.
- **Query brittleness:** Exact‑phrase quoting could zero out provider results; shaping needed to avoid lossy changes while still restoring retrieval.
- **Live vs test divergence:** Some tests executed wrapper paths that the live HTTP route did not, creating gaps between passing tests and live behavior.
- **Content access variability:** PDFs/blocked sites occasionally returned 403 or partial text; downstream semantics depended on coverage being present.
- **Scoring nulls:** In some runs, `rank_score` / `credibility_score` remained unset on items if the ranking pass or shape normalization was bypassed upstream.
- **Lane attribution:** Persisting per‑lane (R1/R2) configs to the final merged payload required explicit propagation; context‑based approaches were easy to lose at merge time.

---

## 4) What Works vs. What Doesn’t (current P29 state)

**Works (observed):**
- Live end‑to‑end preview path returns a trust capsule with `overall` and a single claim payload.
- Two search arms are planned and invoked; provider calls occur when keys are configured.
- Evidence items populate for many claims; content ingestion (P22) adds coverage where accessible.
- Deterministic semantic reader (P23/P24) emits anchored quotes and per‑item stances when text is available.
- Aggregation (P25) yields an overall label+confidence; dual lanes (P26) and consensus reducer (P27) operate and report lane verdicts.

**Intermittent / Not reliable in all runs:**
- `rank_score` / `credibility_score` may be `null` when normalization/ranking is skipped by shape divergence.
- Support arm (A) can be empty for some claims even when the challenge arm has items.
- Off‑topic challenge results can occur when shaping preserves too few claim anchors.
- Full‑text coverage may be missing due to remote blocking (403) or non‑fetchable formats, limiting semantic matches.

**Doesn’t (consistently) work:**
- A single, uniform evidence shape throughout the pipeline (multiple shapes are still tolerated by consumers).
- Guaranteed at least one content‑bearing item per arm for all claims (depends on source accessibility and fetch outcomes).
- Strictly wrapper‑free live execution (historical wrappers exist in the tree, though the intent is a direct `run_preview` path).

---

## 5) Critical Dependencies Between Modules (today)

1. **`run.py` → `extract_claims` (+ enrichment)**  
   The planner expects enriched fields (`numbers`, `cues`, `kind_hint`); without enrichment, planning weakens.

2. **`run.py` → `plan_v2.py` → `gather/pipeline.py` → `gather/online.py`**  
   Plans must be dict‑arms (`{"A":…, "B":…}`) with concrete query lists; `online.py` relies on query shaping to avoid provider zero‑hits.

3. **`gather/online.py` → `gather/normalize.py` → `rank/select.py`**  
   Normalization must assign minimal fields (`title`, `snippet`, `provider`) so ranking can compute `rank_score` and not return `None`.

4. **`rank/select.py` → `content/p22_ingest.py` → `content/p23_semantic.py` / `p24_semantic_frames.py`**  
   Content coverage from P22 is prerequisite for anchored quotes and frame matches in P23/P24; missing coverage reduces semantic output.

5. **`p23_semantic.py` / `p24_semantic_frames.py` → `p25_aggregate.py` → `stance/verdict.py`**  
   Item‑level findings and stances feed per‑arm strengths which drive label/confidence in the final verdict.

6. **`p26_dual_orchestrator.py` → `p27_consensus_reducer.py` → `run.py`**  
   Lane outputs must preserve lane metadata and compatible evidence shapes for consensus and for the final preview payload.

7. **Diagnostics scripts → live API path (`/analyses/preview`)**  
   Scripts assume the API calls `run_preview` directly and that diagnostics never pollute JSON payloads (stdout vs. stderr separation matters).

---

### Appendix — Terminology Snapshot
- **Arm A / Arm B:** Parallel search lanes by stance intent (support/challenge) within each researcher lane.
- **Lane R1 / R2:** Two independent full‑pipeline runs to encourage diversity and enable consensus.
- **Content‑bearing item:** Evidence item with successful fetch (`content_chars > 0`) and excerpt available.
- **Anchored finding:** Quote + byte offsets + local stance signal captured from the item’s text window.