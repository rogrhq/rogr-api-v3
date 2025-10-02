# HANDOFF TO SESSION 01 - FIX SESSION ZERO PROMPTS

**Date:** 2025-09-30
**From:** Session 00 (Planning - FAILED on Session Zero prompts)
**To:** Session 01 (Fix Session Zero prompts)
**Status:** CRITICAL - Session Zero prompts are BROKEN and must be recreated

---

## What Happened (Summary)

Session 00 created implementation framework but FAILED to create proper Session Zero prompts.

**What's BROKEN:**
- `implementation_plan/SESSION_ZERO_A_PROMPT.md` - Has placeholders like "[Continue with complete specifications for P2-P13...]"
- `implementation_plan/SESSION_ZERO_B_PROMPT.md` - Has placeholders like "[Continue with COMPLETE specification...]"
- `implementation_plan/SESSION_ZERO_C_PROMPT.md` - Has placeholders and meta-templates

**These are NOT executable. They are meta-templates that tell Claude to create specs, but don't provide complete specs.**

**What's CORRECT and should NOT be changed:**
- `TENANTS.md` - Complete, ready to use
- `SESSION_START_TEMPLATE.md` - Complete, ready to use
- `SESSION_WRAPUP_TEMPLATE.md` - Complete, ready to use
- `PROGRESS_THREAD.md` - Complete tracking document
- `IMPLEMENTATION_STATE.md` - Complete state snapshot
- `NEXT_SESSION_PROMPT.md` - Complete template
- `README.md` - Complete instructions

---

## Your Task (Session 01)

**DELETE the 3 broken Session Zero prompts and CREATE 3 NEW ones that are COMPLETE and EXECUTABLE.**

**Critical Requirement:** ZERO placeholders, ZERO meta-templates, ZERO "[continue with...]" text.

**The 3-session split is correct** (we cannot fit all specs in one session due to token budget ~155-205KB total).

---

## Specifications for Each Session Zero Prompt

### SESSION_ZERO_A_PROMPT.md (~40-50KB)

**Must contain COMPLETE specifications for:**

#### Phase 0: Regression Test Suite
**COMPLETE means:**
- Every test function fully specified (14+ functions)
- All 13 schemas defined (P1-P13 output structures)
  - P1 schema: Complete with all keys, types, patterns
  - P2 schema: Complete with all keys, types, patterns
  - P3-P13 schemas: Complete with all keys, types, patterns
- All test cases with EXACT inputs and expected outputs
  - Test input 1: "The Eiffel Tower is 330 meters tall."
  - Test input 2: "US GDP grew 3.2% in Q4 2023."
  - Test input 3: "Vaccines do not cause autism."
- Complete implementation for capture_baseline_outputs()
- Complete implementation for validate_output_structure()
- Complete implementation for test_p1_extract_claims()
- Complete implementation for test_p2_interpret()
- Complete implementation for test_p3_plan()
- Complete implementation for test_p4_rank()
- Complete implementation for test_p5_normalize()
- Complete implementation for test_p6_fetch()
- Complete implementation for test_p7_stance()
- Complete implementation for test_p8_snapshot()
- Complete implementation for test_p9_guardrails()
- Complete implementation for test_p10_balance()
- Complete implementation for test_p11_credibility()
- Complete implementation for test_p12_agreement()
- Complete implementation for test_p13_contradict()
- Complete implementation for test_integration_regression()

**NO PLACEHOLDERS. Every function body specified, not "[implement according to spec]".**

#### Phase 1A: Integration Fixes
**COMPLETE means:**
- Investigation instructions (what files to read, what to look for)
- Exact file paths and line numbers to modify
- Exact code changes (before/after) for all 4 modifications:
  1. pipeline.py fix (lines 32-35) - EXACT code before and after
  2. run.py async conversion (line 29 + internal changes) - EXACT code
  3. Multi-claim wiring (lines 37-44) - EXACT code with conditional logic
  4. online.py integration - EXACT pattern with error handling
- All integration test cases with inputs/outputs
- Success criteria checklist

#### Step Prompts
- step01_phase0.md - Complete, copy-paste ready
- step02_phase1a.md - Complete, copy-paste ready

#### Master Plan
- MASTER_PLAN_PARTIAL.md with Steps 01-02 fully detailed

