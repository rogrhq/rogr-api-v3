# Module Testing Methodology

This document captures the systematic approach for testing clean modules post-monkey-patch removal.

## Overview
Each module is tested for:
1. Structural integrity (no crashes, expected fields added)
2. Semantic capabilities (what it actually understands vs keyword matching)
3. Comparison with archived wrapper (was logic lost in migration?)

## Test Case Design

### A. Structural Tests
- **Window bug detection**: Test short evidence (< window size) to catch zero-window bugs
- **Field validation**: Verify module adds all expected output fields
- **Edge cases**: Empty input, malformed data, boundary conditions

### B. Semantic Capability Tests

| Test Type | Variations | Purpose |
|-----------|------------|---------|
| Paraphrase | "boils" vs "boiling point" | Does it understand concept equivalence? |
| Exact match | Identical phrasing | Baseline for comparison |
| Number matching | Exact, close, contradictory | Does it detect numeric contradictions? |
| Stance keywords | confirm/refute/mixed/none | Does it rely on keywords or semantics? |
| Entity matching | Specific entities (CA vs TX) | Does it check WHICH entity or ANY entity? |
| Trigram overlap | Exact phrase vs paraphrase | How does similarity scoring work? |

### C. Claim Type Coverage
- **Scientific**: "Water boils at 100°C" (testable facts, units, numbers)
- **Policy/Economics**: "Unemployment is at 8%" (numbers, entities, trends)
- **Generic**: "Climate change is real" (concept-based, less concrete)

## Success Indicators

### Structural Success
- ✓ Adds all expected fields
- ✓ No crashes on edge cases (short evidence, empty input)
- ✓ Output has valid structure

### Semantic Understanding (Desired)
- ✅ High scores for paraphrases (boils ↔ boiling point)
- ✅ Stance detection without explicit keywords
- ✅ Entity specificity (California ≠ Texas)
- ✅ Number comparison (8% vs 12% → different scores)

### Keyword Matching Only (Gap Found)
- ⚠️ Low scores for paraphrases despite semantic equivalence
- ⚠️ stance=unrelated without keywords like "confirm/refute"
- ⚠️ Same score for different entities
- ⚠️ Same score for contradictory numbers

## Analysis Method

### 1. Trigram Deep-Dive
- Extract tokens after stopword removal
- Build trigrams from claim vs evidence
- Check overlap to understand scoring
- Example: "boils" vs "boiling" → 0 overlap = no stemming

### 2. Scoring Decomposition
- Identify which signals fire (entity/number/year/stance)
- Calculate expected score from formula
- Compare with actual score
- Determine if low scores = missing semantic layer or bugs

### 3. Comparison with Archived Wrapper
- Read: `MONKEY_PATCH_ARCHIVE/wrappers/content/pXX_*.py`
- Check: Does wrapper add semantic logic OR just call clean module?
- Document: What logic (if any) was in wrapper but missing in clean module

## Documentation Criteria

### What to Document ✅
- Structural bugs found (window bugs, crashes, missing fields)
- What it DOES do (exact capabilities with examples)
- What it DOESN'T do (semantic gaps with specific failure cases)
- Example failures: expected vs actual results
- Phase 2 rebuild needs (paraphrase families, concept matching, etc.)

### What NOT to Document ❌
- Assumptions about capabilities without testing
- "Should work but untested" claims
- Vague statements ("semantic understanding is weak" - need specifics)
- Speculation about what wrapper "probably" had

## Complete Testing Workflow (Step-by-Step)

### Phase 1: Module Discovery & Structural Testing

**Step 1: Locate and Read Clean Module**
- Use `Glob` to find module: `intelligence/content/p{XX}_*.py`
- Read entire module to understand:
  - Function signatures and parameters
  - Input expectations (what fields it reads)
  - Output structure (what fields it adds)
  - Core logic (keyword matching, scoring formulas, etc.)

**Step 2: Create Structural Test File**
- File: `tests/test_p{XX}_structural.py`
- Test categories:
  - **Field Validation**: Verify all expected output fields present
  - **Field Structure**: Check nested structures (e.g., `frame_matches[]`, `findings[]`)
  - **Label/Value Validity**: Ensure labels are from expected set, values in correct ranges
  - **Window Bug Detection** (if applicable): Test with < window_size sentences
  - **Edge Cases**: Empty input, missing fields, single item, extreme values
  - **Error Handling**: Malformed data doesn't crash

**Step 3: Run Structural Tests**
```bash
python3 tests/test_p{XX}_structural.py
```

**Step 4: Fix Structural Bugs**
- Common bugs found in P21, P23, P24:
  - **Window sliding bug**: `range(0, max(0, len(sents) - window + 1))` creates empty range for short evidence
  - **Fix**: Handle `len(sents) < window` as single window with all sentences
- Document bugs found and fixes applied

### Phase 2: Capability Testing

**Step 5: Create Capability Test File**
- File: `tests/test_p{XX}_capabilities.py`
- Design tests based on module purpose:
  - **For semantic modules** (P21, P23): paraphrase, entity, number, stance tests
  - **For frame modules** (P24): action detection, negation, frame alignment tests
  - **For aggregation modules** (P25): verdict logic, confidence, arm strength tests
