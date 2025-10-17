# AFTER STATE: Clean Module Semantic Logic Inventory

**Date:** 2025-10-13
**Purpose:** Document semantic capabilities present in clean modules after Phase 1 + Phase 2 work

## EXECUTIVE SUMMARY

✅ **Substantial semantic logic EXISTS in clean modules**
✅ **Shared utilities layer created in Phase 2** with reusable semantic components
✅ **All modules preserved from before** + enhanced with frame-based reasoning

**Key Finding:** Clean modules contain MORE semantic logic than before due to Phase 2 enhancements.

---

## SHARED UTILITIES LAYER

**Location:** `intelligence/content/shared/`

### Created in Phase 2: Days 1-5

Extracted and centralized semantic logic for reuse across all modules.

#### 1. Paraphrases (`paraphrases.py` - 86 lines)

**Functions:**
- `get_paraphrase_family(word)` - Get all paraphrases for a word
- `are_paraphrases(word1, word2)` - Check if two words are paraphrases
- `find_paraphrases_in_text(word, text)` - Find paraphrase matches in text
- `paraphrase_match_score(text1, text2)` - Compute paraphrase similarity score

**Dictionaries:**
- `SCIENTIFIC_PARAPHRASES` - Scientific/academic terminology
  - Example: {"boil": ["boiling point", "vaporize"], ...}
- `POLICY_PARAPHRASES` - Policy/economic terminology
  - Example: {"increase": ["rise", "grow", "expand"], ...}
- `GENERIC_PARAPHRASES` - Common verbs/actions
- `ALL_PARAPHRASES` - Combined dictionary

**Status:** ✅ IMPLEMENTED - Dictionary-based paraphrase matching

**Limitation:** Dictionary-based, not semantic/embedding-based (documented for post-Phase 2)

---

#### 2. Units (`units.py` - 54 lines)

**Functions:**
- `normalize_unit(unit_str)` - Convert units to standard form
- `compute_tolerance(value, abs_tol, rel_tol)` - Compute numeric tolerance
- `values_match(val1, val2, abs_tol, rel_tol)` - Check if values match within tolerance

**Dictionary:**
- `UNIT_CONVERSIONS` - Unit normalization mappings
  - Example: {"°C": "celsius", "degrees celsius": "celsius", "%": "percent", ...}

**Status:** ✅ IMPLEMENTED - Unit normalization and tolerance matching

---

#### 3. Conditions (`conditions.py` - 64 lines)

**Functions:**
- `normalize_condition(cond_str)` - Normalize condition text
- `conditions_equivalent(cond1, cond2)` - Check if conditions are equivalent
- `extract_conditions(text)` - Extract condition phrases from text

**Dictionaries:**
- `CONDITION_EQUIVALENTS` - Condition synonyms
  - Example: {"sea level": ["standard pressure", "1 atm"], ...}
- `FISCAL_PATTERNS` - Fiscal/budget period patterns

**Status:** ✅ IMPLEMENTED - Condition recognition and equivalence

---

#### 4. Entities (`entities.py` - 52 lines)

**Functions:**
- `extract_entities(text)` - Extract entities from text
- `extract_entities_by_type(text)` - Extract entities by type (locations, orgs, etc.)
- `entity_overlap(entities1, entities2)` - Compute entity overlap score

**Dictionary:**
- `ENTITY_PATTERNS` - Regex patterns for entity extraction

**Status:** ✅ IMPLEMENTED - Basic entity extraction

---

#### 5. Frames (`frames.py` - 124 lines)

**Functions:**
- `extract_frame(text, domain)` - Extract semantic frame from text
- `compare_frames(frame1, frame2)` - Compare two frames

**Frame Structure:**
```python
Frame = {
    "entity": str,        # Main entity/subject
    "action": str,        # Action verb
    "direction": str,     # up/down/neutral
    "number": float,      # Numeric value
    "unit": str,          # Unit of measurement
    "condition": str,     # Context/condition
    "phenomenon": str     # Scientific phenomenon
}
```

**Status:** ✅ IMPLEMENTED - Frame-based semantic reasoning

