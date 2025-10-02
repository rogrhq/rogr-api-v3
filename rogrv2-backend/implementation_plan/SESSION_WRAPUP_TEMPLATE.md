# SESSION WRAPUP - ROGRv2 Backend Completion

**Purpose:** Execute quality gates and prepare for next session

**Instructions for User:** Copy-paste this document when approaching end of session or when work is complete.

---

## Your Task

Execute the session wrapup protocol. This ensures all work is properly tested, committed, and documented before session ends.

**Execute these steps in order:**

---

## Step 1: Run Tests

### A. Run Regression Tests (if Phase 0 complete)
```bash
# Run the regression test suite
pytest intelligence/test/s6_harness.py -v
```

**Report:**
- Total tests: [count]
- Passed: [count]
- Failed: [count]
- Status: ✅ ALL PASS / ❌ FAILURES DETECTED

**If failures:** Investigate immediately. Do not proceed until resolved or documented as known issue.

---

### B. Run New Tests (for current step)
```bash
# Run tests for current step implementation
[command based on current step]
```

**Report:**
- Total tests: [count]
- Passed: [count]
- Failed: [count]
- Status: ✅ ALL PASS / ❌ FAILURES DETECTED

---

## Step 2: Git Commit

### A. Check Status
```bash
git status
```

**Report:**
- Modified files: [count]
- New files: [count]
- Ready to commit: [YES/NO]

---

### B. Create Commit (if changes exist)

**Commit message format:**
```
[Session XX] StepYY: [Brief description]

- [Change 1]
- [Change 2]
- [Change 3]

Tests: [status]
Next: [what's next]
```

**Ask permission:**
"May I commit these changes with the above message?"

**After user approval:**
```bash
git add [files]
git commit -m "[message]"
```

**Report commit SHA.**

---

## Step 3: Update Documentation

### A. Update PROGRESS_THREAD.md (APPEND ONLY)

Add new entry using this template:

```markdown
---

## Session XX - [DATE] - [STEP NAME]
**Status**: ✅ COMPLETE | 🔄 IN PROGRESS | ⛔ BLOCKED
**Branch**: rogrv2-backend-wrapup
**Commits**: [SHA list]
**Tokens Used**: XXK / 150K target
**Duration**: [hours or "in progress"]

### Completed
- [bullet list of what was done]

### Files Changed
- NEW: [list]
- MODIFIED: [list]

### Tests
- ✅/❌ Regression (Phase 0): [status]
- ✅/❌ New tests: [status]

### Issues Encountered
- [None or list]

### Next
- [Clear statement of what's next: continuation or next step]

### Notes
- [Any important observations, decisions, or context for future sessions]
```

**Ask permission:**
"May I append this entry to PROGRESS_THREAD.md?"

---

### B. Update IMPLEMENTATION_STATE.md (OVERWRITE)

Replace entire contents with current state snapshot:

```markdown
# IMPLEMENTATION STATE SNAPSHOT
**Last Updated:** [DATE] - Session XX
**Branch:** rogrv2-backend-wrapup
**Last Commit:** [SHA]

---

## Current Status

**Phase:** [Phase X]
**Step:** [Step XX - Name]
**Status:** [COMPLETE / IN PROGRESS / BLOCKED]

---

## Completed Work

### Phase 0: Regression Test Suite
**Status:** ✅ COMPLETE | 🔄 IN PROGRESS | ⏸️ NOT STARTED
**Commit:** [SHA or N/A]
**Tests:** [X/X passing or N/A]

### Phase 1A: Integration Fixes
**Status:** ✅ COMPLETE | 🔄 IN PROGRESS | ⏸️ NOT STARTED
**Commit:** [SHA or N/A]
**Tests:** [status]

### Phase 1B: AI Assist Layer
**Status:** ✅ COMPLETE | 🔄 IN PROGRESS | ⏸️ NOT STARTED
- 1B.1 Query Refinement: [status]
- 1B.2 Passage Triage: [status]
- 1B.3 Contradiction Surfacing: [status]
- 1B.4 Explanation Draft: [status]
- 1B.5 Integration: [status]

### Phase 1C: Multi-Claim Wiring
**Status:** ✅ COMPLETE | 🔄 IN PROGRESS | ⏸️ NOT STARTED
**Commit:** [SHA or N/A]
**Tests:** [status]

### Phase 1D: S3 + S6 Modules
**Status:** ✅ COMPLETE | 🔄 IN PROGRESS | ⏸️ NOT STARTED
**Commit:** [SHA or N/A]
**Tests:** [status]

---

## Current Work Detail

### What's Complete (This Session)
- [list]

### What's Remaining (Current Step)
- [list or "Step complete"]

### Blockers
- [None or list]

---

## Test Status

**Regression Tests (Phase 0):**
- Status: [✅ BUILT & PASSING / 🔄 IN PROGRESS / ⏸️ NOT YET BUILT]
- Last run: [date/time]
- Pass rate: [X/X or N/A]

**Integration Tests:**
- [status per phase]

---

## Next Session

**Next step:** [Step XX - Name]
**Continuation:** [YES (unfinished work) / NO (new step)]
**Estimated tokens:** [XXK]
**Prerequisites:** [any blockers or dependencies]

**Prompt to use:**
- [Path to step prompt or NEXT_SESSION_PROMPT.md]

---

**END OF STATE SNAPSHOT**
```

