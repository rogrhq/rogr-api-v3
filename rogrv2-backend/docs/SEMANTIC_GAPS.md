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
**Status:** ⚠️ INCOMPLETE - Window bug fixed, semantic layer missing

**Testing Results:**
- Fixed: Window sliding bug (now handles evidence < 3 sentences)
- Current capabilities:
  - ✅ Number matching (detects percentages, years)
  - ✅ Stance keywords (confirm/refute/dispute/shows)
  - ✅ Entity token matching (shared words > 2 chars)
  - ✅ Exact trigram matching (Jaccard similarity)
- Missing capabilities:
  - ❌ Paraphrase detection (boils ≠ boiling point)
  - ❌ Stemming (boils ≠ boiling, economy ≠ economic)
  - ❌ Synonym matching (unemployment ≠ jobless)
  - ❌ Semantic concept recognition
  - ❌ Entity specificity (California = Texas in scoring)
  - ❌ Number comparison logic (8% = 12% in scoring)

**Example Gap:**
- Claim: "Water boils at 100 degrees Celsius"
- Evidence: "Water has a boiling point of 100 degrees Celsius"
- Current: grade 0.397, stance: unrelated ❌
- Should be: grade 0.8+, stance: support ✓

**What's Needed:**
- Paraphrase families (boils ↔ boiling point)
- Stemming/lemmatization
- Synonym dictionaries
- Semantic concept matching
- Entity-specific matching (not just token presence)
- Numeric comparison/contradiction detection

**Archived Wrapper Comparison:**
- File: MONKEY_PATCH_ARCHIVE/wrappers/content/p23_semantic.py
- Finding: Wrapper only imports and calls analyze_item from clean module
- Conclusion: No semantic logic was lost - clean module IS the implementation
- Gap existed in original design, not caused by wrapper removal

**Estimated Rebuild:** 2-3 days
**Priority:** HIGH (critical for semantic evidence evaluation)

---

## P24 - Frame Extraction
**Status:** ⚠️ INCOMPLETE - Negation bug fixed, action alignment bug found, semantic gaps remain

**Fixed:**
- ✅ Window sliding bug (now handles evidence < 3 sentences)
- ✅ Negation bug (elif fix) - "did not increase" now correctly contradicts "increased"
- Verified with comprehensive regression tests (11/13 passed)

**Testing Results:**
- ✅ Exact matching works for aligned cases (claim=increase + evidence=increase)
- ✅ Action keyword detection (increase/decrease/cut)
- ✅ Number/year extraction (percentages, years)
- ✅ Negation detection (contradict when "did not X")
- ✅ Slot coverage tracking
- ❌ No paraphrase understanding (increased ≠ went up)
- ❌ No entity identity (California = Texas in scoring)
- ❌ No numeric comparison (8% = 8.2% = 12%)
- 🐛 **Action alignment bug**: Assumes evidence "decrease" = contradiction, doesn't check claim action

**Action Alignment Bug Example:**
- Claim: "Texas **decreased** spending by 5%"
- Evidence: "Texas **decreased** spending by 5%" (exact match!)
- Expected: entail ✓
- Actual: contradict ❌
- Root cause: Line 189 triggers on evidence action alone, not alignment with claim

**Example Gaps:**
- Paraphrase: "increased" (0.800) vs "went up" (0.240) ❌
- Entity identity: California vs Texas → same score (0.160) ❌
- Numeric comparison: 8% = 8.2% = 12% → all score 0.160 ❌

**What's Needed:**
- **Fix action alignment logic** (compare claim action vs evidence action)
- Paraphrase/synonym dictionaries (increased ↔ went up ↔ rose ↔ grew)
- Entity identity verification (not just presence)
- Numeric tolerance and contradiction detection
- Expanded action vocabulary beyond hardcoded lists

**Archived Wrapper Comparison:**
- File: MONKEY_PATCH_ARCHIVE/wrappers/content/p24_semantic_frames.py
- Finding: Wrapper only imports and calls analyze_frames from clean module
- Conclusion: No semantic logic was lost - clean module IS the implementation
- Bugs existed in original design, not caused by wrapper removal

**Estimated Rebuild:** 3-4 days (action logic + semantic layers)
**Priority:** MEDIUM-HIGH (affects contradiction detection in budget/policy claims)

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
- P20 stance detection: 2-3 days (HIGH priority)
- P21 full-read semantic: 2-3 days (HIGH priority)
- P23 semantic findings: 2-3 days (HIGH priority)
- P24 frame extraction: 3-4 days (MEDIUM-HIGH priority - action alignment + semantic)
- P25 aggregation (TBD based on testing): 1-2 days
- Integration & testing: 2-3 days
- **Total: ~3 weeks**

### Success Criteria
- "Water boils at 100°C" with paraphrased evidence → supports, high confidence
- Scientific claims with condition variations → contextual support
- Policy claims with contradictory numbers → challenge
- All verdicts accurate and explainable

---

*This is a living document. Updated as we test each module.*
