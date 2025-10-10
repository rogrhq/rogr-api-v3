# CLEAN_WIRING_SPEC.md
**Purpose:** Document the proper, *no-monkey-patch* integration wiring for the ROGR backend so the production path is explicit, contracts are consistent, and every module is imported and called directly.

> Scope: Wiring map only (no code). This assumes we are at the P29 clean baseline and extracting the *logic* from P20–P29 into explicit call sites (no `sitecustomize`, no runtime `setattr` wrappers).

---

## Global Principles (Production Path Only)
- **Single entry point:** `api/analyses.py` ➜ `intelligence.pipeline.run.run_preview()`.
- **No monkey patches / rebinds / sitecustomize hooks.** Everything imported and called explicitly.
- **Canonical contracts enforced** (examples below).
- **Providers selected centrally** in `intelligence.gather.provider_env.get_enabled_providers()`.
- **Query shaping centralized** in `intelligence.gather.query_compactor.compact_query_preserve_terms()`.
- **Return shapes standardized** (arms as dict; evidence items have required fields).
- **Diagnostics** must not alter behavior. Use structured logs only (no stdout pollution).

### Canonical Contract Shapes (for reference)
- **Claim intake (API body):**
  ```json
  {"text": "<string>", "test_mode": false}
  ```
- **Planner (v2) output:**
  ```json
  {"version":"v2","arms":{"A":{"intent":"support","queries":[...]},
                          "B":{"intent":"challenge","queries":[...]}}}
  ```
- **Evidence item (minimum):**
  ```json
  {
    "url": str, "title": str, "snippet": str, "provider": str,
    "rank_score": float, "credibility_score": float
  }
  ```
- **Content fields (if fetched):**
  ```json
  {"content_chars": int, "content_excerpt": str(max 1200)}
  ```
- **Verdict:**
  ```json
  {"label": str, "confidence": float}
  ```

---

## Wiring Map by Module

### 1) `api/analyses.py`
- **Depends on:** `intelligence.pipeline.run.run_preview`
- **Depended on by:** Public HTTP clients (`/analyses/preview`)
- **Proper integration point:** FastAPI route handler `POST /analyses/preview`
- **Correct import:**
  ```python
  from intelligence.pipeline.run import run_preview
  ```
- **Call:** `await run_preview(text=body.text, test_mode=body.test_mode)`

---

### 2) `intelligence/pipeline/run.py` (Orchestrator)
- **Depends on:**  
  - `intelligence.claims.extract.extract_claims`  
  - `intelligence.claims.enrich.enrich_claim_obj` (or equivalent enrichment to add numbers/cues/kind_hint)  
  - `intelligence.strategy.plan_v2.build_search_plans_v2`  
  - `intelligence.gather.pipeline.build_evidence_for_claim`  
  - `intelligence.content.fetch_sync.fetch_text` (for full-text ingestion in production path)  
  - `intelligence.content.align.align_claim_to_text_windowed` (semantic findings/stance)  
  - `intelligence.rank.select.rank_candidates` (pre/post ranking as needed)  
  - `intelligence.stance.verdict.aggregate_verdict` (final verdict/score)  
  - *(Optional lanes)* `intelligence.consensus.dual.run_two_researchers` and `intelligence.consensus.reducer.reduce_consensus`
- **Depended on by:** `api/analyses.py`
- **Proper integration point:** `async def run_preview(text: str, test_mode: bool=False) -> Dict[str, Any]`
- **Correct imports (examples):**
  ```python
  from intelligence.claims.extract import extract_claims
  from intelligence.claims.enrich import enrich_claim_obj
  # or from intelligence.claims.interpret import parse_claim (if using a two-step enrich)
  from intelligence.strategy.plan_v2 import build_search_plans_v2
  from intelligence.gather.pipeline import build_evidence_for_claim
  from intelligence.content.fetch_sync import fetch_text
  from intelligence.content.align import align_claim_to_text_windowed
  from intelligence.rank.select import rank_candidates
  from intelligence.stance.verdict import aggregate_verdict
  # optional lanes
  # from intelligence.consensus.dual import run_two_researchers
  # from intelligence.consensus.reducer import reduce_consensus
  ```

---

### 3) `intelligence/claims/extract.py`
- **Depends on:** Pydantic (for `ExtractedClaim`)
- **Depended on by:** `intelligence.pipeline.run`
- **Proper integration point:** `def extract_claims(text: str) -> List[ExtractedClaim]`
- **Correct import:**
  ```python
  from intelligence.claims.extract import extract_claims
  ```

---

### 4) `intelligence/claims/interpret.py` & `intelligence/claims/enrich.py`
- **Depends on:** Tokenization/regex utilities
- **Depended on by:** `intelligence.pipeline.run` (to bridge model → planner expectations)
- **Proper integration point:**  
  - `def parse_claim(text: str) -> Dict[str, Any]` (extract numbers, cues, kind_hint)  
  - `def enrich_claim_obj(claim: Dict[str, Any]) -> Dict[str, Any]`
