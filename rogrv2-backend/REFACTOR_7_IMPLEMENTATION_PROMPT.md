# REFACTOR 7 IMPLEMENTATION PROMPT - ITERATIVE LOOP

Use this prompt to implement Refactor 7 one step at a time in an iterative loop.

---

## PROMPT FOR CLAUDE CODE

```
You are implementing Refactor 7: Contextual Claim Analysis for the ROGR v2 fact-checking system.

Your task is to execute ONE implementation step, test it, verify completion, commit it, and prepare for the next step.

## STEP 1: READ CURRENT STATE

Read `rogrv2-backend/REFACTOR_7_IMPLEMENTATION_SPEC.md` focusing on:

1. **CURRENT STATUS section** (lines 50-76) - shows exactly what step you're on
2. **SESSION LOG section** - see what's been completed in previous sessions
3. **The specific week/step** you need to implement next
4. **Exit criteria** for that step
5. **Testing requirements** for that step

**The spec is self-contained** - everything you need is in this one document.

**Note:** This prompt maintains continuity by updating both CURRENT STATUS and SESSION LOG after each step. Each iteration reads these sections to know where to continue. No external session handoff script needed - the prompt IS the handoff mechanism.

## STEP 2: IDENTIFY CURRENT STEP

Based on CURRENT STATUS in the spec, identify:
- Current Week (Week 0, 1, 2, 3, or 4)
- Current Step within that week
- Specific tasks to complete
- Files to create or modify

**Decision logic:**
- If CURRENT STATUS says "Week 0" with "Implementation Started: No" → Start Week 0
- If CURRENT STATUS says "Week X Complete, Week Y Ready" → Start Week Y
- If CURRENT STATUS says "Week X" with specific step → Continue that step
- If SESSION LOG shows Week X completed → Start Week X+1

**Report your decision:** "Starting Week X based on CURRENT STATUS"

## STEP 3: IMPLEMENT THE STEP

**Find implementation details in the spec:**
- Search for "## WEEK-BY-WEEK IMPLEMENTATION PLAN" (around line 807)
- Find your current week's section
- Read the detailed tasks and instructions
- Search for "## FILE-BY-FILE SPECIFICATIONS" (around line 1038) for code examples

**Summary of weeks:**
- Week 0: Create NLP validation script and capture baseline using existing pipeline
- Week 1: Create 3 new files (contextual_variation.py, contextual_mapping.py, stance_contextual.py)
- Week 2: Modify p25_aggregate.py (add optional claim_text parameter to calculate_consistency_score)
- Week 3: Modify intelligence/run.py (integrate context detection with feature flag OFF)
- Week 4: Enable feature flag, test target claim, run full validation

### Critical Rules:
- ✅ Follow the spec's code examples exactly
- ✅ Add file headers as specified
- ✅ Include all error handling
- ✅ Use feature flag (ENABLE_CONTEXTUAL_ANALYSIS = False initially)
- ✅ Add inline comments explaining each section
- ❌ DO NOT skip ahead to later weeks
- ❌ DO NOT modify files not specified for current step
- ❌ DO NOT enable feature flag until Week 4

## STEP 4: TEST THE STEP

Run the tests specified for the current step:

**Week 0:**
```bash
# Test 1: NLP validation script
python scripts/validate_nlp_extraction.py
# Expected: "Detection Rate: 85%+" and "✅ NLP baseline validated"
# Success: Exit code 0, detection rate >= 85%

# Test 2: Capture baseline using existing tested pipeline
mkdir -p baselines
python scripts/dev_preview.py "Water boils at 100 degrees Celsius" > baselines/refactor7_week0.txt
# Expected: Output with verdict and confidence
# Success: File created with pipeline output

