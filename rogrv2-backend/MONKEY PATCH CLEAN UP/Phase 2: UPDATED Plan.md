# Phase 2: Semantic Intelligence Enhancement - UPDATED Execution Plan

**Based on:** `docs/SEMANTIC_LOGIC_INVENTORY.md` (comprehensive audit completed)

**Goal:** Restore semantic intelligence by extracting shared utilities first, then integrating them into content modules, while maintaining IFCN compliance throughout.

**Duration:** 12-15 days

**Testing Philosophy:** FULL PRODUCTION MODE - Every enhancement must pass individual, integration, E2E, and real claims testing before proceeding.

---

## 🎯 STRATEGIC APPROACH (Based on Inventory Findings)

**Key Discovery:** 64% of needed logic already exists but is scattered across modules!

**New Strategy:**
1. **Phase 2A (Days 1-2):** Extract & centralize existing logic → shared utilities
2. **Phase 2B (Days 3-5):** Build missing components (conditions, paraphrases, frames)
3. **Phase 2C (Days 6-10):** Integrate shared utilities into P20-P24
4. **Phase 2D (Days 11-12):** Testing & validation
5. **Phase 2E (Days 13-15):** Optional orchestration enhancements (P27-P29)

**Benefits:**
- ✅ Avoid rebuilding existing logic
- ✅ Single source of truth for each feature
- ✅ Faster implementation (reuse > rebuild)
- ✅ Consistent behavior across modules

---

## 📋 INVENTORY SUMMARY

**Status:** ✅ COMPLETE - `docs/SEMANTIC_LOGIC_INVENTORY.md`

**Findings:**
- **Modules Audited:** 7 (P20, P21, P23, P24, P27, P28, P29)
- **Total Features:** 56
- **Reusable:** 36 (64%) 
- **Gaps:** 20 (36%)

**Key Discoveries:**
- ✅ **P21 has gold-standard tolerance logic** (dual absolute + relative)
- ✅ **P24 has excellent frame structure** (foundation for all modules)
- ✅ **Most text utilities exist** (just duplicated - need consolidation)
- ✅ **P27-P29 are pure orchestration** (config enhancements, not semantic logic)

**Major Gaps to Fill:**
- ❌ Condition recognition (pressure, temporal, location)
- ❌ Paraphrase families (verb ↔ noun, scientific domain)
- ❌ Relationship detection (causal, temporal, conditional)

---

## 🗓️ EXECUTION TIMELINE

### ✅ Pre-Phase 2: Inventory (COMPLETE)
- [X] Comprehensive semantic logic audit
- [X] Created `docs/SEMANTIC_LOGIC_INVENTORY.md`
- [X] Identified reuse strategy

### Phase 2A: Extract & Centralize (Days 1-2)
- [ ] **Day 1:** Core utilities (text_utils, vocabulary)
- [ ] **Day 2:** Numeric & entity utilities (units, entities)

### Phase 2B: Build Missing (Days 3-5)
- [ ] **Day 3:** Conditions system (NEW)
- [ ] **Day 4:** Frames system (from P24)
- [ ] **Day 5:** Paraphrase enhancement

### Phase 2C: Module Integration (Days 6-10)
- [ ] **Day 6:** Update P24 (easiest)
- [ ] **Day 7:** Update P23
- [ ] **Day 8:** Update P21
- [ ] **Days 9-10:** Update P20 (hardest - major redesign)

### Phase 2D: Testing & Validation (Days 11-12)
- [ ] **Day 11:** Comprehensive testing
- [ ] **Day 12:** Documentation & sign-off

### Phase 2E: Orchestration (Days 13-15) - OPTIONAL
- [ ] **Day 13:** P27 consensus enhancements
- [ ] **Day 14:** P28 & P29 config enhancements
- [ ] **Day 15:** Final integration

---

## 📖 DETAILED TASK BREAKDOWN

### PHASE 2A: EXTRACT & CENTRALIZE EXISTING LOGIC

---

## DAY 1: CORE SHARED UTILITIES

### Task 1.1: Create `shared/text_utils.py`

**What:** Consolidate duplicate text processing functions

**From:** P20, P21, P23, P24 all have `_norm()`, `_tokens()`, `_trigrams()`, etc.

**Success:** Single source of truth, no duplicates, unit tests pass

**Time:** 2-3 hours

**Prompt:**
```bash
Create intelligence/content/shared/text_utils.py

Consolidate from all modules:
- normalize_text() from _norm()
- tokenize() from _tokens() 
- trigrams() from _trigrams()
- jaccard_similarity() from _jaccard()
- split_sentences() from _split_sentences()
- sliding_windows() for window creation

Create tests/test_shared_text_utils.py with full coverage.
```

