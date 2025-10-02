# COMPLETE HANDOFF - 3-Session Design Approach

**Date:** 2025-09-30
**From:** Session 00 (Planning)
**Purpose:** Complete design specifications through 3 self-contained sessions

---

## Overview

**Problem:** Session 00 created broken Session Zero prompts with placeholders.

**Solution:** 3-session approach to create complete specifications without drift:
1. **Session 01:** Design all specifications (single coherent design)
2. **Session 02:** Break into master plan with 12 steps
3. **Session 03:** Create 12 executable step prompts

**Each session is self-contained and cannot burn context window.**

---

# SESSION 01: CREATE COMPLETE DESIGN SPECIFICATIONS

**Token Budget:** ~130-170K (safe margin)

## Your Task

Create ONE file: `DESIGN_SPECIFICATIONS_COMPLETE.md` (~140-160KB) containing COMPLETE specifications for ALL phases with ZERO placeholders.

## Required Reading

1. `verification_package/SOURCE_OF_TRUTH_ROGRV2_COMPLETE.md` (focus on Section 4, 7, 8, 9)
2. `verification_package/architect_answers_session3.md` (focus on B3, B4, I11, I12)
3. `verification_package/USER_REQUIREMENTS.md`
4. `implementation_plan/TENANTS.md`

## Output Structure

```markdown
# DESIGN SPECIFICATIONS - ROGRv2 Backend Completion
**Version:** 1.0
**Created:** [DATE]
**Purpose:** Complete implementation specifications for all phases

---

## Phase 0: Regression Test Suite

### File to Create
`intelligence/test/s6_harness.py` (~280-320 lines)

### Complete Function Specifications

#### Function 1: capture_baseline_outputs()
[COMPLETE signature with full docstring]
[COMPLETE implementation requirements]
[COMPLETE error handling]
[EXACT test inputs: "The Eiffel Tower is 330 meters tall.", "US GDP grew 3.2% in Q4 2023.", "Vaccines do not cause autism."]

#### Function 2: validate_output_structure()
[COMPLETE signature]
[COMPLETE implementation]

#### Function 3-16: test_p1_extract_claims() through test_p13_contradict()
[COMPLETE specification for EACH test function]
[EXACT test cases with inputs and expected outputs for EACH]

### Complete Schema Definitions

#### P1 Schema (extract_claims)
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
            "cues": {"type": "dict", "optional_keys": ["negation", "comparison", "attribution"]},
            "scope": {"type": "dict", "optional_keys": ["year_hint", "geo_hint"]}
        }
    }
}
```

#### P2-P13 Schemas
[COMPLETE schema for P2]
[COMPLETE schema for P3]
[COMPLETE schema for P4]
[COMPLETE schema for P5]
[COMPLETE schema for P6]
[COMPLETE schema for P7]
[COMPLETE schema for P8]
[COMPLETE schema for P9]
[COMPLETE schema for P10]
[COMPLETE schema for P11]
[COMPLETE schema for P12]
[COMPLETE schema for P13]

### Success Criteria
[Complete checklist for Phase 0]

---

## Phase 1A: Integration Fixes

### Modification 1: Fix pipeline.py Empty Candidates Bug
**File:** `intelligence/gather/pipeline.py`
**Lines:** 32-35

**Current Code:**
```python
        out[arm_name] = {"arm": arm_name, "strategy": arm["strategy"]}
        out[arm_name]["candidates"] = []
        cands = gather(query, arm=arm, max_per_arm=cand_limit, mode=mode)
```

**New Code:**
```python
        out[arm_name] = {"arm": arm_name, "strategy": arm["strategy"]}
        cands = gather(query, arm=arm, max_per_arm=cand_limit, mode=mode)
        out[arm_name]["candidates"] = cands if cands else []
```

**Why:** [Explanation]
**Testing:** [Exact test requirements]

### Modification 2: Convert run.py to Async
**File:** `intelligence/pipeline/run.py`
**Line:** 29