---

#### 6. Vocabulary (`vocabulary.py` - 41 lines)

**Functions:**
- `is_negation(word)` - Check if word is negation

**Dictionaries:**
- `P24_INC_VERBS` - Increase verbs for P24
- `P24_DEC_VERBS` - Decrease verbs for P24
- `EXTRACT_FACTS_INC` - Increase verbs for extract_facts
- `EXTRACT_FACTS_DEC` - Decrease verbs for extract_facts
- `INC_VERBS` - Generic increase verbs

**Status:** ✅ IMPLEMENTED - Action verb vocabularies

---

#### 7. Text Utils (`text_utils.py` - 65 lines)

**Functions:**
- `normalize_text(text)` - Basic text normalization
- `tokenize(text)` - Basic tokenization
- `clean_text(text)` - Remove punctuation/whitespace
- `normalize_text_advanced(text)` - Advanced normalization
- `tokenize_advanced(text)` - Advanced tokenization

**Constants:**
- `STOP_WORDS` - Common stop words

**Status:** ✅ IMPLEMENTED - Text preprocessing utilities

---

## P20 - grade.py (Enhanced in Phase 2C Task 9.2)

**Lines:** ~250 (after enhancement)
**Public API:**
- `build_finding(claim_text, arm, content_text, ...) -> Dict`
- `attach_finding_to_item(claim_text, arm, item) -> Dict`

### A. CURRENT FUNCTIONS

**Public:**
1. `build_finding()` - Build finding card for evidence item
2. `attach_finding_to_item()` - Attach finding to item dict

**Internal:**
- `_modality_penalty()` - Detect hedged/uncertain language
- `_stance_for_window()` - **ENHANCED** frame-based stance detection
- `_stance_keyword_fallback()` - **NEW** fallback keyword matching

### B. SEMANTIC LOGIC PRESENT

✅ **Frame-based stance detection** (Lines 60-150)
- Extracts frames from claim and evidence
- Compares frames semantically
- Detects paraphrases (rose ↔ increased)
- Recognizes conditions (sea level vs altitude)
- Returns: support, challenge, contextual_support, mixed, unrelated

✅ **Paraphrase detection** (Lines 96-101)
- Uses shared paraphrase dictionaries
- Scores paraphrase similarity
- Threshold-based matching (0.25 for exact, 0.2 for fallback)

✅ **Condition awareness** (Lines 79-87)
- Extracts conditions from claim and evidence
- Checks for condition match/conflict
- Returns contextual_support for same phenomenon, different conditions

✅ **Numeric tolerance** (Lines 113-116)
- Checks if entity + number match
- Uses values_match with abs_tol=0.5, rel_tol=0.10

✅ **Entity extraction** (Imported from extract_facts)
- claim_entities(), claim_numbers(), claim_years()

✅ **Stance keywords** (Fallback function Lines 152-167)
- Support keywords: confirm, verify, corroborate, etc.
- Challenge keywords: contradict, dispute, debunk, etc.

### C. COMPARISON TO BEFORE

**BEFORE (Keywords only):**
```python
def _stance_for_window(text, arm):
    is_inc = any(w in t for w in ("increase","increased","up"))
    is_dec = any(w in t for w in ("decrease","decreased","down"))
    # Simple keyword matching
```

**AFTER (Frame-based):**
```python
def _stance_for_window(text, arm, claim_text=None):
    # Extract frames
    claim_frame = extract_frame(claim_text, domain='policy')
    evidence_frame = extract_frame(text, domain='policy')

    # Extract conditions
    claim_conditions = extract_conditions(claim_text)
    evidence_conditions = extract_conditions(text)

    # Compare frames
    frame_comparison = compare_frames(claim_frame, evidence_frame)

    # Check paraphrases
    paraphrase_score = paraphrase_match_score(...)

    # Decision logic with condition awareness
```

**STATUS:** ✅ SIGNIFICANTLY ENHANCED

---

## P21 - fullread.py (Enhanced in Phase 2C Task 8.1)

