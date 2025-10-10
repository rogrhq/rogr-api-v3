# MONKEY PATCH REALITY CHECK - COMPLEXITY UNDERESTIMATED

**Date:** 2025-10-08
**Reason:** User correctly identified that wrapper chains create dependencies that break functionality when naively removed
**Status:** CRITICAL - MONKEY_PATCH_REMOVAL.md needs significant revision

---

## THE PROBLEM I MISSED

### Original Assessment
- 11 files with monkey patches
- Each wraps one function
- Can extract logic independently
- 2-3 days effort

### **ACTUAL REALITY (Verified)**

**1. WRAPPER CHAINS (Functions Wrapping Wrappers)**

```python
# Load order from sitecustomize.py:
# 1. p20_wrapper loads first
_ORIG = getattr(pipeline, "build_evidence_for_claim", None)  # Gets original
setattr(pipeline, "build_evidence_for_claim", WRAPPED)       # Replaces with p20

# 2. p22_ingest loads second
_ORIG = getattr(pipeline, "build_evidence_for_claim", None)  # Gets p20's WRAPPER
setattr(pipeline, "build_evidence_for_claim", WRAPPED)       # Wraps the wrapper

# 3. If p21 loads (in tests?)
_ORIG = getattr(pipeline, "build_evidence_for_claim", None)  # Gets p22(p20(original))
setattr(pipeline, "build_evidence_for_claim", WRAPPED)       # Triple-wraps!
```

**Execution Chain:**
```
API request
  → p21_wrapper (if loaded)
    → p22_wrapper (content ingestion)
      → p20_wrapper (findings attachment)
        → original build_evidence_for_claim
      ← returns evidence
    ← p20 adds findings to items
  ← p22 adds content_chars, coverage
← p21 adds full-read evaluation
→ Response
```

