# HANDOFF CHECKLIST - Critical Information for Next Session

**Date:** 2025-10-09
**Purpose:** Document what's known, unknown, and risky about the clean integration plan
**Status:** HONEST ASSESSMENT - Includes gaps in analysis

---

## 1. CRITICAL FILES TO PRESERVE

### 1.1 Clean Modules (DO NOT DELETE - Contains Logic)

**P20 Logic:**
- `intelligence/content/grade.py` (134 lines) ✅ TESTED STANDALONE
- `intelligence/content/extract_facts.py` (helper for grade.py)

**P21 Logic:**
- `intelligence/content/fullread.py` (200 lines) ⚠️ NOT TESTED

**P22 Logic:**
- `intelligence/content/fetch.py` (existing, used by P22)
- `intelligence/content/fetch_sync.py` (P17, used by API)

**P23 Logic:**
- `intelligence/content/semantic_read.py` (194 lines) ⚠️ NOT TESTED

**P24 Logic:**
- `intelligence/content/semantic_frames.py` (277 lines) ⚠️ NOT TESTED

**P25 Logic:**
- `intelligence/content/p25_aggregate.py` (102 lines) ⚠️ NOT TESTED
- **AMBIGUOUS:** `intelligence/content/p25_semantic_aggregate.py` (89 lines) - Is this a wrapper or second version?

**P18 and Earlier:**
- `intelligence/content/align.py` (P18 content alignment)
- All files in `intelligence/gather/` (P14-P15 core pipeline)
- All files in `intelligence/stance/` (verdict computation)
- All files in `intelligence/rank/` (ranking)
- All files in `intelligence/analyze/` (stance detection)
- All files in `intelligence/policy/` (guardrails)
- All files in `intelligence/consensus/` (overlap/conflict)
- All files in `intelligence/score/` (labeling)

### 1.2 Wrapper Files (DELETE AFTER CLEAN INTEGRATION)

**Production wrappers (loaded by sitecustomize.py):**
- `sitecustomize.py` (loads p20 + p22)
- `intelligence/gather/p19_wrapper.py` (227 lines) ⚠️ NOT ANALYZED
- `intelligence/content/p20_wrapper.py` (227 lines)
- `intelligence/content/p22_ingest.py` (266 lines)

**Test-only wrappers (not in sitecustomize.py):**
- `intelligence/content/p21_wrapper.py` (144 lines)
- `intelligence/content/p23_semantic.py` (93 lines)
- `intelligence/content/p24_semantic_frames.py` (105 lines)
- `intelligence/content/p25_semantic_aggregate.py` (89 lines) ❓ OR IS THIS CLEAN?
- `intelligence/content/p26_dual_researchers.py` (114 lines)
- `intelligence/content/p27_consensus.py` (163 lines)
- `intelligence/content/p28_diversify.py` (276 lines)
- `intelligence/content/p29_diversify_controls.py` (287 lines)

### 1.3 Files with Ambiguous Status

**CRITICAL: Investigate these before deletion**

1. **`intelligence/content/p25_aggregate.py` vs `p25_semantic_aggregate.py`**
   - p25_aggregate.py: Has `aggregate_verdict()` function, looks like clean logic
   - p25_semantic_aggregate.py: Has `setattr`, looks like wrapper
   - **Question:** Are these the same packet or different versions?
   - **Risk:** Might delete wrong file

2. **`intelligence/gather/p19_wrapper.py`**
   - Found it exists (227 lines)
   - Uses setattr (confirmed)
   - Wraps `online.run_plan` for counter-frames
   - **NOT FULLY ANALYZED** - didn't check if it has clean module
   - **Question:** Does P19 have a clean module somewhere?
   - **Risk:** P19 logic might be embedded in wrapper

3. **API files that import wrappers**
   - `api/analyses.py` imports from `intelligence.pipeline.run`
   - Run.py gets wrapped by P22-P29
   - **Question:** Does API need modifications after unwrapping?