**Lines:** ~280
**Public API:**
- `evaluate_full_evidence(claim_text, item) -> Dict`

### A. CURRENT FUNCTIONS

**Public:**
1. `evaluate_full_evidence()` - Deterministic full-read evaluation

**Internal:**
- `_ngrams()` - N-gram extraction
- `_jaccard()` - Jaccard similarity
- `_window_sentences()` - Window-based sentence extraction
- `_stance_for_chunk()` - Stance detection per chunk
- `_percent_hits()` - Percentage/number matching
- `_year_hit()` - Year matching
- `_entity_overlap()` - Entity overlap scoring
- `_credibility_from()` - Credibility scoring from URL/text

### B. SEMANTIC LOGIC PRESENT

✅ **Window-based semantic reading** (Lines 120-180)
- Splits content into overlapping sentence windows
- Extracts best matching windows using Jaccard similarity

✅ **Stance detection** (Lines 90-110)
- Keyword-based stance cues (confirms, disputes, etc.)
- Supports, challenges, mixed classification

✅ **Paraphrase matching** (Phase 2 enhancement)
- Uses shared paraphrase utilities
- Adds paraphrase score to grading

✅ **Condition awareness** (Phase 2 enhancement)
- Extracts conditions from claim and evidence
- Checks for condition equivalence
- Boosts score for matching conditions

✅ **Numeric tolerance** (Lines 145-170)
- Detects percentage hits with tolerance
- Year matching

✅ **Entity overlap** (Lines 180-200)
- Computes entity overlap score
- Uses tokenization and bigram matching

✅ **Grading algorithm** (Lines 200-250)
- Combines: stance cues (0.3), paraphrases (0.2), entity overlap (0.2), conditions (0.1)
- Returns grade_full (0-1 scale) and stance_full

### C. COMPARISON TO BEFORE

**BEFORE:** Basic keyword matching + trigram overlap
**AFTER:** + Paraphrase matching + Condition awareness + Shared utilities

**STATUS:** ✅ ENHANCED with semantic capabilities

---

## P23 - semantic_read.py (Enhanced in Phase 2C Days 6-7)

**Lines:** ~210
**Public API:**
- `analyze_item(claim_text, item) -> Dict`

### A. CURRENT FUNCTIONS

**Public:**
1. `analyze_item()` - Deterministic semantic pass for single item

**Internal:**
- `_norm()` - Normalize text
- `_tokens()` - Tokenize
- `_split_sentences()` - Sentence splitting
- `_trigrams()` - Trigram extraction
- `_jaccard()` - Jaccard similarity
- `_percent_numbers()` - Extract percentages/numbers
- `_years()` - Extract years
- `_stance_for_window()` - Stance detection
- `_best_offset()` - Find quote offset in content

### B. SEMANTIC LOGIC PRESENT

✅ **Semantic findings extraction** (Lines 90-180)
- Extracts quotes with offsets
- Detects stance signals (confirms, refutes, etc.)
- Computes semantic scores

✅ **Number matching** (Lines 50-70)
- Percentage extraction
- Year extraction
- Exact matching

✅ **Stance keywords** (Lines 110-130)
- Support keywords: confirms, supports, verifies
- Challenge keywords: refutes, disputes, contradicts

✅ **Entity token matching** (Lines 140-160)
- Extracts shared tokens (>2 chars)
- Token overlap scoring

✅ **Trigram similarity** (Lines 70-90)
- Exact trigram matching
- Jaccard similarity

✅ **Uses shared utilities** (Import statements)
- text_utils for normalization
- Prepared for paraphrase integration

### C. COMPARISON TO BEFORE

**BEFORE:** Same logic (was always in clean module)
**AFTER:** Enhanced with shared utilities imports + prepared for Phase 2 integration

**STATUS:** ✅ WORKING, ⚠️ READY FOR SEMANTIC ENHANCEMENT

**Documented Limitations:**
- No paraphrase detection yet (boils ≠ boiling point)
- No stemming (boils ≠ boiling, economy ≠ economic)
- No synonym matching
- Entity specificity issues (California = Texas in scoring)