### Task 1.2: Create `shared/vocabulary.py`

**What:** Merge action families, negation, stance verbs

**From:** 
- P24 INC_VERBS, DEC_VERBS
- extract_facts PRED_INCREASE, PRED_DECREASE  
- All modules have negation lists
- P21/P23 have meta-stance verbs

**Success:** Comprehensive word lists, no conflicts

**Time:** 2-3 hours

**Prompt:**
```bash
Create intelligence/content/shared/vocabulary.py

Merge from modules:
- INC_VERBS (increase verbs from P24 + extract_facts)
- DEC_VERBS (decrease verbs)
- NEGATION_WORDS (from all modules)
- SUPPORT_VERBS (from P21/P23)
- CHALLENGE_VERBS (from P21/P23)
- BUDGET_CONTEXT (from P24)

Helper functions:
- is_action_verb(word) → 'increase'|'decrease'|None
- is_negation(text) → bool

Create tests/test_shared_vocabulary.py
```

### Tasks 1.3-1.4: Test & IFCN Compliance

Standard testing and compliance verification.

---

## DAY 2: NUMERIC & ENTITY UTILITIES

### Task 2.1: Create `shared/units.py`

**What:** Extract P21's gold-standard tolerance logic, add conversions

**From:** P21 (gold standard) + P24 + extract_facts

**Success:** Dual tolerance working, conversions accurate

**Time:** 3-4 hours

**Prompt:**
```bash
Create intelligence/content/shared/units.py

Extract P21's gold-standard tolerance (lines 80-105):
- Dual tolerance: absolute ±0.5 AND relative ±10%
- percent_match() function

Add conversions:
- Temperature (°C ↔ °F ↔ K)
- Distance (km ↔ miles ↔ meters)
- Money ($1M = $1,000,000)

API:
- extract_percentage(text) → List[float]
- extract_temperature(text) → List[Tuple[float, str]]
- normalize_temperature(value, unit) → float (to Celsius)
- values_match(v1, v2, tol_abs, tol_rel) → (bool, reason)

Create tests/test_shared_units.py with conversion tests.
```

### Task 2.2: Create `shared/entities.py`

**What:** Consolidate entity extraction

**From:** extract_facts + P24 + P21

**Success:** Capitalization + domain filtering working

**Time:** 2-3 hours

**Prompt:**
```bash
Create intelligence/content/shared/entities.py

Consolidate:
- extract_facts capitalization logic
- P24 domain-aware filtering
- P21 overlap scoring

API:
- extract_entities(text, domain) → List[str]
- entity_overlap_score(claim_ents, evidence_ents) → float
- entities_match(claim_ents, evidence_ents) → (bool, reason)

Create tests/test_shared_entities.py
```

### Tasks 2.3-2.4: Test & IFCN Compliance

Standard testing and compliance verification.

---

### PHASE 2B: BUILD MISSING COMPONENTS

---

## DAY 3: CONDITIONS SYSTEM (NEW - GAP)

### Task 3.1: Create `shared/conditions.py`

