# CLEAN INTEGRATION PLAN - Wiring Analysis & Execution Strategy

**Date:** 2025-10-09
**Purpose:** Document clean module contracts, wrapper behavior, and direct wiring plan
**Status:** DISCOVERY COMPLETE - Ready for implementation planning

---

## EXECUTIVE SUMMARY

### Key Discovery: Architecture is Already Clean-Ready

**The good news:**
- ✅ All logic exists in standalone clean modules
- ✅ Clean modules have no dependencies on wrappers
- ✅ Clean modules can be imported and called directly
- ✅ Function contracts are straightforward (claim_text + item → enriched item)

**The challenge:**
- ⚠️  Wrappers intercept at different points (pipeline vs run_preview)
- ⚠️  P22 has global state (_FETCH_CACHE) that needs replacement
- ⚠️  Execution order matters (P22 before P20 won't work well)
- ⚠️  Some modules depend on output from previous stages

### Estimated Effort: 3-4 days

**NOT 6-7 days because:**
- Logic already exists in clean modules
- No complex extraction needed
- Just need to wire functions directly
- Main work is P22 cache replacement (1-2 days)

---

## PART 1: CLEAN MODULE CONTRACTS

### 1.1 grade.py (P20 Logic)

**Primary Function:**
```python
def attach_finding_to_item(claim_text: str, arm: str, item: Dict[str, Any]) -> Dict[str, Any]
```

**Contract:**
- **Inputs:**
  - `claim_text`: String - the claim being fact-checked
  - `arm`: String - "A" or "B" (support/challenge)
  - `item`: Dict - evidence item with at minimum: `url`, `snippet`
- **Optional inputs from item:**
  - `content`: Full text (prefers this)
  - `content_excerpt`: Partial text
  - `snippet`: Fallback text
  - `matches`: Pre-computed windows with scores
- **Outputs (mutates item):**
  - `item["grade"]`: float 0-10
  - `item["stance"]`: str ("support", "challenge", "mixed", "unrelated")
  - `item["finding"]`: Dict with:
    - `grade`: float
    - `stance`: str
    - `matched_spans`: List[str]
    - `rationale`: List[str]
    - `similarity`: float
    - `signals`: Dict (entity, number, year matches)

**Dependencies:**
- `intelligence.content.extract_facts` (clean helper module)
- No wrapper dependencies ✅

**Standalone Test:**
```python
from intelligence.content.grade import attach_finding_to_item
item = {"url": "...", "snippet": "Austin budget increased 5%"}
result = attach_finding_to_item("Austin budget increased 5%", "A", item)
# Works independently ✅
```

**Current Wrapper Usage (p20_wrapper.py:50):**
```python
it = attach_finding_to_item(claim_text, arm_key, it)
```

### 1.2 fullread.py (P21 Logic)

**Primary Function:**
```python
def evaluate_full_evidence(claim_text: str, item: Dict[str, Any]) -> Dict[str, Any]
```

**Contract:**
- **Inputs:**
  - `claim_text`: String
  - `item`: Dict with `content`/`content_excerpt`/`snippet`
- **Outputs (mutates item):**
  - `item["grade_full"]`: float 0-10
  - `item["stance_full"]`: str
  - `item["signals_full"]`: Dict (jaccard3, entity_overlap, percent_any, percent_close, year_hit, negation)
  - `item["credibility"]`: float 0-1 (HTTPS, .gov/.edu, authz words)

**Dependencies:**
- No external dependencies beyond stdlib ✅

**Current Wrapper Usage (p21_wrapper.py:82):**
```python
it = evaluate_full_evidence(claim_text, it)
```

### 1.3 semantic_read.py (P23 Logic)

**Primary Function:**
```python
def analyze_item(claim_text: str, item: Dict[str, Any], *, window: int = 3) -> Dict[str, Any]
```

**Contract:**
- **Inputs:**
  - `claim_text`: String
  - `item`: Dict with `content` or `content_excerpt`
  - `window`: int (default 3, sentence window size)
- **Outputs (mutates item):**
  - `item["findings"]`: List[Dict] with:
    - `quote`: str (window text)
    - `offset_start`: int
    - `offset_end`: int
    - `stance`: str
    - `signals`: List[str]
    - `score`: float 0-1
  - `item["item_grade"]`: float 0-1
  - `item["grade_label"]`: str ("high", "medium", "low")

**Dependencies:**
- No external dependencies ✅

**Current Wrapper Usage (p23_semantic.py:42):**
```python
new_items.append(analyze_item(claim_text, it))
```

### 1.4 semantic_frames.py (P24 Logic)

**Primary Function:**
```python
def analyze_frames(claim_text: str, content: str, *, window: int = 3, max_windows: int = 500) -> Dict[str, Any]
```

**Contract:**
- **Inputs:**
  - `claim_text`: String
  - `content`: String (full text to analyze)
  - `window`: int (default 3)
  - `max_windows`: int (default 500)
- **Outputs:**
  - Dict with frame analysis results
  - Returns frame matches, scores, entities, quantities, years

**Dependencies:**
- No external dependencies ✅

**Current Wrapper Usage:**
- Called by p24_semantic_frames.py wrapper
- Extracts frames and attaches to items

### 1.5 p25_aggregate.py (P25 Logic)

**Primary Function:**
```python
def aggregate_verdict(claim_text: str, arm_a_items: List[Dict[str, Any]],
                     arm_b_items: List[Dict[str, Any]], *, delta: float = 0.15) -> Dict[str, Any]
```

**Contract:**
- **Inputs:**
  - `claim_text`: String
  - `arm_a_items`: List of enriched items from arm A
  - `arm_b_items`: List of enriched items from arm B
  - `delta`: float (threshold for label determination)
- **Outputs:**
  - Dict with:
    - `label`: str ("supports", "challenges", "mixed", "insufficient")
    - `confidence`: float 0-1
    - `arm_strength`: Dict {"support": float, "challenge": float, "balance": float}

**Dependencies:**
- Expects items to have: `frame_matches`, `item_grade`, `coverage`
- ⚠️  **Depends on P23+P24 output** (needs `item_grade` and `frame_matches`)

**Current Wrapper Usage (p25_semantic_aggregate.py):**
- Called at claim level after all items processed

---

## PART 2: WRAPPER EXECUTION TRACE

### 2.1 Production Path (sitecustomize.py loads p20 + p22)

**Call chain when `/analyses/preview` is hit:**

```
api/analyses.py:83
  → await run_preview(text, test_mode)
    → (P22 wrapper intercepts if loaded)
      → intelligence/pipeline/run.py:78
        → await build_evidence_for_claim(claim_text, plan, max_per_arm=3)
          → (P20 wrapper intercepts, then P22 intercepts again)
            → intelligence/gather/pipeline.py:104-167
              → [ORIGINAL FUNCTION EXECUTES]
                1. online.run_plan (live providers)
                2. normalize_candidates
                3. rank_candidates
                4. assess_stance (per item)
                5. apply_guardrails_to_arms
                6. compute_overlap_conflict
                7. score_from_evidence → verdict
              → Returns {"arm_A": [...], "arm_B": [...], "verdict": {...}}
            → [P20 WRAPPER EXECUTES AFTER ORIGINAL]
              → For arm_A items: attach_finding_to_item(claim_text, "A", item)
              → For arm_B items: attach_finding_to_item(claim_text, "B", item)
              → Adds: grade, stance, finding to each item
            → [P22 WRAPPER EXECUTES AFTER P20]
              → _collect_missing_urls(bundle)
              → _fallback_fetch_into_cache(urls) → populates _FETCH_CACHE
              → _enrich_items(bundle) → adds: content, content_hash, coverage
          → Returns enriched bundle to run.py
      → [P22 WRAPPER at run_preview level]
        → Claims already have evidence with enriched items
        → May do additional enrichment (redundant in this flow)
    → run.py continues processing claims
      → Adds IFCN labels, guardrails, methodology
    → Returns final trust capsule
```

**Key observations:**
1. **Double-wrapping confirmed:** P22 wraps P20 which wraps original
2. **Execution order:** original → P20 (findings) → P22 (content)
3. **P20 runs on items WITHOUT content** (uses snippet fallback)
4. **P22 fetches content AFTER P20** (P20 doesn't benefit from full content)

### 2.2 Test Path (imports p23-p29)

**Additional layers when tests load all wrappers:**

```
[... same as production until build_evidence_for_claim returns ...]
  → [P23 WRAPPER at run_preview level]
    → For each claim's evidence items:
      → analyze_item(claim_text, item) from semantic_read.py
      → Adds: findings[], item_grade, grade_label
  → [P24 WRAPPER]
    → analyze_frames(claim_text, content)
    → Adds: frame_matches to items
  → [P25 WRAPPER]
    → aggregate_verdict(claim_text, arm_a_items, arm_b_items)
    → Adds verdict fields to claim
  → [P26+ WRAPPERS]
    → Dual researchers, consensus, diversification
```

**Test chain depth: 6-7 wrappers deep**

---

## PART 3: INCOMPATIBILITIES & ISSUES

### 3.1 P22 Global State Issue

**Problem:**
```python
# p22_ingest.py:29
_FETCH_CACHE: Dict[str, str] = {}  # Module-level global, never cleared
```

**Issues:**
1. **Memory leak:** Unbounded growth (production blocker)
2. **Cross-request pollution:** Cache persists across requests
3. **Shared state in P26:** R1 and R2 "independent" researchers share cache

**Solutions:**
1. **Request-scoped cache** (recommended for clean integration):
   ```python
   # Pass cache as parameter through call chain
   async def build_evidence_for_claim(..., fetch_cache: Optional[Dict] = None):
       cache = fetch_cache or {}
       # Use cache
       return bundle, cache  # Return cache for caller to manage
   ```

2. **LRU cache with max size:**
   ```python
   from functools import lru_cache
   @lru_cache(maxsize=1000)
   def get_cached_content(url: str) -> str:
       # Bounded size, automatic eviction
   ```

3. **External cache (Redis/SQLite):**
   - Overkill for initial integration
   - Consider for AI Assist phase

**Recommendation:** Request-scoped cache (Solution 1) for clean integration

### 3.2 Execution Order Dependencies

**Critical constraint: P22 must run BEFORE P23-P25**

**Why:**
- P23 `semantic_read.analyze_item` expects `item["content"]` or `item["content_excerpt"]`
- If content not present, returns low-grade findings
- P22 adds `content` field by fetching full text

**Current problem:**
- P20 runs before P22, so P20's `attach_finding_to_item` uses only `snippet`
- P20 could produce better findings if it had full `content`

**Optimal order for clean integration:**
1. **Original pipeline** (live gather, normalize, rank, stance, guardrails, verdict)
2. **Content enrichment (P22 logic)** - fetch full text, add content/hash/coverage
3. **Findings (P20 logic)** - grade with full content available
4. **Full-read (P21 logic)** - deeper analysis with full content
5. **Semantic (P23 logic)** - extract findings from content
6. **Frames (P24 logic)** - extract frame matches
7. **Aggregation (P25 logic)** - compute arm strengths and verdict

**Note:** Current wrapper order (P20 before P22) is suboptimal but works

### 3.3 Field Name Overlap

**Potential conflict:**
- P20 adds: `item["stance"]` (from grade.py)
- Pipeline adds: `item["stance"]` (from assess_stance)
- Both write to same field!

**Current behavior:**
- P20 wrapper runs AFTER pipeline completes
- P20's `stance` overwrites pipeline's `stance` (from assess_stance.py)

**For clean integration:**
- Keep pipeline's `stance` (from assess_stance - more primitive)
- P20's finding has its own `finding["stance"]` (derived from content analysis)
- Rename one or use namespacing: `stance_original` vs `stance_finding`

**Recommendation:** Keep pipeline's stance, nest P20's stance under `finding["stance"]` (already done)

### 3.4 Data Shape Variations

**Evidence bundle can have multiple shapes:**

Shape 1 (pipeline output):
```python
{
  "A": {"intent": "support", "candidates": [...]},
  "B": {"intent": "challenge", "candidates": [...]},
  "arm_A": [...],  # Flat list
  "arm_B": [...]   # Flat list
}
```

Shape 2 (run.py expects):
```python
{
  "arm_A": [...],
  "arm_B": [...],
  "verdict": {...}
}
```

**Wrappers handle both shapes:**
- p20_wrapper.py:93-119 has `_get_arm_candidates` that handles list or dict
- p22_ingest.py:49-63 expects flat `arm_A`/`arm_B` keys

**For clean integration:**
- Standardize on flat shape: `{"arm_A": [...], "arm_B": [...], "verdict": {...}}`
- Pipeline already returns this (lines 165-166)

---

## PART 4: DIRECT WIRING PLAN

### 4.1 Target Architecture

**Goal:** Call clean modules directly in pipeline, eliminate wrappers

**Proposed execution flow:**

```python
async def build_evidence_for_claim_with_enrichment(
    *,
    claim_text: str,
    plan: Dict[str, Any],
    max_per_arm: int = 3,
    fetch_cache: Optional[Dict[str, str]] = None
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Integrated pipeline with clean module calls.
    Returns (enriched_bundle, updated_cache).
    """
    cache = fetch_cache or {}

    # 1. CORE PIPELINE (existing code)
    bundle = await _original_build_evidence_for_claim(
        claim_text=claim_text, plan=plan, max_per_arm=max_per_arm
    )

    # 2. CONTENT ENRICHMENT (P22 logic)
    from intelligence.content.fetch import fetch_text

    # Collect URLs needing fetch
    urls_to_fetch = []
    for arm_key in ("arm_A", "arm_B"):
        for item in bundle.get(arm_key, []):
            url = item.get("url")
            if url and not item.get("content") and url not in cache:
                urls_to_fetch.append(url)

    # Fetch missing content
    if urls_to_fetch:
        tasks = [fetch_text(url, timeout=8.0) for url in urls_to_fetch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for url, result in zip(urls_to_fetch, results):
            if isinstance(result, dict) and result.get("text"):
                cache[url] = result["text"]

    # Enrich items with content
    for arm_key in ("arm_A", "arm_B"):
        for item in bundle.get(arm_key, []):
            url = item.get("url")
            if url and url in cache and not item.get("content"):
                item["content"] = cache[url]
                item["content_chars"] = len(cache[url])
                item["content_hash"] = f"sha256:{hashlib.sha256(cache[url].encode()).hexdigest()}"

            # Determine coverage
            content = item.get("content") or ""
            excerpt = item.get("content_excerpt") or ""
            chars = item.get("content_chars", 0)
            if content and chars and len(content) >= chars * 0.98:
                item["coverage"] = "full"
            elif content or excerpt:
                item["coverage"] = "partial"
            else:
                item["coverage"] = "snippet_only"

    # 3. FINDINGS ATTACHMENT (P20 logic)
    from intelligence.content.grade import attach_finding_to_item

    for arm_key, arm_label in [("arm_A", "A"), ("arm_B", "B")]:
        for item in bundle.get(arm_key, []):
            try:
                attach_finding_to_item(claim_text, arm_label, item)
            except Exception:
                pass  # Non-critical, continue

    # 4. OPTIONAL: Full-read evaluation (P21 logic)
    # from intelligence.content.fullread import evaluate_full_evidence
    # for arm_key in ("arm_A", "arm_B"):
    #     for item in bundle.get(arm_key, []):
    #         evaluate_full_evidence(claim_text, item)

    return bundle, cache
```

**Changes to run.py:**
```python
async def run_preview(text: str, test_mode: bool = False):
    # ... existing claim creation and planning ...

    # Initialize request-scoped cache
    fetch_cache = {}

    try:
        from intelligence.gather.pipeline import build_evidence_for_claim_with_enrichment
        evidence_bundle, fetch_cache = await build_evidence_for_claim_with_enrichment(
            claim_text=claim["text"],
            plan=plans,
            max_per_arm=3,
            fetch_cache=fetch_cache
        )
    except Exception:
        logging.exception("preview evidence build failed")
        evidence_bundle = {"arm_A": [], "arm_B": []}

    # Cache cleared at end of request (goes out of scope)
    # ... rest of run.py ...
```

### 4.2 Migration Steps

**Phase 1: Prepare Clean Integration (Day 1)**

1. **Create `build_evidence_for_claim_with_enrichment` in pipeline.py**
   - Copy original `build_evidence_for_claim` logic
   - Add content enrichment (P22 logic) inline
   - Add findings attachment (P20 logic) inline
   - Use request-scoped cache parameter

2. **Add optional flag to use clean path:**
   ```python
   USE_CLEAN_PATH = os.getenv("ROGR_USE_CLEAN_PATH", "").lower() in ("1", "true")

   if USE_CLEAN_PATH:
       bundle, cache = await build_evidence_for_claim_with_enrichment(...)
   else:
       bundle = await build_evidence_for_claim(...)  # Wrapped path
   ```

3. **Test both paths produce equivalent output**

**Phase 2: Switch to Clean Path (Day 2)**

1. **Remove sitecustomize.py (or comment out wrapper imports)**
2. **Set `ROGR_USE_CLEAN_PATH=1` in environment**
3. **Test live API with clean path**
4. **Compare outputs (should be identical except memory usage)**

**Phase 3: Remove Wrappers (Day 3)**

1. **Delete wrapper files:**
   - p20_wrapper.py
   - p22_ingest.py
   - sitecustomize.py

2. **Remove `USE_CLEAN_PATH` flag, make clean path default**

3. **Update tests to use clean path**

4. **Verify test_s2p30r_audit.py passes:**
   ```python
   # This test expects NO wrappers
   assert api.run_preview is core.run_preview  # Should pass now
   ```

**Phase 4: Optional - Add P23-P25 Logic (Day 4)**

1. **Add semantic analysis to pipeline:**
   ```python
   # After findings attachment
   from intelligence.content.semantic_read import analyze_item
   for arm_key in ("arm_A", "arm_B"):
       for item in bundle.get(arm_key, []):
           if item.get("content"):
               analyze_item(claim_text, item)
   ```

2. **Add frame analysis:**
   ```python
   from intelligence.content.semantic_frames import analyze_frames
   # Per item or per claim
   ```

3. **Add aggregation:**
   ```python
   from intelligence.content.p25_aggregate import aggregate_verdict
   verdict = aggregate_verdict(
       claim_text,
       bundle.get("arm_A", []),
       bundle.get("arm_B", [])
   )
   ```

### 4.3 Testing Strategy

**Regression tests:**
1. **Baseline capture (before changes):**
   ```bash
   # With wrappers loaded
   python scripts/test_live_claim.py "Test claim" > baseline.json
   ```

2. **Clean path test:**
   ```bash
   # With ROGR_USE_CLEAN_PATH=1
   python scripts/test_live_claim.py "Test claim" > clean.json
   ```

3. **Compare outputs:**
   ```bash
   diff baseline.json clean.json
   # Should be identical except:
   # - No wrapper diagnostic events
   # - Possibly different field order (OK)
   # - Content hashes might differ if fetched at different times (OK)
   ```

**Unit tests for clean modules:**
```python
def test_attach_finding_standalone():
    from intelligence.content.grade import attach_finding_to_item
    item = {"url": "...", "snippet": "Budget increased 5%", "content": "Full text..."}
    result = attach_finding_to_item("Budget increased 5%", "A", item)
    assert "finding" in result
    assert "grade" in result
    assert isinstance(result["grade"], (int, float))

def test_semantic_read_standalone():
    from intelligence.content.semantic_read import analyze_item
    item = {"content": "Full text content..."}
    result = analyze_item("Test claim", item)
    assert "findings" in result
    assert "item_grade" in result
```

---

## PART 5: RISK ANALYSIS

### 5.1 Low Risk Changes

✅ **Adding clean path alongside wrapped path**
- No disruption to existing system
- Can A/B test both paths
- Rollback is trivial (remove flag)

✅ **Request-scoped cache**
- Eliminates memory leak
- No shared state between requests
- Cleaner architecture

✅ **Direct function calls**
- More transparent than setattr
- Easier to debug (normal stack traces)
- Better IDE support

### 5.2 Medium Risk Changes

⚠️  **Changing execution order (P22 before P20)**
- Could affect quality if P20's logic expects snippet-only
- Mitigation: Test both orders, compare outputs
- May need to adjust P20's weights if it gets better input

⚠️  **Removing wrappers entirely**
- Tests depend on wrappers (p21, p23-p29)
- Mitigation: Update tests to use clean modules directly
- Or: Keep test wrappers, remove only production wrappers (p20, p22)

### 5.3 High Risk Changes

❌ **Changing field names or data shapes**
- API contract changes
- Downstream consumers break
- Mitigation: Don't do this, preserve existing field names

❌ **Removing P20/P22 logic without replacement**
- Loss of functionality
- Quality degradation
- Mitigation: Always replace with clean module equivalent

---

## PART 6: ANSWERS TO USER QUESTIONS

### Can these modules be wired directly?

**YES ✅** - All modules are standalone and can be called directly:
- `grade.attach_finding_to_item(claim_text, arm, item)` ✅
- `fullread.evaluate_full_evidence(claim_text, item)` ✅
- `semantic_read.analyze_item(claim_text, item)` ✅
- `semantic_frames.analyze_frames(claim_text, content)` ✅
- `p25_aggregate.aggregate_verdict(claim_text, arm_a, arm_b)` ✅

**Verified through standalone tests:** All import and execute successfully without wrappers.

### What adjustments are needed?

**1. Replace P22 global cache (HIGH PRIORITY):**
- Change `_FETCH_CACHE` from module-level to parameter
- Pass cache through call chain
- Clear cache at end of request
- **Estimated effort:** 4-6 hours

**2. Integrate content fetching into pipeline (MEDIUM):**
- Add fetch logic before findings attachment
- Use asyncio.gather for parallel fetches
- Handle errors gracefully
- **Estimated effort:** 4-6 hours

**3. Remove wrapper indirection (LOW):**
- Delete setattr calls
- Delete wrapper files
- Update imports
- **Estimated effort:** 2-3 hours

**4. Update tests (MEDIUM):**
- Remove wrapper imports
- Call clean modules directly
- Update assertions
- **Estimated effort:** 4-6 hours

**Total estimated effort:** 2-3 days (not 6-7 days)

### What order should they execute?

**Optimal execution order:**

1. **Core pipeline** (gather, normalize, rank, stance, guardrails, verdict)
   - Function: `build_evidence_for_claim` (original logic)
   - Output: `{"arm_A": [...], "arm_B": [...], "verdict": {...}}`

2. **Content enrichment** (P22 logic)
   - Fetch full text for each URL
   - Add: `content`, `content_hash`, `coverage`
   - **Why here:** Provides full text for downstream analysis

3. **Findings attachment** (P20 logic)
   - Function: `attach_finding_to_item`
   - Add: `grade`, `stance`, `finding`
   - **Why here:** Benefits from full content (if available)

4. **Full-read evaluation** (P21 logic, optional)
   - Function: `evaluate_full_evidence`
   - Add: `grade_full`, `stance_full`, `signals_full`, `credibility`
   - **Why here:** Deeper analysis with full content

5. **Semantic reading** (P23 logic, optional for production)
   - Function: `analyze_item`
   - Add: `findings[]`, `item_grade`, `grade_label`
   - **Why here:** Extracts multiple findings from content

6. **Frame extraction** (P24 logic, optional)
   - Function: `analyze_frames`
   - Add: `frame_matches`
   - **Why here:** Needs semantic findings

7. **Aggregation** (P25 logic, optional)
   - Function: `aggregate_verdict`
   - Add: verdict with arm strengths
   - **Why here:** Synthesizes all previous analysis

**Current wrapper order (suboptimal):**
- P20 (findings) → P22 (content)
- P20 uses only snippets because content not yet fetched
- Still works but lower quality

**Clean integration order (optimal):**
- P22 (content) → P20 (findings) → P21+ (optional deep analysis)
- P20 gets full content, produces better findings
- Higher quality, same functionality

---

## PART 7: IMPLEMENTATION CHECKLIST

### Day 1: Prepare Clean Path
- [ ] Create `build_evidence_for_claim_with_enrichment` function
- [ ] Inline P22 content enrichment logic with request-scoped cache
- [ ] Inline P20 findings attachment logic
- [ ] Add `ROGR_USE_CLEAN_PATH` environment flag
- [ ] Test clean path produces equivalent output to wrapped path

### Day 2: Switch to Clean Path
- [ ] Capture baseline outputs with wrappers
- [ ] Enable clean path with environment variable
- [ ] Run full test suite
- [ ] Compare outputs (should be identical)
- [ ] Test live API endpoints
- [ ] Measure memory usage (should be lower without cache leak)

### Day 3: Remove Wrappers
- [ ] Delete p20_wrapper.py
- [ ] Delete p22_ingest.py
- [ ] Delete sitecustomize.py (or comment out wrapper imports)
- [ ] Remove `USE_CLEAN_PATH` flag, make clean path default
- [ ] Verify test_s2p30r_audit.py passes
- [ ] Update any tests that explicitly import wrappers

### Day 4: Optional Enhancements
- [ ] Add P21 full-read evaluation to pipeline
- [ ] Add P23 semantic reading (if desired for production)
- [ ] Add P24 frame extraction (if desired)
- [ ] Add P25 aggregation (if desired)
- [ ] Document which features are production vs test-only

---

## PART 8: SUCCESS CRITERIA

### Must Have (Blocking)
- ✅ No setattr calls in production code
- ✅ No sitecustomize.py (or wrappers not loaded)
- ✅ Memory leak fixed (no unbounded cache growth)
- ✅ test_s2p30r_audit.py passes
- ✅ Live API produces identical output to baseline

### Should Have (High Priority)
- ✅ All clean modules callable without wrappers
- ✅ Request-scoped cache replaces global cache
- ✅ Tests updated to use clean path
- ✅ Documentation updated

### Nice to Have (Optional)
- ⚙️  P21, P23-P25 integrated in production (currently test-only)
- ⚙️  Improved execution order (P22 before P20)
- ⚙️  Unified test suite (no separate wrapped/clean paths)

---

## PART 9: ROLLBACK PLAN

### If Clean Path Has Issues

**Step 1: Immediate rollback (< 1 minute)**
```bash
# Set environment variable back
export ROGR_USE_CLEAN_PATH=0
# Or restart service without the variable

# Wrappers still in place, will re-activate
```

**Step 2: Full rollback (< 5 minutes)**
```bash
# Restore sitecustomize.py from backup
git checkout HEAD -- sitecustomize.py

# Restart service
# Wrappers auto-load, system back to original state
```

**Step 3: Keep both paths (indefinite)**
- Leave clean path code in place
- Keep wrappers as fallback
- Use environment flag to switch
- No data loss, no downtime

---

---

## PART 10: P26-P29 REQUIRED INTELLIGENCE (CRITICAL UPDATE)

### 10.1 Critical Correction

**Previous assessment was INCOMPLETE:**
- ❌ Original plan only covered P20-P25
- ❌ Assumed P26-P29 were "optional test features"
- ✅ **Reality:** P26-P29 contain REQUIRED intelligence for production

**What P26-P29 provide:**
1. **P26:** Dual independent researchers (R1, R2) for verification
2. **P27:** Consensus mechanism to combine R1+R2 intelligently
3. **P28:** Deterministic diversification for true independence
4. **P29:** Telemetry and reproducibility tracking

**Without these:**
- Only single verdict (no verification or consensus)
- No way to detect ambiguous evidence
- Lower quality, less reliable fact-checking

### 10.2 Intelligence Provided by Each Component

#### P26: Dual Independent Researchers

**Core value:**
```
Single run → ONE verdict
Dual run → TWO independent verdicts → comparison + consensus → higher confidence
```

**Why necessary:**
- Detects when evidence is ambiguous (R1 and R2 disagree)
- Provides confidence signal (R1 and R2 agree → boost confidence)
- Foundation for consensus mechanism
- Verifies verdict robustness

**Output structure:**
```json
{
  "claims": [{
    "verdict": {...},      // R1 (backward compatible)
    "evidence": {...},     // R1 (backward compatible)
    "researchers": [
      {"id": "R1", "verdict": {...}, "evidence": {...}},
      {"id": "R2", "verdict": {...}, "evidence": {...}}
    ],
    "consensus": {...}     // From P27
  }]
}
```

#### P27: Consensus Mechanism

**Core logic:**
```python
if R1.label == R2.label:
    # Agreement → confidence boost
    consensus.confidence = avg(R1.conf, R2.conf) + bonus
    consensus.label = R1.label
else:
    # Disagreement → use arm strengths
    if |support_strength - challenge_strength| >= 0.20:
        consensus.label = stronger_side
    else:
        consensus.label = "mixed"
    consensus.confidence = max(R1.conf, R2.conf) - penalty
```

**Why necessary:**
- Combines two verdicts into final judgment with rationale
- Agreement → confidence boost (up to +0.20)
- Disagreement → analyze evidence, pick side or declare mixed
- Higher quality than single-researcher verdict

#### P28: Deterministic Diversification

**Critical insight:**
```
WITHOUT P28: R1 and R2 would be IDENTICAL
  → Same queries in same order
  → Same providers in same order
  → Same results → No benefit from dual run

WITH P28: R1 and R2 are INDEPENDENT but DETERMINISTIC
  → R1 providers: [google, brave, bing]
  → R2 providers: [brave, google, bing]
  → Queries shuffled differently per lane
  → Same claim always produces same shuffle (reproducible)
```

**Why necessary:**
- Makes dual researchers actually independent
- Different provider order → different evidence emphasis
- Different query order → different search variations tried first
- If R1 and R2 still agree despite different paths → high confidence

#### P29: Telemetry & Reproducibility

**Provides:**
- Per-lane execution tracking (which providers called, duration)
- Stable replay IDs for exact reproduction
- Debugging information (why did R1 and R2 differ?)
- Production monitoring

**Output:**
```json
{
  "run_manifest": {
    "replay_id": "a3f9b8c2e1d4f6a8",
    "lanes": {
      "R1": {"providers": ["google", "brave", "bing"], "queries_first3": {...}},
      "R2": {"providers": ["brave", "google", "bing"], "queries_first3": {...}}
    }
  },
  "researchers": [
    {"id": "R1", "telemetry": {"providers": {"google": 3}, "duration_ms": 2340}},
    {"id": "R2", "telemetry": {"providers": {"brave": 3}, "duration_ms": 2280}}
  ]
}
```

### 10.3 Clean Extraction Strategy for P26-P29

**All can be extracted to clean modules.** The wrapper pattern is not fundamental.

#### Extract P27 Consensus (EASIEST - 2-3 hours)

**Create: `intelligence/consensus/dual_lane.py`**
```python
def compute_consensus(
    r1_verdict: Dict[str, Any],
    r2_verdict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Pure function: R1 verdict + R2 verdict → consensus verdict
    No dependencies, no side effects.
    """
    # Copy logic from p27_consensus.py:38-92
    # _lane(), _consensus_for_pair()
```

#### Extract P28 Diversification (4-6 hours)

**Create: `intelligence/planning/diversify.py`**
```python
def diversify_plan_for_lane(
    plan: Dict[str, Any],
    lane_id: str,  # "R1" or "R2"
    claim_text: str,
    available_providers: List[str]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate lane-specific plan with deterministic diversification.
    Returns: (modified_plan, lane_config)
    """
    # Generate deterministic seed from lane + claim
    seed = hashlib.md5(f"{lane_id}::{claim_text}".encode()).hexdigest()

    # Order providers by lane preference
    if lane_id == "R1":
        provider_order = ["google", "brave", "bing"]
    else:  # R2
        provider_order = ["brave", "google", "bing"]

    # Shuffle queries deterministically
    rng = random.Random(int(seed[:8], 16))
    for arm in plan["arms"]:
        queries = list(arm["queries"])
        rng.shuffle(queries)
        arm["queries"] = queries
        arm["providers"] = provider_order
```

#### Extract P29 Telemetry (3-4 hours)

**Create: `intelligence/telemetry/collect.py`**
```python
class LaneTelemetry:
    def __init__(self, lane_id: str):
        self.lane_id = lane_id
        self.providers = {}
        self.start_time = time.time()

    def record_provider_call(self, provider: str):
        self.providers[provider] = self.providers.get(provider, 0) + 1

    def finalize(self) -> Dict[str, Any]:
        return {
            "providers": self.providers,
            "duration_ms": int((time.time() - self.start_time) * 1000)
        }

def generate_manifest(claim_text: str, r1_config: Dict, r2_config: Dict) -> Dict:
    replay_id = hashlib.sha256(f"{claim_text}::v2".encode()).hexdigest()[:16]
    return {"replay_id": replay_id, "lanes": {"R1": r1_config, "R2": r2_config}}
```

#### Integrate P26 in run.py (6-8 hours)

**Modify: `intelligence/pipeline/run.py`**

```python
async def run_preview_with_dual_researchers(
    text: str,
    test_mode: bool = False
) -> Dict[str, Any]:
    from intelligence.planning.diversify import diversify_plan_for_lane
    from intelligence.consensus.dual_lane import compute_consensus
    from intelligence.telemetry.collect import LaneTelemetry, generate_manifest

    # 1. Create claim
    claim = {"id": "c-0", "text": text, "tier": "primary"}

    # 2. Generate base plan
    base_plan = build_plan_v2(claim, test_mode=test_mode)

    # 3. Diversify for R1 and R2
    available_providers = _get_available_providers()
    r1_plan, r1_config = diversify_plan_for_lane(base_plan, "R1", text, available_providers)
    r2_plan, r2_config = diversify_plan_for_lane(base_plan, "R2", text, available_providers)

    # 4. Run both lanes with telemetry
    r1_telem = LaneTelemetry("R1")
    r2_telem = LaneTelemetry("R2")

    r1_evidence = await build_evidence_for_claim_with_enrichment(
        claim_text=text, plan=r1_plan, telemetry=r1_telem
    )
    r1_verdict = _compute_verdict_from_evidence(r1_evidence)

    r2_evidence = await build_evidence_for_claim_with_enrichment(
        claim_text=text, plan=r2_plan, telemetry=r2_telem
    )
    r2_verdict = _compute_verdict_from_evidence(r2_evidence)

    # 5. Compute consensus
    consensus = compute_consensus(r1_verdict, r2_verdict)

    # 6. Build response
    return {
        "overall": consensus,
        "run_manifest": generate_manifest(text, r1_config, r2_config),
        "claims": [{
            "verdict": r1_verdict,     # R1 (back-compat)
            "evidence": r1_evidence,   # R1 (back-compat)
            "consensus": consensus,
            "researchers": [
                {"id": "R1", "verdict": r1_verdict, "evidence": r1_evidence,
                 "lane_config": r1_config, "telemetry": r1_telem.finalize()},
                {"id": "R2", "verdict": r2_verdict, "evidence": r2_evidence,
                 "lane_config": r2_config, "telemetry": r2_telem.finalize()}
            ]
        }]
    }
```

### 10.4 Telemetry Integration

**Challenge:** How to track provider calls without wrappers?

**Solution:** Pass telemetry collector as parameter

**Modify `intelligence/gather/online.py`:**
```python
async def run_plan(
    plan: Dict[str, Any],
    *,
    max_per_query: int = 10,
    telemetry: Optional[LaneTelemetry] = None  # NEW
) -> Dict[str, Any]:
    # Existing code...

    # Before calling provider:
    if telemetry:
        telemetry.record_provider_call(provider_name)

    # Call provider
    results = await provider_call(...)
```

**Effort:** 2-3 hours to add hooks
**Risk:** Low (additive, optional parameter)

### 10.5 Dependency Order for P26-P29

```
P27 (consensus) → No dependencies [Extract first]
    ↓
P28 (diversify) → No dependencies [Extract second]
    ↓
P29 (telemetry) → No dependencies [Extract third]
    ↓
P26 (orchestration) → Uses P27, P28, P29 [Integrate last in run.py]
```

### 10.6 Updated Timeline

**REVISED TOTAL: 8-10 days**

**Week 1: Item Enrichment (Days 1-4)**
- Day 1: P22 content enrichment (cache fix)
- Day 2: P20 findings + P21 full-read
- Day 3: P23-P25 semantic + frames + aggregation
- Day 4: Test item enrichment path

**Week 2: Dual Researchers (Days 5-8)**
- Day 5: Extract P27 consensus module (2-3 hours) + test
- Day 6: Extract P28 diversification module (4-6 hours) + test
- Day 7: Extract P29 telemetry module (3-4 hours) + test
- Day 8: Integrate P26 orchestration in run.py (6-8 hours)

**Week 2-3: Validation (Days 9-10)**
- Day 9: Test dual-researcher path, compare to wrappers
- Day 10: Remove all wrappers (P20-P29), validate audit test

### 10.7 Effort Breakdown (COMPLETE)

| Component | Extraction | Integration | Testing | Total |
|-----------|-----------|-------------|---------|-------|
| **P20-P22** | 6h | 6h | 4h | 16h (2 days) |
| **P23-P25** | 4h | 4h | 2h | 10h (1.5 days) |
| **P27 Consensus** | 3h | 2h | 1h | 6h (0.75 days) |
| **P28 Diversify** | 5h | 4h | 2h | 11h (1.5 days) |
| **P29 Telemetry** | 4h | 3h | 1h | 8h (1 day) |
| **P26 Orchestration** | - | 8h | 4h | 12h (1.5 days) |
| **Validation & Removal** | - | 4h | 8h | 12h (1.5 days) |
| **TOTAL** | **22h** | **31h** | **22h** | **75h (9-10 days)** |

### 10.8 Critical Questions

**Q: Can R1 and R2 run in parallel?**
- Current: Sequential (to avoid rate limits)
- Clean integration: Start sequential, add parallel flag later
- Parallel could halve time but risks provider rate limits

**Q: What if only one provider available?**
- Diversification becomes query-order-only
- Still provides some independence
- Handle gracefully in diversify_plan_for_lane()

**Q: Backward compatible?**
- Yes: Existing fields (verdict, evidence) preserved
- New fields added (consensus, researchers, run_manifest)
- Additive only, no breaking changes

### 10.9 Success Criteria (UPDATED)

#### Must Have
- ✅ All P20-P29 logic in clean modules
- ✅ No setattr, no wrappers, no monkey patches
- ✅ Dual researchers produce R1 and R2 verdicts
- ✅ Consensus computed and included
- ✅ Diversification working (different provider/query order)
- ✅ Telemetry collected per lane
- ✅ Manifest generated with replay ID
- ✅ Backward compatible API
- ✅ test_s2p30r_audit.py passes

#### Should Have
- ✅ Sequential R1/R2 execution (rate limit safe)
- ✅ Deterministic diversification (reproducible)
- ✅ Unit tests for consensus, diversify, telemetry
- ✅ Integration tests for dual researchers

#### Nice to Have
- ⚙️ Parallel R1/R2 execution (optional flag)
- ⚙️ Search result caching (reduce provider calls)
- ⚙️ Configurable diversification parameters

---

## FINAL RECOMMENDATION (UPDATED)

**Proceed with complete clean integration: 8-10 days of focused work**

**What changed from original estimate:**
- Original: 3-4 days for P20-P25 only
- Updated: 8-10 days including P26-P29 (required, not optional)

**Why this is achievable:**
1. ✅ P20-P25 logic exists in clean modules (2-4 days integration)
2. ✅ P26-P29 logic can be extracted cleanly (4-6 days extraction + integration)
3. ✅ All are pure functions or simple orchestration
4. ✅ Low risk with gradual rollout (flag-controlled)
5. ✅ Easy rollback if issues arise
6. ✅ Backward compatible (additive only)

**Confidence level: HIGH ✅**

Based on:
- Direct code inspection of ALL modules (P20-P29)
- Understanding of dual-researcher architecture
- Clear extraction path for embedded logic
- Understanding of all dependencies
- Telemetry integration strategy defined
- Migration path with rollback options

**Next step:**
1. Extract P27, P28, P29 to clean modules (Days 5-7)
2. Integrate P26 orchestration in run.py (Day 8)
3. Validate complete system (Days 9-10)
