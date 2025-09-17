# AI Session Start Protocol

## CRITICAL: Every New AI Session Must Follow This Protocol

### Pre-Implementation Checklist (8 minutes total)

#### 1. Context Recovery (5 minutes)
- [ ] **Read `CURRENT_SESSION_STATE.md`** - Understand what was accomplished last session
- [ ] **Read `NEXT_SESSION_OBJECTIVES.md`** - Know exactly what to do this session  
- [ ] **Review `IMPLEMENTATION_PROGRESS.md`** - Check completion status and blocking issues
- [ ] **Check `ARCHITECTURE_DECISIONS.md`** - Understand key architectural choices made
- [ ] **Read `RDT_v2.md`** - Understand enhanced methodology standards and compliance requirements

#### 2. Git State Validation (2 minutes)
- [ ] **Check current branch**: `git status`
- [ ] **Review recent commits**: `git log --oneline -5` 
- [ ] **Confirm working directory clean**: No uncommitted changes that could conflict

#### 3. User Context Confirmation (1 minute)
- [ ] **Confirm understanding with user**: 
  - "Based on session context, I understand we're at [current phase] with [specific objectives]. Is this correct?"
  - "Any changes to priorities or new issues discovered since last session?"

### Implementation Start Checklist

#### 4. Session Objectives Validation
- [ ] **Confirm session time available**: How long is this development session?
- [ ] **Adjust objectives if needed**: Scale objectives to available time
- [ ] **Identify stopping points**: Plan clean breakpoints for session end

#### 5. Development Environment Ready
- [ ] **Navigate to correct directory**: `cd /Users/txtk/Documents/ROGR/github/rogr-api`
- [ ] **Verify dependencies**: Check if any new imports or installations needed
- [ ] **Confirm testing approach**: Know how to validate implementation

### Success Criteria for Protocol
- ✅ **Context restored in <8 minutes** - No time wasted figuring out "what were we doing?"
- ✅ **Clear objectives confirmed** - Both AI and user know exactly what to accomplish
- ✅ **No architectural confusion** - Previous decisions understood and respected
- ✅ **Ready for productive implementation** - Environment and context prepared

### If Context Documents Missing or Unclear
**STOP IMMEDIATELY** and ask user to clarify:
- "The session context documents are missing/unclear. Can you confirm what we should focus on this session?"
- Do NOT guess or make assumptions about implementation priorities
- Do NOT start coding without clear context understanding

### Example Context Confirmation
"Based on the session context documents, I understand we're beginning Phase 1 of the parallel architecture migration. The next objectives are to:
1. Create legacy_evidence_system/ directory and migrate 13 shepherd files
2. Implement basic ThreadSafeResourcePool with thread-local storage  
3. Add feature flag integration in main.py

The current performance issue is 396s processing time vs <30s target, caused by sequential dual-AI execution. The architecture analysis is complete and we have approval to proceed with the parallel system implementation.

Is this understanding correct? Any updates to priorities?"

### Session End Protocol Reference
Remember: Every session must end with updating context documents:
- `CURRENT_SESSION_STATE.md`
- `NEXT_SESSION_OBJECTIVES.md`  
- `IMPLEMENTATION_PROGRESS.md`
- Any new patterns in `CODE_PATTERNS.md`

**Context continuity is critical for project success with AI partnership limitations.**