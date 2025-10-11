# Semantic Layer Gaps - Post Monkey Patch Removal

## Overview
Monkey patches removed during clean integration. Clean architecture in place, but semantic intelligence layers need to be rebuilt.

This document tracks ACTUAL findings from testing, not assumptions.

## Testing & Documentation Strategy
1. Test each clean module with clear test cases
2. Document what it actually does vs what's needed
3. Reference archived monkey patch for comparison
4. Estimate rebuild effort
5. Prioritize based on impact

---

## P19 - Counter-Frame Queries
**Status:** ✅ FIXED
**What was done:**
- Added claim-type detection (scientific, policy_econ, generic)
- Added concept extraction (boils → boiling point)
- Implemented template families per claim type

**No Phase 2 work needed**

---

## P20 - Stance Detection
**Status:** ⚠️ INCOMPLETE - Documented, minimal fix applied

**Testing Results:**
- Uses keyword matching (increase/decrease/higher/lower)
- Sequential if statements caused overwrites (fixed with elif)
- Fails on scientific claims with comparative language
- Example: "lower at altitude" → marked "challenge" (wrong)

**What's Needed:**
- Frame-based reasoning with numeric/unit comparison
- Condition awareness (sea level vs altitude)
- Decision tree logic (phenomenon → numeric → directional)

**Reference:** MONKEY_PATCH_ARCHIVE/wrappers/content/p20_wrapper.py

**Estimated Rebuild:** 2-3 days
**Priority:** HIGH (affects all verdicts)

---

## P21 - Full Read Evaluation
**Status:** ⚠️ INCOMPLETE - Window bug fixed, semantic layer missing

**Testing Results:**
- Fixed: Window sliding bug (now handles short evidence)
- Current: Uses keyword stance cues + trigram overlap + entity overlap
- Missing: Paraphrase matching, unit normalization, condition reasoning
- Example: "boiling point of 100 degrees Celsius" → grade: 2.69, stance: unrelated (wrong)

**What's Needed:**
- Paraphrase families (boils ↔ boiling point)
- Unit normalization (°C ↔ degrees Celsius ↔ 100 degrees Celsius)
- Numeric tolerance matching
- Condition equivalence (sea level ↔ standard atmospheric pressure)
- Phenomenon-first matching

**Reference:** MONKEY_PATCH_ARCHIVE/wrappers/content/p21_wrapper.py

**Estimated Rebuild:** 2-3 days
**Priority:** HIGH (critical for evidence evaluation)

---

## P23 - Semantic Findings
**Status:** TESTING IN PROGRESS

**Testing Results:**
[To be filled after testing]

**Reference:** MONKEY_PATCH_ARCHIVE/wrappers/content/p23_semantic.py

**Estimated Rebuild:** TBD
**Priority:** TBD

---

## P24 - Frame Extraction
**Status:** NOT YET TESTED

---

## P25 - Verdict Aggregation
**Status:** NOT YET TESTED

---

## Phase 2 Implementation Plan (After Execution Plan Complete)

### Approach
1. One module at a time, starting with highest priority
2. Use archived monkey patches as reference for intended logic
3. Rebuild semantic layers in clean modules (no patches)
4. Test each module standalone before integration
5. Full pipeline testing after all semantic layers complete

### Estimated Timeline
- P20 stance detection: 2-3 days
- P21 full-read semantic: 2-3 days
- P23/P24 (TBD based on testing): 1-2 days each
- Integration & testing: 2-3 days
- **Total: ~2 weeks**

### Success Criteria
- "Water boils at 100°C" with paraphrased evidence → supports, high confidence
- Scientific claims with condition variations → contextual support
- Policy claims with contradictory numbers → challenge
- All verdicts accurate and explainable

---

*This is a living document. Updated as we test each module.*
