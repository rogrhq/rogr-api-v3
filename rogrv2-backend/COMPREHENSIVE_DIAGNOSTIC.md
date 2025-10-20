# COMPREHENSIVE DIAGNOSTIC: ROGR Pipeline Intelligence Breakdown

**Date:** 2025-10-19
**Test Claim:** "Water boils at 100 degrees Celsius at sea level"

---

## Executive Summary

**Problem:** Pipeline produces garbage results despite all 15 tasks being "complete"

**Root Cause:** Silent failures in critical intelligence functions wrapped in try/except blocks

---

## Diagnostic Results

### 1. Overall Verdict: ❌ WRONG

```
Verdict: Mixed (46%)
Expected: True (90%+)
```

**Issue:** Simple scientific fact receives "insufficient" verdict

---

### 2. Classification: ❌ MISSING

```
Classification: None
Expected: {"category": "SCIENTIFIC", "verifiability": "HIGHLY_VERIFIABLE"}
```

**Root Cause:** Classification likely not in claim_obj, or classify_claim() failing silently

**Location:** intelligence/preprocess/classify.py:classify_claim()

---

### 3. Evidence Quality: ❌ BROKEN

```
Total items: 6
├─ Support: 1 item (should be 5-6)
├─ Challenge: 5 items (should be 0-1)
└─ Unrelated: 4/6 (66.7%) - most evidence marked unrelated
```

**Issues:**
- Evidence in wrong arms (support in challenge arm)
- Most evidence marked "unrelated" to claim
- Stance detection completely broken

---

### 4. Evidence Grading: ❌ ALL ZERO

```
Item 1: Grade = 0/100 ❌
Item 2: Grade = 0/100 ❌
Item 3: Grade = 0/100 ❌
Item 4: Grade = 0/100 ❌
Item 5: Grade = 0/100 ❌
Item 6: Grade = 0/100 ❌
```

**Root Cause:** P20 fusion formula not executing or failing silently

**Location:** intelligence/content/grade.py:fuse_module_grades()

**Called by:** attach_finding_to_item() at line 83 of run.py

**Problem:** Wrapped in try/except at line 84-86:
```python
try:
    attach_finding_to_item(claim_text, arm_label, item)
except:
    pass  # ← Swallows ALL errors silently
```

---

### 5. Authority/Credibility: ❌ ALL LOW

```
All items: 0.12 - 0.24 credibility (12-24%)
Expected: 0.5+ for authoritative sources
```

**Issues:**
- homework.study.com: 12% (should be 40-50% for .com educational)
- engineeringtoolbox.com: 12% (should be 50-60% for technical reference)
- Credibility scoring completely broken

**Root Cause:** P21 authority scoring failing or not executing

**Location:** intelligence/content/fullread.py:evaluate_full_evidence()

**Called by:** Line 89-93 of run.py, also wrapped in try/except

---

### 6. Stance Detection: ❌ MOSTLY UNRELATED

```
Stance results:
├─ Support: 2/6 (33%)
├─ Refute: 0/6 (0%)
└─ Unrelated: 4/6 (67%)
```

**Root Cause:** P23 semantic analysis not working

**Location:** intelligence/content/semantic_read.py:analyze_item()

**Called by:** Line 96-101 of run.py, also wrapped in try/except

---

### 7. Researchers: ⚠️ DISAGREE

```
R1 (Skeptic): "challenges" (49.5%)
R2 (Explorer): "mixed" (52.9%)
```

**Issue:** Researchers disagree due to bad evidence quality

**Root Cause:** Both researchers get broken evidence → disagree

---

### 8. Consensus: ❌ INSUFFICIENT

```
Label: insufficient
Confidence: 46.1%
Rule: disagree_evidence_quality
```

**Root Cause:** Consensus sees:
- Low support arm quality (23%)
- Low challenge arm quality (41%)
- Researchers disagree
→ Concludes "insufficient evidence"

**Location:** intelligence/consensus/dual_lane.py:compute_consensus()

---

### 9. Summary: ⚠️ SHOWS ISSUES

```
Summary: "...support:1, refute:0, neutral:4..."
```

**Issue:** Summary correctly reports the broken evidence counts

**Shows:** Summary generation (TASK 15) works, but gets garbage input

---

## Root Cause Analysis

### Silent Failure Pattern

**Location:** intelligence/pipeline/run.py:70-110

All critical intelligence functions are wrapped in try/except that swallows errors:

```python
# P20: Grading
try:
    attach_finding_to_item(claim_text, arm_label, item)
except:
    pass  # ← SWALLOWS ERRORS

# P21: Authority
try:
    evaluate_full_evidence(claim_text, item, claim_classification)
except:
    pass  # ← SWALLOWS ERRORS

# P23: Semantic analysis
try:
    analyze_item(claim_text, item, window=3, stance_threshold=stance_threshold)
except:
    pass  # ← SWALLOWS ERRORS

# P24: Frame analysis
try:
    frames = analyze_frames(claim_text, content, window=3)
    item.update(frames)
except:
    pass  # ← SWALLOWS ERRORS
```

### Actual Failures

1. **attach_finding_to_item** (P20) → Grade = 0
   - Function fails or returns 0
   - Error swallowed
   - Item gets grade=0

2. **evaluate_full_evidence** (P21) → Credibility = 0.12
   - Function fails or returns low score
   - Error swallowed
   - Item gets minimal credibility

3. **analyze_item** (P23) → Stance = "unrelated"
   - Function fails or can't match claim to content
   - Error swallowed
   - Item marked unrelated