**What:** Build condition recognition and equivalence (doesn't exist anywhere)

**Gap:** Needed for scientific claims (pressure, altitude, temporal)

**Success:** Condition extraction and equivalence working

**Time:** Full day

**Prompt:**
```bash
Create intelligence/content/shared/conditions.py

Build NEW condition system:

1. Pressure conditions:
   - Patterns: "at sea level", "at altitude", "1 atm", "101.325 kPa"
   - Equivalence: sea level = standard pressure = 1 atm

2. Temporal conditions:
   - Patterns: "in FY2024", "fiscal year 2024", "Q3 2023"
   - Equivalence: FY2024 = fiscal year 2024

3. Location conditions:
   - Patterns: "in California", "statewide", "nationwide"

@dataclass
class Condition:
    type: str  # "pressure", "time", "location"
    value: str
    normalized: str

API:
- extract_conditions(text) → List[Condition]
- conditions_compatible(c1, c2) → 'equivalent'|'compatible'|'incompatible'

Create tests/test_shared_conditions.py with scientific examples.
```

---

## DAY 4: FRAMES SYSTEM (FROM P24)

### Task 4.1: Create `shared/frames.py`

**What:** Extract P24's excellent frame structure, enhance for multi-domain

**From:** P24 (lines 121-206) - already working well

**Success:** Frames work for budget AND scientific domains

**Time:** Full day

**Prompt:**
```bash
Create intelligence/content/shared/frames.py

Extract P24 foundation (lines 121-144, 177-206):
- Frame dataclass
- extract_claim_frame()
- extract_window_frame()
- _entail_contradict() logic

ENHANCE:
- Add condition field (from Day 3)
- Add domain field ("budget", "scientific", "generic")
- Multi-domain adapters

@dataclass
class Frame:
    entity: List[str]
    action: str  # "increase"|"decrease"|"unknown"
    quantity: List[float]
    year: List[int]
    scope: str
    condition: Optional[Condition] = None  # NEW
    domain: str = "unknown"  # NEW

API:
- extract_frame(text, domain) → Frame
- compare_frames(claim, evidence) → ('entail'|'contradict'|'mixed'|'unrelated', rules)

Create tests/test_shared_frames.py with budget + scientific examples.
```

---

## DAY 5: PARAPHRASE ENHANCEMENT

### Task 5.1: Enhance `shared/vocabulary.py`

**What:** Add paraphrase families (verb ↔ noun, scientific domain)

**Gap:** Exists partially, needs expansion

**Success:** Scientific + policy paraphrases working

**Time:** Full day

**Prompt:**
```bash
Enhance intelligence/content/shared/vocabulary.py

ADD paraphrase families:

1. Scientific domain:
   - Verb ↔ Noun: "boil" → ["boils", "boiling", "boiling point", "boil temperature"]
   - Phenomena: "freeze" → ["freezes", "freezing", "freezing point", "solidification"]

2. Synonym expansion:
   - "unemployment" → ["unemployment", "jobless", "joblessness", "without work"]

3. Domain vocabularies:
   SCIENTIFIC_CONTEXT = {"temperature", "pressure", "altitude", "boiling", "freezing", ...}

API additions:
- expand_synonyms(word, domain) → Set[str]
- get_paraphrase_family(word) → Set[str]
- is_paraphrase(word1, word2) → bool

Create tests/test_shared_paraphrases.py with:
- Verb/noun mapping tests
- Scientific domain tests
- Synonym expansion tests
```

---

### PHASE 2C: MODULE INTEGRATION

---

## DAY 6: UPDATE P24 (EASIEST)

**Why easiest:** P24 already has best logic, just needs to import from shared and fix action bug

### Task 6.1: Import from Shared Modules

**Prompt:**
```bash
Update P24 to use shared utilities.

REPLACE local implementations with imports:
- from shared.text_utils import normalize_text, tokenize, ...
- from shared.vocabulary import INC_VERBS, DEC_VERBS, is_negation, ...
- from shared.units import extract_percentage, values_match, ...
- from shared.entities import extract_entities, entities_match, ...

Remove duplicate code, keep only P24-specific logic.
```

### Task 6.2: Fix Action Alignment Bug

**THE BUG (lines 189-190):**
- Assumes ANY "decrease" in evidence = contradiction
- Doesn't compare claim action vs evidence action
- Example: Claim "decreased 5%" + Evidence "decreased 5%" → contradict ❌

**The Fix:**
```bash
Fix action alignment bug in P24.

CURRENT (buggy):
if action == "decrease" and (eok and sok):
    label = "contradict"

FIX:
1. Extract action from BOTH claim and evidence
2. Compare: 
   - increase + increase = entail
   - decrease + decrease = entail
   - increase + decrease = contradict
   - decrease + increase = contradict

Use shared/frames.py compare_frames() logic.
```

### Task 6.3: Add Condition Awareness

**Prompt:**
```bash
Add condition awareness to P24 frames.

Import from shared.conditions:
- extract_conditions()
- conditions_compatible()

Update entailment logic:
- If numbers match BUT different conditions → contextual support
- If conditions incompatible → explain variation
```

### Tasks 6.4-6.8: Testing Suite

Full testing: individual → integration → E2E → real claims → IFCN compliance

---

## DAY 7: UPDATE P23

**Complexity:** Medium - add paraphrases and units

### Tasks 7.1-7.8

Similar structure to Day 6:
1. Import shared utilities
2. Add paraphrase matching to similarity
3. Add unit normalization for numbers
4. Full testing suite

---

## DAY 8: UPDATE P21

**Complexity:** Medium - add paraphrases and conditions

### Tasks 8.1-8.8

Similar structure to Day 6:
1. Import shared utilities (P21's tolerance becomes the shared standard)
2. Add paraphrase expansion before trigram matching
3. Add condition extraction to signals
4. Full testing suite

---

## DAYS 9-10: UPDATE P20 (HARDEST)

**Complexity:** High - complete redesign from keyword to frame-based

### Task 9.1: Replace Keyword Stance with Frame-Based Logic

**CURRENT (buggy):**
```python
# P20 grade.py lines 54-56
is_inc = any(w in t for w in ("increase","higher","up"))
is_dec = any(w in t for w in ("decrease","lower","down"))
# Returns "support" or "challenge"
```

**PROBLEMS:**
- No phenomenon matching (water vs unemployment)
- No numeric comparison
- No unit awareness
- No condition handling
- Breaks on scientific claims

**NEW (frame-based):**
```python
# Import from shared modules
from shared.frames import extract_frame, compare_frames
from shared.conditions import extract_conditions
from shared.units import values_match

# Decision tree:
# 1. Extract frames from claim and evidence
# 2. Check phenomenon match (same topic?)
# 3. Check numeric match (with unit normalization)
# 4. Check condition compatibility
# 5. Return stance based on frame comparison
```

### Task 9.2: Implement Decision Tree

**Prompt:**
```bash
Implement frame-based decision tree in P20.

DECISION TREE (in order):

1. PHENOMENON MATCH
   - Extract frames from claim and evidence
   - Same entity + same action type? → proceed
   - Different? → "unrelated"

2. NUMERIC COMPARISON
   - Extract numbers with units
   - Normalize units (100°C = 212°F)
   - Compare with tolerance
   - Match? → check conditions

3. CONDITION AWARENESS
   - Extract conditions from both
   - conditions_compatible()?
   - Same conditions + numeric match → "support"
   - Different conditions + numeric match → "contextual_support"
   - Same conditions + numeric mismatch → "challenge"

4. DIRECTIONAL CUES (fallback for non-numeric)
   - Compare actions (increase vs decrease)
   - Aligned → "support"
   - Opposite → "challenge"

5. DEFAULT → "unrelated"

Implement in intelligence/content/grade.py
```

### Tasks 9.3-9.10: Implementation & Testing

- Add phenomenon matching
- Add numeric comparison with unit normalization
- Add condition awareness
- Full testing suite (emphasize scientific claims!)

---

### PHASE 2D: TESTING & VALIDATION

---

## DAY 11: COMPREHENSIVE TESTING

### Task 11.1: Full Regression Suite

**Prompt:**
```bash
Run all P20-P24 tests.

pytest tests/test_p20*.py tests/test_p21*.py tests/test_p23*.py tests/test_p24*.py -v

Verify:
- All existing tests still pass
- No regressions
- New features working
```

### Task 11.2: Scientific Claim Test Suite

**Prompt:**
```bash
Test scientific claims (previously failing).

Test cases:
1. "Water boils at 100°C at sea level"
   + "Boiling point is 212°F at standard pressure"
   → SUPPORT ✓ (was mixed/insufficient ❌)

2. "Water boils at 100°C"
   + "Boiling point lower at high altitude"
   → CONTEXTUAL_SUPPORT ✓ (was challenge ❌)

3. "Ice melts at 0°C"
   + "Freezing point is 32°F"
   → SUPPORT ✓

Run full suite, document results.
```

### Task 11.3: Policy Claim Test Suite

**Prompt:**
```bash
Test policy claims (should still work).

Test cases:
1. "Austin budget increased 8%"
   + "Austin spending grew 8 percent"
   → SUPPORT ✓

2. "California decreased spending"
   + "California spending fell"
   → SUPPORT ✓ (was contradict due to P24 bug ❌)

Verify no regressions.
```

### Tasks 11.4-11.6: Performance & Memory

- Performance benchmarking (compare to Phase 1)
- Memory leak verification
- Load testing

---

## DAY 12: DOCUMENTATION & SIGN-OFF

### Task 12.1: Update SEMANTIC_GAPS.md

**Prompt:**
```bash
Update docs/SEMANTIC_GAPS.md

Mark P20-P24 as COMPLETE:
- P20: ✅ ENHANCED - Frame-based stance detection
- P21: ✅ ENHANCED - Paraphrase & normalization
- P23: ✅ ENHANCED - Semantic findings
- P24: ✅ ENHANCED - Action alignment fixed, multi-domain frames

Add summary of improvements.
```

### Task 12.2: Create Shared Utilities API Docs

**Prompt:**
```bash
Create docs/SHARED_UTILITIES_API.md

Document all shared modules:
- text_utils API
- vocabulary API
- units API
- entities API
- conditions API
- frames API

Include usage examples.
```

### Task 12.3: Create Phase 2 Completion Report

**Prompt:**
```bash
Create docs/PHASE2_COMPLETION_REPORT.md

Summary:
- What was enhanced (P20-P24)
- Shared utilities created (6 modules)
- Test results (pass rates, improvements)
- Performance impact
- IFCN compliance maintained
- Before/after examples
```

### Tasks 12.4-12.5: IFCN & Final Sign-off

- IFCN compliance documentation
- Final validation checklist

---

### PHASE 2E: ORCHESTRATION ENHANCEMENTS (OPTIONAL)

---

## DAY 13: P27 CONSENSUS ENHANCEMENT

**What:** Restore wrapper's variable formulas

**Current:** Fixed adjustments (+0.10, -0.05, -0.10)

**Wrapper had:**
- Variable bonus: `min(0.20, 0.10 + 0.50 * abs(c1 - c2))`
- Variable penalty: `min(0.30, 0.15 + 0.50 * abs(c1 - c2))`
- Average confidence: `(c1 + c2) / 2.0`

**Prompt:**
```bash
Enhance P27 consensus with variable formulas.

UPDATE: intelligence/pipeline/consensus.py (or similar)

Replace fixed adjustments with wrapper's variable formulas.

Test consensus behavior with edge cases.
```

---

## DAY 14: P28 & P29 ENHANCEMENTS

### P28 Enhancements

**What:** Multi-env-var provider detection, arm name mapping

**Prompt:**
```bash
Enhance P28 diversification.

1. Multi-env-var provider detection:
   BING_API_KEY or BING_SUBSCRIPTION_KEY or AZURE_BING_KEY

2. Arm name mapping:
   "A_SUPPORT" → "A", "ARM_A" → "A"

UPDATE: intelligence/planning/diversify.py
```

### P29 Enhancements

**What:** Enhanced manifest fields (knobs, parity, environment snapshot)

**Prompt:**
```bash
Enhance P29 telemetry for full reproducibility.

ADD to manifest:
1. providers_available (environment snapshot)
2. knobs per lane (query_shuffle, timeout_jitter_ms, max_per_provider)
3. parity.providers_equal (R1 vs R2 provider equality)
4. diversified flag

Consider: Auto-telemetry via ContextVar

UPDATE: intelligence/telemetry/collect.py
```

---

## DAY 15: FINAL INTEGRATION

### Task 15.1: Full System Integration Test

**Prompt:**
```bash
Run complete system test.

Test full pipeline with all enhancements:
- P20-P24 semantic enhancements
- P27-P29 orchestration enhancements
- Dual researchers + consensus
- Manifest generation

Verify end-to-end flow.
```

### Task 15.2: Replay Verification

**Prompt:**
```bash
Test perfect reproducibility.

1. Run claim with specific config
2. Save manifest
3. Replay using manifest
4. Verify identical results

Validate P29 reproducibility features.
```

### Task 15.3: Production Readiness

Final checklist before deployment.

---

## SUCCESS CRITERIA

### Technical Validation:
- ✅ All unit tests passing (P20-P24 + shared)
- ✅ All integration tests passing
- ✅ All E2E tests passing
- ✅ Real claims: 80%+ improved/same
- ✅ No regressions
- ✅ Performance: max 20% slower
- ✅ Memory: stable (no leaks)

### IFCN Compliance:
- ✅ P20-P24 maintain method transparency
- ✅ Shared utilities documented
- ✅ Evidence trails preserved
- ✅ Decision rules documented
- ✅ Audit trail complete
- ✅ Reproducibility verified (P29)

### Deliverables:
- ✅ 6 shared utility modules
- ✅ P20-P24 enhanced modules
- ✅ P27-P29 enhanced (optional)
- ✅ Complete test suite
- ✅ API documentation
- ✅ Completion report

---

## FILE LOCATIONS

**To access this plan:**
```bash
# From terminal/Claude Code:
cat /mnt/user-data/outputs/PHASE2_EXECUTION_PLAN_UPDATED.md

# Or download from:
/mnt/user-data/outputs/PHASE2_EXECUTION_PLAN_UPDATED.md
```

**Related documents:**
- Inventory: `docs/SEMANTIC_LOGIC_INVENTORY.md`
- Semantic gaps: `docs/SEMANTIC_GAPS.md`
- Plain English summary: `/tmp/phase2_semantic_enhancements_summary.md`

---

**Phase 2 is now optimized for maximum reuse and minimum duplication! 🚀**