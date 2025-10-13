# P20 Stance Detection - Enhancement Analysis

## Executive Summary

**Current Status:** Basic keyword matching (increase/decrease/higher/lower)
**Target:** Frame-based reasoning with domain awareness
**Priority:** HIGH - affects all verdict quality
**Estimated Effort:** 2-3 days

**Key Finding:** The P20 "wrapper" (MONKEY_PATCH_ARCHIVE/wrappers/content/p20_wrapper.py) is just infrastructure that wraps the pipeline to call `attach_finding_to_item`. The actual stance detection logic IS in the clean module (`intelligence/content/grade.py`), but it's currently too simplistic.

**What's Missing:** Frame-based reasoning, numeric comparison, unit normalization, condition awareness, paraphrase understanding.

---

## 1. Current Implementation Analysis

### File: `intelligence/content/grade.py`

**Current Decision Logic:**
```python
def _stance_for_window(text: str, arm: str) -> str:
    t = (text or "").lower()
    is_inc = any(w in t for w in ("increase","increased","up","rise","grew","growth","higher"))
    is_dec = any(w in t for w in ("decrease","decreased","down","lower","reduced","reduction"))
    neg = any(w in t for w in ("not ","no ","false","incorrect","deny","dispute","refute","contradict","debunk"))

    stance = "unrelated"
    if is_inc and not neg:
        stance = "support"
    elif (is_dec and not neg) or (neg and is_inc):
        stance = "challenge"
    if is_inc and neg and arm.upper()=="A":
        stance = "mixed"
    return stance
```

**Limitations:**
1. **No phenomenon matching** - Doesn't check if evidence is about the same topic
2. **No numeric comparison** - "100°C" vs "90°C" both match as numbers, no contradiction detection
3. **No unit awareness** - "100 degrees Celsius" ≠ "100°C" in matching
4. **No condition parsing** - "at sea level" vs "at altitude" treated the same
5. **Policy-oriented keywords** - Designed for budget/economic claims (increase/decrease)
6. **No paraphrase understanding** - "boils" ≠ "boiling point"

**Example Failures:**

| Claim | Evidence | Current Stance | Correct Stance | Why It Fails |
|-------|----------|---------------|----------------|--------------|
| "Water boils at 100°C" | "Water boils at lower temps at altitude" | challenge ❌ | support ✓ | Keyword "lower" triggers challenge, ignores condition |
| "CA unemployment is 8%" | "CA unemployment dropped to 7%" | challenge ❌ | challenge ✓ | Numeric contradiction not detected |
| "Water boils at 100°C" | "H2O has a boiling point of 100 degrees Celsius" | unrelated ❌ | support ✓ | No paraphrase matching |

---

## 2. Semantic Features Needed

### A. Paraphrase Dictionaries

**Verb/Noun Form Families:**
```python
PARAPHRASE_FAMILIES = {
    "boil": ["boils", "boiling", "boiled", "boiling point", "boil temperature"],
    "increase": ["increased", "increases", "increasing", "rise", "rose", "rising", "growth", "grew", "went up", "climbed"],
    "decrease": ["decreased", "decreases", "decreasing", "decline", "declined", "fall", "fell", "drop", "dropped", "went down"],
    "unemployment": ["unemployed", "jobless", "joblessness", "unemployment rate", "without work"],
    "temperature": ["temp", "degrees", "°C", "°F", "celsius", "fahrenheit"]
}
```

**Usage:** Expand entity/concept matching beyond exact keywords.

### B. Unit Normalization Rules

**Temperature:**
```python
TEMP_UNITS = {
    "celsius": ["°C", "degrees celsius", "degrees C", "deg c", "celsius"],
    "fahrenheit": ["°F", "degrees fahrenheit", "degrees F", "deg f", "fahrenheit"]
}

def normalize_temperature(text: str, value: float) -> Tuple[float, str]:
    """Extract temperature and normalize to Celsius"""
    # "100 degrees Celsius" → (100.0, "celsius")
    # "212°F" → (100.0, "celsius")  # after conversion
```

**Money:**
```python
MONEY_UNITS = {
    "usd": ["$", "USD", "dollars", "dollar"],
    "percent": ["%", "percent", "percentage", "pct"]
}
```