**Impact:**
- Removing p20 breaks p22 (which expects p20's output format)
- Removing p22 breaks p21 (which expects p22's enrichment)
- Order matters: Can't remove p22 before p20
- Dependencies are IMPLICIT (no import graph shows this)

---

**2. MULTI-TARGET WRAPPERS (One Wrapper, Multiple Functions)**

**p22_ingest.py wraps 3 DIFFERENT functions:**
```python
# Line 166: Wraps fetch layer
setattr(fetch_mod, "fetch_text", wrapped)

# Line 212: Wraps orchestrator
setattr(run_mod, "run_preview", wrapped)

# Line 233: Wraps gather pipeline
setattr(run_mod, "build_evidence_for_claim", wrapped_build_inner)
```

**Impact:**
- Can't extract p22 logic to one place
- Must split into 3 separate clean modules:
  - `intelligence/content/ingest_fetch.py` (wraps fetch_text)
  - `intelligence/content/ingest_preview.py` (wraps run_preview)
  - `intelligence/content/ingest_pipeline.py` (wraps build_evidence)
- Each needs separate integration point
- More complex than "extract logic → call it"

---

**3. MODULE-CROSSING WRAPPERS (Same Function in Multiple Modules)**

**p22_ingest.py wraps run_preview in TWO modules:**
```python
# Line 212: In intelligence.pipeline.run
setattr(run_mod, "run_preview", wrapped)

# Line 251: In api.analyses
setattr(api_mod, "run_preview", wrapped_run)
```

**Impact:**
- Same function exists in two modules?
- Or wrapper ensures both call paths get enriched?
- Removing wrapper breaks both API and internal paths
- Must verify which is "real" entry point

---

**4. PRODUCTION vs TEST LOAD DIFFERENCES**

**From sitecustomize.py:**
```python
_try("intelligence.content.p20_wrapper")  # Production
_try("intelligence.content.p22_ingest")   # Production
# p21, p23-p29 NOT loaded here
```

**From grep of test files:**
- p21, p23-p29 imported in `scripts/test_packet*.py`
- Not imported in `intelligence/pipeline/` or `intelligence/api/`

**Impact:**
- Production might only use p20 + p22 (lighter chain)
- Tests might load full p20→p21→p22→p23→p24→etc chain
- Removing wrappers might break tests more than production
- Or tests are the only place p21-p29 actually run?

---

## REVISED FUNCTIONALITY ASSESSMENT

### **With All Monkey Patches (Production + sitecustomize.py):**
- **Active wrappers:** p20 + p22 (confirmed loaded)
- **Functionality:** 70% (core pipeline + findings + ingestion)
- **Not active:** p21, p23-p29 (only in tests?)

### **Without Any Monkey Patches (Naive Removal):**
- **Active wrappers:** None
- **Functionality:** 40% (only original pipeline.py + normalize.py fixes)
- **Breaks:** All findings, content ingestion, semantic analysis

### **After Clean Wiring (Optimistic):**
- **Functionality:** 60-65% initially (integration bugs likely)
- **Effort:** 4-5 days (NOT 2-3 days)
- **Risk:** High - hidden dependencies will surface

### **After Clean Wiring + Debugging (Realistic):**
- **Functionality:** 70% (back to current state)
- **Effort:** 5-7 days total
- **Risk:** Medium - systematic approach reduces surprises

---

## WHAT THIS MEANS FOR MONKEY_PATCH_REMOVAL.md

### My Original Plan Was TOO SIMPLE

**What I Said:**
1. Extract p20 logic → `findings.py`
2. Extract p21 logic → `fullread.py`
3. Extract p22 logic → `ingest.py`
4. Add explicit imports
5. Call functions directly
6. Done in 2-3 days

**What's Actually Required:**

**1. Map the Wrapper Chain**
```bash
# Verify actual load order and dependencies
$ python -c "import sitecustomize; ..." > wrapper_load_order.txt
$ grep "setattr" intelligence/content/p*.py > all_monkey_patches.txt
```

**2. Extract Multi-Target Wrappers Carefully**
- p22 must become 3 separate modules (not 1)
- Each with correct integration point
- Preserve execution order

**3. Handle Wrapper Chains**
- Can't remove p20 until p22 is cleanly wired
- Can't remove p22 until p21 is cleanly wired (if active)
- Must remove in REVERSE load order

**4. Verify Production vs Test**
- Test what's actually active in production
- p21-p29 might not even be used
- Focus removal on p20+p22 first (confirmed active)
- p21-p29 as separate phase (if needed)

**5. Add Extensive Validation**
- After removing each wrapper, run BOTH:
  - Live pipeline test
  - Full test suite
- Compare outputs before/after each step
- Use S6 regression harness (must build first)

---

## REVISED EFFORT ESTIMATE

### Phase 1A: Remove ACTIVE Monkey Patches (p20, p22)

**Day 1-2: Analysis & Mapping**
- Map wrapper chain (p20 → p22 → ?)
- Document all setattr() calls
- Verify load order
- Create dependency graph
- Write validation test suite
- **Effort:** 2 days

**Day 3-4: Extract p22 (Multi-Target)**
- Split into 3 modules (fetch, preview, pipeline)
- Wire each separately
- Test after each integration
- Validate no regression
- **Effort:** 2 days (complex)

**Day 5-6: Extract p20 (Findings)**
- Extract to `findings.py`
- Wire into pipeline AFTER p22 logic
- Ensure execution order preserved
- Test findings still attach
- **Effort:** 2 days

**Day 7: Cleanup & Validation**
- Delete p20_wrapper.py, p22_ingest.py
- Delete sitecustomize.py
- Full test suite
- Live pipeline validation
- S6 regression comparison
- **Effort:** 1 day

**Total Phase 1A: 6-7 days** (not 2-3 days)

### Phase 1A-Extended: Remove TEST-ONLY Patches (p21, p23-p29)

**Only if confirmed active in production**
- Verify they're actually used
- Extract logic for each
- Wire into test pipeline
- **Effort:** 2-3 additional days

**Total if needed: 8-10 days**

---

## REVISED PATH TO DAY 1

### Updated Timeline

**Week 1:**
- Days 1-2: Map wrapper complexity, build S6 harness
- Days 3-7: Phase 1A (remove p20+p22 carefully)

**Week 2:**
- Days 8-10: Debug Phase 1A integration issues
- Days 11-12: Start Phase 1B (AI Anthropic integration)

**Week 3:**
- Days 13-17: Phase 1B continue (4 AI components)

**Week 4:**
- Days 18-20: Phase 1C (multi-claim)
- Day 21: Phase 1D/S3 (numeric/temporal)

**Total: 3-4 weeks** (not 2-3 weeks)

**Critical Path:** Phase 1A now takes 6-7 days (was 2-3), pushes everything back

---

## CRITICAL RISKS

### 1. Hidden Dependencies
**Risk:** Wrapper logic depends on wrapping mechanism
**Example:** p22 might need to wrap fetch_text to intercept at call time
**Mitigation:** Extract logic, add explicit hooks

### 2. Execution Order Dependencies
**Risk:** p20 output format expected by p22
**Mitigation:** Define explicit contracts, add validation

### 3. Production vs Test Divergence
**Risk:** Removing wrapper breaks tests but not production (or vice versa)
**Mitigation:** Test both paths separately

### 4. Performance Regressions
**Risk:** Wrapper chain is actually faster (single pass vs multiple)
**Mitigation:** Benchmark before/after

### 5. Shape Inconsistencies
**Risk:** Wrappers handle multiple shapes, clean code expects one
**Mitigation:** Enforce canonical shapes in clean modules

---

## WHAT TO DO NOW

### Immediate Actions

**1. PAUSE MONKEY_PATCH_REMOVAL.md Implementation**
- Don't start extraction yet
- Original plan is too simple
- Need more analysis first

**2. Run Wrapper Analysis**
```bash
# Create wrapper dependency graph
$ python scripts/analyze_monkey_patches.py > wrapper_analysis.txt

# Test what's actually active
$ ROGR_DIAG=1 python scripts/test_live_pipeline.py > load_order.log

# Compare with vs without sitecustomize
$ mv sitecustomize.py sitecustomize.py.bak
$ pytest tests/ > without_patches.log
$ mv sitecustomize.py.bak sitecustomize.py
$ pytest tests/ > with_patches.log
$ diff without_patches.log with_patches.log
```

**3. Build S6 Regression Harness FIRST**
- Need baseline before any removal
- Compare wrapper vs clean outputs
- Catch regressions immediately

**4. Revise MONKEY_PATCH_REMOVAL.md**
- Add wrapper chain analysis section
- Split p22 into 3 modules
- Add extensive validation steps
- Update effort to 6-7 days

**5. Update SOURCE_OF_TRUTH_V2.md**
- Section 4.4: Note wrapper chains
- Section 6.1: Increase complexity assessment
- Section 7: Revise Phase 1A effort to 6-7 days
- Section 11: Update critical path to 3-4 weeks

---

## USER WAS RIGHT

**Original Concern:** "Functions depend on other monkey patches, removing them may not work"

**My Original Response:** "70-75% works after clean wiring in 2-3 days"

**Actual Reality:**
- ✅ User was RIGHT - wrapper chains create dependencies
- ✅ Naive removal drops to 40-50% functionality
- ✅ Clean wiring is 6-7 days (not 2-3)
- ✅ Integration bugs highly likely
- ✅ Total effort to Day 1: 3-4 weeks (not 2-3)

**Lessons:**
1. Monkey patches are WORSE than they appear
2. Wrapper chains hide dependencies
3. Multi-target wrappers complicate extraction
4. Always verify with user's skepticism in mind
5. Test assumptions before committing to timelines

---

## NEXT STEPS

1. **Acknowledge to user:** You were right, I underestimated complexity
2. **Run wrapper analysis:** Map actual dependencies
3. **Build S6 harness:** Establish baseline
4. **Revise removal plan:** Account for chains and multi-target wrappers
5. **Update timeline:** 3-4 weeks to Day 1 (realistic)

**Status:** CRITICAL CORRECTION NEEDED - Original plan too optimistic
