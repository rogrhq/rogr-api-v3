# IMPLEMENTATION PLAN - ROGRv2 Backend Completion

**Purpose:** Complete framework for multi-session implementation with context preservation

**Created:** 2025-09-30 - Session 00 (Planning)

**Status:** Framework complete, ready for Session Zero

---

## What This Directory Contains

### 📋 Core Documents

#### TENANTS.md
**Purpose:** Behavior guidelines for Claude Code sessions (RDT v3.0)

**Key Features:**
- 7 streamlined tenants (reduced from RDT v2.0's 10)
- Structural enforcement (investigation block required)
- Mandatory ✅/❌ RDT self-certification
- Zero bias and IFCN compliance emphasis

**When to read:** Start of EVERY session

---

#### SESSION_START_TEMPLATE.md
**Purpose:** Universal session initialization prompt

**When to use:** Beginning of EVERY new Claude Code session

**What it does:**
- Initializes Claude with project context
- Has Claude read key documents
- Has Claude report understanding
- Creates checkpoint before actual work begins

**Instructions:** Copy-paste entire file into Claude at session start

---

#### SESSION_WRAPUP_TEMPLATE.md
**Purpose:** Quality gates and session end protocol

**When to use:** End of EVERY session (or when approaching token limit)

**What it does:**
- Runs regression tests
- Commits code changes
- Updates PROGRESS_THREAD.md (append)
- Updates IMPLEMENTATION_STATE.md (overwrite)
- Generates NEXT_SESSION_PROMPT.md if needed

**Instructions:** Copy-paste entire file when ready to end session

---

#### SESSION_ZERO_A_PROMPT.md
**Purpose:** Design Phase 0 + 1A specifications (first design session)

**When to use:** NEXT SESSION (immediate next step)

**What it produces:**
- DESIGN_SPECIFICATIONS_PHASE_0_1A.md (~30KB) - Complete Phase 0 and 1A specs
- step_prompts/step01_phase0.md and step02_phase1a.md - Ready-to-use prompts
- MASTER_PLAN_PARTIAL.md - Steps 01-02 breakdown

**Token estimate:** 80-100K

**Instructions:** Copy-paste into fresh Claude Code session to execute Session Zero-A

---

#### SESSION_ZERO_B_PROMPT.md
**Purpose:** Design Phase 1B specifications (second design session - AI assist layer)

**When to use:** After Session Zero-A completes

**What it produces:**
- DESIGN_SPECIFICATIONS_PHASE_1B.md (~55KB) - Complete Phase 1B specs (4 AI components)
- step_prompts/step03-step07.md (5 prompts) - Ready-to-use prompts
- MASTER_PLAN_UPDATE.md - Steps 03-07 breakdown

**Token estimate:** 100-120K

**Instructions:** Copy-paste into fresh Claude Code session after Zero-A

---

#### SESSION_ZERO_C_PROMPT.md
**Purpose:** Design Phase 1C + 1D specifications (final design session)

**When to use:** After Session Zero-B completes

**What it produces:**
- DESIGN_SPECIFICATIONS_PHASE_1C_1D.md (~40KB) - Complete Phase 1C and 1D specs
- step_prompts/step08-step12.md (5 prompts) - Ready-to-use prompts
- MASTER_PLAN_COMPLETE.md - Final merged master plan (all 12 steps)

**Token estimate:** 80-100K

**Instructions:** Copy-paste into fresh Claude Code session after Zero-B

---

### 📊 Tracking Documents

#### PROGRESS_THREAD.md
**Purpose:** Complete chronological history of all sessions

**Format:** APPEND-ONLY (never overwrite)

**Structure:** One entry per session with:
- Status (✅ COMPLETE / 🔄 IN PROGRESS / ⛔ BLOCKED)
- What was done
- Files changed
- Test results
- Issues encountered
- Next steps

**Updated:** End of every session (via SESSION_WRAPUP_TEMPLATE)

---

#### IMPLEMENTATION_STATE.md
**Purpose:** Current state snapshot (overwritten each session)

**Format:** OVERWRITE with current state

**Structure:**
- Current phase/step
- Completion status of all phases
- Test status
- Blockers
- Next session information

**Updated:** End of every session (via SESSION_WRAPUP_TEMPLATE)

---

#### NEXT_SESSION_PROMPT.md
**Purpose:** Continuation instructions for incomplete work

**Format:** Auto-generated when session ends with incomplete work

**Structure:**
- Context from previous session
- What remains to be done
- Specific continuation instructions
- References to design spec sections

**Updated:** Dynamically generated during SESSION_WRAPUP if step incomplete

---

### 📁 Subdirectories

#### step_prompts/
**Purpose:** Individual task prompts for each implementation step

**Contents (after Session Zero):**
- step00_session_zero.md (completed)
- step01_phase0_s6.md (build regression tests)
- step02_phase1a_integration.md (fix integration)
- step03_phase1b1_query_refine.md (AI query refinement)
- step04_phase1b2_triage.md (AI passage triage)
- ... (15-20 total steps)

**Format:** Copy-paste ready prompts with:
- Plain English explanation
- Technical specifications reference
- Success criteria
- Integration points
- Testing requirements

**Created by:** Session Zero

---

## How to Use This Framework

### Design Phase: Session Zero (3 Sessions)

**Session Zero is split into 3 design sessions to stay within token budgets:**

#### Session Zero-A: Phase 0 + 1A Design

1. **Start fresh Claude Code session**
2. **Copy-paste** `SESSION_ZERO_A_PROMPT.md` in its entirety
3. **Let Claude investigate** code and report findings
4. **Confirm investigation** before Claude proceeds
5. **Claude designs** Phase 0 and 1A specifications (~80-100K tokens)
6. **Claude produces:**
   - DESIGN_SPECIFICATIONS_PHASE_0_1A.md (complete)
   - step01_phase0.md and step02_phase1a.md (prompts)
   - MASTER_PLAN_PARTIAL.md

---

#### Session Zero-B: Phase 1B Design (AI Assist Layer)

1. **Start fresh Claude Code session** (after Zero-A completes)
2. **Copy-paste** `SESSION_ZERO_B_PROMPT.md` in its entirety
3. **Let Claude investigate** AI infrastructure and report
4. **Confirm investigation** before Claude proceeds
5. **Claude designs** all 4 AI components + integration (~100-120K tokens)
6. **Claude produces:**
   - DESIGN_SPECIFICATIONS_PHASE_1B.md (complete)
   - step03-step07 prompts (5 prompts)
   - MASTER_PLAN_UPDATE.md

---

#### Session Zero-C: Phase 1C + 1D Design

1. **Start fresh Claude Code session** (after Zero-B completes)
2. **Copy-paste** `SESSION_ZERO_C_PROMPT.md` in its entirety
3. **Let Claude investigate** multi-claim and S3 code and report
4. **Confirm investigation** before Claude proceeds
5. **Claude designs** Phase 1C and 1D specifications (~80-100K tokens)
6. **Claude produces:**
   - DESIGN_SPECIFICATIONS_PHASE_1C_1D.md (complete)
   - step08-step12 prompts (5 prompts)
   - MASTER_PLAN_COMPLETE.md (final merged plan)

**After all 3 design sessions: Complete implementation blueprint ready**

---

### Implementation Sessions (After All 3 Design Sessions)

#### Every Session Follows This Pattern:

**1. SESSION START**
- Copy-paste `SESSION_START_TEMPLATE.md`
- Claude reads context and reports understanding
- You confirm understanding ✓

**2. TASK ASSIGNMENT**
- Copy-paste step-specific prompt (e.g., `step_prompts/step01_phase0_s6.md`)
- OR copy-paste `NEXT_SESSION_PROMPT.md` if continuing work
- Claude implements per design specifications

**3. SESSION WRAPUP**
- Copy-paste `SESSION_WRAPUP_TEMPLATE.md`
- Claude executes quality gates:
  - Runs tests
  - Commits code
  - Updates PROGRESS_THREAD.md
  - Updates IMPLEMENTATION_STATE.md
  - Generates NEXT_SESSION_PROMPT.md if needed

---

## Your Checklist (Use Every Session)

### Before Starting Session
- [ ] Which step am I working on? (Check MASTER_PLAN.md)
- [ ] Is this new step or continuation? (Check IMPLEMENTATION_STATE.md)
- [ ] Do I have correct prompt ready? (step_prompts/stepXX.md or NEXT_SESSION_PROMPT.md)
- [ ] Branch correct? (rogrv2-backend-wrapup)
- [ ] Estimated tokens for this step? (Check MASTER_PLAN.md)

### Starting Session
- [ ] Paste SESSION_START_TEMPLATE.md
- [ ] Claude reports understanding
- [ ] I confirmed understanding ✓
- [ ] Paste task prompt (step-specific or NEXT_SESSION_PROMPT.md)

### During Session
- [ ] Claude following TENANTS.md? (✅/❌ RDT at start of responses)
- [ ] Claude investigating before proposing? (🔍 INVESTIGATION blocks)
- [ ] Claude asking permission before file changes?
- [ ] At ~75K tokens: Is PROGRESS_THREAD updated?
- [ ] At ~100K tokens: Is NEXT_SESSION_PROMPT ready as backup?

### Ending Session
- [ ] Paste SESSION_WRAPUP_TEMPLATE.md
- [ ] Tests run and pass? (regression + new)
- [ ] Code committed with clear message?
- [ ] PROGRESS_THREAD.md updated (appended)?
- [ ] IMPLEMENTATION_STATE.md updated (overwritten)?
- [ ] NEXT_SESSION_PROMPT.md created (if incomplete)?
- [ ] Session ready for handoff?

---

## Recovery Procedures

### If Session Fails or Context Lost

1. **Read PROGRESS_THREAD.md** (last complete entry)
2. **Check git log** (last commit SHA)
3. **Run regression tests** (verify current state)
4. **Read IMPLEMENTATION_STATE.md** (current snapshot)
5. **Use NEXT_SESSION_PROMPT.md** (if it exists)
6. **Continue from last known good state**

### If Tests Fail

1. **Do NOT proceed to next step**
2. **Document failure in PROGRESS_THREAD.md**
3. **Mark step as BLOCKED in IMPLEMENTATION_STATE.md**
4. **Create detailed NEXT_SESSION_PROMPT.md** explaining issue
5. **Investigate and resolve before continuing**

### If Design Spec Is Ambiguous

1. **STOP immediately**
2. **Ask user for clarification**
3. **Do NOT guess or assume**
4. **Update design spec after clarification**
5. **Continue with corrected spec**

---

## Key Principles

### Quality Over Speed
- Complete solutions, no band-aids
- Comprehensive testing at each step
- Thorough documentation always

### Context Preservation
- PROGRESS_THREAD captures complete history
- IMPLEMENTATION_STATE always current
- NEXT_SESSION_PROMPT for seamless handoffs

### Zero Interpretation Drift
- Design specifications are authoritative
- Implementation sessions execute, don't reinterpret
- Ask for clarification rather than assume

### Atomic Progress
- Each step is complete, testable unit
- Git commits are clean checkpoints
- Can rollback to any previous step

---

## Current Status

**Planning:** ✅ COMPLETE (Session 00)
**Design:** ⏸️ READY TO START (Session Zero-A, Zero-B, Zero-C)
**Implementation:** ⏸️ WAITING (after all 3 design sessions)

**Next Action:** Execute Session Zero-A using SESSION_ZERO_A_PROMPT.md

**Estimated Timeline:**
- Design Phase (Session Zero-A, B, C): 3 sessions (~260-320K tokens total)
  - Session Zero-A: ~80-100K tokens (Phase 0 + 1A)
  - Session Zero-B: ~100-120K tokens (Phase 1B - AI Assist)
  - Session Zero-C: ~80-100K tokens (Phase 1C + 1D)
- Implementation Phase: 12 sessions (3-4 weeks)
  - 12 steps (Step 01 through Step 12)
- **Total: 15 sessions (3 design + 12 implementation)**

---

## Questions?

If anything is unclear:
- Read TENANTS.md (behavior guidelines)
- Read SESSION_ZERO_A_PROMPT.md (immediate next steps)
- Check PROGRESS_THREAD.md (session history)
- Review IMPLEMENTATION_STATE.md (current state)

---

**Framework ready. Execute Session Zero-A to begin design work.**

**END OF README**