**Distance:**
```python
DISTANCE_UNITS = {
    "meters": ["m", "meter", "meters", "metre"],
    "feet": ["ft", "foot", "feet", "'"]
}
```

### C. Condition Recognition

**Scientific Conditions:**
```python
CONDITION_PATTERNS = {
    "pressure": ["at sea level", "standard pressure", "1 atm", "atmospheric pressure",
                 "at altitude", "high altitude", "low pressure", "elevated"],
    "time": ["in 2020", "by 2022", "as of", "during", "before", "after"],
    "location": ["in California", "in CA", "in Texas", "nationwide", "nationally"]
}
```

**Condition Equivalences:**
```python
EQUIVALENT_CONDITIONS = {
    ("at sea level", "standard pressure"): True,
    ("at sea level", "at altitude"): False,
    ("in California", "in CA"): True,
    ("in 2020", "in 2021"): False
}
```

### D. Numeric Tolerance Settings

**For Numeric Comparison:**
```python
NUMERIC_TOLERANCES = {
    "temperature": 0.5,    # ±0.5°C
    "percentage": 0.1,     # ±0.1%
    "currency": 100,       # ±$100
    "year": 0              # Exact match for years
}

def numbers_match(claim_val: float, evidence_val: float, domain: str) -> str:
    """
    Returns: "exact", "close", "contradiction", or "unrelated"
    - exact: Within tolerance
    - close: Within 2x tolerance
    - contradiction: Opposite direction or large difference
    """
```

---

## 3. Frame-Based Decision Logic

### Proposed Decision Tree

```
1. PHENOMENON MATCH
   ├─ Does evidence mention the same phenomenon?
   │  (boils → boiling point, unemployment → jobless)
   │  ├─ YES → Continue to step 2
   │  └─ NO  → Return "unrelated"
   │
2. NUMERIC/UNIT CHECK
   ├─ Does claim have numbers/units?
   │  ├─ YES → Extract and normalize both
   │  │        ├─ Values match (±tolerance)? → Support
   │  │        ├─ Values contradict? → Challenge
   │  │        └─ Different values? → Check conditions (step 3)
   │  └─ NO  → Skip to step 4
   │
3. CONDITION AWARENESS
   ├─ Do claim and evidence have conditions?
   │  (at sea level, in 2020, in California)
   │  ├─ Conditions match? → Apply numeric comparison result
   │  ├─ Conditions differ but compatible?
   │  │  (e.g., "at altitude" explains variation in boiling point)
   │  │  → Return "support" with contextual note
   │  └─ Conditions incompatible? → Return "unrelated"
   │
4. DIRECTIONAL CUES (for policy claims)
   ├─ Keywords: increase/decrease/higher/lower
   │  ├─ Aligned with arm? → Support/Challenge
   │  └─ Negation present? → Invert
   │
5. DEFAULT
   └─ Return "unrelated" if no clear stance detected
```

### Example Walkthrough

**Claim:** "Water boils at 100 degrees Celsius at sea level"

**Evidence 1:** "Water has a boiling point of 100°C at standard pressure"
```
1. Phenomenon: "boils" ~ "boiling point" ✓
2. Numeric: 100 = 100 ✓
3. Condition: "at sea level" ~ "standard pressure" ✓
→ Result: SUPPORT
```

**Evidence 2:** "Water boils at lower temperatures at high altitude"
```
1. Phenomenon: "boils" ~ "boils" ✓
2. Numeric: No specific value in evidence
3. Condition: "at sea level" ≠ "at high altitude" but explains variation ✓
4. Directional: "lower" BUT different condition context
→ Result: SUPPORT (contextual: explains variation)
```

**Evidence 3:** "Water boils at 90°C"
```
1. Phenomenon: "boils" ~ "boils" ✓
2. Numeric: 100 ≠ 90 (contradiction)
3. Condition: No condition specified (assumes same as claim)
→ Result: CHALLENGE (numeric contradiction)
```

---

## 4. Integration Points

### File Structure

```
intelligence/content/
├── grade.py (current)
├── paraphrases.py (NEW) - Paraphrase families and synonym dictionaries
├── units.py (NEW) - Unit normalization and conversion
├── conditions.py (NEW) - Condition extraction and comparison
└── frame_logic.py (NEW) - Frame-based decision tree
```

### A. New Helper Modules