---

## 2. KNOWN ISSUES NOT IN PLAN

### 2.1 P19 Wrapper Not Analyzed

**What I know:**
- File exists: `intelligence/gather/p19_wrapper.py`
- Wraps `online.run_plan` (line 24: `setattr(online, "_ROGR_P19_INSTALLED", True)`)
- Purpose: "Non-existence aware counter-frames + coverage for arm_B"
- Has logic for anchor extraction, counter-frame queries
- 227 lines of code

**What I DON'T know:**
- Is there a clean P19 module somewhere?
- Is the logic embedded in the wrapper or extracted?
- Is P19 loaded in production? (sitecustomize.py only mentions p20+p22)
- Does removing P19 break anything?

**Risk:** MEDIUM
- P19 might contain required intelligence for arm_B
- Might need extraction like P26-P29
- Plan doesn't account for P19 at all

**Recommendation:** Next session should analyze P19 first

### 2.2 P25 File Confusion

**The mystery:**
```
intelligence/content/p25_aggregate.py        (102 lines, no setattr)
intelligence/content/p25_semantic_aggregate.py  (89 lines, has setattr)
```

**What I observed:**
- p25_aggregate.py looks like clean module with `aggregate_verdict()` function
- p25_semantic_aggregate.py is clearly a wrapper (uses setattr, imports p25_aggregate)
- Wrapper imports clean module: `from .p25_aggregate import aggregate_verdict`

**What I DON'T know:**
- Why are there two P25 files?
- Is this the pattern for all P20+?
- Did I miss clean modules for P26-P29?

**Risk:** LOW
- Relationship is clear (wrapper imports clean)
- But confusing naming might cause deletion mistakes

### 2.3 Memory Leak Impact Unknown

**What I know:**
- `_FETCH_CACHE` in p22_ingest.py:29 is unbounded Dict
- Never cleared, grows indefinitely
- Production blocker

**What I DON'T know:**
- How many URLs get fetched per request? (10? 100? 1000?)
- Average content size? (10KB? 100KB? 1MB?)
- How quickly does it grow? (1GB/day? 1GB/week?)
- Has this caused production issues already?

**Risk:** HIGH
- Might be causing production problems NOW
- Might be low priority if growth is slow
- Can't estimate urgency without data

**Recommendation:** Check production logs for memory usage trends

### 2.4 Execution Order Reversal Untested

**Claim in plan:**
- "Current order (P20 before P22) is suboptimal"
- "Optimal: P22 before P20 (gives P20 full content)"

**What I DON'T know:**
- Does P20 logic expect snippet-only input?
- Are there weights/thresholds tuned for snippet quality?
- Will P20 produce BETTER results with full content or just DIFFERENT?
- Could reversing order degrade quality?

**Risk:** MEDIUM
- Assumption not tested
- Quality impact unknown
- Might need A/B testing

### 2.5 Test Coverage Gaps

**What I observed:**
- Only 1 test file: `tests/test_s2p30r_audit.py`
- Test expects clean path (no wrappers)
- Many test files in `scripts/test_packet*.py` (per-packet tests)

**What I DON'T know:**
- Do packet tests actually run?
- Do they pass with current wrappers?
- What breaks if wrappers removed?
- Is there a test suite that validates end-to-end?

**Risk:** HIGH
- Can't validate clean integration without tests
- Unknown what breaks

**Recommendation:** Run all packet tests BEFORE starting clean integration

---

## 3. UNTESTED ASSUMPTIONS

### 3.1 Clean Modules Work Together

**Tested:**
- ✅ `grade.attach_finding_to_item()` works standalone
- ✅ Imported successfully, executed, produced output

**NOT tested:**
- ❌ `fullread.evaluate_full_evidence()` standalone
- ❌ `semantic_read.analyze_item()` standalone
- ❌ `semantic_frames.analyze_frames()` standalone
- ❌ `p25_aggregate.aggregate_verdict()` standalone
- ❌ Any combination of modules together
- ❌ Execution with real claim + real evidence

