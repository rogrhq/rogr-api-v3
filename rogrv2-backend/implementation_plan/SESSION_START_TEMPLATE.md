# SESSION START - ROGRv2 Backend Completion

**Purpose:** Initialize Claude Code session with project context

**Instructions for User:** Copy-paste this entire document into Claude Code at the start of every new session.

---

## Your Task

You are joining the ROGRv2 Backend completion project. This is a multi-session implementation plan with strict quality standards.

**Your immediate task:**
1. Read the required documents listed below (in order)
2. Report your understanding using the structured format provided
3. Wait for my confirmation before I give you the actual work task

---

## Required Reading (Read in This Order)

### 1. Project Tenants
**File:** `implementation_plan/TENANTS.md`
**Why:** Core behavior guidelines you must follow (especially Tenants 4, 6, 7)

### 2. Current Implementation State
**File:** `implementation_plan/IMPLEMENTATION_STATE.md`
**Why:** Current snapshot of what's done, what's in progress, what's next

### 3. Progress History (Last 2-3 Entries Only)
**File:** `implementation_plan/PROGRESS_THREAD.md`
**Why:** Historical context of recent sessions (read from bottom up)

### 4. Design Specifications
**File:** `implementation_plan/DESIGN_SPECIFICATIONS.md`
**Why:** Complete technical design you'll be implementing from

**Note:** Don't read the entire file now - you'll read specific sections when given your task. Just understand it exists and what it contains.

### 5. Source of Truth (Optional Reference)
**File:** `verification_package/SOURCE_OF_TRUTH_ROGRV2_COMPLETE.md`
**Why:** Verified codebase assessment, use only if you need deeper context

**Note:** Only read this if your task requires understanding existing code state. Most sessions won't need this.

---

## After Reading: Report Your Understanding

Use this exact structured format:

```markdown
## 🎯 PROJECT CONTEXT

**What we're building:** [1-2 sentence plain English explanation]

**Project goal:** [High-level objective]

**Current phase:** [Phase X: name]

**Branch:** [branch name]

---

## 📊 CURRENT STATE

**Last completed session:** [Session XX - brief description]

**Last commit:** [SHA + message, or "No commits yet"]

**Test status:**
- Regression tests (Phase 0): [✅ PASS / ❌ FAIL / ⏸️ NOT YET BUILT / status]
- Current step tests: [status]

**Pending work:** [What's incomplete or next in queue]

---

## 🎯 READY FOR TASK

**I have read:**
- ✅ TENANTS.md - I understand the 7 core tenants
- ✅ IMPLEMENTATION_STATE.md - I know current state
- ✅ PROGRESS_THREAD.md - I understand recent history
- ✅ DESIGN_SPECIFICATIONS.md - I know design exists

**Key constraints I will follow:**
- Zero bias (no domain hardcoding)
- IFCN compliance (methodology-first)
- Design spec adherence (no creative interpretation)
- Investigation required before proposals (Tenant 4)
- Ask permission before file changes (Tenant 6)
- ✅/❌ RDT at start of every response (Tenant 7)

**Token budget for this session:** ~150K target

---

## 🚦 AWAITING YOUR TASK

I am ready to receive the specific task prompt for this session.

Please provide either:
- A step-specific prompt (from `step_prompts/stepXX_[name].md`)
- A continuation prompt (from `NEXT_SESSION_PROMPT.md`)
```

---

## Important Notes

- **Do NOT start working yet** - wait for user to confirm understanding and provide task
- **Do NOT read entire DESIGN_SPECIFICATIONS.md** - you'll read specific sections per task
- **Do NOT make any changes** - this is context loading only

---

**After you report understanding, I will confirm and give you the actual work task.**