- **Correct imports:**
  ```python
  from intelligence.claims.interpret import parse_claim
  from intelligence.claims.enrich import enrich_claim_obj
  ```

---

### 5) `intelligence/strategy/plan_v2.py`
- **Depends on:** Enriched claim dict (must include `numbers`, `cues`, `kind_hint`, `entities`, `scope`)
- **Depended on by:** `intelligence.pipeline.run`
- **Proper integration point:**  
  `def build_search_plans_v2(claim: Dict[str, Any]) -> Dict[str, Any]  # {"version":"v2","arms":{...}}`
- **Correct import:**
  ```python
  from intelligence.strategy.plan_v2 import build_search_plans_v2
  ```

---

### 6) `intelligence/gather/query_compactor.py`
- **Depends on:** `re`
- **Depended on by:** `intelligence.gather.online`
- **Proper integration point:**  
  `def compact_query_preserve_terms(q: str) -> str` (normalize quotes/percents *without* losing core tokens)
- **Correct import:**
  ```python
  from intelligence.gather.query_compactor import compact_query_preserve_terms
  ```

---

### 7) `intelligence/gather/provider_env.py`
- **Depends on:** `os`
- **Depended on by:** `intelligence.gather.online`
- **Proper integration point:**  
  `def get_enabled_providers() -> List[str]` (e.g., ["google","brave"] based on env keys)
- **Correct import:**
  ```python
  from intelligence.gather.provider_env import get_enabled_providers
  ```

---

### 8) `intelligence/gather/online.py`
- **Depends on:**  
  - `intelligence.gather.query_compactor.compact_query_preserve_terms`  
  - `intelligence.gather.provider_env.get_enabled_providers`  
  - Internal provider clients/helpers (`_google_search`, `_brave_search`, `_bing_search`)
- **Depended on by:** `intelligence.gather.pipeline`
- **Proper integration point:**  
  `async def run_plan(plan: Dict[str, Any], *, max_per_query:int=3, providers:Optional[List[str]]=None) -> Dict[str, Any]  # {"A":[...],"B":[...]}`
- **Correct import:**
  ```python
  from intelligence.gather.online import run_plan
  ```

---

### 9) `intelligence/gather/pipeline.py`
- **Depends on:**  
  - `intelligence.gather.online.run_plan`  
  - `intelligence.gather.normalize.dedupe` / `normalize_candidates`  
  - `intelligence.rank.select.rank_candidates`
- **Depended on by:** `intelligence.pipeline.run`
- **Proper integration point:**  
  `async def build_evidence_for_claim(*, claim_text:str, plan:Dict[str, Any], max_per_arm:int=3) -> Dict[str, Any]`  
  Returns canonical evidence bundle: `{"arm_A":[...], "arm_B":[...], "guardrails":{...}}`
- **Correct import:**
  ```python
  from intelligence.gather.pipeline import build_evidence_for_claim
  ```

---

### 10) `intelligence/gather/normalize.py`
- **Depends on:** `re`, url parsing
- **Depended on by:** `intelligence.gather.pipeline`
- **Proper integration point:**  
  - `def dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]`  
  - `def normalize_candidates(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]`
- **Correct import:**
  ```python
  from intelligence.gather.normalize import dedupe, normalize_candidates
  ```

---

### 11) `intelligence/rank/select.py`
- **Depends on:** math/scoring utilities
- **Depended on by:** `intelligence.gather.pipeline`, optionally `intelligence.pipeline.run`
- **Proper integration point:**  
  `def rank_candidates(items: List[Dict[str, Any]], top_k: Optional[int]=None) -> List[Dict[str, Any]]`  
  (Adds/uses `rank_score` consistently.)
- **Correct import:**
  ```python
  from intelligence.rank.select import rank_candidates
  ```

---

### 12) `intelligence/content/fetch_sync.py`
- **Depends on:** `requests`/`httpx` or similar
- **Depended on by:** `intelligence.pipeline.run` (production path) or `intelligence.gather.pipeline` (if preferred)
- **Proper integration point:**  
  `def fetch_text(url: str, timeout: float=5.0) -> Dict[str, Any]  # {"text": str, "status": int}`  
  Or async variant if standardized.
- **Correct import:**
  ```python
  from intelligence.content.fetch_sync import fetch_text
  ```

---

### 13) `intelligence/content/align.py`
- **Depends on:** `re`, token utilities
- **Depended on by:** `intelligence.pipeline.run`
- **Proper integration point:**  
  `def align_claim_to_text_windowed(claim: str, text: str) -> Dict[str, Any]`  
  (Produces `matches`, `content_score`, `item_stance`, anchored quotes with offsets.)
- **Correct import:**
  ```python
  from intelligence.content.align import align_claim_to_text_windowed
  ```

---