---

## P24 - semantic_frames.py (Enhanced in Phase 2C Days 6-7)

**Lines:** ~320
**Public API:**
- `extract_claim_frame(claim_text) -> Dict`
- `extract_window_frame(win_text) -> Dict`
- `analyze_frames(claim_text, content) -> Dict`

### A. CURRENT FUNCTIONS

**Public:**
1. `extract_claim_frame()` - Extract frame from claim
2. `extract_window_frame()` - Extract frame from evidence window
3. `analyze_frames()` - Analyze frames for full content

**Internal:**
- `_split_sentences()` - Sentence splitting
- `_trigrams()` - Trigram extraction
- `_jaccard_tris()` - Jaccard for trigrams
- `_best_offset()` - Find best quote offset
- `_has_budget_context()` - Detect budget context
- `_detect_action()` - Detect action verbs (increase/decrease)
- `_percent_numbers()` - Extract percentages
- `_years()` - Extract years
- `_entities_from_claim_tokens()` - Entity extraction
- `_quantity_compatible()` - Check quantity compatibility
- `_year_compatible()` - Check year compatibility
- `_entity_overlap()` - Check entity overlap
- `_scope_ok()` - Check scope compatibility
- `_entail_contradict()` - Determine entailment/contradiction

### B. SEMANTIC LOGIC PRESENT

✅ **Frame extraction** (Lines 90-150)
- Entity detection (budget entities, tokens >2 chars)
- Action detection (increase, decrease, cut, etc.)
- Quantity extraction (percentages, decimals)
- Year extraction (1900-2099)
- Scope detection (billion, million, national)

✅ **Frame comparison** (Lines 200-280)
- Quantity compatibility (with 1.0 pp tolerance)
- Year compatibility
- Entity overlap
- Scope matching

✅ **Entailment detection** (Lines 280-320)
- Compare claim vs evidence frames
- Returns: entail, contradict, mixed, unrelated
- Provides rationale with slot matching

✅ **Action alignment** (Lines 150-180)
- Uses shared vocabulary (INC_VERBS, DEC_VERBS)
- Detects directional actions

✅ **Negation detection** (Lines 140-150)
- Handles "did not increase" vs "increased"

✅ **Uses shared utilities**
- text_utils for normalization
- vocabulary for action verbs

### C. COMPARISON TO BEFORE

**BEFORE:** Same logic (was always in clean module)
**AFTER:** Enhanced with shared utilities + action alignment bug fixes

**STATUS:** ✅ WORKING

**Known Issues (Documented):**
- Action alignment bug (fixed in Phase 2)
- No paraphrase understanding (increased ≠ went up)
- No entity identity (California = Texas)
- No numeric comparison tolerance

---

## P25 - p25_aggregate.py

**Lines:** ~80
**Public API:**
- `aggregate_verdict(claim_text, A, B, delta) -> Dict`

### A. CURRENT FUNCTIONS

**Public:**
1. `aggregate_verdict()` - Aggregate arm strengths and compute verdict

**Internal:**
- `_arm_strength()` - Compute strength for single arm
- `_verdict_label()` - Determine verdict label from strengths

### B. SEMANTIC LOGIC PRESENT

✅ **Arm strength calculation** (Lines 20-40)
- Counts findings by stance
- Weights: entail/support (1.0), contextual (0.5), mixed (0.25), challenge/contradict (-1.0)
- Normalizes by item count

✅ **Verdict determination** (Lines 40-60)
- Compares arm_A vs arm_B strength
- Delta threshold (default 0.15)
- Returns: largely_true, largely_false, mostly_true, mostly_false, mixed, insufficient

✅ **Confidence scoring** (Lines 60-75)
- Based on strength magnitude and item count
- Returns confidence (0-1 scale)

### C. COMPARISON TO BEFORE

**BEFORE:** Same logic (was always in clean module)
**AFTER:** Unchanged - already working correctly

**STATUS:** ✅ WORKING

---

## P22 - fetch_enrichment.py