4. **Cascade Effect:**
   - Bad grades → Low confidence
   - Unrelated stance → Evidence ignored
   - Low credibility → Low authority
   - All combine → Wrong verdict

---

## Critical Functions Status

### Functions Being Called: ✅

```
✓ attach_finding_to_item (P20 - grading)
✓ evaluate_full_evidence (P21 - authority)
✓ analyze_item (P23 - semantic/stance)
✓ analyze_frames (P24 - frame analysis)
✓ aggregate_verdict (P25 - aggregation)
✓ compute_consensus (P27 - consensus)
```

### Functions Actually Working: ❌

```
❌ attach_finding_to_item → All grades = 0
❌ evaluate_full_evidence → All credibility < 0.3
❌ analyze_item → 67% marked unrelated
❌ analyze_frames → No visible impact
❌ aggregate_verdict → Garbage in = garbage out
❌ compute_consensus → Correctly identifies low quality
```

---

## Evidence Items Detail

### Item 1: homework.study.com (Arm A)
```
Title: "Water boils at 100 degrees Celsius at sea level..."
Stance: support ✅
Grade: 0 ❌
Credibility: 0.12 ❌
Issue: Perfect title match, but grade=0 and low credibility
```

### Item 2: homework.study.com (Arm B) - DUPLICATE
```
Title: "Water boils at 100 degrees Celsius at sea level..."
Stance: support ✅
Grade: 0 ❌
Credibility: 0.12 ❌
Issue: DUPLICATE of Item 1, should be deduped
```

### Item 3: worldwildlife.org (Arm B)
```
Title: "High Cost of Cheap Water: The True Value of Water..."
Stance: unrelated ✅ CORRECT
Grade: 0 ❌
Credibility: 0.12 ❌
Issue: Correctly marked unrelated, but still has 0 grade
```

### Item 4: engineeringtoolbox.com (Arm B)
```
Title: "Water - Boiling Points vs. Altitude"
Stance: unrelated ❌ WRONG
Grade: 0 ❌
Credibility: 0.12 ❌
Issue: HIGHLY RELEVANT (boiling points!), marked unrelated
```

### Item 5: watercheck.com (Arm B)
```
Title: "Watercheck - NTL - Residential & Commercial Water Testing"
Stance: unrelated ✅ CORRECT
Grade: 0 ❌
Credibility: 0.24 ❌
Issue: Correctly unrelated, but why in results at all?
```

### Item 6: truevalue.com (Arm B)
```
Title: "True Value Hardware: Home"
Stance: unrelated ✅ CORRECT
Grade: 0 ❌
Credibility: 0.24 ❌
Issue: Correctly unrelated, but why in results at all?
```

---

## Next Steps: Diagnostic Actions

### 1. Add Error Logging (IMMEDIATE)

Replace all try/except blocks with error logging:

```python
try:
    attach_finding_to_item(claim_text, arm_label, item)
except Exception as e:
    print(f"❌ P20 ERROR: {e}")
    import traceback
    traceback.print_exc()
```

### 2. Test Individual Functions

Test each function in isolation:

```python
# Test P20 grading
from intelligence.content.grade import attach_finding_to_item
item = {"title": "Water boils at 100C", "content": "...", "url": "..."}
attach_finding_to_item("Water boils at 100C", "A", item)
print(f"Grade: {item.get('grade')}")
```

### 3. Check Dependencies

- Verify semantic models are loaded
- Check if content fetching is working
- Verify all imports are correct

### 4. Trace One Item End-to-End

Follow one evidence item through entire pipeline:
1. Search → URL
2. Fetch → Content
3. P20 → Grade
4. P21 → Credibility
5. P23 → Stance
6. P25 → Verdict contribution

### 5. Fix Root Causes

Once errors are visible:
1. Fix P20 grading (fuse_module_grades)
2. Fix P21 authority (evaluate_full_evidence)
3. Fix P23 stance (analyze_item)
4. Remove duplicate results
5. Fix filtering (remove unrelated items)

---

## Conclusion

**The 15 tasks are "integrated" but none are actually working.**

The pipeline runs end-to-end without crashing, but:
- ❌ Every grade is 0
- ❌ Every credibility is near 0
- ❌ Most stances are wrong
- ❌ Evidence is in wrong arms
- ❌ Final verdict is wrong

**Root cause:** Silent failures hidden by try/except blocks

**Solution:** Add error logging to expose actual failures, then fix them

---

## Files to Investigate

Priority order:

1. **intelligence/content/grade.py** - P20 fusion (all grades = 0)
2. **intelligence/content/fullread.py** - P21 authority (all credibility low)
3. **intelligence/content/semantic_read.py** - P23 stance (unrelated)
4. **intelligence/pipeline/run.py:70-110** - Remove silent error swallowing
5. **intelligence/consensus/dual_lane.py** - Why "disagree_evidence_quality"?

---

## Test Command

To reproduce:

```bash
python3 << 'EOF'
import asyncio
from intelligence.pipeline.run import run_preview

result = asyncio.run(run_preview("Water boils at 100 degrees Celsius at sea level"))

# Check results
claim = result['claims'][0]
evidence = claim['evidence']
arm_a = evidence['arm_A']

print(f"Arm A items: {len(arm_a)}")
for item in arm_a:
    print(f"  Grade: {item.get('grade')}, Stance: {item.get('stance')}")
EOF
```

Expected: Grade > 0, Stance = support
Actual: Grade = 0, Stance varies

---

**Status:** Pipeline integrated but not functional
**Priority:** HIGH - Core intelligence completely broken
**Impact:** 0% accuracy on simple facts