**Current:**
```python
def run_preview(text: str, test_mode: bool = False) -> Dict[str, Any]:
```

**New:**
```python
async def run_preview(text: str, test_mode: bool = False) -> Dict[str, Any]:
```

**Downstream changes required:**
- `api/analyses.py` line ~28: Change `def preview_analysis()` to `async def preview_analysis()`
- Add `await` to all `run_preview()` calls

### Modification 3: Wire Multi-Claim Extraction
**File:** `intelligence/pipeline/run.py`
**Lines:** 37-44

**Current Code:**
```python
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

**New Code:**
```python
    from intelligence.claims.extract import extract_claims

    if test_mode:
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
        extracted = extract_claims(text)
        claims_list = [claim.dict() for claim in extracted] if hasattr(extracted[0], 'dict') else extracted
        if not claims_list:
            claims_list = [{
                "id": "c-0",
                "text": (text or "").strip(),
                "tier": "primary",
                "entities": [],
                "numbers": [],
                "cues": {},
                "scope": {}
            }]
```

### Modification 4: Wire online.py Integration
[COMPLETE specification for where and how to integrate online.py]
[EXACT code pattern with error handling]

### Test Cases for Phase 1A
[5 COMPLETE test cases with exact inputs and expected outputs]

### Success Criteria
[Complete checklist for Phase 1A]

---

## Phase 1B: AI Assist Layer

### Shared Infrastructure

#### File: intelligence/ai_assist/config.py
[COMPLETE code for config.py including:]
- Imports
- Constants (DEFAULT_MODEL, TOKEN_BUDGETS, DEFAULT_TIMEOUT, MAX_RETRIES)
- AIAssistError exception class
- TokenBudgetExceeded exception class
- AsyncOpenAI client initialization
- call_openai() function (complete implementation with retry logic)

### Component 1B.1: Query Refinement

#### File: intelligence/ai_assist/refine.py

**EXACT System Prompt:**
```python
SYSTEM_PROMPT = """You are a search query optimization expert for fact-checking.

Your task: Generate 2-3 refined search queries that will find the best evidence for verifying a claim.

Consider:
1. Key entities and their variations (official names, acronyms, alternative spellings)
2. Temporal context (specific dates, year ranges, time periods)
3. Negation cues (if claim says "not X", search for both X and evidence of negation)
4. Domain-specific terminology (use technical/scientific terms when appropriate)
5. Authoritative source signals (search for peer-reviewed, government, primary sources)

CRITICAL: Do NOT suggest specific domains or websites. Focus on query terms only.

Output must be valid JSON:
{
    "refined_queries": ["query1", "query2", "query3"],
    "reasoning": "Why these refinements improve search quality",
    "search_hints": {
        "time_filter": "2020-2024" or null,
        "suggested_providers": ["general", "academic", "news"]
    }
}

Suggested providers must be generic categories, NOT specific sites."""
```

**EXACT User Prompt Template:**
```python
def build_user_prompt(claim: Dict[str, Any]) -> str:
    numbers_str = ", ".join([f"{n['value']} ({n['type']})" for n in claim.get("numbers", [])]) or "None"
    entities_str = ", ".join(claim.get("entities", [])) or "None"
    cues_str = []
    if claim.get("cues", {}).get("negation"):
        cues_str.append("Negation detected")
    if claim.get("cues", {}).get("comparison"):
        cues_str.append("Comparison detected")
    if claim.get("cues", {}).get("attribution"):
        cues_str.append(f"Attribution: {claim['cues']['attribution']}")
    cues_final = "; ".join(cues_str) or "None"
    temporal_str = claim.get("scope", {}).get("year_hint") or "None"
    geo_str = claim.get("scope", {}).get("geo_hint") or "None"

    return f"""Claim: {claim['text']}

Numbers in claim: {numbers_str}
Entities: {entities_str}
Cues: {cues_final}
Temporal context: {temporal_str}
Geographic context: {geo_str}

Generate 2-3 refined search queries."""
```

**COMPLETE Function Implementation:**
```python
async def refine_query(claim: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """[COMPLETE docstring with Args, Returns, Raises]"""

    original_query = claim["text"]

    try:
        user_prompt = build_user_prompt(claim)

        response = await call_openai(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model="gpt-4-turbo",
            temperature=0.3,
            max_tokens=300,
            response_format={"type": "json_object"}
        )

        if response["usage"]["total_tokens"] > TOKEN_BUDGETS["query_refinement"]:
            logger.warning(f"Query refinement exceeded token budget: {response['usage']['total_tokens']} > {TOKEN_BUDGETS['query_refinement']}")
            raise TokenBudgetExceeded("Token budget exceeded")

        ai_output = json.loads(response["content"])

        if "refined_queries" not in ai_output or not isinstance(ai_output["refined_queries"], list):
            raise ValueError("Invalid AI response structure")

        if len(ai_output["refined_queries"]) < 2:
            raise ValueError("AI returned fewer than 2 queries")

        # Zero bias check
        for query in ai_output["refined_queries"]:
            if any(domain in query.lower() for domain in [".com", ".org", ".gov", ".edu", "site:", "domain:"]):
                logger.warning(f"AI query contains domain reference: {query}")
                raise ValueError("AI introduced domain bias")

        return {
            "original_query": original_query,
            "refined_queries": ai_output["refined_queries"][:3],
            "refinement_reasoning": ai_output.get("reasoning", ""),
            "search_hints": ai_output.get("search_hints", {}),
            "token_usage": response["usage"]["total_tokens"],
            "fallback_used": False
        }

    except Exception as e:
        logger.error(f"Query refinement failed: {e}. Using fallback.")
        return {
            "original_query": original_query,
            "refined_queries": [original_query, original_query + " evidence", original_query + " fact check"],
            "refinement_reasoning": f"AI refinement failed ({type(e).__name__}). Using fallback queries.",
            "search_hints": {},
            "token_usage": 0,
            "fallback_used": True
        }
```

**5 COMPLETE Test Cases:**
[Test 1: Simple factual claim - exact input, exact expected output]
[Test 2: Temporal context - exact input, exact expected output]
[Test 3: Negation cue - exact input, exact expected output]
[Test 4: API failure fallback - exact test pattern]
[Test 5: Token budget enforcement - exact verification]

**Integration Point:**
[EXACT location in pipeline.py or run.py]
[EXACT code to add]

### Component 1B.2: Passage Triage
[COMPLETE specification following same pattern as 1B.1]
[EXACT system prompt]
[EXACT user prompt template]
[COMPLETE implementation]
[5 COMPLETE test cases]
[Integration point]

### Component 1B.3: Contradiction Surfacing
[COMPLETE specification following same pattern]

### Component 1B.4: Explanation Draft
[COMPLETE specification following same pattern]

### Component 1B.5: Integration
[COMPLETE wiring specifications]

### Success Criteria for Phase 1B
[Complete checklist]

---

## Phase 1C: Multi-Claim Wiring

### Function: process_single_claim()
[COMPLETE signature]
[COMPLETE implementation]

### Function: aggregate_multi_claim_results()
[COMPLETE signature]
[COMPLETE implementation including:]
- Verdict aggregation logic
- Trust capsule format (exact structure)
- Summary generation

### Modifications to run.py
[EXACT code changes for multi-claim loop]

### Test Cases
[4 COMPLETE test cases]

### Success Criteria
[Complete checklist]

---

## Phase 1D: S3 + S6 Modules

### Phase 1D.1: S3 Numeric Module

#### File: intelligence/s3/numeric.py

**COMPLETE Function:**
```python
def compare_numeric_claims(
    claim_value: float,
    evidence_value: float,
    value_type: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """[COMPLETE docstring]"""

    diff = abs(claim_value - evidence_value)

    if value_type == "percent":
        tolerance = 3.0
        matches = diff <= tolerance
        reasoning = f"Percentage difference: {diff:.1f}pp (tolerance: {tolerance}pp)"

    elif value_type == "year":
        tolerance = 0
        matches = diff == 0
        reasoning = "Years must match exactly"

    elif claim_value >= 1000:
        tolerance_pct = 0.05
        diff_pct = diff / claim_value
        matches = diff_pct <= tolerance_pct
        reasoning = f"Large number: {diff_pct*100:.1f}% difference (tolerance: {tolerance_pct*100}%)"
        tolerance = tolerance_pct

    else:
        tolerance = 1.0
        matches = diff <= tolerance
        reasoning = f"Small number: {diff:.1f} difference (tolerance: {tolerance})"

    return {
        "matches": matches,
        "difference": diff,
        "difference_percent": (diff / claim_value * 100) if claim_value != 0 else 0,
        "tolerance_used": tolerance,
        "reasoning": reasoning
    }
```

**Test Cases:**
[5 COMPLETE test cases with exact inputs/outputs]

**Integration Point:**
Replace existing logic in `intelligence/analyze/stance.py` function `_compare_numbers()` (lines 76-85)

### Phase 1D.2: S3 Temporal Module
[COMPLETE specification for temporal reasoning]
[Functions for Q1/Q2/Q3/Q4 parsing]
[Functions for "recent" interpretation]

### Phase 1D.3: S6 Module Additions
[COMPLETE test functions to add to s6_harness.py]
[Multi-claim regression test]
[Numeric edge case tests]
[Temporal edge case tests]

### Success Criteria for Phase 1D
[Complete checklist]

---

**END OF DESIGN_SPECIFICATIONS_COMPLETE.md**
```

## Quality Standards for Session 01

**ZERO PLACEHOLDERS:**
- Search output file for "[" - should only be in code or markdown
- No "[continue with...]"
- No "[implement...]"
- No "[etc.]"
- No "..." indicating omitted content

**COMPLETENESS:**
- Every function fully specified
- Every test case has exact input and expected output
- Every code modification has exact before/after
- Every schema fully defined

**Use SOURCE_OF_TRUTH evidence:**
- P1-P13 schemas based on actual code in Section 9
- Line numbers from Section 9 file evidence
- Integration gaps from Section 4

## Deliverable

**File:** `DESIGN_SPECIFICATIONS_COMPLETE.md` (~140-160KB)

**Confirm complete when:**
- [ ] All phases specified (0, 1A, 1B, 1C, 1D)
- [ ] Zero placeholders verified
- [ ] All functions have complete implementations or exact specifications
- [ ] All test cases have exact inputs/outputs
- [ ] All code modifications have exact before/after code

---

# SESSION 02: CREATE MASTER PLAN

**Token Budget:** ~50-70K (safe margin)

## Your Task

Read `DESIGN_SPECIFICATIONS_COMPLETE.md` and create `MASTER_PLAN_COMPLETE.md` breaking the work into 12 implementation steps.

## Required Reading

1. `DESIGN_SPECIFICATIONS_COMPLETE.md` (from Session 01)
2. `verification_package/CONSENSUS_ANALYSIS_FINAL.md` (for effort estimates validation)

## Output Structure

```markdown
# MASTER PLAN - ROGRv2 Backend Completion
**Version:** 1.0
**Created:** [DATE]
**Based on:** DESIGN_SPECIFICATIONS_COMPLETE.md

---

## Overview

**Total Duration:** 3-4 weeks
**Total Steps:** 12
**Total Tokens:** ~1.2M across all implementation sessions
**Branch:** rogrv2-backend-wrapup
**Quality Principle:** Quality, Consistency, Accuracy over Speed

---

## Step Breakdown

### Step 01: Phase 0 - Build Regression Test Suite
**Purpose:** Create S6 harness for safety net
**Token Estimate:** ~100-120K
**Duration:** 1 session (4-6 hours)
**Dependencies:** None
**Design Spec Reference:** DESIGN_SPECIFICATIONS_COMPLETE.md - Phase 0 section

**Files to Create:**
- intelligence/test/s6_harness.py (280-320 lines)

**What to Implement:**
- 14+ test functions (capture_baseline through test_integration_regression)
- All P1-P13 schemas
- All test cases with exact inputs from spec

**Success Criteria:**
- [ ] s6_harness.py created with all functions
- [ ] Baseline captured
- [ ] All tests passing
- [ ] Test suite runs in <10 seconds
- [ ] Code committed: "[Session 01] Phase 0: Build S6 regression harness"

**Risks:** Low - isolated test code
**Mitigation:** Clear complete specifications, no integration dependencies

**Token Breakdown:**
- Context loading: ~10K
- Implementation: ~80K
- Testing/debugging: ~20K
- Documentation: ~10K

---

### Step 02: Phase 1A - Fix Integration Gaps
**Purpose:** Fix pipeline.py, wire online.py, enable multi-claim
**Token Estimate:** ~80-100K
**Duration:** 1 session (4-6 hours)
**Dependencies:** Step 01 (need S6 tests to verify no regressions)
**Design Spec Reference:** DESIGN_SPECIFICATIONS_COMPLETE.md - Phase 1A section

**Files to Modify:**
- intelligence/gather/pipeline.py (lines 32-35)
- intelligence/pipeline/run.py (line 29, lines 37-44, gather integration)
- api/analyses.py (preview_analysis endpoint)

**What to Implement:**
- Modification 1: Fix candidates bug (exact code from spec)
- Modification 2: Async conversion (exact changes from spec)
- Modification 3: Multi-claim wiring (exact conditional from spec)
- Modification 4: online.py integration (exact pattern from spec)

**Success Criteria:**
- [ ] All 4 modifications complete per spec
- [ ] S6 tests still pass
- [ ] Integration tests pass
- [ ] Guardrails confirmed executing
- [ ] Live mode end-to-end works
- [ ] Code committed: "[Session 02] Phase 1A: Fix integration gaps"

**Risks:** Medium - core pipeline changes, async conversion
**Mitigation:** S6 regression tests catch breakage, exact code specifications

**Token Breakdown:**
- Context loading: ~10K
- Code changes (4 modifications): ~40K
- Testing/debugging: ~20K
- Documentation: ~10K

---

### Step 03: Phase 1B.1 - Query Refinement
**Purpose:** Implement AI query refinement per spec
**Token Estimate:** ~100-110K
**Duration:** 1 session (4-6 hours)
**Dependencies:** Step 02 (need integration working)
**Design Spec Reference:** DESIGN_SPECIFICATIONS_COMPLETE.md - Phase 1B Component 1B.1

[Continue for all 12 steps with same detail level]

---

## Dependency Graph

```
Step 01 (Phase 0)
    ↓
Step 02 (Phase 1A)
    ↓
Step 03 (1B.1) ← Sequential
    ↓
Step 04 (1B.2) ← Sequential
    ↓
Step 05 (1B.3) ← Sequential
    ↓
Step 06 (1B.4) ← Sequential
    ↓
Step 07 (1B.5) ← Needs all 1B components
    ↓
Step 08 (1C) ← Can be parallel with 1D if needed
    ↓
Step 09-11 (1D) ← Sequential or parallel with 1C
    ↓
Step 12 (Integration test) ← Needs everything
```

---

## Token Budget Summary

| Phase | Steps | Est. Tokens | Sessions |
|-------|-------|-------------|----------|
| Phase 0 | 1 | ~110K | 1 |
| Phase 1A | 1 | ~90K | 1 |
| Phase 1B | 5 | ~530K | 5 |
| Phase 1C | 1 | ~100K | 1 |
| Phase 1D | 3 | ~270K | 3 |
| Integration | 1 | ~80K | 1 |
| **Total** | **12** | **~1.2M** | **12** |

---

## Risk Mitigation

[For each risk type, provide mitigation strategy]

---

## Recovery Procedures

[Complete procedures for session failure, test failure, spec ambiguity]

---

**END OF MASTER_PLAN_COMPLETE.md**
```

## Deliverable

**File:** `MASTER_PLAN_COMPLETE.md` (~20-30KB)

**Confirm complete when:**
- [ ] All 12 steps detailed
- [ ] Each step has: purpose, token estimate, dependencies, files, success criteria, risks, token breakdown
- [ ] Complete dependency graph
- [ ] Complete token budget summary
- [ ] Risk mitigation for all phases
- [ ] Recovery procedures documented

---

# SESSION 03: CREATE STEP PROMPTS

**Token Budget:** ~60-85K (safe margin)

## Your Task

Read both design documents and create 12 individual step prompt files.

## Required Reading

1. `DESIGN_SPECIFICATIONS_COMPLETE.md`
2. `MASTER_PLAN_COMPLETE.md`

## Output Files

Create 12 files in `step_prompts/`:
- step01_phase0.md
- step02_phase1a.md
- step03_phase1b1.md
- step04_phase1b2.md
- step05_phase1b3.md
- step06_phase1b4.md
- step07_phase1b5.md
- step08_phase1c.md
- step09_phase1d1.md
- step10_phase1d2.md
- step11_phase1d3.md
- step12_integration.md

## Template for Each Prompt

```markdown
# STEP XX - [Phase/Component Name]

**Purpose:** [From master plan]

**Plain English:** [Non-developer explanation of what this does]

**Token Estimate:** ~XXK

---

## Required Reading

**Before starting:**
1. `implementation_plan/TENANTS.md` - Behavior guidelines
2. `implementation_plan/IMPLEMENTATION_STATE.md` - Current state
3. `DESIGN_SPECIFICATIONS_COMPLETE.md` - **[Specific phase section]**
4. `MASTER_PLAN_COMPLETE.md` - Step XX details

---

## Your Task

Implement [phase/component] exactly as specified in DESIGN_SPECIFICATIONS_COMPLETE.md [section reference].

**Files to create/modify:**
- [List from master plan]

**What to implement:**
- [List from master plan]

**DO NOT:**
- Deviate from specifications
- Add features not specified
- Skip any functions or requirements

---

## Success Criteria

Complete when:
- [ ] [Criteria from master plan]
- [ ] [Criteria from master plan]
- [ ] S6 regression tests pass
- [ ] New tests pass
- [ ] Code committed: "[Session XX] [Commit message]"

---

## Run Tests

```bash
[Test commands from spec]
```

Expected: [Pass criteria]

---

**May I proceed with implementing this step per the specifications?**
```

## Deliverable

**12 files:** `step_prompts/step01_phase0.md` through `step12_integration.md` (~2-3KB each)

**Confirm complete when:**
- [ ] All 12 prompt files created
- [ ] Each references correct design spec section
- [ ] Each has complete success criteria
- [ ] Each is copy-paste ready

---

# SUMMARY FOR USER

## Session 01 Prompt
Copy-paste the **"SESSION 01: CREATE COMPLETE DESIGN SPECIFICATIONS"** section into fresh Claude session.

## Session 02 Prompt
Copy-paste the **"SESSION 02: CREATE MASTER PLAN"** section into fresh Claude session (after Session 01 completes).

## Session 03 Prompt
Copy-paste the **"SESSION 03: CREATE STEP PROMPTS"** section into fresh Claude session (after Session 02 completes).

## After All 3 Sessions
You'll have:
- DESIGN_SPECIFICATIONS_COMPLETE.md (complete, zero drift)
- MASTER_PLAN_COMPLETE.md (12 steps planned)
- 12 step prompt files (ready for implementation)

Then begin implementation with Step 01.

---

**END OF COMPLETE HANDOFF**
