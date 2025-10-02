# SESSION ZERO-A PROMPT - Design Phase 0 + 1A Specifications

**Purpose:** Design COMPLETE specifications for Phase 0 (regression tests) and Phase 1A (integration fixes)

**Instructions:** Copy-paste this entire document into a fresh Claude Code session.

---

## Overview

This is **Session Zero-A** - the first of three design sessions for ROGRv2 Backend completion.

You will design complete, detailed specifications for:
- **Phase 0:** Regression test suite (S6 harness)
- **Phase 1A:** Integration fixes (pipeline.py, run.py, online.py wiring)

**Critical:** These specifications must be COMPLETE. No outlines, no TBDs, no "implementation will decide." Implementation sessions will execute your specs exactly as written.

---

## Your Deliverables

You MUST produce:

1. **DESIGN_SPECIFICATIONS_PHASE_0_1A.md** (~25-35KB)
   - Complete Phase 0 specifications
   - Complete Phase 1A specifications

2. **step_prompts/step01_phase0.md** (~2-3KB)
   - Copy-paste ready prompt for implementing Phase 0

3. **step_prompts/step02_phase1a.md** (~2-3KB)
   - Copy-paste ready prompt for implementing Phase 1A

4. **MASTER_PLAN_PARTIAL.md** (~8-10KB)
   - Step 01-02 breakdown with dependencies, token estimates, risks

**Token Budget:** 80-100K (spillover acceptable if needed for completeness)

---

## Required Reading (In Order)

### 1. Behavior Guidelines
**File:** `implementation_plan/TENANTS.md`
**Why:** Understand investigation requirements (Tenant 4), permission requirements (Tenant 6)

### 2. Source of Truth - Phase 0 Context
**File:** `verification_package/SOURCE_OF_TRUTH_ROGRV2_COMPLETE.md`
**Read these sections:**
- Section 8: Completion Plan - Phase 0 description (lines ~580-610)
- Section 9: Detailed File Evidence for P1-P13 (lines ~640-1100) - Need to understand what each packet does to test it

**Why:** Understand what regression tests must validate

### 3. Source of Truth - Phase 1A Context
**File:** `verification_package/SOURCE_OF_TRUTH_ROGRV2_COMPLETE.md`
**Read these sections:**
- Section 4: What's Broken (lines ~210-280) - The 3 integration gaps
- Section 8: Completion Plan - Phase 1A description (lines ~610-640)
- File evidence for pipeline.py, run.py, online.py (Section 9)

**Why:** Understand exactly what's broken and needs fixing

### 4. Architect Context
**File:** `verification_package/architect_answers_session3.md`
**Read:**
- B4 (S6 regression harness - lines ~220-260)
- Question about async/await patterns

**Why:** Architect's guidance on testing approach

---

## PART 0: Investigation (REQUIRED - Tenant 4)

Before designing specifications, you MUST investigate actual code.

### Files to Read and Analyze

**For Phase 0 (understanding what to test):**
- `intelligence/claims/extract.py` - P1 packet (understand output structure)
- `intelligence/claims/interpret.py` - P2 packet (understand output structure)
- `intelligence/rank/select.py` - P4 packet (understand output structure)
- `intelligence/analyze/stance.py` - P7 packet (understand output structure)

**For Phase 1A (understanding what to fix):**
- `intelligence/gather/pipeline.py` (focus on lines 32-68 - the bug area)
- `intelligence/pipeline/run.py` (focus on lines 29-44 - sync vs async issue)
- `intelligence/gather/online.py` (focus on lines 73-127 - understand the interface)
- `api/analyses.py` (understand how run_preview is called from API)

### Investigation Report Format

After reading code, produce:

```markdown
## 🔍 CODE INVESTIGATION

### Phase 0 Context
**P1-P13 Packet Outputs:**
- P1 (extract_claims): Returns [structure found in code]
- P2 (interpret): Returns [structure found in code]
- P3-P13: [key output structures]

**What tests must validate:**
- [List based on actual code review]

### Phase 1A Context
**Current Implementation Analysis:**

**Issue 1 - pipeline.py line 33:**
- Current code: [exact code found]
- Why it breaks: [analysis]
- Fix approach: [specific approach]

**Issue 2 - run.py async:**
- Current signature: [found in code]
- Downstream callers: [where it's called from]
- Async conversion requirements: [specific changes needed]

**Issue 3 - online.py integration:**
- online.py interface: [actual function signatures]
- Expected input format: [from code]
- Integration approach: [how to wire it]

**Integration touch points identified:**
- [Specific file:function connections found in code]
```

**Wait for user confirmation after investigation report before proceeding to design.**

---

## PART 1: Design DESIGN_SPECIFICATIONS_PHASE_0_1A.md

### Completeness Standards

Every specification must include:

**For functions:**
- Complete signature with parameter names and types
- Complete docstring with Args, Returns, Raises
- Implementation requirements (specific algorithms, data structures)
- Error handling (every failure mode, every fallback)
- Example code for complex logic

