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

## Testing Workflow

1. **Structural test**: Fix window bugs, validate fields
2. **Capability tests**: Run systematic variations (paraphrase, numbers, entities, etc.)
3. **Analyze results**: Decompose scoring, understand why low/high
4. **Check archive**: Compare wrapper to clean module
5. **Document findings**: Specific capabilities, specific gaps, specific examples
6. **Commit**: Bug fixes + comprehensive findings

## Applied to P23 Example

See P23_COMPLETE_EVALUATION_REPORT.md for full application of this methodology.

Key findings:
- ✅ Works: Number matching, stance keywords, entity tokens, exact trigrams
- ❌ Missing: Paraphrase detection, stemming, synonyms, semantic concepts
- Example: "boils" ≠ "boiling point" (score 0.397 vs should be 0.8+)
- Archive check: Wrapper has identical logic (no lost semantic layer)

---

*Use this methodology for P24, P25, and future module testing*
