# User AI Session Management Checklist

## **CRITICAL: Follow this checklist EXACTLY for every AI session**

---

## **PRE-SESSION PREPARATION (5 minutes)**

### **Step 1: Environment Setup**
- [ ] **Navigate to project directory**: `cd /Users/txtk/Documents/ROGR/github/rogr-api`
- [ ] **Check git status**: `git status` (ensure clean working directory)
- [ ] **Check current branch**: Should be on `main` or development branch
- [ ] **Estimate available session time**: Plan 75-90 minutes for productive development session

### **Step 2: Context Document Review (Optional)**
*Only if you want to refresh your understanding before the session*
- [ ] **Quick scan of CURRENT_SESSION_STATE.md** - know what was last accomplished
- [ ] **Review NEXT_SESSION_OBJECTIVES.md** - understand planned priorities

---

## **SESSION INITIATION (10 minutes)**

### **Step 3: AI Context Loading Prompt**
**Copy/paste this EXACT prompt to start every session:**

```
I'm continuing development on the ROGR parallel evidence architecture project. 

Please start by reading the following context files to understand our current state:
1. AI-SESSION-CONTEXT/CURRENT_SESSION_STATE.md
2. AI-SESSION-CONTEXT/NEXT_SESSION_OBJECTIVES.md  
3. AI-SESSION-CONTEXT/SESSION_START_PROTOCOL.md
4. RDT_v2.md (Enhanced development methodology standards)

After reading these files, please confirm your understanding by telling me:
- What phase of implementation we're currently in
- What specific objectives you understand for this session
- What the current performance issue is and our target
- Any blocking issues from the previous session
- Confirmation you understand and are committed to strictly follow the RDT v2.0 compliance requirements

Once you confirm understanding, we'll proceed with implementation following the established patterns and RDT v2.0 standards.
```

### **Step 4: AI Understanding Validation**
**Wait for AI to read context files and provide summary**
- [ ] **AI confirms current phase** (Phase 1, 2, 3, 4, or 5)
- [ ] **AI states session objectives** (should match your expectations)  
- [ ] **AI identifies current performance gap** (396s → 30s target)
- [ ] **AI mentions any blocking issues** from previous session
- [ ] **AI confirms RDT v2.0 understanding** (new methodology standards)

**If AI understanding is incorrect or unclear:**
- Stop and clarify: "The context isn't clear. Let me clarify our current state: [explain current situation]"
- Don't proceed with implementation until understanding is correct

### **Step 5: Session Time Planning**
**Tell AI your available time:**

```
I have approximately [X] minutes available for this session. Based on the objectives in NEXT_SESSION_OBJECTIVES.md, what should we prioritize to make the best progress?
```

**AI should adjust objectives to fit available time**
- 30-45 minutes: Focus on debugging or single component implementation
- 60-75 minutes: Complete component implementation with testing
- 90+ minutes: Full phase implementation or major feature

---

## **ACTIVE DEVELOPMENT PHASE (60-75 minutes)**

### **Step 6: Implementation Execution**
**AI should follow these patterns automatically:**

#### **For Phase 1 Sessions:**
- [ ] **AI follows PHASE_1_CHECKLIST.md exactly**
- [ ] **AI uses exact bash commands provided** for file migration
- [ ] **AI implements ThreadSafeResourcePool** with provided code patterns
- [ ] **AI creates feature flag integration** as specified

#### **For Phase 2+ Sessions:**
- [ ] **AI follows COMPLETE_ARCHITECTURE_PLAN.md** for current phase
- [ ] **AI uses CODE_PATTERNS.md** for all new implementations
- [ ] **AI implements specified components** with thread safety patterns

### **Step 7: Progress Monitoring**
**YOU must initiate progress checks every 20-30 minutes:**

**Use this prompt:**
```
Status check - please provide:
- Current task completion status
- Any issues encountered and solutions applied  
- How much of our session objectives we've completed
- Recommendation for priorities if we need to start wrapping up soon
```

**⚠️ IMPORTANT: AI will NOT automatically remind you about session time limits**

### **Step 8: Validation and Testing**
**AI should test implementations before moving to next component:**
- [ ] **Run any test files created** (e.g., `python test_resource_pool.py`)
- [ ] **Test legacy system still works** after migrations
- [ ] **Validate git commits** are clean with descriptive messages

---

## **SESSION CONCLUSION (10-15 minutes) - CRITICAL**
**⚠️ YOU must initiate session end - AI will NOT remind you**

### **When to Start Session End Protocol:**
- **75+ minutes elapsed**: Start wrapping up immediately
- **Current task nearly complete**: Good stopping point
- **Session feeling "heavy" or slow**: May be approaching auto-compact
- **Better safe than sorry**: End early rather than lose context

### **Step 9: Context Update Protocol**
**Copy/paste this exact prompt to AI:**