**For tests:**
- Exact test inputs (actual strings/data, not "sample data")
- Expected outputs (exact structure, not "valid output")
- Assertion specifications (what exactly to check)
- Pass/fail criteria

**For code modifications:**
- Exact file paths
- Exact line numbers (from SOURCE_OF_TRUTH)
- Before code (what's there now)
- After code (what it should be)
- Why the change is needed
- What it fixes/enables

---

### Document Structure

```markdown
# DESIGN SPECIFICATIONS - Phase 0 & Phase 1A
**Version:** 1.0
**Created:** [DATE] - Session Zero-A
**Status:** Complete - Ready for implementation

---

## How to Use This Document

**For Step 01 (Phase 0):**
- Read Phase 0 section completely
- Implement exactly as specified
- No interpretation needed

**For Step 02 (Phase 1A):**
- Read Phase 1A section completely
- Make exact code changes specified
- Follow integration approach exactly

**If anything is unclear:** STOP and ask user for clarification. Do not guess.

---

## Phase 0: Regression Test Suite

### Overview
**Purpose:** Build automated test suite that validates P1-P13 packets produce correct outputs

**Plain English:** Create a safety net of tests that check all 13 core components work correctly. Run before and after making changes to catch accidental breakage.

**Implementation Complexity:** Moderate - new test code, no existing code changes

**Token Estimate:** ~100-120K for implementation

---

### File to Create

**Path:** `intelligence/test/s6_harness.py`
**Estimated Lines:** 280-320 lines
**Dependencies:** pytest, all P1-P13 packet modules

---

### Complete Function Specifications

#### Function 1: `capture_baseline_outputs()`

**Purpose:** Execute P1-P13 packets with known test inputs and save outputs as baseline for regression comparison.

**Complete Signature:**
```python
def capture_baseline_outputs(
    test_claims: Optional[List[str]] = None,
    output_file: str = "intelligence/test/baseline_outputs.json"
) -> Dict[str, Any]:
    """
    Captures baseline outputs from P1-P13 packets for regression testing.

    Args:
        test_claims: List of test claim strings. If None, uses default test claims.
        output_file: Path to save baseline JSON. Defaults to baseline_outputs.json.

    Returns:
        Dict with structure:
        {
            "metadata": {
                "timestamp": "ISO8601 datetime",
                "git_commit": "SHA",
                "test_claims": ["claim1", "claim2", ...],
                "python_version": "3.x.x"
            },
            "p1_extract": {"claim": "...", "output": {...}},
            "p2_interpret": {"claim": "...", "output": {...}},
            ...
            "p13_contradict": {"claim": "...", "output": {...}}
        }

    Raises:
        PacketExecutionError: If any packet fails to execute
        BaselineWriteError: If baseline file cannot be written
    """
```

**Default Test Claims (use these):**
```python
DEFAULT_TEST_CLAIMS = [
    "The Eiffel Tower is 330 meters tall.",
    "US GDP grew 3.2% in Q4 2023.",
    "Vaccines do not cause autism."
]
```

**Implementation Requirements:**
1. Get git commit SHA: `subprocess.run(["git", "rev-parse", "HEAD"])`
2. For each test claim:
   - Run P1 (extract_claims) - capture output
   - Run P2 (interpret) on P1 output - capture output
   - Continue through P3-P13 in sequence
3. Save complete output dict to JSON file with pretty formatting
4. Return the dict

**Error Handling:**
- If any packet import fails: Raise with packet name and import error
- If any packet execution fails: Raise with packet name, claim, and stack trace
- If git command fails: Use "unknown" for commit SHA, log warning
- If file write fails: Raise BaselineWriteError with file path and error

**Test Data:**
- Claim 1 tests: Simple factual claim, no numbers, no cues
- Claim 2 tests: Numbers (3.2%), temporal context (Q4 2023)
- Claim 3 tests: Negation cue ("not")

---

#### Function 2: `validate_output_structure()`

**Purpose:** Validate packet output matches expected schema.

**Complete Signature:**
```python
def validate_output_structure(
    packet_name: str,
    output: Any,
    schema: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validates packet output against expected schema.

    Args:
        packet_name: Name of packet (e.g., "p1_extract_claims")
        output: Actual output from packet (can be dict, list, or other)
        schema: Expected schema definition with:
            - "type": Expected type ("dict", "list", "str", etc.)
            - "required_keys": List of required dict keys (if type is dict)
            - "key_schemas": Dict mapping keys to their schemas (recursive)
            - "list_item_schema": Schema for list items (if type is list)

    Returns:
        Tuple of (is_valid: bool, error_messages: List[str])
        If valid: (True, [])
        If invalid: (False, ["error1", "error2", ...])

    Raises:
        ValueError: If schema itself is malformed
    """
```

**Schema Definitions (complete schemas for each packet):**

**P1 Schema (extract_claims):**
```python
P1_SCHEMA = {
    "type": "list",
    "list_item_schema": {
        "type": "dict",
        "required_keys": ["id", "text", "tier", "entities", "numbers", "cues", "scope"],
        "key_schemas": {
            "id": {"type": "str", "pattern": r"^c-\d+$"},
            "text": {"type": "str", "min_length": 1},
            "tier": {"type": "str", "enum": ["primary", "secondary", "tertiary"]},
            "entities": {"type": "list", "list_item_schema": {"type": "str"}},
            "numbers": {
                "type": "list",
                "list_item_schema": {
                    "type": "dict",
                    "required_keys": ["value", "type"],
                    "key_schemas": {
                        "value": {"type": "float"},
                        "type": {"type": "str", "enum": ["percent", "year", "number"]}
                    }
                }
            },
            "cues": {
                "type": "dict",
                "optional_keys": ["negation", "comparison", "attribution"]
            },
            "scope": {
                "type": "dict",
                "optional_keys": ["year_hint", "geo_hint"]
            }
        }
    }
}
```

[Continue with complete schemas for P2-P13 based on SOURCE_OF_TRUTH evidence]

**P2 Schema (interpret):** [Complete schema]
**P3 Schema (plan):** [Complete schema]
**P4 Schema (rank):** [Complete schema]
...
**P13 Schema (contradict):** [Complete schema]

**Implementation Requirements:**
- Recursive schema validation
- Type checking (str, int, float, dict, list, bool)
- Required vs optional keys
- Pattern matching for strings (regex)
- Enum validation
- Min/max length validation
- Collect ALL errors (don't stop at first)

**Error Message Format:**
- "Missing required key: {key} in {location}"
- "Wrong type for {key}: expected {expected}, got {actual}"
- "Invalid enum value for {key}: {value} not in {allowed_values}"
- "Pattern mismatch for {key}: {value} does not match {pattern}"

---

#### Function 3: `test_p1_extract_claims()`

**Purpose:** Test P1 claim extraction packet.

**Complete Signature:**
```python
@pytest.mark.parametrize("test_input,expected_output", [
    # Test case 1: Single claim
    (
        "The Eiffel Tower is 330 meters tall.",
        {
            "claim_count": 1,
            "tiers": ["primary"],
            "has_numbers": False,
            "has_entities": True
        }
    ),
    # Test case 2: Multi-claim
    (
        "The US economy grew 3.2% in Q4 2023. Unemployment fell to 3.5%.",
        {
            "claim_count": 2,
            "tiers": ["primary", "secondary"],
            "has_numbers": True,
            "numbers_count": 3  # 3.2%, Q4 2023, 3.5%
        }
    ),
    # Test case 3: Negation cue
    (
        "Vaccines do not cause autism.",
        {
            "claim_count": 1,
            "has_negation": True,
            "negation_cue": "not"
        }
    )
])
def test_p1_extract_claims(test_input: str, expected_output: Dict[str, Any]):
    """
    Test P1 claim extraction with various inputs.

    Validates:
    - Output structure matches P1_SCHEMA
    - Correct number of claims extracted
    - Tier classification appropriate
    - Numbers/entities/cues extracted when present
    """
```

**Implementation Requirements:**
```python
from intelligence.claims.extract import extract_claims

def test_p1_extract_claims(test_input, expected_output):
    # Execute P1
    result = extract_claims(test_input)

    # Convert to dict if needed
    if hasattr(result[0], 'dict'):
        result = [claim.dict() for claim in result]

    # Validate structure
    is_valid, errors = validate_output_structure("p1_extract", result, P1_SCHEMA)
    assert is_valid, f"P1 output structure invalid: {errors}"

    # Validate claim count
    assert len(result) == expected_output["claim_count"], \
        f"Expected {expected_output['claim_count']} claims, got {len(result)}"

    # Validate tiers
    tiers = [claim["tier"] for claim in result]
    assert tiers == expected_output["tiers"], \
        f"Expected tiers {expected_output['tiers']}, got {tiers}"

    # Validate numbers if expected
    if "has_numbers" in expected_output:
        has_numbers = any(claim["numbers"] for claim in result)
        assert has_numbers == expected_output["has_numbers"], \
            f"Expected has_numbers={expected_output['has_numbers']}, got {has_numbers}"

    # Validate negation if expected
    if "has_negation" in expected_output:
        has_negation = any("negation" in claim["cues"] for claim in result)
        assert has_negation == expected_output["has_negation"], \
            f"Expected has_negation={expected_output['has_negation']}, got {has_negation}"
```

**Test Cases (complete):**
- Test 1: Single factual claim (no numbers, no cues)
- Test 2: Multi-claim with numbers and dates
- Test 3: Negation cue detection
- Test 4: Entities extraction
- Test 5: Empty input handling

---

[Continue with complete specifications for test_p2_interpret through test_p13_contradict]

**Function 4: test_p2_interpret()** [Complete specification]
**Function 5: test_p3_plan()** [Complete specification]
...
**Function 13: test_p13_contradict()** [Complete specification]

---

#### Function 14: `test_integration_regression()`

**Purpose:** Full pipeline regression test comparing current outputs to baseline.

**Complete Signature:**
```python
def test_integration_regression():
    """
    Full P1-P13 pipeline test with baseline comparison.

    Loads baseline outputs and compares current execution to baseline.
    Uses tolerance for non-deterministic fields (timestamps, floats).

    Raises:
        AssertionError: If outputs differ beyond tolerance
        FileNotFoundError: If baseline not found (run capture_baseline first)
    """
```

**Implementation:**
```python
import json
from pathlib import Path

def test_integration_regression():
    # Load baseline
    baseline_path = Path("intelligence/test/baseline_outputs.json")
    assert baseline_path.exists(), "Baseline not found. Run capture_baseline_outputs() first."

    with open(baseline_path) as f:
        baseline = json.load(f)

    # Execute current pipeline
    current = capture_baseline_outputs(
        test_claims=baseline["metadata"]["test_claims"]
    )

    # Compare each packet output
    for packet_name in ["p1_extract", "p2_interpret", ..., "p13_contradict"]:
        baseline_output = baseline[packet_name]["output"]
        current_output = current[packet_name]["output"]

        # Compare with tolerance
        diff = compare_outputs(baseline_output, current_output, tolerance=TOLERANCE_CONFIG)

        assert not diff["has_differences"], \
            f"Regression detected in {packet_name}: {diff['differences']}"
```

**Tolerance Configuration:**
```python
TOLERANCE_CONFIG = {
    "ignore_keys": ["timestamp", "execution_time_ms"],
    "float_tolerance": 0.01,
    "list_order_sensitive": {
        "claim_ids": True,  # Order matters
        "candidates": False  # Order doesn't matter
    }
}
```

**Comparison Function:**
```python
def compare_outputs(
    baseline: Any,
    current: Any,
    tolerance: Dict[str, Any],
    path: str = "root"
) -> Dict[str, Any]:
    """
    Recursively compare baseline and current outputs with tolerance.

    Returns:
        {
            "has_differences": bool,
            "differences": List[str]  # List of difference descriptions
        }
    """
    # [Complete implementation with recursive comparison]
```

---

### Success Criteria for Phase 0

Phase 0 implementation is complete when:
- [ ] `intelligence/test/s6_harness.py` created with all 14+ functions
- [ ] All schemas defined (P1-P13)
- [ ] Baseline captured successfully
- [ ] All 14+ tests passing
- [ ] Test suite runs in <10 seconds
- [ ] No domain hardcoding in test data (zero bias check)
- [ ] Code committed with message: "[Session 01] Phase 0: Build S6 regression harness"

---

## Phase 1A: Integration Fixes

### Overview
**Purpose:** Fix three integration gaps so pipeline.py calls online.py and guardrails execute

**Plain English:** Wire up the live evidence gathering code (which exists but isn't called) and fix the bugs preventing the pipeline from working end-to-end.

**Implementation Complexity:** Medium - modifying core pipeline code, async conversion

**Token Estimate:** ~80-100K for implementation

---

### Integration Gap Analysis

**Gap 1: pipeline.py line 33 - Empty candidates bug**
- Location: `intelligence/gather/pipeline.py:33`
- Current: `out[arm_name]["candidates"] = []` then `cands = gather(...)` but cands not stored
- Effect: Lines 50-68 unreachable (guardrails, consensus, scoring)
- Fix: Store cands in out dictionary

**Gap 2: run.py sync vs online.py async**
- Location: `intelligence/pipeline/run.py:29`
- Current: `def run_preview()` is sync
- Problem: Cannot `await online.run_plan()` from sync function
- Fix: Convert run_preview to async, update all callers

**Gap 3: Multi-claim bypass**
- Location: `intelligence/pipeline/run.py:37-44`
- Current: Manual single-claim dict creation
- Problem: P1 extract_claims exists but not used
- Fix: Call extract_claims for live mode, keep manual for test mode

---

### Complete Modification Specifications

#### Modification 1: Fix pipeline.py Empty Candidates Bug

**File:** `intelligence/gather/pipeline.py`
**Lines to modify:** 32-35

**Current Code (lines 32-35):**
```python
        # Line 32
        out[arm_name] = {"arm": arm_name, "strategy": arm["strategy"]}
        # Line 33 - BUG: Sets empty list
        out[arm_name]["candidates"] = []
        # Line 35 - gather() called but result not used
        cands = gather(query, arm=arm, max_per_arm=cand_limit, mode=mode)
```

**New Code (replace lines 32-35):**
```python
        # Line 32
        out[arm_name] = {"arm": arm_name, "strategy": arm["strategy"]}
        # Line 33-35 - FIX: Actually store gathered candidates
        cands = gather(query, arm=arm, max_per_arm=cand_limit, mode=mode)
        out[arm_name]["candidates"] = cands if cands else []
```

**Why this fixes it:**
- cands variable now assigned BEFORE being stored
- out[arm_name]["candidates"] contains actual candidates
- Lines 50-68 now reachable because candidates list is populated
- Guardrails, consensus, and scoring will execute

**Testing requirement:**
- Run S6 tests (must still pass)
- Add logging at line 51: `print(f"Guardrails executing for {arm_name}")`
- Verify guardrails section executes in test mode

---

#### Modification 2: Convert run.py to Async

**File:** `intelligence/pipeline/run.py`
**Lines to modify:** 29, and all async calls within function

**Current Code (line 29):**
```python
def run_preview(text: str, test_mode: bool = False) -> Dict[str, Any]:
    """
    Run fact-check preview pipeline on input text.
    """
```

**New Code (line 29):**
```python
async def run_preview(text: str, test_mode: bool = False) -> Dict[str, Any]:
    """
    Run fact-check preview pipeline on input text.

    Note: Changed to async to support calling async online.py for live gathering.
    """
```

**Internal async calls to add:**
Within run_preview function body, when calling gather for live mode:
```python
# Around line 60-70 (wherever gather is called for live mode)
if not test_mode:
    # Call online.py asynchronously
    evidence = await online.run_plan(plan, max_per_query=3)
else:
    # Test mode uses sync gather
    evidence = gather_test_mode(claim)
```

**Downstream Changes Required:**

**File:** `api/analyses.py`
**Function:** `preview_analysis()` endpoint

**Current (line ~28):**
```python
@router.post("/preview")
def preview_analysis(request: PreviewRequest):
    result = run_preview(request.text, test_mode=request.test_mode)
    return result
```

**New:**
```python
@router.post("/preview")
async def preview_analysis(request: PreviewRequest):
    result = await run_preview(request.text, test_mode=request.test_mode)
    return result
```

**Why this fixes it:**
- run_preview can now `await` async functions like online.run_plan
- FastAPI natively supports async endpoints
- No breaking changes to API contract (response format unchanged)

**Testing requirement:**
- S6 tests still pass (test mode is sync path)
- Live mode test confirms async execution works

---

#### Modification 3: Wire Multi-Claim Extraction

**File:** `intelligence/pipeline/run.py`
**Lines to modify:** 37-44 (manual claim dict creation)

**Current Code (lines 37-44):**
```python
    # Line 37-44: Manual single-claim creation
    claim: Dict[str, Any] = {
        "id": "c-0",
        "text": (text or "").strip(),
        "tier": "primary",
        "entities": [],
        "numbers": [],
        "cues": {},
        "scope": {}
    }
    claims_list = [claim]
```

**New Code (replace lines 37-44):**
```python
    # Import at top of file
    from intelligence.claims.extract import extract_claims

    # Lines 37-50: Multi-claim extraction for live mode
    if test_mode:
        # Test mode: Keep simple single-claim behavior for test stability
        claim: Dict[str, Any] = {
            "id": "c-0",
            "text": (text or "").strip(),
            "tier": "primary",
            "entities": [],
            "numbers": [],
            "cues": {},
            "scope": {}
        }
        claims_list = [claim]
    else:
        # Live mode: Use P1 multi-claim extraction
        extracted = extract_claims(text)
        claims_list = [claim.dict() for claim in extracted] if hasattr(extracted[0], 'dict') else extracted

        # Fallback if extraction returns empty
        if not claims_list:
            claim: Dict[str, Any] = {
                "id": "c-0",
                "text": (text or "").strip(),
                "tier": "primary",
                "entities": [],
                "numbers": [],
                "cues": {},
                "scope": {}
            }
            claims_list = [claim]
```

**Why this fixes it:**
- Live mode now uses actual P1 claim extraction
- Test mode unchanged (backward compatible with existing tests)
- Graceful fallback if extraction fails
- Multi-claim processing enabled for live mode

**Testing requirement:**
- S6 tests pass (test mode path unchanged)
- New test: "The US economy grew 3.2% in Q4. Unemployment fell to 3.5%." → 2 claims extracted
- Verify both claims processed through pipeline

---

#### Modification 4: Wire online.py for Live Gathering

**File:** `intelligence/pipeline/run.py` or `intelligence/gather/pipeline.py` (depending on where gather() is called)
**Context:** Need to call online.py for live mode instead of test mode gather

**Investigation needed:** Find where `gather()` function is called in the pipeline. Replace with conditional:

**Pattern to find:**
```python
evidence = gather(claim_text, ...)
```

**Replace with:**
```python
if test_mode:
    # Test mode: Use synthetic data
    evidence = gather_test_mode(claim_text, max_per_arm=3)
else:
    # Live mode: Use online.py
    from intelligence.gather.online import run_plan

    # Build strategy plan from claim
    plan = {
        "claim_id": claim["id"],
        "strategies": [
            {
                "arm": "for",
                "queries": [claim["text"]],
                "providers": ["brave", "google_cse"]
            },
            {
                "arm": "against",
                "queries": [claim["text"]],
                "providers": ["brave", "google_cse"]
            }
        ]
    }

    # Call online.py (async)
    evidence = await run_plan(plan, max_per_query=3)
```

**Verify online.py interface:**
Based on SOURCE_OF_TRUTH (online.py:86-127), `run_plan` expects:
```python
async def run_plan(plan: Dict, max_per_query: int = 2) -> Dict:
    """
    plan structure:
    {
        "strategies": [
            {
                "arm": "for" | "against",
                "queries": List[str],
                "providers": List[str]  # ["brave", "google_cse", "bing"]
            }
        ]
    }

    Returns:
    {
        "for": {"candidates": [...]},
        "against": {"candidates": [...]}
    }
    """
```

**Integration contract:**
- Input: Claim dict with id, text, tier
- Output: Evidence dict with "for"/"against" arms containing candidates
- Error handling: If online.py fails, log error and return empty candidates (degrade gracefully)

**Error Handling:**
```python
try:
    evidence = await run_plan(plan, max_per_query=3)
except Exception as e:
    # Log error
    logger.error(f"Live gathering failed for claim {claim['id']}: {e}")
    # Degrade gracefully
    evidence = {
        "for": {"candidates": []},
        "against": {"candidates": []},
        "error": str(e)
    }
```

---

### Integration Call Chain (After Phase 1A)

**Complete end-to-end flow:**

```
User Request: POST /analyses/preview {"text": "...", "test_mode": false}
    ↓
api/analyses.py:
    async def preview_analysis(request)
    ↓
intelligence/pipeline/run.py:
    async def run_preview(text, test_mode=False)
    ├─ calls: extract_claims(text)  [P1]
    │   ↓ returns: List[claim_dict]
    │
    ├─ for each claim:
    │   ├─ calls: interpret(claim)  [P2]
    │   ├─ calls: plan_strategy(claim)  [P3]
    │   ├─ calls: pipeline.process_claim(claim, strategy)
    │   │   ↓
    │   │   intelligence/gather/pipeline.py:
    │   │       for each arm in ["for", "against"]:
    │   │           ├─ calls: online.run_plan(strategy)  [async]
    │   │           │   ↓
    │   │           │   intelligence/gather/online.py:
    │   │           │       ├─ calls: search providers in parallel
    │   │           │       │   (brave, google_cse, bing)
    │   │           │       ├─ interleaves results
    │   │           │       └─ returns: candidates
    │   │           │
    │   │           ├─ stores: candidates in out[arm]["candidates"]
    │   │           ├─ calls: apply_guardrails(out)  [P9]
    │   │           ├─ calls: compute_consensus(out)  [P12]
    │   │           └─ calls: score_evidence(out)  [P11]
    │   │
    │   └─ returns: evidence with guardrails/consensus/scoring
    │
    └─ returns: complete fact-check result
```

---

### Testing Requirements for Phase 1A

**Test Case 1: Pipeline stores candidates**
```python
def test_pipeline_stores_candidates():
    """Verify pipeline.py fix - candidates actually stored."""
    from intelligence.gather.pipeline import process_claim

    claim = {"id": "c-0", "text": "Test claim", "tier": "primary"}
    result = process_claim(claim, test_mode=True, max_per_arm=3)

    # Check candidates stored
    assert "for" in result
    assert "candidates" in result["for"]
    assert isinstance(result["for"]["candidates"], list)
    # In test mode, should have synthetic candidates
    assert len(result["for"]["candidates"]) > 0
```

**Test Case 2: Guardrails execute**
```python
def test_guardrails_reachable():
    """Verify guardrails section executes (was unreachable before)."""
    # Add debug logging to pipeline.py line 51
    # Run pipeline
    # Check logs contain "Guardrails executing"
    pass
```

**Test Case 3: Multi-claim extraction**
```python
async def test_multi_claim_extraction():
    """Verify multi-claim extraction works in live mode."""
    text = "The US economy grew 3.2% in Q4. Unemployment fell to 3.5%."

    result = await run_preview(text, test_mode=False)

    # Should process 2 claims
    assert "claims" in result
    assert len(result["claims"]) >= 2
```

**Test Case 4: Online gathering integration**
```python
async def test_online_gathering():
    """Verify online.py called for live mode."""
    text = "The Eiffel Tower is 330 meters tall."

    result = await run_preview(text, test_mode=False)

    # Check candidates have real URLs (not synthetic)
    candidates = result["evidence"]["for"]["candidates"]
    assert len(candidates) > 0
    assert all("url" in c for c in candidates)
    # Real URLs should have http/https
    assert any("http" in c["url"] for c in candidates)
```

**Test Case 5: Test mode still works**
```python
async def test_mode_still_works():
    """Verify test mode unchanged (backward compatibility)."""
    text = "Test claim"

    result = await run_preview(text, test_mode=True)

    # Should complete quickly (no real API calls)
    # Should have synthetic data
    assert "evidence" in result
```

---

### Success Criteria for Phase 1A

Phase 1A implementation is complete when:
- [ ] pipeline.py modified (candidates stored correctly)
- [ ] run.py converted to async
- [ ] api/analyses.py endpoint converted to async
- [ ] Multi-claim extraction wired (test/live mode conditional)
- [ ] online.py integration wired (live mode calls online.run_plan)
- [ ] S6 regression tests still pass
- [ ] All 5 new integration tests pass
- [ ] Guardrails confirmed executing (check logs)
- [ ] End-to-end live mode test works
- [ ] Code committed: "[Session 02] Phase 1A: Fix integration gaps"

---

**END OF DESIGN_SPECIFICATIONS_PHASE_0_1A.md**
```

---

## PART 2: Create Step Prompts

### Step 01 Prompt Specification

**File:** `step_prompts/step01_phase0.md`

**Content:**
```markdown
# STEP 01 - Phase 0: Build Regression Test Suite

**Purpose:** Implement S6 regression harness per complete specifications

**Plain English:** Build automated tests that verify all 13 core components (P1-P13) work correctly. This is your safety net for catching bugs during future changes.

---

## Before Starting

1. Read `implementation_plan/TENANTS.md`
2. Read `implementation_plan/DESIGN_SPECIFICATIONS_PHASE_0_1A.md` - **Phase 0 section**
3. Confirm branch: `rogrv2-backend-wrapup`

---

## Your Task

Implement **Phase 0 specifications exactly as written** in DESIGN_SPECIFICATIONS_PHASE_0_1A.md.

**File to create:**
- `intelligence/test/s6_harness.py` (280-320 lines)

**What to implement:**
- All 14 functions specified (capture_baseline, validate_output_structure, test_p1-p13, test_integration_regression)
- All schemas (P1-P13)
- All test cases with exact inputs/outputs from spec
- Error handling as specified

**DO NOT:**
- Deviate from specifications
- Add extra tests not specified
- Change test claim text
- Skip any functions or test cases

---

## Success Criteria

- [ ] All functions implemented per spec
- [ ] All schemas defined
- [ ] Baseline captured successfully
- [ ] pytest runs: 14+ tests pass in <10 seconds
- [ ] No domain hardcoding (zero bias)
- [ ] S6 tests pass (they test themselves)
- [ ] Code committed: "[Session 01] Phase 0: Build S6 regression harness"

---

## Run Tests

```bash
# Capture baseline first
python -c "from intelligence.test.s6_harness import capture_baseline_outputs; capture_baseline_outputs()"

# Run tests
pytest intelligence/test/s6_harness.py -v
```

---

**May I proceed with implementing Phase 0 per the specifications?**
```

---

### Step 02 Prompt Specification

**File:** `step_prompts/step02_phase1a.md`

**Content:**
```markdown
# STEP 02 - Phase 1A: Fix Integration Gaps

**Purpose:** Fix 3 integration bugs per complete specifications

**Plain English:** Wire up live evidence gathering and fix the bugs preventing the pipeline from working end-to-end.

---

## Before Starting

1. Read `implementation_plan/TENANTS.md` (especially Tenant 4 - investigation required)
2. Read `implementation_plan/DESIGN_SPECIFICATIONS_PHASE_0_1A.md` - **Phase 1A section**
3. Run S6 tests (must pass before starting): `pytest intelligence/test/s6_harness.py -v`
4. Confirm branch: `rogrv2-backend-wrapup`

---

## Your Task

Implement **Phase 1A modifications exactly as written** in DESIGN_SPECIFICATIONS_PHASE_0_1A.md.

**Files to modify:**
1. `intelligence/gather/pipeline.py` (lines 32-35)
2. `intelligence/pipeline/run.py` (line 29, lines 37-44, gather call location)
3. `api/analyses.py` (preview_analysis endpoint)

**What to implement:**
- Modification 1: Fix empty candidates bug (exact code specified)
- Modification 2: Convert run_preview to async (exact signature specified)
- Modification 3: Wire multi-claim extraction (exact conditional specified)
- Modification 4: Wire online.py integration (exact pattern specified)

**DO NOT:**
- Deviate from specified code changes
- Make additional refactors
- Add features not specified

---

## Success Criteria

- [ ] All 4 modifications implemented per spec
- [ ] S6 regression tests still pass
- [ ] 5 new integration tests pass
- [ ] Guardrails confirmed executing (check logs)
- [ ] End-to-end live mode test works
- [ ] Code committed: "[Session 02] Phase 1A: Fix integration gaps"

---

## Run Tests

```bash
# Regression tests must still pass
pytest intelligence/test/s6_harness.py -v

# New integration tests
pytest intelligence/test/test_integration_phase1a.py -v
```

---

**May I proceed with implementing Phase 1A modifications per the specifications?**
```

---

## PART 3: Create Partial Master Plan

**File:** `MASTER_PLAN_PARTIAL.md`

```markdown
# MASTER PLAN - Phase 0 & 1A
**Version:** 1.0 (Partial - Steps 01-02 only)
**Created:** [DATE] - Session Zero-A
**Status:** Partial - Will be completed by Session Zero-C

---

## Overview

This is a partial master plan covering Phase 0 and Phase 1A.

**Phase 1B-1D will be planned in Session Zero-B and Zero-C.**

---

## Step 01: Phase 0 - Build Regression Test Suite

**Purpose:** Create S6 harness for safety net

**Token Estimate:** ~100-120K

**Duration:** 1 session (4-6 hours)

**Dependencies:** None (can start immediately after Zero-B and Zero-C complete)

**Prompt File:** `step_prompts/step01_phase0.md`

**Deliverables:**
- `intelligence/test/s6_harness.py` (280-320 lines)
- Baseline outputs captured
- 14+ tests passing

**Success Criteria:**
- [ ] All functions implemented per spec
- [ ] All schemas defined
- [ ] Tests pass in <10 seconds
- [ ] Code committed

**Risks:**
- **Low risk** - isolated test code, no integration
- **Mitigation:** Clear complete specifications provided

**Token Breakdown:**
- Context loading: ~10K
- Implementation: ~80K
- Testing/debugging: ~20K
- Documentation: ~10K

---

## Step 02: Phase 1A - Fix Integration Gaps

**Purpose:** Fix pipeline.py, wire online.py, enable multi-claim

**Token Estimate:** ~80-100K

**Duration:** 1 session (4-6 hours)

**Dependencies:** Step 01 (need S6 tests to verify no regressions)

**Prompt File:** `step_prompts/step02_phase1a.md`

**Deliverables:**
- `pipeline.py` fixed (candidates stored)
- `run.py` async conversion complete
- Multi-claim extraction wired
- online.py integration complete
- 5 integration tests passing

**Success Criteria:**
- [ ] All 4 modifications complete
- [ ] S6 tests still pass
- [ ] Integration tests pass
- [ ] Guardrails execute
- [ ] Live mode works end-to-end
- [ ] Code committed

**Risks:**
- **Medium risk** - core pipeline changes, async conversion
- **Mitigation:** S6 tests catch regressions, complete specifications minimize guesswork

**Token Breakdown:**
- Context loading: ~10K
- Investigation/code reading: ~15K
- Modifications (4 changes): ~40K
- Testing/debugging: ~20K
- Documentation: ~10K

---

## Dependency Graph (Partial)

```
Step 01 (Phase 0)
    ↓
Step 02 (Phase 1A)
    ↓
Step 03-12 (To be planned in Zero-B and Zero-C)
```

---

## Phase 0-1A Summary

| Phase | Steps | Est. Tokens | Sessions |
|-------|-------|-------------|----------|
| Phase 0 | 1 | ~110K | 1 |
| Phase 1A | 1 | ~90K | 1 |
| **Subtotal** | **2** | **~200K** | **2** |

---

## Recovery Procedures

**If Step 01 fails:**
1. Check S6 test output for specific failures
2. Verify all schemas match SOURCE_OF_TRUTH evidence
3. Check baseline_outputs.json exists and is valid JSON
4. Re-run with verbose pytest output: `pytest -vv`

**If Step 02 fails:**
1. Run S6 tests to verify no regressions
2. Check async conversion in api/analyses.py
3. Verify online.py imports correctly
4. Test in test_mode first (simpler, no external calls)

---

**This partial plan will be merged with Phase 1B-1D plans from Zero-B and Zero-C.**

---

**END OF MASTER_PLAN_PARTIAL.md**
```

---

## Your Execution Plan

1. ✅ Read required documents
2. ✅ Perform code investigation (REQUIRED - Tenant 4)
3. ✅ Report investigation findings - **WAIT FOR USER CONFIRMATION**
4. ✅ Design complete Phase 0 specifications
5. ✅ Design complete Phase 1A specifications
6. ✅ Create step01 prompt
7. ✅ Create step02 prompt
8. ✅ Create partial master plan
9. ✅ Update PROGRESS_THREAD.md
10. ✅ Update IMPLEMENTATION_STATE.md
11. ✅ Report completion

---

## Important Reminders

- **Complete specifications only** - No outlines, no TBDs, no "[fill in later]"
- **Investigation required** - Read actual code before designing (Tenant 4)
- **Ask permission** - Before creating files (Tenant 6)
- **Zero bias** - No domain hardcoding anywhere
- **IFCN compliance** - Methodology-first approach

---

## Token Budget

**Target:** 80-100K
**Spillover acceptable if needed for completeness**

If approaching 90K and specifications not complete:
- Update NEXT_SESSION_PROMPT.md to continue design work
- Do NOT compromise on completeness

---

**Ready to begin Session Zero-A?**

**Confirm you understand the scope: Complete specifications for Phase 0 + 1A only.**