**Note:** Not analyzed in detail - primarily fetch/API enrichment logic, not semantic analysis.

---

## SEMANTIC CAPABILITIES SUMMARY

### ✅ IMPLEMENTED CAPABILITIES

| Feature | P20 | P21 | P23 | P24 | P25 | Shared |
|---------|-----|-----|-----|-----|-----|--------|
| Paraphrase matching | ✅ | ✅ | ⚠️ | ⚠️ | - | ✅ |
| Unit normalization | - | ⚠️ | - | - | - | ✅ |
| Condition recognition | ✅ | ✅ | - | - | - | ✅ |
| Numeric tolerance | ✅ | ✅ | - | ✅ | - | ✅ |
| Entity extraction | ✅ | ✅ | ✅ | ✅ | - | ✅ |
| Frame extraction | ✅ | - | - | ✅ | - | ✅ |
| Stance detection | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| Action vocabularies | ✅ | - | - | ✅ | - | ✅ |

Legend:
- ✅ Fully implemented and integrated
- ⚠️ Implemented but not yet integrated into module
- - Not applicable for this module

### ⚠️ DOCUMENTED LIMITATIONS

1. **Paraphrase system is dictionary-based**
   - Not semantic/embedding-based
   - Limited vocabulary
   - Post-Phase 2 upgrade planned

2. **P23 semantic enhancements not integrated**
   - Paraphrase utils imported but not used yet
   - Stemming not implemented
   - Synonym matching not implemented

3. **P24 semantic gaps**
   - No paraphrase understanding
   - No entity identity verification
   - No numeric comparison tolerance

4. **No embedding-based similarity**
   - All matching is keyword/dictionary-based
   - No semantic similarity scoring

---

## PHASE 2 IMPACT SUMMARY

### What Phase 2 Added

✅ **Shared utilities layer** (Days 1-5)
- 7 new modules with reusable semantic logic
- ~500 lines of centralized semantic capabilities

✅ **P20 frame-based redesign** (Task 9.2)
- Replaced keyword matching with frame-based reasoning
- Added condition awareness
- Added paraphrase detection
- New stance type: contextual_support

✅ **P21 semantic enhancements** (Task 8.1)
- Integrated paraphrase matching
- Added condition awareness
- Uses shared utilities

✅ **Integration work** (Days 6-7)
- Connected P23, P24 with shared utilities
- Text processing standardization
- Prepared for future semantic enhancements

### What Still Needs Work (Post-Phase 2)

❌ **Embedding-based semantic matching**
- Current: Dictionary/keyword-based
- Needed: Neural embeddings for semantic similarity

❌ **Complete P23 semantic integration**
- Paraphrase utils exist but not used
- Stemming/lemmatization needed
- Synonym expansion needed

❌ **P24 semantic enhancements**
- Entity identity verification
- Numeric tolerance in frame comparison
- Expanded action vocabulary

---

## CONCLUSION

### Before vs After Comparison

**BEFORE Phase 1+2:**
- Semantic logic existed in clean modules
- Keyword-based matching only
- Duplicated logic across modules
- No shared utilities

**AFTER Phase 1+2:**
- ✅ All semantic logic preserved
- ✅ Shared utilities layer created
- ✅ Frame-based reasoning added (P20)
- ✅ Condition awareness added (P20, P21)
- ✅ Paraphrase dictionaries added (shared)
- ✅ Centralized entity/unit/condition logic

**NET RESULT:** Significantly more semantic capabilities than before.

### Integration Status

| Module | Semantic Logic | Shared Utils | Status |
|--------|---------------|--------------|--------|
| P20 | ✅ Enhanced | ✅ Integrated | Complete |
| P21 | ✅ Enhanced | ✅ Integrated | Complete |
| P23 | ✅ Present | ⚠️ Partial | Ready for integration |
| P24 | ✅ Present | ⚠️ Partial | Ready for enhancement |
| P25 | ✅ Working | - | Complete |

**VERDICT:** Clean modules contain substantial semantic logic. Phase 2 added more than existed before. Any remaining gaps are enhancement opportunities, not restoration tasks.
