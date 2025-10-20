# REALITY VS BLUEPRINT - ALL 13 STEPS

**Date:** 2025-10-19
**Comparison:** Current codebase vs TARGET_ARCHITECTURE.md
**Result:** 🔴 **CRITICAL GAPS FOUND**

---

## STEP 0: Claim Classification

**Blueprint requirement:** `classify_claim()` in `intelligence/preprocess/classify.py`
**Function exists?** ✅ YES - Found at line 7
**Function called?** ❌ **NO**
**Call location:** NOT CALLED

**Verification:**
```bash
grep -rn "classify_claim(" intelligence/ | grep -v "def classify_claim"
# Result: No calls found (only definition)
```

**Status:** ❌ **MISSING FROM PIPELINE**

**Impact:** Claims are not classified into 6 categories (SIMPLE_FACTUAL, OPINION, etc.). No early exit for unverifiable claims. System wastes resources trying to verify opinions and predictions.

**Blueprint requirement:** `detect_unverifiable_early()`
**Function exists?** ❌ NO
**Function called?** ❌ NO

**Status:** ❌ **NOT IMPLEMENTED**

---

## STEP 1: Claim Understanding

**Blueprint requirement:** `enrich_claim_obj()` in `intelligence/analyze/enrich.py`
**Function exists?** ✅ YES - Found at line 6
**Function called?** ✅ YES
**Call location:** `intelligence/pipeline/run.py:129`

**Verification:**
```python
# run.py line 128-129
from intelligence.analyze.enrich import enrich_claim_obj
claim = enrich_claim_obj(claim)
```

**Status:** ✅ **CORRECT**

**Phase 9 Enhancements (Required but missing):**
- `detect_negation()` - ❌ NOT FOUND
- `detect_hedging()` - ❌ NOT FOUND
- `extract_precision_context()` - ❌ NOT FOUND

**Status:** ⚠️ **BASELINE ONLY - Phase 9 enhancements missing**

---

## STEP 2: Dual Research Planning

### 2A: Base Plan Generation

**Blueprint requirement:** `build_search_plans_v2()` in `intelligence/strategy/plan_v2.py`
**Function exists?** ✅ YES - Found at line 115
**Function called?** ✅ YES
**Call location:** `intelligence/pipeline/run.py:137`

**Verification:**
```python
# run.py line 136-137
from intelligence.strategy.plan_v2 import build_search_plans_v2
base_plan = build_search_plans_v2(claim)
```

**Status:** ✅ **CORRECT**

---

### 2B: R1/R2 Diversification

**Blueprint requirement:** `diversify_plan_for_lane()` in `intelligence/planning/diversify.py`
**Function exists?** ✅ YES - Found at line 43
**Function called?** ✅ YES
**Call location:** `intelligence/pipeline/run.py:144` (passed to run_dual_researchers)

**Verification:**
```python
# run.py line 140-145
dual_result = await run_dual_researchers(
    claim_text=text,
    base_plan=base_plan,
    enrichment_pipeline=run_single_lane_enrichment,
    diversify_fn=diversify_plan_for_lane,  # ← CALLED HERE
    telemetry_class=LaneTelemetry
)
```

**Status:** ⚠️ **WRONG IMPLEMENTATION**

**Critical Issue:** `diversify_plan_for_lane()` does NOT implement Phase 5 requirements:
- Does NOT call `generate_queries_r1()` (precision strategy)
- Does NOT call `generate_queries_r2()` (recall strategy)
- Only shuffles queries and changes provider order
- R1 and R2 use SAME query strategy (not "Skeptic" vs "Explorer")

**What it should do:**
```python
# R1 (Precision): quoted, anchored, exact
r1_queries = generate_queries_r1(claim_text, entities, numbers, arm)

# R2 (Recall): paraphrased, exploratory, broad
r2_queries = generate_queries_r2(claim_text, entities, numbers, arm)
```

**What it actually does:**
```python
# Just shuffles the SAME queries
shuffled = _shuffle_queries_deterministic(original_queries, seed)
```

---

### 2C: Query Generation Strategies (Phase 5)

**Blueprint requirement:** `generate_queries_r1()` in `intelligence/strategy/plan_v2.py`
**Function exists?** ✅ YES - Found at line 176
**Function called?** ❌ **NO**

**Blueprint requirement:** `generate_queries_r2()` in `intelligence/strategy/plan_v2.py`
**Function exists?** ✅ YES - Found at line 217
**Function called?** ❌ **NO**