# Test 3: Verify baseline captured correctly
grep -q "Verdict:" baselines/refactor7_week0.txt && grep -q "Confidence:" baselines/refactor7_week0.txt && echo "✓ Baseline captured"
# Expected: "✓ Baseline captured"
# Success: Baseline file contains verdict and confidence
```

**Week 1:**
```bash
# Test 1: Import new modules
python -c "from intelligence.content.contextual_variation import detect_context_dependency_from_evidence; print('✓ contextual_variation OK')"
python -c "from intelligence.content.contextual_mapping import map_to_ifcn_label; print('✓ contextual_mapping OK')"
python -c "from intelligence.content.stance_contextual import assess_stance_with_context; print('✓ stance_contextual OK')"
# Expected: All print "✓ ... OK", no ImportError
# Success: All 3 imports work

# Test 2: Verify no pipeline changes
python -c "from intelligence.run import run_single_lane_enrichment; print('Pipeline unchanged')"
# Expected: Imports without using new modules (flag not integrated yet)
# Success: No errors
```

**Week 2:**
```bash
# Test 1: Backward compatibility (old calls still work)
python -c "from intelligence.content.p25_aggregate import calculate_consistency_score; print('Old call:', calculate_consistency_score([], []))"
# Expected: Returns 1.0 (default for no items), no errors
# Success: Works without claim_text parameter

# Test 2: New parameter accepted
python -c "from intelligence.content.p25_aggregate import calculate_consistency_score; print('New call:', calculate_consistency_score([], [], 'test claim'))"
# Expected: Returns consistency score, no errors
# Success: Works with claim_text parameter

# Test 3: Run regression tests
python scripts/regression_check.py --baseline baselines/refactor7_week0.json --tolerance-confidence 0.05
# Expected: All protected claims within ±5% confidence tolerance
# Success: "✅ All claims within tolerance"
```

**Week 3:**
```bash
# Test 1: Integration imports (feature flag OFF)
python -c "from intelligence.run import run_single_lane_enrichment; print('✓ Integration imports OK')"
# Expected: No import errors
# Success: Imports successfully

# Test 2: Feature flag exists and is OFF
python -c "from intelligence.run import ENABLE_CONTEXTUAL_ANALYSIS; print(f'Flag: {ENABLE_CONTEXTUAL_ANALYSIS}'); assert ENABLE_CONTEXTUAL_ANALYSIS == False"
# Expected: Prints "Flag: False"
# Success: Flag is False

# Test 3: Protected claims unchanged (flag OFF)
python scripts/dev_preview.py "COVID vaccines cause autism"
# Expected: Same verdict/confidence as baseline (within ±5%)
# Success: No regression detected
```

**Week 4:**
```bash
# FIRST: Enable feature flag
# Edit intelligence/run.py: Change ENABLE_CONTEXTUAL_ANALYSIS = False to True

# Test 1: Target claim improvement
python scripts/dev_preview.py "Water boils at 100 degrees Celsius"
# Expected: Confidence 80-85%, verdict "MOSTLY TRUE", contextual_status present
# Success: Shows context detection, improved confidence

# Test 2: Full regression suite
python scripts/regression_check.py --baseline baselines/refactor7_week0.json --tolerance-verdict 0.0 --tolerance-confidence 0.05
# Expected: All protected claims pass (COVID vaccines, etc.)
# Success: "✅ All X claims within tolerance"

# Test 3: Adversarial tests
pytest tests/test_refactor7_adversarial.py -v
# Expected: All 4 test cases pass
# Success: "4 passed" in output