**Token Estimate:** ~80-100K for Session Zero-A execution

---

### SESSION_ZERO_B_PROMPT.md (~50-65KB)

**Must contain COMPLETE specifications for:**

#### Shared AI Infrastructure
- Complete config.py implementation
  - Full code for AIAssistError exception
  - Full code for TokenBudgetExceeded exception
  - Full code for call_openai() function with retry logic
  - Full code for client initialization
  - All constants defined

#### Phase 1B.1: Query Refinement
**COMPLETE means:**
- EXACT system prompt text (full text, not "see example")
- EXACT user prompt template (full code)
- EXACT function signature with complete docstring
- COMPLETE implementation (full function body)
- EXACT API call structure (model, temperature, max_tokens, timeout)
- EXACT error handling (all failure modes)
- EXACT fallback logic (what to return on failure)
- EXACT zero bias verification code
- All 5 test cases with EXACT inputs and expected outputs
- Integration point instructions (where to call from, exact pattern)

#### Phase 1B.2: Passage Triage
**COMPLETE specifications (same level of detail as 1B.1):**
- EXACT system prompt
- EXACT user prompt template
- COMPLETE function implementation
- EXACT API call structure
- EXACT error handling
- All 5 test cases
- Integration point

#### Phase 1B.3: Contradiction Surfacing
**COMPLETE specifications (same level of detail):**
- EXACT system prompt
- EXACT user prompt template
- COMPLETE function implementation
- EXACT API call structure
- EXACT error handling
- All 5 test cases
- Integration point

#### Phase 1B.4: Explanation Draft
**COMPLETE specifications (same level of detail):**
- EXACT system prompt
- EXACT user prompt template
- COMPLETE function implementation
- EXACT API call structure
- EXACT error handling
- All 5 test cases
- Integration point

#### Phase 1B.5: Integration
**COMPLETE specifications:**
- Exact modification points in pipeline.py
- Exact code to add (before/after markers)
- Error handling strategy
- Non-blocking failure approach
- All integration test cases

#### Step Prompts
- step03_phase1b1.md through step07_phase1b5.md - All complete

#### Master Plan Update
- MASTER_PLAN_UPDATE.md with Steps 03-07 fully detailed

**Token Estimate:** ~100-120K for Session Zero-B execution

---

### SESSION_ZERO_C_PROMPT.md (~40-50KB)

**Must contain COMPLETE specifications for:**

#### Phase 1C: Multi-Claim Wiring
**COMPLETE means:**
- EXACT process_single_claim() implementation
- EXACT aggregate_multi_claim_results() implementation
- EXACT multi-claim loop code in run.py
- Trust capsule format definition (exact structure)
- All test cases with inputs/outputs
- Success criteria checklist

#### Phase 1D.1: S3 Numeric Module
**COMPLETE means:**
- EXACT compare_numeric_claims() implementation
  - Exact tolerance values for each type
  - Exact comparison logic (if/elif/else structure)
  - Exact reasoning strings
- Integration point (where to call from)
- All test cases

#### Phase 1D.2: S3 Temporal Module
**COMPLETE means:**
- EXACT function implementations for temporal reasoning
- Exact logic for parsing Q1/Q2/Q3/Q4
- Exact logic for "recent" (last 6 months)
- Integration point
- All test cases

#### Phase 1D.3: S6 Module Additions
**COMPLETE means:**
- Exact test functions to add to s6_harness.py
- Exact test cases for multi-claim regression
- Exact test cases for numeric edge cases
- Exact test cases for temporal edge cases

#### Step Prompts
- step08_phase1c.md through step12_integration_test.md - All complete

#### Master Plan Complete
- MASTER_PLAN_COMPLETE.md - Merge of all 3 partial plans with:
  - All 12 steps fully detailed
  - Complete dependency graph
  - Complete token budget summary
  - Complete risk mitigation
  - Complete recovery procedures
  - Final timeline (3-4 weeks)

**Token Estimate:** ~80-100K for Session Zero-C execution

---

## How to Structure Each Prompt

### Template Structure