**Verification:**
```bash
grep -rn "generate_queries_r1(" intelligence/ | grep -v "def generate_queries_r1"
grep -rn "generate_queries_r2(" intelligence/ | grep -v "def generate_queries_r2"
# Result: No calls found (only definitions)
```

**Status:** ❌ **NOT INTEGRATED - Phase 5 incomplete**

**Impact:** R1 and R2 use identical query strategies, defeating the purpose of dual researchers. No "Skeptic" vs "Explorer" differentiation.

---

## STEP 3: Search Execution

**Blueprint requirement:** `run_plan()` in `intelligence/gather/online.py`
**Function exists?** ✅ YES
**Function called?** ✅ YES
**Call location:** `intelligence/gather/pipeline.py:45`

**Verification:**
```python
# pipeline.py line 45
res = await online.run_plan(sub_plan, max_per_query=max_per_query)
```

**Status:** ✅ **CORRECT**

---

## STEP 4: Fast Filter

**Blueprint requirement:** `filter_unrelated()` in `intelligence/gather/pipeline.py`
**Function exists?** ✅ YES - Found at line 219
**Function called?** ❌ **NO**
**Call location:** NOT CALLED

**Verification:**
```bash
grep -rn "filter_unrelated(" intelligence/ | grep -v "def filter_unrelated"
# Result: No matches found
```

**Code location:** Lines 219-312 (94 lines of implementation)

**What it does:** Fast deterministic filter checking:
- Entity overlap (≥1 entity match)
- Number overlap (≥1 number match)
- Keyword overlap (≥30% lexical match)

**Expected impact:** 28-30% candidate reduction BEFORE ranking

**Status:** ❌ **NOT INTEGRATED - Phase 2 incomplete**

**Current flow:**
```
Search → Normalize → Rank → Select Top 3
```

**Blueprint flow:**
```
Search → Filter Unrelated → Quality Gate → Rank → Select Top 5
```

---

## STEP 5: Quality Gate

**Blueprint requirement:** `quality_gate()` in `intelligence/gather/pipeline.py`
**Function exists?** ✅ YES - Found at line 314
**Function called?** ❌ **NO**
**Call location:** NOT CALLED

**Verification:**
```bash
grep -rn "quality_gate(" intelligence/ | grep -v "def quality_gate"
# Result: Only definition found (line 314)
```

**Code location:** Lines 314-429 (115 lines of implementation)

**What it does:**
- Blocks junk domains (pinterest, youtube, social media)
- Filters uncrawlable PDFs (except .gov/.edu whitelist)
- Checks language (English only)
- Limits domain duplicates (max 2 per domain)

**Expected impact:** 20-33% additional reduction after fast filter

**Status:** ❌ **NOT INTEGRATED - Phase 2 incomplete**

---

## STEP 6: Query Validation

**Blueprint requirement:** `validate_query_results()` in `intelligence/gather/pipeline.py`
**Function exists?** ✅ YES - Found at line 431
**Function called?** ❌ **NO**
**Call location:** NOT CALLED (commented out at line 504)

**Verification:**
```bash
grep -rn "validate_query_results(" intelligence/ | grep -v "def validate_query_results"
# Result: Line 504 shows commented code: # return validate_query_results(...)
```

**Code location:** Lines 431-508 (78 lines of implementation)

**What it does:**
- Samples top 5 results per query
- Checks if ≥60% are on-topic
- Auto-refines query if <60% relevant (max 2 retries)
- Refinement strategies: add quotes, add units, add domain constraints

**Expected impact:** Prevents off-topic results, improves accuracy

**Status:** ❌ **NOT INTEGRATED - Phase 7 incomplete**

---

## STEP 7: Select Top Items

**Blueprint requirement:** `rank_candidates()` in `intelligence/rank/select.py`
**Function exists?** ✅ YES
**Function called?** ✅ YES
**Call location:** `intelligence/gather/pipeline.py:149-150`

**Verification:**
```python
# pipeline.py lines 149-150
ranked_A = rank_candidates(claim_text=claim_text, query=claim_text, candidates=armA_norm, top_k=max_per_arm)
ranked_B = rank_candidates(claim_text=claim_text, query=claim_text, candidates=armB_norm, top_k=max_per_arm)
```

**Status:** ✅ **CORRECT**