# Test 4: Verify flag is ON
python -c "from intelligence.run import ENABLE_CONTEXTUAL_ANALYSIS; assert ENABLE_CONTEXTUAL_ANALYSIS == True; print('✓ Feature enabled')"
# Expected: Prints "✓ Feature enabled"
# Success: Flag is True
```

## STEP 5: VERIFY EXIT CRITERIA

Check the spec's exit criteria for current step:

**Week 0 Exit Criteria:**
- [ ] Script created: validate_nlp_extraction.py
- [ ] NLP baseline validation passes (85%+ detection rate)
- [ ] Baseline captured for target claim using existing pipeline (Water boils at 100°C)
- [ ] Baseline directory created (baselines/)
- [ ] Baseline file contains verdict and confidence data

**Week 1 Exit Criteria:**
- [ ] All 3 files created with complete implementations
- [ ] All imports work without errors
- [ ] File headers present with correct metadata
- [ ] No modifications to existing pipeline files

**Week 2 Exit Criteria:**
- [ ] calculate_consistency_score() accepts optional claim_text parameter
- [ ] Backward compatibility verified (old calls still work)
- [ ] New logic only executes when claim_text provided
- [ ] Regression tests pass (no verdict changes)

**Week 3 Exit Criteria:**
- [ ] Context detection integrated in run.py
- [ ] Feature flag present and set to False
- [ ] contextual_status field added to return dict
- [ ] Protected claims still return same verdicts

**Week 4 Exit Criteria:**
- [ ] Feature flag enabled (ENABLE_CONTEXTUAL_ANALYSIS = True)
- [ ] "Water boils at 100°C" shows 80-85% confidence, MOSTLY TRUE
- [ ] All protected claims within tolerance (±5% confidence)
- [ ] No regressions in existing functionality
- [ ] Adversarial tests pass

If exit criteria NOT met:
- Debug the issue
- Fix the problem
- Re-run tests
- DO NOT proceed to next step until exit criteria met

## STEP 6: COMMIT THE STEP

Use standardized commit format from spec:

```bash
git add <files changed in this step>
git commit -m "[Refactor 7 - Week X] <Brief description>

<Detailed description of what was implemented>

Files changed:
- <file1>: <what changed>
- <file2>: <what changed>

Testing:
- <test results summary>

Exit criteria: <all met / pending>

See: REFACTOR_7_IMPLEMENTATION_SPEC.md Week X