**Assumption:** "All clean modules are standalone and work"
**Reality:** Only tested ONE module
**Risk:** HIGH - other modules might have hidden dependencies

### 3.2 Wrappers Actually Work in Production

**Observed:**
- Ran live test with PYTHONPATH=., wrappers loaded
- Output included `finding`, `content`, `content_hash` fields
- Confirmed P20 and P22 added fields

**NOT tested:**
- ❌ Whether P23-P29 produce valid output
- ❌ Whether consensus logic works correctly
- ❌ Whether diversification actually differs R1 vs R2
- ❌ Whether telemetry collection works

**Assumption:** "P26-P29 work as described in comments"
**Reality:** Never ran P26-P29, only read code
**Risk:** HIGH - might extract broken logic

### 3.3 Wrapper Removal is Safe

**Assumption:** "Can remove wrappers after extracting logic"

**NOT tested:**
- ❌ Whether anything else imports wrappers
- ❌ Whether tests depend on wrapper side effects
- ❌ Whether wrapper import order matters beyond sitecustomize
- ❌ Whether API has timing dependencies on wrappers

**Risk:** MEDIUM - unknown breakage

### 3.4 Sequential Execution is Safe

**Assumption:** "R1 and R2 should run sequentially (rate limits)"

**NOT tested:**
- ❌ Actual provider rate limits
- ❌ Whether providers throttle or reject on parallel calls
- ❌ Cost impact of dual execution
- ❌ Whether sequential is actually necessary

**Risk:** LOW - conservative approach, but might be over-cautious

### 3.5 Diversification Works

**Assumption:** "Query shuffle + provider order = independent results"

**NOT tested:**
- ❌ Whether different query order actually changes results
- ❌ Whether provider order matters (do they return different results?)
- ❌ Whether R1 and R2 meaningfully differ
- ❌ Whether diversification is sufficient

**Risk:** MEDIUM - might not achieve independence

### 3.6 Consensus Logic is Correct

**Assumption:** "Agreement bonus, disagreement penalty logic is sound"

**NOT tested:**
- ❌ Whether consensus thresholds (delta=0.20) are calibrated
- ❌ Whether bonus/penalty values make sense
- ❌ Whether logic handles edge cases correctly
- ❌ Whether rationale is useful

**Risk:** MEDIUM - might produce unreliable verdicts

---

## 4. DEPENDENCIES YOU'RE UNSURE ABOUT

### 4.1 P19 Dependencies Unknown

**Question:** What does P19 depend on? What depends on P19?

**Unknown:**
- Does P19 have dependencies on earlier packets?
- Does P20-P29 depend on P19?
- Is P19 required for arm_B to work correctly?

**Risk:** Can't plan P19 extraction without this

### 4.2 Circular Import Risk

**Not checked:**
- Whether any clean modules import each other
- Whether wrappers create circular dependencies
- Whether extraction will cause import errors

**Example concern:**
- If `semantic_read.py` imports `semantic_frames.py`
- And `semantic_frames.py` imports `semantic_read.py`
- Circular import error

**Risk:** MEDIUM - could block integration

**Recommendation:** Run `python -c "import intelligence.content.grade"` for each clean module

### 4.3 Hidden Dependencies in Wrappers

**Concern:** Wrappers might depend on each other implicitly

**Example from P26:**
```python
# p26_dual_researchers.py:74-83
for m in (
    "intelligence.content.p22_ingest",
    "intelligence.content.p23_semantic",
    "intelligence.content.p24_semantic_frames",
    "intelligence.content.p25_semantic_aggregate",
):
    try:
        import_module(m)
    except Exception:
        pass
```

**What this means:**
- P26 explicitly imports P22-P25 wrappers
- Ensures they load before P26
- Implies P26 depends on their side effects