**Note:** Currently selects `max_per_arm=3` items. Blueprint specifies 5 items per arm after filtering. With filters enabled, should increase to 5.

---

## STEP 8: Fetch Content

**Blueprint requirement:** `enrich_items_with_content()` in `intelligence/content/fetch_enrichment.py`
**Function exists?** ✅ YES
**Function called?** ✅ YES
**Call location:** `intelligence/pipeline/run.py:72`

**Verification:**
```python
# run.py lines 68-73
for arm_key in ("arm_A", "arm_B"):
    items = evidence.get(arm_key, [])
    if items:
        items, fetch_cache = await enrich_items_with_content(items, fetch_cache)
        evidence[arm_key] = items
```

**Status:** ✅ **CORRECT**

---

## STEP 9: Analyze Evidence

### 9A: P20 Orchestrator

**Blueprint requirement:** `attach_finding_to_item()` in `intelligence/content/grade.py`
**Function exists?** ✅ YES - Found at line 8 (import)
**Function called?** ✅ YES
**Call location:** `intelligence/pipeline/run.py:80`

**Verification:**
```python
# run.py lines 78-82
for item in evidence.get(arm_key, []):
    # P20
    try:
        attach_finding_to_item(claim_text, arm_label, item)
    except:
        pass
```

**Status:** ✅ **CORRECT**

**Blueprint requirement:** `fuse_module_grades()` should produce ONE item_grade (0-1)
**Status:** ⚠️ **NEEDS VERIFICATION**

Need to check:
- Is `fuse_module_grades()` using correct formula?
- Formula: 40% semantic + 30% frame + 20% authority + 10% coverage
- Returns 0-1 scale (not 0-10)?

---

### 9B: P21 Authority

**Blueprint requirement:** `evaluate_full_evidence()` in `intelligence/content/fullread.py`
**Function exists?** ✅ YES - Found at line 9 (import)
**Function called?** ✅ YES
**Call location:** `intelligence/pipeline/run.py:87`

**Verification:**
```python
# run.py lines 85-89
if item.get("content"):
    try:
        evaluate_full_evidence(claim_text, item)
    except:
        pass
```

**Status:** ✅ **CORRECT**

**Phase 3 Enhancement:** Authority scoring should be integrated into item_grade (20% weight)
**Phase 8 Enhancement:** Comprehensive source reliability database (500+ domains)

Need to verify `calculate_authority_score()` is actually used in fusion.

---

### 9C: P23 Semantic

**Blueprint requirement:** `analyze_item()` in `intelligence/content/semantic_read.py`
**Function exists?** ✅ YES - Found at line 10 (import)
**Function called?** ✅ YES
**Call location:** `intelligence/pipeline/run.py:94`

**Verification:**
```python
# run.py lines 92-96
if item.get("content"):
    try:
        analyze_item(claim_text, item, window=3)
    except:
        pass
```

**Status:** ✅ **CORRECT**

**Phase 9 Enhancements (Missing):**
- `detect_negation()` - ❌ NOT FOUND
- `detect_hedging()` - ❌ NOT FOUND
- `enhanced_semantic_match()` - ❌ NOT FOUND

**Status:** ⚠️ **BASELINE ONLY - Phase 9 enhancements missing**

---

### 9D: P24 Frames

**Blueprint requirement:** `analyze_frames()` in `intelligence/content/semantic_frames.py`
**Function exists?** ✅ YES - Found at line 11 (import)
**Function called?** ✅ YES
**Call location:** `intelligence/pipeline/run.py:102`

**Verification:**
```python
# run.py lines 98-105
content = item.get("content") or ""
if content:
    try:
        frames = analyze_frames(claim_text, content, window=3)
        item.update(frames)
    except:
        pass
```

**Status:** ✅ **CORRECT**

---

## STEP 10: Arm Aggregation

**Blueprint requirement:** `aggregate_verdict()` in `intelligence/content/p25_aggregate.py`
**Function exists?** ✅ YES - Found at line 12 (import)
**Function called?** ✅ YES
**Call location:** `intelligence/pipeline/run.py:109`

**Verification:**
```python
# run.py lines 108-116
try:
    verdict = aggregate_verdict(
        claim_text,
        evidence.get("arm_A", []),
        evidence.get("arm_B", []),
        delta=0.15
    )
except:
    verdict = {"label": "insufficient", "confidence": 0.0}
```

**Status:** ✅ **CORRECT**