🤖 Generated with Claude Code (https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Examples:**

Week 0:
```
[Refactor 7 - Week 0] Create NLP validation and capture baseline

Created NLP validation script and captured baseline using existing pipeline.

Files changed:
- scripts/validate_nlp_extraction.py: Created NLP validation with 18 test cases
- baselines/refactor7_week0.txt: Baseline captured using dev_preview.py

Testing:
- NLP validation: 93% detection rate (exceeds 85% target)
- Baseline captured: "Water boils at 100°C" using existing tested pipeline
- Baseline contains verdict and confidence data

Exit criteria: All met ✅

See: REFACTOR_7_IMPLEMENTATION_SPEC.md Week 0
```

Week 1:
```
[Refactor 7 - Week 1] Implement contextual analysis modules

Created three new modules for context detection, IFCN mapping, and stance analysis.
All modules feature-flagged and zero-integration (no pipeline modifications).

Files changed:
- intelligence/content/contextual_variation.py: Context detection using NLP (318 lines)
- intelligence/content/contextual_mapping.py: IFCN label mapping logic (215 lines)
- intelligence/content/stance_contextual.py: Context-aware stance wrapper (128 lines)

Testing:
- All imports successful
- Unit tests pass (if created)
- No impact on existing pipeline (flag not integrated yet)

Exit criteria: All met ✅

See: REFACTOR_7_IMPLEMENTATION_SPEC.md Week 1
```

## STEP 7: UPDATE PROGRESS TRACKING

**CRITICAL:** Update TWO sections in `REFACTOR_7_IMPLEMENTATION_SPEC.md` so the next iteration knows where to continue.

### A) Update CURRENT STATUS section (search for "## CURRENT STATUS" around line 50):

```markdown
## CURRENT STATUS

**Current Week:** Week X (or "Week X Complete, Week Y Ready")
**Current Step:** <next specific task>
**Last Completed:** <what you just finished>
**Implementation Started:** Yes
**Feature Flag Status:** <False/True>

**Files Created:**
- <list all files created so far>

**Files Modified:**
- <list all files modified so far>

**Tests Status:**
- Week 0: <Complete/Not started>
- Week 1: <Complete/Not started>
- Week 2: <Complete/Not started>
- Week 3: <Complete/Not started>
- Week 4: <Complete/Not started>

**Next Action:**
<Clear description of the next step to implement>

⚠️ **UPDATE THIS SECTION AFTER EVERY SESSION** ⚠️
```

**Important:**
- Change "Current Week" to show completed week + next week (e.g., "Week 1 Complete, Week 2 Ready")
- Update "Next Action" with specific next step
- This tells the next iteration what to do!

### B) Add entry to SESSION LOG section (search for "## SESSION LOG" around line 2823):

```markdown
| X | 2025-11-XX | Xh | Week Y | <Brief description> | ✅ PASS | abc1234 |
```

And add detailed session notes below the table:

```markdown
### Session X - 2025-11-XX

**Week/Step:** Week Y
**Duration:** Xh
**Files Changed:** file1.py (+123 lines), file2.py (modified)

**What Was Done:**
- Implemented X
- Tested Y
- Verified Z

**Tests Run:**
- <test results>

**Exit Criteria:** All met ✅

**Next Session Should:**
- Implement Week Y+1
```

## STEP 8: REPORT COMPLETION

Provide a summary to the user:

```
## STEP COMPLETED: Week X - <Step Name>

### What Was Done:
- <bullet list of implementations>

### Files Changed:
- <files with line counts>

### Tests Run:
- <test results>

### Exit Criteria:
- ✅ <criterion 1>
- ✅ <criterion 2>
- ✅ <criterion 3>

### Committed:
- Commit: <commit hash>
- Message: "<commit title>"

### Next Step:
<Clear description of what to do next>

To continue, run this prompt again. Claude Code will read the updated CURRENT STATUS and proceed to the next step.
```

---

## EXAMPLE EXECUTION (Week 0)

**Input:** User runs this prompt

**Output:**

1. ✅ Read REFACTOR_7_IMPLEMENTATION_SPEC.md
   - CURRENT STATUS: Week 0 (not started)
   - SESSION LOG: Planning complete, implementation not started
2. ✅ Identified: Week 0 tasks (create NLP validation, capture baseline)
3. ✅ Implemented:
   - Created scripts/validate_nlp_extraction.py
   - Captured baseline using existing pipeline (scripts/dev_preview.py)
   - Created baselines/ directory
4. ✅ Tested:
   - NLP validation: 93% (✅ exceeds 85%)
   - Baseline captured: "Water boils at 100°C" using trusted pipeline
   - Baseline file verified with verdict and confidence
5. ✅ Exit criteria: All met
6. ✅ Committed: [Refactor 7 - Week 0] Create baseline infrastructure
7. ✅ Updated CURRENT STATUS: Week 0 Complete, Week 1 Ready
8. ✅ Report: "Week 0 complete. Next: Create contextual_variation.py"

**To continue:** User runs prompt again → Claude reads updated status → Executes Week 1

---

## EMERGENCY ROLLBACK

If something breaks:

1. Check last commit: `git log -1 --oneline`
2. Rollback: `git reset --hard HEAD~1`
3. Report issue to user
4. Wait for guidance before proceeding

---

## STOPPING CONDITIONS

Stop and report to user if:
- ❌ Exit criteria not met after 3 attempts
- ❌ Tests fail and cause is unclear
- ❌ Protected claims regress beyond tolerance
- ❌ Import errors that can't be resolved
- ❌ Token budget running low (<20K remaining)

DO NOT proceed to next step until current step is fully validated.

---

## SUCCESS MARKERS

You'll know you're done when:
- ✅ CURRENT STATUS shows "Week 4 Complete - All Exit Criteria Met"
- ✅ Feature flag enabled (ENABLE_CONTEXTUAL_ANALYSIS = True)
- ✅ "Water boils at 100°C" returns 80-85% confidence, MOSTLY TRUE
- ✅ All protected claims pass regression tests
- ✅ Adversarial tests pass

At that point, report:
"🎉 REFACTOR 7 COMPLETE - Ready for production deployment"

---

END OF PROMPT
```

## HOW TO USE

1. Copy the prompt section above (between the ``` marks)
2. Start a new Claude Code session
3. Paste the prompt
4. Claude will execute one step, commit, and tell you what's next
5. Run the prompt again to continue to the next step
6. Repeat until complete

Each iteration is self-contained and safe to pause/resume.
