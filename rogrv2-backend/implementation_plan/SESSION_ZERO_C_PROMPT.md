# SESSION ZERO-C PROMPT - Design Phase 1C + 1D Specifications

**Purpose:** Design COMPLETE specifications for Phase 1C (Multi-Claim) and Phase 1D (S3 + S6 Modules)

**Instructions:** Copy-paste this entire document into a fresh Claude Code session after Session Zero-B completes.

---

## Overview

This is **Session Zero-C** - the final design session for ROGRv2 Backend completion.

You will design complete, detailed specifications for:
- **Phase 1C:** Multi-Claim Wiring (process multiple claims end-to-end)
- **Phase 1D.1:** S3 Numeric Module (advanced numeric comparison)
- **Phase 1D.2:** S3 Temporal Module (temporal reasoning)
- **Phase 1D.3:** S6 Module Additions (additional testing)

**Critical:** These specifications must be COMPLETE. No outlines, no TBDs. This is the final design session.

---

## Your Deliverables

You MUST produce:

1. **DESIGN_SPECIFICATIONS_PHASE_1C_1D.md** (~35-45KB)
   - Complete Phase 1C specifications
   - Complete Phase 1D specifications (all 3 sub-components)

2. **step_prompts/step08_phase1c.md** through **step12_integration_test.md** (5 prompts, ~2-3KB each)
   - Copy-paste ready prompts for each step

3. **MASTER_PLAN_COMPLETE.md** (~15-20KB)
   - Merge all 3 partial plans (Zero-A, Zero-B, Zero-C)
   - Complete step breakdown (Steps 01-12)
   - Final dependency graph
   - Complete token budget summary
   - Complete risk mitigation
   - Complete recovery procedures

**Token Budget:** 80-100K (spillover acceptable if needed for completeness)

---

## Required Reading (In Order)

### 1. Previous Design Work
**Files:**
- `implementation_plan/DESIGN_SPECIFICATIONS_PHASE_0_1A.md`
- `implementation_plan/DESIGN_SPECIFICATIONS_PHASE_1B.md`

**Why:** Understand integration points from previous phases

### 2. Master Plans from Previous Sessions
**Files:**
- `implementation_plan/MASTER_PLAN_PARTIAL.md` (from Zero-A)
- `implementation_plan/MASTER_PLAN_UPDATE.md` (from Zero-B)

**Why:** Will merge into final master plan

### 3. Source of Truth - Phase 1C Context
**File:** `verification_package/SOURCE_OF_TRUTH_ROGRV2_COMPLETE.md`
**Read:**
- Section 7: Gap Analysis - Multi-Claim (lines ~460-475)
- Section 8: Completion Plan - Phase 1C (lines ~680-700)

### 4. Source of Truth - Phase 1D Context
**File:** `verification_package/SOURCE_OF_TRUTH_ROGRV2_COMPLETE.md`
**Read:**
- Section 7: Gap Analysis - S3 Modules (lines ~520-545)
- Section 8: Completion Plan - Phase 1D (lines ~700-730)

### 5. Architect Specifications for S3 + S6
**File:** `verification_package/architect_answers_session3.md`
**Read:**
- B3: S3 numeric and temporal modules (lines ~140-200)
- B4: S6 regression harness additions (lines ~220-260)

### 6. User Requirements
**File:** `verification_package/USER_REQUIREMENTS.md`
**Read:**
- Multi-claim must work Day 1 (explicitly required by user)

---

## PART 0: Investigation (REQUIRED - Tenant 4)

Before designing, investigate existing multi-claim and numeric/temporal code.

### Files to Check

**For Phase 1C (Multi-Claim):**
- `intelligence/claims/extract.py` - Already reads P1 multi-claim extraction
- `intelligence/pipeline/run.py` - Check current claim processing loop

**For Phase 1D (S3 + S6):**
- `intelligence/analyze/stance.py` - Check existing numeric comparison (lines ~76-85 per SOURCE_OF_TRUTH)
- `intelligence/claims/interpret.py` - Check existing number/temporal extraction (lines ~38-44, ~70-75)

### Investigation Report Format