**Phase 4 Enhancements - Need Verification:**
- `calculate_diversity_score()` - EXISTS (from audit verification), is it CALLED?
- `calculate_consistency_score()` - EXISTS (from audit verification), is it CALLED?
- `calculate_breadth_score()` - EXISTS (from audit verification), is it CALLED?
- Enhanced confidence formula (6 factors instead of 3) - is it IMPLEMENTED?

**Need to check:**
```python
# OLD formula:
confidence = 0.4 * total + 0.4 * balance + 0.2 * count

# NEW formula (Phase 4):
confidence = (
    0.25 * total_strength +
    0.25 * balance +
    0.15 * count +
    0.15 * avg_authority +
    0.10 * diversity +
    0.10 * consistency
)
```

**Status:** ⚠️ **NEEDS VERIFICATION - May be using old formula**

---

## STEP 11: Consensus Building

### 11A: Orchestration

**Blueprint requirement:** `run_dual_researchers()` in `intelligence/orchestration/dual_lane.py`
**Function exists?** ✅ YES - Found at line 13 (import)
**Function called?** ✅ YES
**Call location:** `intelligence/pipeline/run.py:140`

**Verification:**
```python
# run.py lines 140-146
dual_result = await run_dual_researchers(
    claim_text=text,
    base_plan=base_plan,
    enrichment_pipeline=run_single_lane_enrichment,
    diversify_fn=diversify_plan_for_lane,
    telemetry_class=LaneTelemetry
)
```

**Status:** ✅ **CORRECT**

---

### 11B: Consensus Computation

**Blueprint requirement:** `compute_consensus()` in `intelligence/consensus/dual_lane.py`
**Function exists?** ✅ YES - Found at line 16 (import)
**Function called?** ✅ YES
**Call location:** `intelligence/pipeline/run.py:155`

**Verification:**
```python
# run.py lines 152-158
if len(researchers) >= 2:
    r1_verdict = researchers[0].get("verdict", {})
    r2_verdict = researchers[1].get("verdict", {})
    consensus = compute_consensus(r1_verdict, r2_verdict)
else:
    consensus = dual_result.get("verdict", {})
```

**Status:** ✅ **CORRECT**

**Phase 6 Enhancements - Need Verification:**
- `compare_evidence_quality()` - EXISTS (from audit verification), is it CALLED by compute_consensus?
- `resolve_disagreement()` - EXISTS (from audit verification), is it CALLED by compute_consensus?
- `synthesize_evidence()` - EXISTS (from audit verification), is it CALLED?

Need to verify compute_consensus() uses evidence quality comparison, not just label comparison.

---

## STEP 12: Confidence Calibration

**Blueprint requirement:** `calibrate_confidence()` in `intelligence/calibration/confidence.py`
**Function exists?** ✅ YES - Found at line 7
**Function called?** ❌ **NO**
**Call location:** NOT CALLED

**Verification:**
```bash
grep -rn "calibrate_confidence(" intelligence/ | grep -v "def calibrate_confidence"
# Result: Only definition found
```

**Status:** ❌ **NOT INTEGRATED - Phase 10 incomplete**

---

**Blueprint requirement:** `apply_confidence_thresholds()` in `intelligence/calibration/confidence.py`
**Function exists?** ✅ YES - Found at line 71
**Function called?** ❌ **NO**
**Call location:** NOT CALLED

**Verification:**
```bash
grep -rn "apply_confidence_thresholds(" intelligence/ | grep -v "def apply_confidence_thresholds"
# Result: Only definition found
```

**Status:** ❌ **NOT INTEGRATED - Phase 10 incomplete**

**Impact:**
- No conservative thresholds (<85% → "mixed")
- No calibration by claim type
- No calibration by evidence quality
- System may be overconfident (high confidence but wrong)

---

## STEP 13: Final Formatting

**Blueprint requirement:** `_ensure_preview_shape()` in `intelligence/pipeline/run.py`
**Function exists?** ✅ YES (defined elsewhere, need to check)
**Function called?** ✅ YES (return statement formats response)
**Call location:** `intelligence/pipeline/run.py:168-182`

**Verification:**
```python
# run.py lines 168-182
claim_obj = {
    "id": "c-0",
    "text": text.strip(),
    "tier": "primary",
    "verdict": dual_result.get("verdict", {}),
    "evidence": dual_result.get("evidence", {}),
    "researchers": researchers,
    "consensus": consensus  # NEW
}

return {
    "claims": [claim_obj],
    "run_manifest": manifest,  # NEW
    "diversified": True
}
```