**Unknown:**
- Are there other hidden dependencies?
- Do wrappers communicate via global state?
- Do they depend on import order?

**Risk:** HIGH - might break when extracting

### 4.4 ContextVar Propagation

**P28 uses ContextVar for lane tracking:**
```python
LANE_ID: ContextVar[str] = ContextVar("LANE_ID", default="R1")
```

**Unknown:**
- How does ContextVar work in async contexts?
- Does it propagate correctly through await calls?
- Will clean integration preserve this behavior?

**Risk:** MEDIUM - lane tracking might break

### 4.5 External Dependencies

**Haven't checked:**
- Which external packages are required? (beyond stdlib)
- Are all dependencies in requirements.txt?
- Are there optional dependencies?

**Could be missing:**
- Anthropic API client (for AI Assist)
- Provider libraries (Google CSE, Brave, Bing)
- HTML parsing libraries (for content extraction)

**Risk:** MEDIUM - might not have all dependencies

---

## 5. QUESTIONS FOR NEXT SESSION

### 5.1 Immediate Verification (BEFORE STARTING WORK)

**Test all clean modules standalone:**
```bash
# Do these all work without wrappers?
python3 -c "from intelligence.content.grade import attach_finding_to_item; print('OK')"
python3 -c "from intelligence.content.fullread import evaluate_full_evidence; print('OK')"
python3 -c "from intelligence.content.semantic_read import analyze_item; print('OK')"
python3 -c "from intelligence.content.semantic_frames import analyze_frames; print('OK')"
python3 -c "from intelligence.content.p25_aggregate import aggregate_verdict; print('OK')"
```

**Test wrappers actually work:**
```bash
# Enable all wrappers, test dual researchers
# Does P26-P29 produce valid output?
# Does consensus differ from single-researcher?
```

**Analyze P19:**
```bash
# What does P19 do?
# Is there a clean P19 module?
# Is it required?
```

### 5.2 Critical Clarifications

**Q1: What is the ACTUAL completion percentage?**
- Previous assessments: 70%, 85%, 60-65%
- Which is correct?
- How much is really done?

**Q2: Is AI Assist truly blocking Day 1?**
- Can ship without AI Assist?
- What's the quality delta?
- Is it must-have or nice-to-have?

**Q3: What's the production deployment process?**
- How is code deployed?
- Can we do gradual rollout?
- What's the rollback procedure?

**Q4: Are there production issues NOW?**
- Memory leaks causing problems?
- Wrapper bugs in production?
- Performance issues?

**Q5: What's the test strategy?**
- How to validate clean integration works?
- What's the acceptance criteria?
- Who tests? When?

### 5.3 Risk Assessment Questions

**Q1: What's the riskiest part of this plan?**

**My assessment:**
1. **P26-P29 extraction** (HIGHEST RISK)
   - Logic embedded in wrappers
   - Complex orchestration
   - Untested assumptions about how they work
   - 40+ hours of work

2. **P22 cache replacement** (HIGH RISK)
   - Memory leak must be fixed
   - Request-scoped cache changes data flow
   - Might affect other components

3. **Telemetry integration** (MEDIUM RISK)
   - Need to modify `online.run_plan`
   - Pass telemetry through multiple layers
   - Easy to miss a spot

4. **P19 unknown status** (MEDIUM RISK)
   - Not analyzed
   - Might contain required logic
   - Might need extraction too

**Q2: What could completely derail this plan?**

**Potential derailers:**
1. **P26-P29 don't actually work as described**
   - Comments lie, actual behavior differs
   - Extraction would fail

2. **Clean modules have hidden dependencies**
   - Can't run standalone despite appearance
   - Need significant refactoring

3. **Tests don't validate the right things**
   - Pass but system is broken
   - Can't detect regressions

4. **Performance unacceptable**
   - Dual researchers too slow
   - Provider costs too high
   - Users reject latency

5. **P19 is critical and complex**
   - Requires extraction like P26-P29
   - Adds 2-3 days to timeline