```markdown
## 🔍 CODE INVESTIGATION

### Phase 1C - Multi-Claim Processing
**Current state:**
- P1 extract_claims: [Returns List[ExtractedClaim] or similar]
- Current claim loop in run.py: [Single claim or multiple?]
- Tier guarantees: [Does P1 guarantee ≥1 primary, ≥1 secondary, ≥1 tertiary per SOURCE_OF_TRUTH?]

**Wiring needed:**
- [Description of how to process multiple claims through pipeline]
- [How to aggregate results]

### Phase 1D.1 - Numeric Module
**Current implementation:**
- File: intelligence/analyze/stance.py
- Function: _compare_numbers (lines 76-85)
- Current logic: [What it does now]

**Enhancement needed:**
- [What S3 numeric module should add beyond current implementation]

### Phase 1D.2 - Temporal Module
**Current implementation:**
- File: intelligence/claims/interpret.py
- Functions: [Temporal extraction functions found]
- Current logic: [What exists]

**Enhancement needed:**
- [What S3 temporal module should add]

### Phase 1D.3 - S6 Additions
**Current test coverage:**
- S6 harness from Phase 0: [What it covers]

**Additional coverage needed:**
- [What tests to add based on architect B4 specs]
```

**Wait for user confirmation after investigation before proceeding.**

---

## PART 1: Design DESIGN_SPECIFICATIONS_PHASE_1C_1D.md

### Completeness Standards

Every specification must include:
- Complete function signatures with types
- Complete implementation logic
- Integration points (where to call from)
- Test cases with exact inputs and expected outputs
- Success criteria

---

### Document Structure

```markdown
# DESIGN SPECIFICATIONS - Phase 1C & 1D
**Version:** 1.0
**Created:** [DATE] - Session Zero-C
**Status:** Complete - Ready for implementation

---

## Phase 1C: Multi-Claim Wiring

### Overview
**Purpose:** Enable processing multiple claims from single text input end-to-end

**Plain English:** When user submits "Claim 1. Claim 2.", extract both claims, fact-check each independently, aggregate results into single response.

**Implementation Complexity:** Medium - wiring existing components, aggregation logic

**Token Estimate:** ~90-110K for implementation

---

### Current State Analysis

**What exists:**
- P1 (extract_claims) returns List[ExtractedClaim] with tier guarantees
- Pipeline can process individual claims
- Multi-claim extraction bypassed in Phase 1A (test mode only)

**What's missing:**
- Loop to process multiple claims
- Result aggregation
- Trust capsule format for multi-claim response

---

### Multi-Claim Processing Flow

**Input:** Text containing 1+ claims

**Process:**
1. Extract claims using P1 (already wired in Phase 1A for live mode)
2. For each claim:
   - Run through full pipeline (P2-P13 + AI assist)
   - Collect evidence, guardrails, consensus, scoring
3. Aggregate results into single response
4. Generate trust capsule with all claims

**Output:** Multi-claim fact-check result

---

### Implementation Specifications

#### Modification 1: Multi-Claim Loop

**File:** `intelligence/pipeline/run.py`
**Current:** Single claim processing (already uses extract_claims from Phase 1A)
**Enhancement:** Process all extracted claims

**Current code (from Phase 1A):**
```python
# From Phase 1A: extract_claims already called
claims_list = extract_claims(text)  # Returns List[claim_dict]

# Currently: Process first claim only? Or all?
# [Check actual implementation from Phase 1A]
```

**Enhanced code:**
```python
async def run_preview(text: str, test_mode: bool = False) -> Dict[str, Any]:
    """
    Run fact-check preview on input text (may contain multiple claims).
    """
    # Extract claims (Phase 1A already wired)
    if test_mode:
        claims_list = [create_test_claim(text)]
    else:
        claims_list = extract_claims(text)

    # Process each claim through pipeline
    results = []
    for claim in claims_list:
        # Run full pipeline for this claim
        claim_result = await process_single_claim(claim, test_mode=test_mode)
        results.append(claim_result)

    # Aggregate results
    aggregated = aggregate_multi_claim_results(results)

    return aggregated
