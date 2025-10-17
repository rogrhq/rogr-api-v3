# BEFORE STATE: Monkey Patch Wrapper Analysis

**Date:** 2025-10-13
**Purpose:** Document what existed in monkey patch wrappers before Phase 1 cleanup

## CRITICAL FINDING

🔍 **ALL WRAPPERS WERE PURE ORCHESTRATION CODE**

- ✅ No semantic logic was contained in wrapper files
- ✅ All semantic logic was in clean modules (which still exist)
- ✅ Wrappers only handled: pipeline integration, async/sync detection, error handling, diagnostics

**Implication:** Phase 1 cleanup did NOT lose semantic logic. Any "missing" capabilities were never implemented.

---

## P20 Wrapper Analysis

**File:** `MONKEY_PATCH_ARCHIVE/wrappers/content/p20_wrapper.py`
**Lines:** 228

### A. FUNCTIONS WRAPPED
- **Target:** `intelligence.gather.pipeline.build_evidence_for_claim`
- **Method:** Async/sync wrapper with pipeline replacement

### B. SEMANTIC LOGIC CONTAINED
**❌ NONE** - Pure orchestration wrapper

### C. WRAPPER RESPONSIBILITIES
1. **Call delegation** (Line 50): `attach_finding_to_item(claim_text, arm_key, it)`
2. **Claim text extraction** (Lines 61-91): Heuristic parsing from various argument structures
3. **Arm detection** (Lines 93-119): Handle both `arm_A` and `A` key aliases
4. **List/dict shape handling** (Lines 93-134): Support both evidence[key] -> list and evidence[key] -> {candidates: list}
5. **Error handling** (Lines 54-57): Catch and log errors without breaking pipeline
6. **Diagnostics** (Lines 29-37): Optional ROGR_DIAG_P20 logging

### D. SEMANTIC LOGIC LOCATION
**All semantic logic** is in: `intelligence/content/grade.py`
- Function called: `attach_finding_to_item(claim_text, arm, item)`
- This function contains: stance detection, grading, rationale, span matching

---

## P21 Wrapper Analysis

**File:** `MONKEY_PATCH_ARCHIVE/wrappers/content/p21_wrapper.py`
**Lines:** 145

### A. FUNCTIONS WRAPPED
- **Target:** `intelligence.gather.pipeline.build_evidence_for_claim`
- **Method:** Async/sync wrapper (installed AFTER P20)

### B. SEMANTIC LOGIC CONTAINED
**❌ NONE** - Pure orchestration wrapper

### C. WRAPPER RESPONSIBILITIES
1. **Call delegation** (Line 83, 115): `evaluate_full_evidence(claim_text, it)`
2. **Claim text extraction** (Lines 70-72, 102-104): Simple kwargs/args parsing
3. **Arm iteration** (Lines 75-91, 107-123): Process arm_A, A, arm_B, B
4. **List/dict shape handling** (Lines 29-65): Support both list and dict-with-candidates shapes
5. **Result verification** (Lines 84, 116): Check for `grade_full` and `stance_full` fields
6. **Error handling & diagnostics** (Lines 87-91, 119-123)

### D. SEMANTIC LOGIC LOCATION
**All semantic logic** is in: `intelligence/content/fullread.py`
- Function called: `evaluate_full_evidence(claim_text, item)`
- This function contains: window-based semantic reading, stance detection, grading

---

## P23 Wrapper Analysis

**File:** `MONKEY_PATCH_ARCHIVE/wrappers/content/p23_semantic.py`
**Lines:** 94

### A. FUNCTIONS WRAPPED
- **Target:** `intelligence.pipeline.run.run_preview`
- **Method:** Async wrapper on preview endpoint (runs after P22)

### B. SEMANTIC LOGIC CONTAINED
**❌ NONE** - Pure orchestration wrapper

### C. WRAPPER RESPONSIBILITIES
1. **Call delegation** (Line 42): `analyze_item(claim_text, it)`
2. **Relative import** (Line 16): `from .semantic_read import analyze_item`
3. **Claims iteration** (Lines 34-47): Process all claims in preview result
4. **Arm processing** (Lines 37-45): Handle arm_A and arm_B
5. **Error handling** (Lines 49-50)

### D. SEMANTIC LOGIC LOCATION
**All semantic logic** is in: `intelligence/content/semantic_read.py`
- Function called: `analyze_item(claim_text, item)`
- This function contains: semantic findings, quote extraction, stance signals, grading

**KEY INSIGHT:** Wrapper imports from `.semantic_read`, meaning `semantic_read.py` was a SIBLING module in the same package. This clean module still exists today.

---

## P24 Wrapper Analysis

**File:** `MONKEY_PATCH_ARCHIVE/wrappers/content/p24_semantic_frames.py`
**Lines:** 106