**paraphrases.py:**
```python
PARAPHRASE_FAMILIES = { ... }

def expand_concept(word: str) -> List[str]:
    """Return all paraphrases of a word/phrase"""

def concepts_match(claim_text: str, evidence_text: str) -> Tuple[bool, List[str]]:
    """Check if claim and evidence share concepts"""
```

**units.py:**
```python
def extract_numeric_value(text: str) -> Optional[Tuple[float, str, str]]:
    """Extract (value, unit, domain) from text"""
    # "100 degrees Celsius" → (100.0, "celsius", "temperature")

def normalize_value(value: float, unit: str, domain: str) -> float:
    """Normalize to standard unit"""
    # (212, "fahrenheit", "temperature") → 100.0

def values_match(claim_val: Tuple, evidence_val: Tuple) -> str:
    """Compare normalized values"""
    # Returns: "exact", "close", "contradiction", "unrelated"
```

**conditions.py:**
```python
def extract_conditions(text: str) -> List[Tuple[str, str]]:
    """Extract (condition_type, condition_value) from text"""
    # "at sea level in 2020" → [("pressure", "sea level"), ("time", "2020")]

def conditions_match(claim_conditions: List, evidence_conditions: List) -> str:
    """Compare conditions"""
    # Returns: "equivalent", "different_but_compatible", "incompatible"
```

**frame_logic.py:**
```python
def analyze_stance_with_frames(
    claim_text: str,
    evidence_text: str,
    arm: str
) -> Tuple[str, List[str]]:
    """
    Main decision tree implementation.
    Returns: (stance, rationale_items)
    """
    # Implement the decision tree from section 3
```

### B. Updated grade.py

**Replace `_stance_for_window` with:**
```python
def _stance_for_window_v2(claim_text: str, window_text: str, arm: str) -> Tuple[str, List[str]]:
    """
    Enhanced stance detection with frame-based reasoning.
    Returns: (stance, rationale)
    """
    from intelligence.content.frame_logic import analyze_stance_with_frames
    return analyze_stance_with_frames(claim_text, window_text, arm)
```

**Update `build_finding`:**
```python
def build_finding(claim_text: str, arm: str, content_text: str, ...):
    # ... existing window selection ...

    # NEW: Frame-based stance detection
    stance, frame_rationale = _stance_for_window_v2(claim_text, window, arm)

    # Merge frame rationale with existing scoring rationale
    rationale: List[str] = frame_rationale + [...]

    # ... rest of scoring ...
```

### C. Backward Compatibility

**Preserve existing API:**
- `attach_finding_to_item(claim_text, arm, item)` - Same signature
- `build_finding(...)` - Same signature, enhanced internals
- Return structure - Same fields, better values

**Gradual rollout:**
1. Add new modules (paraphrases, units, conditions, frame_logic)
2. Add feature flag: `USE_FRAME_LOGIC = os.getenv("ROGR_USE_FRAME_LOGIC", "0") == "1"`
3. Test in parallel: Compare old vs new stance
4. Replace when validated

---

## 5. Testing Scenarios

### A. Scientific Claims (Currently Failing)

**Test 1: Basic Boiling Point**
```python
claim = "Water boils at 100 degrees Celsius"
evidence = "Water has a boiling point of 100°C at standard atmospheric pressure"
expected = "support"
rationale_should_include = [
    "phenomenon matched (boils ~ boiling point)",
    "numeric value matched (100 = 100)",
    "condition matched (implied sea level ~ standard pressure)"
]
```

**Test 2: Altitude Variation**
```python
claim = "Water boils at 100 degrees Celsius at sea level"
evidence = "Water boils at lower temperatures at high altitude"
expected = "support"  # Contextual support (explains variation)
rationale_should_include = [
    "phenomenon matched (boils)",
    "contextual condition (sea level vs altitude explains variation)"
]
```

**Test 3: Numeric Contradiction**
```python
claim = "Water boils at 100 degrees Celsius"
evidence = "Water boils at 90 degrees Celsius"
expected = "challenge"
rationale_should_include = [
    "phenomenon matched (boils)",
    "numeric contradiction (100 vs 90)"
]
```

### B. Policy Claims (Should Still Work)