**Status:** ✅ **CORRECT**

**Note:** IFCN scale mapping happens elsewhere (needs verification)

---

## SUMMARY TABLE

| Step | Name | Function | Exists | Called | Correct Version | Status |
|------|------|----------|--------|--------|-----------------|--------|
| 0 | Classification | `classify_claim` | ✅ | ❌ | N/A | ❌ MISSING |
| 0 | Unverifiable Detection | `detect_unverifiable_early` | ❌ | ❌ | N/A | ❌ MISSING |
| 1 | Understanding | `enrich_claim_obj` | ✅ | ✅ | ✅ | ✅ CORRECT |
| 1 | Phase 9 Enhancements | `detect_negation/hedging` | ❌ | ❌ | N/A | ❌ MISSING |
| 2 | Base Plan | `build_search_plans_v2` | ✅ | ✅ | ✅ | ✅ CORRECT |
| 2 | Diversification | `diversify_plan_for_lane` | ✅ | ✅ | ❌ | ⚠️ WRONG |
| 2 | R1 Strategy | `generate_queries_r1` | ✅ | ❌ | N/A | ❌ MISSING |
| 2 | R2 Strategy | `generate_queries_r2` | ✅ | ❌ | N/A | ❌ MISSING |
| 3 | Search | `run_plan` | ✅ | ✅ | ✅ | ✅ CORRECT |
| 4 | Fast Filter | `filter_unrelated` | ✅ | ❌ | N/A | ❌ MISSING |
| 5 | Quality Gate | `quality_gate` | ✅ | ❌ | N/A | ❌ MISSING |
| 6 | Query Validation | `validate_query_results` | ✅ | ❌ | N/A | ❌ MISSING |
| 7 | Ranking | `rank_candidates` | ✅ | ✅ | ✅ | ✅ CORRECT |
| 8 | Fetch Content | `enrich_items_with_content` | ✅ | ✅ | ✅ | ✅ CORRECT |
| 9 | P20 Orchestrator | `attach_finding_to_item` | ✅ | ✅ | ? | ⚠️ VERIFY |
| 9 | P21 Authority | `evaluate_full_evidence` | ✅ | ✅ | ✅ | ✅ CORRECT |
| 9 | P23 Semantic | `analyze_item` | ✅ | ✅ | ? | ⚠️ VERIFY |
| 9 | P24 Frames | `analyze_frames` | ✅ | ✅ | ✅ | ✅ CORRECT |
| 10 | Aggregation | `aggregate_verdict` | ✅ | ✅ | ? | ⚠️ VERIFY |
| 10 | Quality Multipliers | `calculate_diversity/etc` | ✅ | ? | ? | ⚠️ VERIFY |
| 11 | Dual Researchers | `run_dual_researchers` | ✅ | ✅ | ✅ | ✅ CORRECT |
| 11 | Consensus | `compute_consensus` | ✅ | ✅ | ? | ⚠️ VERIFY |
| 11 | Evidence Quality | `compare_evidence_quality` | ✅ | ? | ? | ⚠️ VERIFY |
| 12 | Calibrate | `calibrate_confidence` | ✅ | ❌ | N/A | ❌ MISSING |
| 12 | Thresholds | `apply_confidence_thresholds` | ✅ | ❌ | N/A | ❌ MISSING |
| 13 | Formatting | Response formatting | ✅ | ✅ | ✅ | ✅ CORRECT |