**Ask permission:**
"May I overwrite IMPLEMENTATION_STATE.md with this current state?"

---

## Step 4: Generate Next Session Prompt (If Needed)

**Only if current step is INCOMPLETE:**

Create/update `NEXT_SESSION_PROMPT.md` with continuation instructions:

```markdown
# NEXT SESSION PROMPT - Continue Session XX

**⚠️ CRITICAL: Read these documents BEFORE proceeding**

## Required Reading (In Order)
1. `implementation_plan/TENANTS.md` - Behavior guidelines
2. `implementation_plan/PROGRESS_THREAD.md` - History (last 2 entries)
3. `implementation_plan/IMPLEMENTATION_STATE.md` - Current state
4. `implementation_plan/DESIGN_SPECIFICATIONS.md` - Section: [specific section]
5. [Any other relevant files]

---

## Context From Previous Session

**What was completed:**
- [list]

**What remains:**
- [list with specifics]

**Current state:**
- Branch: rogrv2-backend-wrapup
- Last commit: [SHA + message]
- Tests: [status]
- Files modified: [list]

---

## Your Task (Continuation)

[Specific instructions for what to do next]

[Reference to design spec section]

[Any context needed to continue]

---

## Success Criteria

Complete these to finish current step:

- [ ] [remaining criterion 1]
- [ ] [remaining criterion 2]
- [ ] Tests pass (regression + new)
- [ ] Code committed
- [ ] Documentation updated

---

## Integration Points

**Files you'll work with:**
- [list]

**Functions you'll modify/create:**
- [list]

**How this connects:**
- [brief integration explanation]

---

## Quality Gates

Before ending next session:
1. Run regression tests (must pass)
2. Run new tests (must pass)
3. Commit code
4. Update PROGRESS_THREAD.md
5. Update IMPLEMENTATION_STATE.md

---

**Estimated tokens for completion:** ~[XX]K
```

**Ask permission:**
"May I create/update NEXT_SESSION_PROMPT.md with these continuation instructions?"

---

## Step 5: Final Report

Provide completion summary:

```markdown
## 🏁 SESSION WRAPUP COMPLETE

### Quality Gates Status
- ✅/❌ Regression tests passed
- ✅/❌ New tests passed
- ✅/❌ Code committed (SHA: [sha])
- ✅/❌ PROGRESS_THREAD.md updated
- ✅/❌ IMPLEMENTATION_STATE.md updated
- ✅/❌ NEXT_SESSION_PROMPT.md created (if needed)

### Session Summary
**Tokens used:** XXK / 150K target
**Step status:** ✅ COMPLETE | 🔄 IN PROGRESS | ⛔ BLOCKED
**Next action:** [Continue current step | Start new step | Blocked on X]

### For Next Session
**Prompt to use:** [file path]
**Prerequisites:** [any setup needed]
**Estimated tokens:** ~XXK

---

**Session ready for handoff.** ✅
```

---

## Emergency: If Quality Gates Fail

**If tests fail or other quality gates can't be met:**

1. **Document the issue** in PROGRESS_THREAD.md
2. **Mark step as BLOCKED** in IMPLEMENTATION_STATE.md
3. **Create detailed NEXT_SESSION_PROMPT.md** explaining:
   - What failed
   - Why it failed
   - What needs to be investigated
   - Suggested approach to resolve
4. **Report blocker** to user with recommendation

**Do NOT hide failures. Transparent reporting is critical.**

---

**END OF SESSION WRAPUP PROTOCOL**