**Test 4: Budget Increase**
```python
claim = "California increased education spending by 8 percent"
evidence = "CA education budget grew by 8% in 2022"
expected = "support"
rationale_should_include = [
    "phenomenon matched (spending ~ budget)",
    "numeric value matched (8% = 8%)",
    "directional matched (increased ~ grew)"
]
```

**Test 5: Budget Contradiction**
```python
claim = "Texas increased spending by 5 percent"
evidence = "Texas cut spending by 5 percent"
expected = "challenge"
rationale_should_include = [
    "phenomenon matched (spending)",
    "directional contradiction (increased vs cut)"
]
```

### C. Edge Cases

**Test 6: No Numeric Value**
```python
claim = "Unemployment is high"
evidence = "Jobless rates have increased significantly"
expected = "support"
rationale_should_include = [
    "phenomenon matched (unemployment ~ jobless)",
    "directional matched (high ~ increased)"
]
```

**Test 7: Different Phenomena**
```python
claim = "Water boils at 100 degrees"
evidence = "The unemployment rate is 8 percent"
expected = "unrelated"
rationale_should_include = [
    "phenomenon not matched (water vs unemployment)"
]
```

**Test 8: Unit Conversion**
```python
claim = "Water boils at 212 degrees Fahrenheit"
evidence = "Water has a boiling point of 100 degrees Celsius"
expected = "support"
rationale_should_include = [
    "phenomenon matched (boils ~ boiling point)",
    "numeric value matched after conversion (212°F = 100°C)"
]
```

---

## 6. Implementation Phases

### Phase 1: Foundation (Day 1 Morning)
- Create paraphrases.py with basic families
- Create units.py with temperature normalization
- Create conditions.py with pattern extraction
- Write unit tests for each module

### Phase 2: Frame Logic (Day 1 Afternoon)
- Create frame_logic.py with decision tree
- Implement phenomenon matching
- Implement numeric comparison
- Implement condition awareness
- Write integration tests

### Phase 3: Integration (Day 2 Morning)
- Update grade.py to use new frame logic
- Add feature flag for gradual rollout
- Test with P20 test suite
- Fix any regressions

### Phase 4: Validation (Day 2 Afternoon - Day 3)
- Run end-to-end tests
- Compare old vs new stance assignments
- Validate scientific claim handling
- Validate policy claim handling
- Document any remaining gaps
- Remove feature flag and deploy

---

## 7. Success Criteria

**Must Pass:**
- ✅ All 8 test scenarios above pass
- ✅ No regressions on existing policy claim tests
- ✅ Scientific claims correctly handled (water boiling example)
- ✅ Numeric contradictions detected
- ✅ Condition awareness working (sea level vs altitude)

**Quality Metrics:**
- Stance accuracy on test set: > 85%
- False positive rate (unrelated marked as support/challenge): < 10%
- Scientific claim accuracy: > 90%
- Policy claim accuracy: > 85%

**Documentation:**
- Updated docs/SEMANTIC_GAPS.md with P20 status → COMPLETE
- New test suite in tests/test_p20_frames.py
- Architecture doc for frame-based logic

---

## 8. Risk Assessment

**Low Risk:**
- Paraphrase matching (additive, doesn't break existing)
- Unit normalization (isolated module)

**Medium Risk:**
- Condition awareness (complex, many edge cases)
- Decision tree logic (core algorithm change)

**Mitigation:**
- Feature flag for gradual rollout
- Comprehensive test coverage
- Parallel comparison (old vs new)
- User feedback loop

**Rollback Plan:**
- Keep old `_stance_for_window` as `_stance_for_window_legacy`
- If issues arise, toggle feature flag off
- All existing tests still pass with old logic

---

## 9. Future Enhancements (Post-Phase 2)

**Beyond Initial Rebuild:**
- Machine learning stance classifier (trained on fact-checking data)
- Context-aware LLM fallback for ambiguous cases
- Claim-type specific adapters (scientific, policy, historical)
- Multi-language support
- Temporal reasoning (before/after, trends)

**Data-Driven Improvements:**
- Collect misclassified examples
- Expand paraphrase dictionaries from real data
- Tune numeric tolerances based on domain
- Build condition equivalence knowledge base

---

*This analysis provides a complete roadmap for restoring P20 semantic intelligence. Implementation can begin immediately with the foundation modules.*