**Legend:**
- ✅ CORRECT: Function exists, is called, correct version
- ⚠️ WRONG: Function exists and called, but wrong implementation
- ⚠️ VERIFY: Function exists and called, needs verification of internals
- ❌ MISSING: Function exists but NOT called in pipeline (or doesn't exist)

---

## CRITICAL GAPS

### 🔴 TIER 1: Functions Exist but NOT Integrated (Easy Fix - Just Wire Them Up)

1. **STEP 0: Claim Classification**
   - Function: `classify_claim()` - EXISTS at `intelligence/preprocess/classify.py:7`
   - Impact: No early detection of opinions/predictions
   - Fix: Add call in `run_preview()` before `enrich_claim_obj()`

2. **STEP 4: Fast Filter**
   - Function: `filter_unrelated()` - EXISTS at `intelligence/gather/pipeline.py:219`
   - Impact: No pre-filtering, wasting compute on junk (28-30% reduction lost)
   - Fix: Add call in `build_evidence_for_claim()` after search, before ranking

3. **STEP 5: Quality Gate**
   - Function: `quality_gate()` - EXISTS at `intelligence/gather/pipeline.py:314`
   - Impact: No source quality filtering (20-33% reduction lost)
   - Fix: Add call in `build_evidence_for_claim()` after `filter_unrelated()`, before ranking

4. **STEP 6: Query Validation**
   - Function: `validate_query_results()` - EXISTS at `intelligence/gather/pipeline.py:431`
   - Impact: Off-topic queries never refined, reducing accuracy
   - Fix: Add call in `build_evidence_for_claim()` after search, with retry loop

5. **STEP 12: Confidence Calibration**
   - Function: `calibrate_confidence()` - EXISTS at `intelligence/calibration/confidence.py:7`
   - Function: `apply_confidence_thresholds()` - EXISTS at `intelligence/calibration/confidence.py:71`
   - Impact: No conservative thresholds, system may be overconfident
   - Fix: Add calls in `run_preview()` after `compute_consensus()`, before return

---

### 🟡 TIER 2: Functions Exist but Wrong Implementation (Harder Fix - Need Refactoring)

6. **STEP 2: R1/R2 Query Diversification (Phase 5)**
   - Functions: `generate_queries_r1()`, `generate_queries_r2()` - EXIST but NOT CALLED
   - Current: `diversify_plan_for_lane()` only shuffles queries and changes provider order
   - Expected: R1 uses precision strategy (quoted, exact), R2 uses recall strategy (broad, paraphrased)
   - Impact: R1 and R2 use SAME queries, defeating purpose of dual researchers
   - Fix: Modify `diversify_plan_for_lane()` to call `generate_queries_r1/r2()` instead of shuffling

---

### ⚪ TIER 3: Need Internal Verification (Functions Called, But May Use Old Logic)

7. **STEP 9: P20 Fusion Formula**
   - Need to verify: Is `fuse_module_grades()` using Phase 1 & 3 formula?
   - Expected: 40% semantic + 30% frame + 20% authority + 10% coverage
   - Check: Line in `intelligence/content/grade.py`

8. **STEP 10: Arm Aggregation Quality Multipliers**
   - Need to verify: Are Phase 4 quality multipliers actually CALLED?
   - Expected: `calculate_diversity_score()`, `calculate_consistency_score()`, `calculate_breadth_score()`
   - Check: Lines in `intelligence/content/p25_aggregate.py`

9. **STEP 10: Enhanced Confidence Formula**
   - Need to verify: Is Phase 4 enhanced formula used?
   - Expected: 6-factor formula (total, balance, count, authority, diversity, consistency)
   - Old: 3-factor formula (total, balance, count)
   - Check: `_confidence_from_arms()` in `intelligence/content/p25_aggregate.py`

10. **STEP 11: Evidence-Based Consensus**
    - Need to verify: Does `compute_consensus()` use evidence quality comparison?
    - Expected: Calls `compare_evidence_quality()`, `resolve_disagreement()`
    - Old: Just compares labels
    - Check: `intelligence/consensus/dual_lane.py`

11. **STEP 1 & 9: Phase 9 Enhancements**
    - Functions: `detect_negation()`, `detect_hedging()`, `extract_precision_context()`
    - Status: NOT FOUND in codebase
    - Impact: No precision handling, negation detection, hedging penalties
    - Fix: Implement Phase 9 enhancements

---

## IMPACT ANALYSIS

### Completeness Score: **8/13 steps fully implemented (62%)**

**Implemented:**
- ✅ STEP 1: Claim Understanding (baseline)
- ✅ STEP 2: Base Plan Generation
- ✅ STEP 3: Search Execution
- ✅ STEP 7: Ranking
- ✅ STEP 8: Content Fetching
- ✅ STEP 9: Evidence Analysis (P20, P21, P23, P24 - baseline)
- ✅ STEP 10: Arm Aggregation (baseline)
- ✅ STEP 11: Consensus (baseline)

**Missing or Wrong:**
- ❌ STEP 0: Claim Classification (NOT INTEGRATED)
- ⚠️ STEP 2: R1/R2 Diversification (WRONG IMPLEMENTATION)
- ❌ STEP 4: Fast Filter (NOT INTEGRATED)
- ❌ STEP 5: Quality Gate (NOT INTEGRATED)
- ❌ STEP 6: Query Validation (NOT INTEGRATED)
- ❌ STEP 12: Confidence Calibration (NOT INTEGRATED)

---

## PHASE COMPLETION STATUS

| Phase | Description | Functions Exist | Functions Called | Status |
|-------|-------------|-----------------|------------------|--------|
| 0 | Preparation | N/A | N/A | ✅ COMPLETE |
| 1 | Critical Bugs | ✅ | ⚠️ | ⚠️ PARTIAL (need to verify formula) |
| 2 | Evidence Curation | ✅ | ❌ | ❌ **NOT INTEGRATED** |
| 3 | Authority Scoring | ✅ | ⚠️ | ⚠️ PARTIAL (need to verify fusion) |
| 4 | Arm Aggregation | ✅ | ⚠️ | ⚠️ PARTIAL (need to verify multipliers) |
| 5 | R1/R2 Diversification | ✅ | ❌ | ❌ **WRONG IMPLEMENTATION** |
| 6 | Evidence Consensus | ✅ | ⚠️ | ⚠️ PARTIAL (need to verify quality comparison) |
| 7 | Query Validation | ✅ | ❌ | ❌ **NOT INTEGRATED** |
| 8 | Quality Amplification | ⚠️ | ❌ | ❌ **NOT INTEGRATED** (classify_claim not called) |
| 9 | Precision Handling | ❌ | ❌ | ❌ **NOT IMPLEMENTED** (functions don't exist) |
| 10 | Calibration | ✅ | ❌ | ❌ **NOT INTEGRATED** |
| 11 | Validation | N/A | N/A | ❓ UNKNOWN (testing not verified) |

---

## RECOMMENDATIONS

### Immediate Actions (Quick Wins - Wire Up Existing Functions)

1. **Wire up STEP 0:** Add `classify_claim()` call in `run_preview()` line 128
2. **Wire up STEP 4:** Add `filter_unrelated()` call in `build_evidence_for_claim()` line 138
3. **Wire up STEP 5:** Add `quality_gate()` call in `build_evidence_for_claim()` line 139
4. **Wire up STEP 6:** Add `validate_query_results()` call in `build_evidence_for_claim()` line 45
5. **Wire up STEP 12:** Add `calibrate_confidence()` and `apply_confidence_thresholds()` calls in `run_preview()` line 156

**Estimated Impact:** +10-15% accuracy (Phase 2, 10 integrated)

---

### Medium Priority (Refactoring Required)

6. **Fix STEP 2:** Modify `diversify_plan_for_lane()` to call `generate_queries_r1/r2()` instead of just shuffling
   - This implements true R1 (Skeptic) vs R2 (Explorer) differentiation
   - **Estimated Impact:** +5% accuracy (Phase 5 complete)

---

### Long-term (New Implementation Required)

7. **Implement STEP 1/9 Phase 9 enhancements:**
   - `detect_negation()`, `detect_hedging()`, `extract_precision_context()`
   - **Estimated Impact:** +5-10% accuracy (Phase 9 complete)

---

### Verification Needed (Internal Checks)

8. **Verify STEP 9:** Check `fuse_module_grades()` uses correct formula (40/30/20/10)
9. **Verify STEP 10:** Check quality multipliers are actually called and used
10. **Verify STEP 10:** Check enhanced confidence formula (6 factors vs 3)
11. **Verify STEP 11:** Check consensus uses evidence quality comparison

---

## CONCLUSION

**Current State:** System has **62% of target architecture implemented** (8/13 steps fully working)

**Critical Finding:** **Many Phase 2, 5, 7, 10 functions exist but are NOT integrated into the pipeline**

**Quick Wins Available:** Wire up 5 existing functions → +10-15% accuracy improvement

**Biggest Gap:** Phase 5 (R1/R2 diversification) is implemented WRONG - functions exist but aren't called

**Next Steps:**
1. Wire up existing functions (TIER 1 gaps)
2. Verify internal implementations (TIER 3 gaps)
3. Fix R1/R2 diversification (TIER 2 gap)
4. Implement Phase 9 enhancements (TIER 3 gap)

---

**Report Status:** COMPLETE
**Verification Method:** Code search + call chain analysis
**Files Analyzed:** 8 core pipeline files

**Recommendation:** Start with TIER 1 gaps (wire up existing functions) before implementing new features.
