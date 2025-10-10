# CURRENT_REALITY.md

## Packets Implemented (P14–P29)

> **Legend:** Integrated = called directly by production code path; Monkey‑patched = injected at runtime via wrappers/rebinds (e.g., `sitecustomize`), not first‑class wiring.

- **P14 — Gather planning & A/B arm viability checks**
  - Added: diagnostics for provider calls per arm; fixed evidence shape (both `A/B` and `arm_A/arm_B` recognized)
  - Status: **Integrated**

- **P15 — Candidate normalization & ranking prep**
  - Added: normalization of gather results; per‑arm dedupe; rank scaffolding
  - Status: **Integrated**

- **P16 — Verdict envelope fields**
  - Added: `verdict.confidence` in API response
  - Status: **Integrated**

- **P17 — Evidence ranking surface (lightweight)**
  - Added: rank fields carried on items (placeholders populated by later stages)
  - Status: **Integrated**

- **P18 — Content alignment (windowed sampling)**
  - Added: windowed alignment utility and sentence splitting; basic entity/number/year hits
  - Status: **Integrated**

- **P19 — Claim↔content alignment & challenge‑arm tolerance**
  - Added: alignment scoring + relaxed matching; allowance for “no credible counter‑evidence”
  - Status: **Integrated**

- **P20 — Deterministic reading + finding attachment (initial)**
  - Added: pass over content to attach `findings` (quotes+offsets) per item; shallow scoring hooks
  - Status: **Monkey‑patched**

- **P21 — Item grading surface (pre‑semantic)**
  - Added: item‐level grade placeholders to be filled by semantic read
  - Status: **Monkey‑patched**

- **P22 — Full‑text ingestion & coverage fields**
  - Added: fetch full text, set `content_chars`, `content_excerpt`, `coverage`
  - Status: **Monkey‑patched**

- **P23 — Deterministic semantic reading & item grades**
  - Added: anchored quotes (with offsets), stance per finding, `item_grade`/`grade_label`
  - Status: **Monkey‑patched**

- **P24 — Frame extraction & entailment (deterministic)**
  - Added: `item_frame` (entity/action/quantity/year/scope) and frame matches with labels
  - Status: **Monkey‑patched**

- **P25 — Verdict aggregation**
  - Added: per‑claim aggregation → `verdict.label`, `verdict.confidence`, arm strengths
  - Status: **Monkey‑patched**

- **P26 — Dual‑researcher orchestration**
  - Added: R1/R2 lanes (each with A/B arms); top‑level verdict back‑compat fields
  - Status: **Monkey‑patched**

- **P27 — Consensus reducer**
  - Added: combine R1/R2 into consensus verdict; simple agreement rules
  - Status: **Monkey‑patched**

- **P28 — Lane diversification**
  - Added: provider/order diversification per lane; inject `lane_config`
  - Status: **Monkey‑patched**

- **P29 — Telemetry & diagnostics surface**
  - Added: run telemetry and compact audit fields; smoke tests for wiring
  - Status: **Monkey‑patched**


## What Actually Works Now (with repo restored to P29 state)

- **Trust capsule returned?** **Yes** (returns `overall` + `claims[0]` envelope)
- **Live evidence gathering works?** **No** (not reliably on the production path without later hotfixes)
- **AI assist works?** **No** (LLM not integrated; deterministic only)
- **Multi‑claim works?** **No** (single‑claim preview is the exercised path; multi‑claim not reliably wired)


## What’s Still Broken (facts only)

- **Integration issues**
  - Multiple return shapes must be reconciled at runtime (`A/B` vs `arm_A/arm_B` vs nested `candidates`)
  - Planner receives under‑enriched claims (missing `numbers`, `cues`, `kind_hint` unless enriched explicitly)
  - Live path can return empty arms without explicit error propagation
  - Execution flow depends on import order due to wrappers

- **Monkey patches to remove**
  - P20–P29 runtime wrappers (function rebinds via `setattr` and `sitecustomize`)
  - Auto‑loading of packet modules (partial) rather than explicit composition

- **Missing wiring between modules**
  - No single canonical query‑policy function enforced across providers
  - `run_preview` does not mandate enrichment step from extracted claim → enriched claim
  - Evidence ranking (`rank_score`) and credibility (`credibility_score`) not consistently populated
  - Content ingestion not guaranteed on the live path (coverage fields absent when fetch not invoked)


## Percentage Complete

- **Before:** 90% complete (reported)
- **Now:** **58% complete**  
  (Core modules exist and many pass unit/packet tests, but production path relies on monkey‑patches, shapes are inconsistent, and live evidence is not reliably gathered/scored without later hotfixes.)