```
We're approaching the end of this session. Please update all context documents following the session end protocol:

1. Update CURRENT_SESSION_STATE.md with what we accomplished
2. Update NEXT_SESSION_OBJECTIVES.md with priorities for next session  
3. Update IMPLEMENTATION_PROGRESS.md with completed checkboxes
4. Add any new code patterns to CODE_PATTERNS.md if we established new patterns
5. Commit all changes with descriptive commit messages

Make sure the next AI session will have clear context to continue immediately.
```

### **Step 10: Final Validation**
**AI should provide session summary:**
- [ ] **List of accomplishments this session**
- [ ] **Current completion status** (what % of current phase is done)
- [ ] **Clear objectives set for next session**
- [ ] **Any blocking issues identified** that need attention
- [ ] **Git commits completed** with clean repository state

### **Step 11: Next Session Preparation**
**AI should confirm:**
- [ ] **NEXT_SESSION_OBJECTIVES.md updated** with 1-hour plan
- [ ] **No uncommitted changes** in git repository
- [ ] **Context transfer complete** for seamless handoff

---

## **TROUBLESHOOTING SCENARIOS**

### **If AI Seems Confused About Context:**
```
Stop. Please re-read AI-SESSION-CONTEXT/CURRENT_SESSION_STATE.md and tell me specifically:
- What was accomplished in the last session?
- What specific files were we working on?
- What is our current architecture approach?

If the context documents are unclear, I'll clarify before we proceed.
```

### **If AI Suggests Deviating from Plan:**
```
Please check COMPLETE_ARCHITECTURE_PLAN.md and CODE_PATTERNS.md before suggesting changes. We have an established plan that should be followed unless there's a critical blocker. What specific issue requires deviation from the plan?
```

### **If Session is Running Low on Time:**
```
We have about [X] minutes left. What's the best stopping point that leaves us in a clean state for the next session? Please update the context documents with current progress before we end.
```

### **If AI Asks About Architecture Decisions:**
```
Check AI-SESSION-CONTEXT/ARCHITECTURE_DECISIONS.md - all major architectural decisions are documented there with rationale. Follow the established decisions unless you identify a critical flaw.
```

### **If Implementation Gets Stuck:**
```
Let's follow the troubleshooting approach:
1. Check if this issue is addressed in PROBLEM_SOLUTIONS.md
2. Document the specific issue and attempted solutions
3. Create a clear objective for next session to resolve this
4. Update context documents with the blocking issue

Don't spend more than 15 minutes on any single bug - document and move on.
```

---

## **SESSION SUCCESS CRITERIA**

### **Every Session Should Achieve:**
- [ ] **Context successfully transferred** from previous session (0 time lost)
- [ ] **Clear objectives identified** and worked toward
- [ ] **Measurable progress made** toward parallel architecture implementation
- [ ] **Context documents updated** for next session continuity
- [ ] **Repository in clean state** with descriptive commit messages

### **Red Flags That Indicate Problems:**
- ❌ AI spends >10 minutes figuring out "what we were doing"
- ❌ AI suggests starting over or major architecture changes without clear rationale
- ❌ AI creates new files without following established CODE_PATTERNS.md
- ❌ Session ends without updating context documents
- ❌ AI asks about decisions already documented in ARCHITECTURE_DECISIONS.md

---

## **COMMUNICATION TEMPLATES**

### **Session Start Template:**
```
Starting ROGR parallel architecture development session.

Context transfer: Please read AI-SESSION-CONTEXT/SESSION_START_PROTOCOL.md and follow it exactly.

Available time: [X] minutes
Session goals: Follow objectives in NEXT_SESSION_OBJECTIVES.md

Confirm your understanding before we begin implementation.
```

### **Progress Check Template:**
```
Status check: 
- How are we progressing against the session objectives?
- Any issues encountered that need attention?
- Should we adjust priorities based on remaining time?
```

### **Session End Template:**
```
Session wrap-up time. Please:
1. Follow the session end protocol in SESSION_START_PROTOCOL.md
2. Update all context documents for next session
3. Provide a summary of accomplishments and next priorities
4. Ensure repository is in clean state with commits
```

### **Emergency Stop Template:**
```
I need to end this session unexpectedly. Please immediately:
1. Commit any working code changes
2. Update CURRENT_SESSION_STATE.md with current progress
3. Set clear priorities in NEXT_SESSION_OBJECTIVES.md
4. Note any incomplete work or blocking issues
```

---

## **SUCCESS METRICS**

### **Context Continuity Success:**
- New AI session productive within 10 minutes ✅
- Zero architecture confusion or conflicting decisions ✅
- Consistent code patterns maintained across sessions ✅
- Previous session's work preserved and built upon ✅

### **Development Velocity Success:**
- 80%+ of session time spent on productive implementation ✅
- Clear measurable progress each session ✅
- No time lost to "what were we building?" questions ✅
- Systematic progression through implementation phases ✅

### **Quality Success:**
- All implementations follow established CODE_PATTERNS.md ✅
- Thread safety maintained across all parallel components ✅
- Git history clean with descriptive commits ✅
- Documentation updated with each session's discoveries ✅

**Following this checklist ensures seamless AI partnership development despite Claude Code context limitations.**