### A. FUNCTIONS WRAPPED
- **Target:** `intelligence.pipeline.run.run_preview`
- **Method:** Async wrapper (runs after P22/P23)

### B. SEMANTIC LOGIC CONTAINED
**❌ NONE** - Pure orchestration wrapper

### C. WRAPPER RESPONSIBILITIES
1. **Call delegation** (Line 46): `analyze_frames(claim_text, content, window=3)`
2. **Relative import** (Line 17): `from .semantic_frames import analyze_frames`
3. **Content extraction** (Line 44): Get content or content_excerpt
4. **Empty structure fallback** (Lines 49-52): Attach empty frame structures if no content
5. **Claims/arms iteration** (Lines 34-56)

### D. SEMANTIC LOGIC LOCATION
**All semantic logic** is in: `intelligence/content/semantic_frames.py`
- Function called: `analyze_frames(claim_text, content, window=3)`
- This function contains: frame extraction, entity detection, action detection, quantity/year extraction, entailment detection

---

## P25 Wrapper Analysis

**File:** `MONKEY_PATCH_ARCHIVE/wrappers/content/p25_semantic_aggregate.py`
**Lines:** 90

### A. FUNCTIONS WRAPPED
- **Target:** `intelligence.pipeline.run.run_preview`
- **Method:** Async wrapper (runs after P22/P23/P24)

### B. SEMANTIC LOGIC CONTAINED
**❌ NONE** - Pure orchestration wrapper

### C. WRAPPER RESPONSIBILITIES
1. **Call delegation** (Line 38): `aggregate_verdict(claim_text, A, B, delta=0.15)`
2. **Relative import** (Line 14): `from .p25_aggregate import aggregate_verdict`
3. **Verdict merging** (Lines 39-45): Preserve existing fields, overwrite label/confidence/arm_strength
4. **Claims iteration** (Lines 32-46)

### D. SEMANTIC LOGIC LOCATION
**All semantic logic** is in: `intelligence/content/p25_aggregate.py`
- Function called: `aggregate_verdict(claim_text, A, B, delta=0.15)`
- This function contains: arm strength calculation, verdict determination

---

## P22 Ingest Wrapper

**Note:** P22 wrapper not analyzed in detail as it's primarily fetch/enrichment orchestration, not semantic logic.

---

## WRAPPER ARCHITECTURE SUMMARY

### Pattern: All Wrappers Follow Same Design

```
┌─────────────────────────────────────┐
│  Monkey Patch Wrapper               │
│  (Pure Orchestration)               │
│                                     │
│  • Wrap pipeline function           │
│  • Extract arguments                │
│  • Call clean module function   ────┼─────┐
│  • Handle errors                    │     │
│  • Add diagnostics                  │     │
└─────────────────────────────────────┘     │
                                            │
                                            ▼
                                ┌───────────────────────────┐
                                │  Clean Module             │
                                │  (Contains ALL Logic)     │
                                │                           │
                                │  • Semantic analysis      │
                                │  • Grading                │
                                │  • Stance detection       │
                                │  • Frame extraction       │
                                │  • Entity recognition     │
                                │  • etc.                   │
                                └───────────────────────────┘
```

### Clean Module Mapping

| Wrapper | Calls Function | From Clean Module |
|---------|---------------|-------------------|
| P20 | `attach_finding_to_item()` | `intelligence/content/grade.py` |
| P21 | `evaluate_full_evidence()` | `intelligence/content/fullread.py` |
| P23 | `analyze_item()` | `intelligence/content/semantic_read.py` |
| P24 | `analyze_frames()` | `intelligence/content/semantic_frames.py` |
| P25 | `aggregate_verdict()` | `intelligence/content/p25_aggregate.py` |

---

## PHASE 1 CLEANUP IMPACT

### What Was Removed
✅ Pure orchestration code (wrappers)
✅ Pipeline monkey-patching
✅ Async/sync detection boilerplate
✅ Diagnostic logging

### What Was Preserved
✅ **ALL semantic logic** (in clean modules)
✅ All algorithms
✅ All intelligence capabilities
✅ All function APIs

### Conclusion

**NO SEMANTIC LOGIC WAS LOST IN PHASE 1 CLEANUP**

The wrappers were infrastructure code only. All semantic intelligence that existed before Phase 1 still exists after Phase 1 in the clean modules.

Any "gaps" in semantic capabilities are:
1. **Never implemented** (not lost)
2. **Documented limitations** of existing clean modules
3. **Targets for Phase 2 enhancement** (not restoration)

---

## NEXT STEP

Analyze clean modules to document:
- What semantic logic EXISTS
- What capabilities are WORKING
- What features are DOCUMENTED AS MISSING
- What Phase 2 needs to BUILD (not restore)