```markdown
# SESSION ZERO-X PROMPT - [Phase Description]

## Overview
[Brief description]

## Your Task
You will read this prompt and OUTPUT the complete specifications exactly as written below.

You are NOT designing. You are OUTPUTTING pre-designed specifications.

## Required Reading
[List of files to read for context]

## PART 1: Output DESIGN_SPECIFICATIONS_PHASE_X.md

Copy the following specifications EXACTLY into a new file:

```markdown
[COMPLETE SPECIFICATIONS - EVERY FUNCTION, EVERY TEST, EVERY CODE CHANGE]
[NO PLACEHOLDERS]
[NO "[continue with...]" TEXT]
[EVERYTHING SPECIFIED IN FULL]
```

## PART 2: Output step_prompts/stepXX.md

[COMPLETE step prompts - copy-paste ready]

## PART 3: Output MASTER_PLAN_X.md

[COMPLETE master plan section]

---

**Your deliverables checklist:**
- [ ] DESIGN_SPECIFICATIONS_PHASE_X.md created
- [ ] All step prompts created
- [ ] Master plan created
- [ ] Zero placeholders confirmed
- [ ] Ready for implementation
```

---

## Critical Requirements

### NO INVESTIGATION IN SESSION ZERO PROMPTS

**Session Zero A/B/C should NOT investigate code.**

Investigation happens in IMPLEMENTATION sessions (Step 01, Step 02, etc.).

Session Zero just OUTPUTS the pre-designed specifications you provide.

**Why:** Investigation wastes tokens. Specs should be designed based on:
- SOURCE_OF_TRUTH_ROGRV2_COMPLETE.md (already verified by 3 sessions)
- Architect answers (already verified)
- Existing code evidence (already documented in SOURCE_OF_TRUTH)

### COMPLETENESS STANDARD

**"Complete" means an implementation session can:**
1. Read the spec
2. Write the code exactly as specified
3. Run the tests exactly as specified
4. Commit the code
5. ZERO interpretation needed

**If implementation Claude has to "figure out" anything, the spec is incomplete.**

---

## Source Material You Must Use

### For Phase 0 Specs:
**Read:** `verification_package/SOURCE_OF_TRUTH_ROGRV2_COMPLETE.md`
- Section 9: Detailed File Evidence (lines 640-1100) - Shows P1-P13 actual output structures
- Use actual code evidence to define schemas

**Read:** `verification_package/architect_answers_session3.md`
- B4: S6 regression harness guidance (lines 220-260)

### For Phase 1A Specs:
**Read:** `verification_package/SOURCE_OF_TRUTH_ROGRV2_COMPLETE.md`
- Section 4: What's Broken (lines 210-280) - The 3 integration gaps with exact line numbers
- Section 9: File evidence for pipeline.py (lines 705-728), run.py (lines 730-765), online.py (lines 795-830)

### For Phase 1B Specs:
**Read:** `verification_package/architect_answers_session3.md`
- I11: AI model selection and token budgets (lines 310-380)
- I12: Provider configuration (lines 385-415)

**Read:** `verification_package/USER_REQUIREMENTS.md`
- AI assist requirements (MUST HAVE Day 1)

### For Phase 1C Specs:
**Read:** `verification_package/SOURCE_OF_TRUTH_ROGRV2_COMPLETE.md`
- Section 9: File evidence for extract.py (lines 785-794) - P1 multi-claim extraction already exists

### For Phase 1D Specs:
**Read:** `verification_package/SOURCE_OF_TRUTH_ROGRV2_COMPLETE.md`
- Section 9: File evidence for stance.py (lines 850-868) - Existing numeric comparison
- Section 9: File evidence for interpret.py (lines 795-808) - Existing number/temporal extraction

---

## Token Budget Allocation

**You have ~140K tokens remaining in this session.**

**Allocate:**
- SESSION_ZERO_A_PROMPT.md: ~45-50KB (Phase 0 + 1A complete specs)
- SESSION_ZERO_B_PROMPT.md: ~55-65KB (Phase 1B complete specs - 4 AI components)
- SESSION_ZERO_C_PROMPT.md: ~40-50KB (Phase 1C + 1D complete specs)
- **Total: ~140-165KB**

**If approaching 180K tokens:** Use spillover to next session. Update NEXT_SESSION_PROMPT.md with continuation instructions.

---

## Deliverables Checklist

You MUST produce:

- [ ] SESSION_ZERO_A_PROMPT.md (45-50KB, COMPLETE, zero placeholders)
- [ ] SESSION_ZERO_B_PROMPT.md (55-65KB, COMPLETE, zero placeholders)
- [ ] SESSION_ZERO_C_PROMPT.md (40-50KB, COMPLETE, zero placeholders)
- [ ] All 3 prompts verified for completeness
- [ ] README.md updated if needed
- [ ] PROGRESS_THREAD.md updated (append Session 01 entry)
- [ ] IMPLEMENTATION_STATE.md updated (Session Zero prompts ready)

---

## Quality Standard

**Before marking any prompt complete, verify:**

1. **Zero Placeholders Check:**
   - Search for "[" in file - should only appear in markdown formatting or code examples
   - No "[continue with...]" text
   - No "[implement according to...]" text
   - No "[etc.]" text
   - No "..." indicating omitted content

2. **Completeness Check:**
   - Every function has FULL implementation or EXACT specification
   - Every test case has EXACT input and expected output
   - Every code modification has EXACT before/after
   - Every schema has ALL keys defined

3. **Executability Check:**
   - An implementation session can copy-paste and execute
   - Zero design decisions left for implementation Claude
   - Zero interpretation needed

---

## Execution Plan

1. **Delete broken prompts:**
   - rm SESSION_ZERO_A_PROMPT.md
   - rm SESSION_ZERO_B_PROMPT.md
   - rm SESSION_ZERO_C_PROMPT.md

2. **Create SESSION_ZERO_A_PROMPT.md:**
   - Read source material (SOURCE_OF_TRUTH Section 4, 9)
   - Design COMPLETE Phase 0 specs (all 14+ functions, all schemas)
   - Design COMPLETE Phase 1A specs (all 4 modifications with exact code)
   - Create 2 complete step prompts
   - Create partial master plan
   - VERIFY zero placeholders

3. **Create SESSION_ZERO_B_PROMPT.md:**
   - Read source material (architect_answers I11, I12)
   - Design COMPLETE shared AI infrastructure
   - Design COMPLETE 1B.1 specs (query refinement - full implementation)
   - Design COMPLETE 1B.2 specs (passage triage - full implementation)
   - Design COMPLETE 1B.3 specs (contradiction - full implementation)
   - Design COMPLETE 1B.4 specs (explanation - full implementation)
   - Design COMPLETE 1B.5 specs (integration)
   - Create 5 complete step prompts
   - Create master plan update
   - VERIFY zero placeholders

4. **Create SESSION_ZERO_C_PROMPT.md:**
   - Read source material (SOURCE_OF_TRUTH Section 9)
   - Design COMPLETE Phase 1C specs (multi-claim wiring)
   - Design COMPLETE Phase 1D.1 specs (S3 numeric)
   - Design COMPLETE Phase 1D.2 specs (S3 temporal)
   - Design COMPLETE Phase 1D.3 specs (S6 additions)
   - Create 5 complete step prompts
   - Create final merged master plan
   - VERIFY zero placeholders

5. **Update tracking documents:**
   - Append to PROGRESS_THREAD.md
   - Update IMPLEMENTATION_STATE.md
   - Update README.md if changes needed

6. **Verify quality:**
   - All 3 prompts have zero placeholders
   - All 3 prompts are executable
   - All 3 prompts are complete

---

## What Success Looks Like

**After your session, a user should be able to:**

1. Copy-paste SESSION_ZERO_A_PROMPT.md → Claude outputs complete Phase 0+1A specs
2. Copy-paste SESSION_ZERO_B_PROMPT.md → Claude outputs complete Phase 1B specs
3. Copy-paste SESSION_ZERO_C_PROMPT.md → Claude outputs complete Phase 1C+1D specs
4. All 3 outputs have ZERO placeholders
5. Implementation can begin immediately with step01_phase0.md

---

## Important Reminders

- **Quality over speed** - Take time to make specs complete
- **Zero placeholders** - Non-negotiable
- **Use SOURCE_OF_TRUTH** - It's already verified, use its evidence
- **No investigation in Session Zero** - Session Zero outputs pre-designed specs
- **Token budget** - Monitor usage, spillover if needed

---

**This is critical work. The entire implementation depends on these 3 prompts being COMPLETE and EXECUTABLE.**

**Do NOT repeat Session 00's mistakes. Create prompts that actually work.**

---

**END OF HANDOFF**
