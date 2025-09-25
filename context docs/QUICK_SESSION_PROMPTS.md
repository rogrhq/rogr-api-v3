# Quick Copy-Paste Session Prompts

## **SESSION START PROMPT (Copy/Paste Exactly)**

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
- Confirmation you understand RDT v2.0 compliance requirements

Once you confirm understanding, we'll proceed with implementation following the established patterns and RDT v2.0 standards.
```

---

## **TIME PLANNING PROMPT**

```
I have approximately [X] minutes available for this session. Based on the objectives in NEXT_SESSION_OBJECTIVES.md, what should we prioritize to make the best progress?
```

---

## **SESSION END PROMPT (Copy/Paste Exactly)**

```
We're approaching the end of this session. Please update all context documents following the session end protocol:

1. Update CURRENT_SESSION_STATE.md with what we accomplished
2. Update NEXT_SESSION_OBJECTIVES.md with priorities for next session  
3. Update IMPLEMENTATION_PROGRESS.md with completed checkboxes
4. Add any new code patterns to CODE_PATTERNS.md if we established new patterns
5. Commit all changes with descriptive commit messages

Make sure the next AI session will have clear context to continue immediately.
```

---

## **TROUBLESHOOTING PROMPTS**

### **If AI Seems Confused:**
```
Stop. Please re-read AI-SESSION-CONTEXT/CURRENT_SESSION_STATE.md and tell me specifically:
- What was accomplished in the last session?
- What specific files were we working on?
- What is our current architecture approach?

If the context documents are unclear, I'll clarify before we proceed.
```

### **If AI Suggests Major Changes:**
```
Please check COMPLETE_ARCHITECTURE_PLAN.md and CODE_PATTERNS.md before suggesting changes. We have an established plan that should be followed unless there's a critical blocker. What specific issue requires deviation from the plan?
```

### **If Running Low on Time:**
```
We have about [X] minutes left. What's the best stopping point that leaves us in a clean state for the next session? Please update the context documents with current progress before we end.
```

### **If AI Asks About Previous Decisions:**
```
Check AI-SESSION-CONTEXT/ARCHITECTURE_DECISIONS.md - all major architectural decisions are documented there with rationale. Follow the established decisions unless you identify a critical flaw.
```

---

## **EMERGENCY SESSION END PROMPT**

```
I need to end this session unexpectedly. Please immediately:
1. Commit any working code changes
2. Update CURRENT_SESSION_STATE.md with current progress
3. Set clear priorities in NEXT_SESSION_OBJECTIVES.md
4. Note any incomplete work or blocking issues
```

---

## **VALIDATION PROMPTS**

### **Context Understanding Check:**
```
Before we start implementing, confirm you understand:
1. Our current phase: [Phase 1/2/3/4]
2. Target performance: <30s total (from 396s current)
3. Architecture approach: Parallel system with legacy preservation
4. This session's specific objectives: [list from NEXT_SESSION_OBJECTIVES.md]
```

### **Progress Status Check (Use Every 20-30 Minutes):**
```
Status check: 
- How are we progressing against the session objectives?
- Any issues encountered that need attention?  
- Should we adjust priorities based on remaining time?
```

### **Session Time Management Prompts:**

#### **60-Minute Check:**
```
We should start thinking about session end soon. What's a good stopping point for the current work?
```

#### **75-Minute Warning:**
```
Time to start wrapping up this session. Please finish the current task and prepare for context document updates.
```

#### **Emergency Session End:**
```
I need to end this session immediately due to time constraints. Please:
1. Commit any current work
2. Update CURRENT_SESSION_STATE.md with progress
3. Set clear NEXT_SESSION_OBJECTIVES.md
```

### **Implementation Validation:**
```
Before moving to the next component, please:
1. Test the current implementation works
2. Verify it follows CODE_PATTERNS.md
3. Commit changes with descriptive message
4. Confirm next steps align with COMPLETE_ARCHITECTURE_PLAN.md
```

---

## **USAGE INSTRUCTIONS**

### **Every Session Start:**
1. Copy/paste **SESSION START PROMPT**
2. Wait for AI context confirmation
3. Use **TIME PLANNING PROMPT** to set session scope

### **During Development:**
- Use **PROGRESS STATUS CHECK** every 20-30 minutes
- Use **TROUBLESHOOTING PROMPTS** if AI gets confused
- Use **VALIDATION PROMPTS** before major transitions

### **Every Session End:**
1. Copy/paste **SESSION END PROMPT** 
2. Verify AI updates all context documents
3. Confirm clean repository state

### **Emergency Situations:**
- Use **EMERGENCY SESSION END PROMPT** if session interrupted
- Use **CONTEXT UNDERSTANDING CHECK** if AI seems lost

**These prompts ensure consistent, efficient AI sessions with perfect context continuity.**