### 14) `intelligence/stance/verdict.py`
- **Depends on:** none (scoring math)
- **Depended on by:** `intelligence.pipeline.run`
- **Proper integration point:**  
  `def aggregate_verdict(evidence: Dict[str, Any]) -> Dict[str, Any]  # {"label": str, "confidence": float}`
- **Correct import:**
  ```python
  from intelligence.stance.verdict import aggregate_verdict
  ```

---

### 15) Optional Lanes & Consensus (post-P26)
#### a) `intelligence/consensus/dual.py`
- **Depends on:** `intelligence.pipeline.run` inner helpers (or parameterized to call gather → grade pipeline twice)
- **Depended on by:** `intelligence.pipeline.run` (only if dual-researcher mode enabled)
- **Proper integration point:**  
  `async def run_two_researchers(text: str, *, test_mode: bool=False) -> Dict[str, Any]  # {"R1": {...}, "R2": {...}}`
- **Correct import:**
  ```python
  from intelligence.consensus.dual import run_two_researchers
  ```

#### b) `intelligence/consensus/reducer.py`
- **Depends on:** output of dual lanes
- **Depended on by:** `intelligence.pipeline.run`
- **Proper integration point:**  
  `def reduce_consensus(r1: Dict[str, Any], r2: Dict[str, Any]) -> Dict[str, Any]  # {"label":..., "confidence":...}`
- **Correct import:**
  ```python
  from intelligence.consensus.reducer import reduce_consensus
  ```

---

### 16) `intelligence/telemetry/audit.py` (Diagnostics Only)
- **Depends on:** none (logging only)
- **Depended on by:** `intelligence.pipeline.run` (optional)
- **Proper integration point:** Call audit helpers at key milestones; **never** alter control flow; **never** write to stdout that contaminates request bodies.
- **Correct import:**
  ```python
  from intelligence.telemetry.audit import emit_event  # example
  ```

---

## Execution Order (High-Level, No Patches)
1. **API** receives body `{"text": ..., "test_mode": false}` ➜ calls `run_preview`.
2. **Extract** claims ➜ **Enrich** each (add numbers/cues/kind_hint).
3. **Plan** with v2 ➜ arms dict with queries for A/B.
4. **Gather** via `online.run_plan` (using **provider_env** and **query_compactor**).
5. **Normalize/Dedupe** and **Rank** items (adds `rank_score`).
6. **Fetch Content** for top N items per arm (fill `content_chars`, `content_excerpt`).
7. **Align/Semantic**: `align_claim_to_text_windowed` ➜ findings, `content_score`, `item_stance`.
8. **Per-Item Grade** (combine `rank_score`, `credibility_score`, `content_score`).
9. **Aggregate Verdict** (label/confidence).
10. *(Optional)* **Dual lanes** ➜ **Reducer** consensus.
11. Return capsule: `{"overall": {...}, "claims":[...], "methodology": {...}}`.

---

## Critical Dependency Notes
- **`enrich_claim_obj` must run before `build_search_plans_v2`** so planner fields exist.
- **`compact_query_preserve_terms` must be the only query shaper** used by `online.run_plan`.
- **`provider_env.get_enabled_providers` must gate which providers are used**; do not inline ENV checks elsewhere.
- **`fetch_text` and `align_claim_to_text_windowed` must be called in the production path** (no wrappers) so grading has real content.
- **Verdict aggregation must receive item-level grades**; otherwise confidence will be low/flat.
- **No alternative shapes:** pipeline must always return `{"arm_A":[...], "arm_B":[...]}` at the bundle level (API can adapt to legacy if absolutely necessary, but internal modules should not).

---

## Minimal Import Matrix (Quick Reference)
- `api/analyses.py` ➜ `from intelligence.pipeline.run import run_preview`
- `pipeline/run.py` ➜
  - `from intelligence.claims.extract import extract_claims`
  - `from intelligence.claims.enrich import enrich_claim_obj`
  - `from intelligence.strategy.plan_v2 import build_search_plans_v2`
  - `from intelligence.gather.pipeline import build_evidence_for_claim`
  - `from intelligence.content.fetch_sync import fetch_text`
  - `from intelligence.content.align import align_claim_to_text_windowed`
  - `from intelligence.rank.select import rank_candidates`
  - `from intelligence.stance.verdict import aggregate_verdict`
  - *(optional lanes)* imports from `intelligence.consensus.*`
- `gather/pipeline.py` ➜
  - `from intelligence.gather.online import run_plan`
  - `from intelligence.gather.normalize import dedupe, normalize_candidates`
  - `from intelligence.rank.select import rank_candidates`
- `gather/online.py` ➜
  - `from intelligence.gather.query_compactor import compact_query_preserve_terms`
  - `from intelligence.gather.provider_env import get_enabled_providers`

---

## Notes
- This wiring map is **implementation-agnostic**: it documents *where* modules should plug in, not *how* they’re implemented.
- The goal is to remove uncertainty: each import and call site is explicit, stable, and visible in code review.