- Include both positive tests (should work) and negative tests (known gaps)

**Step 6: Run Capability Tests**
```bash
python3 tests/test_p{XX}_capabilities.py
```

**Step 7: Analyze Results**
- For each capability:
  - ✅ **Works**: Document exact behavior with examples
  - ❌ **Doesn't work**: Document failure case with expected vs actual
  - 🐛 **Bug found**: Isolate root cause (e.g., sequential if statements)
- Create debugging tests if needed to understand unexpected behavior
- Decompose scoring formulas to understand low/high scores

### Phase 3: Wrapper Comparison

**Step 8: Read Archived Wrapper**
- File: `MONKEY_PATCH_ARCHIVE/wrappers/content/p{XX}_*.py`
- Understand wrapper structure:
  - Does it import a function from clean module?
  - Does it add additional logic on top?
  - Or does it only wrap for pipeline integration?

**Step 9: Compare Wrapper to Clean Module**
- Key questions:
  - **Logic location**: Is semantic logic in wrapper or clean module?
  - **Lost logic**: Did wrapper have semantic intelligence missing in clean module?
  - **Conclusion**: Was logic lost in migration OR was gap pre-existing?
- Document comparison result:
  - "Wrapper only imports X from clean module - no lost logic"
  - OR "Wrapper had Y logic missing in clean module - gap caused by migration"

### Phase 4: Documentation & Commit

**Step 10: Update SEMANTIC_GAPS.md**
- Section structure:
  ```markdown
  ## P{XX} - Module Name
  **Status:** ✅ COMPLETE | ⚠️ INCOMPLETE | 🐛 BUGS FOUND

  **Fixed:** (if bugs were fixed)
  - ✅ Bug description and fix applied

  **Testing Results:**
  - ✅ What works (with examples)
  - ❌ What doesn't work (with examples)
  - 🐛 Bugs found (with root cause)

  **Example Gap:** (concrete failure case)
  - Claim: "X"
  - Evidence: "Y"
  - Current: Z ❌
  - Should be: W ✓

  **What's Needed:** (Phase 2 rebuild list)

  **Archived Wrapper Comparison:**
  - File: path
  - Finding: comparison result
  - Conclusion: logic lost or pre-existing gap

  **Estimated Rebuild:** X days
  **Priority:** HIGH/MEDIUM/LOW
  ```

**Step 11: Commit Changes**
- Files to commit:
  - Modified clean module (if bugs fixed)
  - `docs/SEMANTIC_GAPS.md` (updated section)
  - `tests/test_p{XX}_*.py` (all test files)
- Commit message structure:
  ```
  Fix P{XX} bugs and document capabilities

  FIXES: (if applicable)
  - Bug description and fix

  TESTING (X/Y passed):
  ✅ What works
  ❌ What doesn't (Phase 2)
  🐛 Bugs found (root cause)

  COMPARISON:
  - Archived wrapper analysis

  Priority: X, Timeline: Y days
  ```

**Step 12: Push to Remote**
```bash
git push
```

---

## Testing Checklist (Copy for each module)

- [ ] Step 1: Read clean module (`intelligence/content/p{XX}_*.py`)
- [ ] Step 2: Create structural test (`tests/test_p{XX}_structural.py`)
- [ ] Step 3: Run structural test
- [ ] Step 4: Fix any structural bugs found
- [ ] Step 5: Create capability test (`tests/test_p{XX}_capabilities.py`)
- [ ] Step 6: Run capability test
- [ ] Step 7: Analyze results (what works, what doesn't, any bugs)
- [ ] Step 8: Read archived wrapper (`MONKEY_PATCH_ARCHIVE/wrappers/content/p{XX}_*.py`)
- [ ] Step 9: Compare wrapper to clean module
- [ ] Step 10: Update `docs/SEMANTIC_GAPS.md`
- [ ] Step 11: Commit all changes
- [ ] Step 12: Push to remote

---

## Modules Tested (Status)

- ✅ P19: Complete (claim-type detection working)
- ✅ P20: Documented (stance detection needs Phase 2)
- ✅ P21: Window fixed, semantic missing (Phase 2)
- ✅ P23: Window fixed, semantic missing (Phase 2)
- ✅ P24: Window + negation fixed, action alignment bug + semantic missing (Phase 2)
- ✅ P25: Complete (no Phase 2 work needed)
- ⏳ P26: Dual researchers (TODO)
- ⏳ P27: Consensus (TODO)
- ⏳ P28: Diversify (TODO)
- ⏳ P29: Diversify controls (TODO)

## Applied to P23 Example

See P23_COMPLETE_EVALUATION_REPORT.md for full application of this methodology.

Key findings:
- ✅ Works: Number matching, stance keywords, entity tokens, exact trigrams
- ❌ Missing: Paraphrase detection, stemming, synonyms, semantic concepts
- Example: "boils" ≠ "boiling point" (score 0.397 vs should be 0.8+)
- Archive check: Wrapper has identical logic (no lost semantic layer)

---

*Use this methodology for P24, P25, and future module testing*