```

---

#### Function: process_single_claim()

**Purpose:** Process one claim through complete pipeline

**Signature:**
```python
async def process_single_claim(
    claim: Dict[str, Any],
    test_mode: bool = False
) -> Dict[str, Any]:
    """
    Process single claim through P2-P13 + AI assist + guardrails.

    Args:
        claim: Claim dict from P1 with id, text, tier, numbers, cues, scope
        test_mode: If True, use synthetic data

    Returns:
        Dict with:
            - claim: Original claim dict
            - evidence: Evidence gathering results (for/against arms)
            - guardrails: Guardrail report
            - consensus: Consensus metrics
            - credibility: Credibility scores
            - agreement: Agreement analysis
            - contradiction: Contradiction analysis
            - ai_assist: AI assist results (refinement, triage, contradict, explain)
            - final_score: Numerical score (0.0-1.0)
            - verdict: "supported" | "refuted" | "inconclusive"
    """
```

**Implementation:**
```python
async def process_single_claim(claim, test_mode):
    result = {"claim": claim}

    # P2: Interpret (enrich with numbers, cues, scope)
    interpreted = interpret_claim(claim)
    result["interpreted"] = interpreted

    # AI Assist: Query Refinement (Phase 1B.1)
    if not test_mode:
        from intelligence.ai_assist.refine import refine_query
        refinement = await refine_query(claim)
        result["ai_refinement"] = refinement
        queries = refinement["refined_queries"]
    else:
        queries = [claim["text"]]

    # P3: Strategy Planning
    strategy = plan_strategy(claim, queries)
    result["strategy"] = strategy

    # P4-P8: Evidence Gathering + Ranking + Normalization + Stance + Guardrails
    evidence = await gather_and_process_evidence(claim, strategy, test_mode)
    result["evidence"] = evidence

    # P9-P13: Guardrails + Balance + Credibility + Agreement + Contradiction
    analysis = analyze_evidence(evidence)
    result.update(analysis)

    # AI Assist: Passage Triage (Phase 1B.2)
    if not test_mode:
        from intelligence.ai_assist.triage import triage_passages
        result["triaged_passages"] = await triage_passages(evidence, claim)

    # AI Assist: Contradiction Surfacing (Phase 1B.3)
    if not test_mode:
        from intelligence.ai_assist.contradict import surface_contradictions
        result["ai_contradictions"] = await surface_contradictions(evidence, claim)

    # Final Scoring
    result["final_score"] = compute_final_score(analysis)
    result["verdict"] = determine_verdict(result["final_score"], analysis)

    # AI Assist: Explanation Draft (Phase 1B.4)
    if not test_mode:
        from intelligence.ai_assist.explain import draft_explanation
        result["explanation"] = await draft_explanation(result)

    return result