**Q3: What's the fallback if clean integration fails?**

**Options:**
1. **Keep wrappers, fix memory leak in-place**
   - Add LRU cache to P22
   - Ship with wrappers
   - Clean integration becomes "later"

2. **Ship with partial clean integration**
   - Extract P20-P25 (easier)
   - Keep P26-P29 as wrappers
   - Incremental progress

3. **Focus on AI Assist instead**
   - Wrappers aren't blocking AI Assist
   - Build AI features on top of current system
   - Clean up later

### 5.4 Validation Strategy

**What tests should run before declaring success?**

1. **Baseline capture:**
   - Run with wrappers, capture full output
   - Save to baseline.json

2. **Clean path test:**
   - Run with clean integration, capture output
   - Save to clean.json

3. **Diff comparison:**
   - Compare baseline vs clean
   - Should be identical (except diagnostic logs)

4. **Specific checks:**
   - All claims have `researchers[]`?
   - Consensus differs from single verdict?
   - R1 and R2 have different evidence?
   - Telemetry present?
   - Manifest has replay_id?

5. **Performance check:**
   - Clean path faster or slower?
   - Memory usage better?
   - Provider call count same?

### 5.5 Timeline Reality Check

**Q: Is 8-10 days realistic?**

**Optimistic case (8 days):**
- All clean modules work standalone ✅
- P26-P29 extraction goes smoothly ✅
- No surprises ✅
- Tests validate correctly ✅

**Realistic case (10-12 days):**
- Some clean modules need fixes ⚠️
- P26-P29 extraction hits issues ⚠️
- Test gaps require new tests ⚠️
- Need iteration on consensus logic ⚠️

**Pessimistic case (15-20 days):**
- P19 needs extraction (not planned) ❌
- Clean modules have hidden dependencies ❌
- P26-P29 don't work as documented ❌
- Significant refactoring needed ❌

**Recommendation:** Plan for 12 days, hope for 8

---

## 6. HONEST ASSESSMENT OF ANALYSIS QUALITY

### 6.1 What I'm Confident About

✅ **P20-P25 architecture:**
- Clean modules exist and are standalone
- Wrappers call clean functions
- Extraction path is clear

✅ **P20 grade.py works:**
- Tested standalone
- Produces valid output
- No wrapper dependencies

✅ **Wrapper mechanism understood:**
- setattr monkey patching
- Import-time execution
- Function interception

✅ **P22 memory leak exists:**
- Confirmed in code
- Unbounded Dict
- Production issue

✅ **P26-P29 structure:**
- Logic embedded in wrapper files
- No separate clean modules (yet)
- Need extraction

### 6.2 What I'm Uncertain About

⚠️ **Other clean modules (P21, P23-P25):**
- Haven't tested them
- Assume they work based on structure
- Could have issues

⚠️ **P26-P29 functionality:**
- Never ran them
- Assume they work based on comments
- Could be broken or incomplete

⚠️ **Execution order impact:**
- Theory makes sense (P22 before P20)
- Haven't tested quality difference
- Could be wrong

⚠️ **Test coverage:**
- Don't know what tests exist
- Don't know what they validate
- Can't assess regression risk

⚠️ **Telemetry integration:**
- Plan makes sense
- Haven't tested implementation
- Could have edge cases

### 6.3 What I Don't Know

❌ **P19 status:**
- Not analyzed
- Unknown if required
- Unknown complexity

❌ **Production state:**
- Memory leak impact?
- Current issues?
- Performance characteristics?

❌ **Dependencies:**
- Complete list?
- Circular imports?
- External packages needed?

❌ **Deployment process:**
- How is code deployed?
- Testing process?
- Rollback capability?

❌ **User requirements:**
- What's truly must-have?
- What's nice-to-have?
- What's the priority?

---

## 7. RECOMMENDED NEXT STEPS

### Phase 0: Validation (4-6 hours) - DO THIS FIRST