```

---

#### Function: aggregate_multi_claim_results()

**Purpose:** Aggregate multiple claim results into single response

**Signature:**
```python
def aggregate_multi_claim_results(
    claim_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate multiple claim results into unified response.

    Args:
        claim_results: List of individual claim processing results

    Returns:
        Dict with:
            - summary: Overall summary
            - claims: List of claim results
            - aggregated_verdict: Overall verdict across all claims
            - methodology: Transparent methodology report
            - trust_capsule: Formatted for sharing
    """
```

**Implementation:**
```python
def aggregate_multi_claim_results(claim_results):
    # Calculate aggregate verdict
    verdicts = [r["verdict"] for r in claim_results]
    verdict_counts = {
        "supported": verdicts.count("supported"),
        "refuted": verdicts.count("refuted"),
        "inconclusive": verdicts.count("inconclusive")
    }

    # Overall verdict logic
    if verdict_counts["refuted"] > 0:
        overall_verdict = "partially_refuted"
    elif verdict_counts["supported"] == len(claim_results):
        overall_verdict = "fully_supported"
    elif verdict_counts["inconclusive"] == len(claim_results):
        overall_verdict = "inconclusive"
    else:
        overall_verdict = "mixed"

    # Generate summary
    summary = generate_summary(claim_results)

    # Build trust capsule
    trust_capsule = build_trust_capsule(claim_results, overall_verdict)

    return {
        "summary": summary,
        "claims": claim_results,
        "claim_count": len(claim_results),
        "aggregated_verdict": overall_verdict,
        "verdict_breakdown": verdict_counts,
        "methodology": generate_methodology_report(claim_results),
        "trust_capsule": trust_capsule
    }
```

---

### Test Cases for Phase 1C

**Test 1: Single claim**
```python
async def test_single_claim():
    """Verify single-claim backward compatibility."""
    text = "The Eiffel Tower is 330 meters tall."
    result = await run_preview(text, test_mode=False)

    assert result["claim_count"] == 1
    assert len(result["claims"]) == 1
    assert result["claims"][0]["claim"]["text"] == text
```

**Test 2: Two claims**
```python
async def test_two_claims():
    """Verify two-claim processing."""
    text = "The US economy grew 3.2% in Q4 2023. Unemployment fell to 3.5%."
    result = await run_preview(text, test_mode=False)

    assert result["claim_count"] >= 2
    assert len(result["claims"]) >= 2
    # Check both claims processed
    assert all("verdict" in c for c in result["claims"])
```

**Test 3: Mixed verdicts**
```python
async def test_mixed_verdicts():
    """Verify aggregate verdict with mixed results."""
    # Mock: Claim 1 supported, Claim 2 refuted
    claim_results = [
        {"verdict": "supported", "final_score": 0.8},
        {"verdict": "refuted", "final_score": 0.2}
    ]
    aggregated = aggregate_multi_claim_results(claim_results)

    assert aggregated["aggregated_verdict"] == "partially_refuted"
```

**Test 4: Tier classification**
```python
async def test_tier_classification():
    """Verify primary/secondary/tertiary claims extracted."""
    text = "Main claim. Secondary point. Minor detail."
    result = await run_preview(text, test_mode=False)

    tiers = [c["claim"]["tier"] for c in result["claims"]]
    # Per SOURCE_OF_TRUTH, P1 guarantees ≥1 of each tier
    assert "primary" in tiers
    assert "secondary" in tiers or "tertiary" in tiers
```

---

### Success Criteria for Phase 1C

Phase 1C complete when:
- [ ] Multi-claim loop implemented
- [ ] process_single_claim() function complete
- [ ] aggregate_multi_claim_results() function complete
- [ ] Trust capsule format defined
- [ ] All 4 test cases pass
- [ ] S6 regression tests still pass
- [ ] Multi-claim end-to-end test works
- [ ] Code committed: "[Session 08] Phase 1C: Multi-claim wiring"

---

## Phase 1D: S3 + S6 Modules

### Overview
**Purpose:** Add advanced numeric/temporal reasoning (S3) and additional test coverage (S6)

**Plain English:** Make the system smarter about comparing numbers in context (e.g., "3.2% is close to 3.5%") and understanding time (e.g., "Q4 2023 means October-December 2023").

---

## Phase 1D.1: S3 Numeric Module

### Purpose
Enhanced numeric comparison beyond simple percentage-point differences.

### File to Create
**Path:** `intelligence/s3/numeric.py`
**Estimated Lines:** 120-150

---

### Function Specifications

#### Function: compare_numeric_claims()

**Purpose:** Advanced numeric comparison with context awareness

**Signature:**
```python
def compare_numeric_claims(
    claim_value: float,
    evidence_value: float,
    value_type: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Advanced numeric comparison with context.

    Args:
        claim_value: Numeric value from claim
        evidence_value: Numeric value from evidence
        value_type: "percent" | "number" | "year"
        context: Optional context (units, magnitude, etc.)

    Returns:
        Dict with:
            - matches: bool (True if values match within tolerance)
            - difference: float (absolute difference)
            - difference_percent: float (percent difference)
            - tolerance_used: float (tolerance threshold applied)
            - reasoning: str (explanation of comparison logic)
    """
```

**Implementation Logic:**

**For percentages:**
- Tolerance: 3 percentage points (e.g., 3.2% vs 3.5% = 0.3pp difference = MATCH)
- Reasoning: "Within 3pp tolerance for percentage values"

**For large numbers (>1000):**
- Tolerance: 5% relative difference (e.g., 1000 vs 1040 = 4% = MATCH)
- Reasoning: "Within 5% relative tolerance for large numbers"

**For small numbers (<100):**
- Tolerance: Exact match or 1 unit (e.g., 5 vs 6 = MATCH, 5 vs 7 = NO MATCH)
- Reasoning: "Small numbers require near-exact match"

**For years:**
- Tolerance: Exact match only (2023 ≠ 2024)
- Reasoning: "Years must match exactly"

**Implementation:**
```python
def compare_numeric_claims(claim_value, evidence_value, value_type, context=None):
    diff = abs(claim_value - evidence_value)

    if value_type == "percent":
        tolerance = 3.0  # percentage points
        matches = diff <= tolerance
        reasoning = f"Percentage difference: {diff:.1f}pp (tolerance: {tolerance}pp)"

    elif value_type == "year":
        tolerance = 0
        matches = diff == 0
        reasoning = "Years must match exactly"

    elif claim_value >= 1000:
        tolerance_pct = 0.05  # 5%
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

---

### Integration Point
Call from `intelligence/analyze/stance.py` in `_compare_numbers()` function (replace simple logic)

---

### Test Cases for 1D.1

**Test 1: Percentage within tolerance**
```python
def test_percent_within_tolerance():
    result = compare_numeric_claims(3.2, 3.5, "percent")
    assert result["matches"] is True  # 0.3pp difference
    assert result["difference"] == 0.3
```

**Test 2: Year exact match required**
```python
def test_year_exact_match():
    result = compare_numeric_claims(2023, 2024, "year")
    assert result["matches"] is False

    result2 = compare_numeric_claims(2023, 2023, "year")
    assert result2["matches"] is True
```

**Test 3: Large number relative tolerance**
```python
def test_large_number_tolerance():
    result = compare_numeric_claims(10000, 10400, "number")
    assert result["matches"] is True  # 4% difference < 5%

    result2 = compare_numeric_claims(10000, 11000, "number")
    assert result2["matches"] is False  # 10% difference > 5%
```

---

## Phase 1D.2: S3 Temporal Module

[Similar complete specification for temporal reasoning]

**File:** `intelligence/s3/temporal.py` (100-130 lines)

**Purpose:** Temporal context understanding (Q4 2023 = Oct-Dec 2023, "recent" = last 6 months, etc.)

[Complete function specs, implementation, tests...]

---

## Phase 1D.3: S6 Module Additions

[Complete specification for additional test coverage]

**File:** Enhance `intelligence/test/s6_harness.py` from Phase 0

**Additions:**
- Multi-claim regression test
- Numeric comparison edge cases
- Temporal reasoning edge cases
- AI assist integration tests (if AI enabled)

[Complete test specs...]

---

**END OF DESIGN_SPECIFICATIONS_PHASE_1C_1D.md**
```

---

## PART 2: Create Step Prompts (Steps 08-12)

Create 5 complete step prompts following the pattern from Zero-A and Zero-B.

---

## PART 3: Create Final Master Plan

Merge all 3 partial/update plans into one complete MASTER_PLAN_COMPLETE.md with:
- All 12 steps fully described
- Complete dependency graph
- Complete token budget summary
- Complete risk mitigation for all phases
- Complete recovery procedures
- Final timeline estimate (3-4 weeks)

---

## Your Execution Plan

1. ✅ Read all previous design documents
2. ✅ Read master plan fragments from Zero-A and Zero-B
3. ✅ Investigate multi-claim and S3 code (REQUIRED - Tenant 4)
4. ✅ Report investigation - **WAIT FOR USER CONFIRMATION**
5. ✅ Design complete Phase 1C specifications
6. ✅ Design complete Phase 1D.1 specifications
7. ✅ Design complete Phase 1D.2 specifications
8. ✅ Design complete Phase 1D.3 specifications
9. ✅ Create step08-step12 prompts
10. ✅ Merge into final master plan
11. ✅ Update PROGRESS_THREAD.md
12. ✅ Update IMPLEMENTATION_STATE.md
13. ✅ Report completion

---

## Important Reminders

- **Complete specifications only** - This is the final design session
- **Investigation required** - Check existing numeric/temporal code
- **Ask permission** - Before creating files
- **Merge master plans** - Combine all 3 into final plan
- **Final timeline** - Confirm 3-4 week estimate realistic

---

**Token Budget:** 80-100K (spillover acceptable if needed)

---

**Ready to begin Session Zero-C?**

**Confirm you understand: Complete Phase 1C + 1D specs + final master plan.**