1. **Test all clean modules standalone** (1 hour)
   ```bash
   cd /Users/txtk/Documents/ROGR/github/rogrv2-backend
   python3 -c "from intelligence.content.fullread import evaluate_full_evidence"
   python3 -c "from intelligence.content.semantic_read import analyze_item"
   python3 -c "from intelligence.content.semantic_frames import analyze_frames"
   python3 -c "from intelligence.content.p25_aggregate import aggregate_verdict"
   ```

2. **Test P26-P29 wrappers work** (1-2 hours)
   - Modify sitecustomize.py to load ALL wrappers
   - Run preview with dual researchers enabled
   - Verify R1, R2, consensus present
   - Capture output for comparison

3. **Analyze P19** (1-2 hours)
   - Read p19_wrapper.py completely
   - Check if clean module exists
   - Determine if extraction needed
   - Update plan if necessary

4. **Run existing tests** (1 hour)
   ```bash
   # Find all test files
   find scripts/ -name "test_*.py" | xargs ls -lh

   # Try running them
   python3 scripts/test_packet20.py
   python3 scripts/test_packet26.py
   # etc.
   ```

5. **Check for circular imports** (30 min)
   ```bash
   # Import all modules, check for errors
   python3 << EOF
   import sys
   modules = [
       "intelligence.content.grade",
       "intelligence.content.fullread",
       "intelligence.content.semantic_read",
       "intelligence.content.semantic_frames",
       "intelligence.content.p25_aggregate",
   ]
   for m in modules:
       try:
           __import__(m)
           print(f"✓ {m}")
       except Exception as e:
           print(f"✗ {m}: {e}")
   EOF
   ```

### Phase 1: Based on Validation Results

**If validation passes:** Proceed with plan as documented

**If validation fails:** Revise plan based on findings

---

## 8. CRITICAL WARNINGS

### 🚨 DO NOT START WITHOUT VALIDATION

- Plan assumes clean modules work - NOT VERIFIED
- Plan assumes P26-P29 work - NOT VERIFIED
- Plan ignores P19 - MIGHT BE CRITICAL

### 🚨 P25 FILE CONFUSION

- Two files: p25_aggregate.py and p25_semantic_aggregate.py
- Unclear which to keep, which to delete
- VERIFY BEFORE DELETING

### 🚨 TEST COVERAGE UNKNOWN

- Only verified one test file exists
- Don't know what tests validate
- Can't detect regressions without tests

### 🚨 MEMORY LEAK IN PRODUCTION

- If system is running now, memory leak is active
- Growing unbounded
- MIGHT BE CAUSING ISSUES NOW

### 🚨 TIMELINE OPTIMISTIC

- 8-10 days assumes no surprises
- P19 could add 2-3 days
- Debugging could add 3-5 days
- Realistic: 12-15 days

---

## 9. FINAL RECOMMENDATION

**Before starting clean integration:**

1. ✅ **Validate Phase 0** (4-6 hours)
2. ✅ **Review findings** with team
3. ✅ **Revise plan** based on validation
4. ✅ **Get approval** for revised timeline
5. ✅ **Then proceed** with implementation

**If you skip validation and just start coding:**
- Risk discovering blockers mid-implementation
- Risk wasting days on wrong approach
- Risk breaking production
- Risk missing critical dependencies

**This handoff document is an HONEST assessment.**
- I've documented what I know
- I've documented what I DON'T know
- I've documented the risks
- I've documented the unknowns

**Use this to make an informed decision about proceeding.**

---

## 10. DOCUMENT VERSION CONTROL

**This document reflects:**
- Analysis completed: 2025-10-09
- Files analyzed: P20-P29 wrappers and clean modules
- Tests run: grade.py standalone import
- Assumptions: Documented in Section 3
- Unknowns: Documented in Section 6

**If circumstances change:**
- Update this document
- Note what changed
- Revise risk assessment
- Adjust timeline

**Good luck with the integration! 🚀**
