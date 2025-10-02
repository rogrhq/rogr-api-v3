# ROGR Development Tenants v3.0
**Streamlined for ROGRv2 Backend Completion**

---

## **MANDATORY RESPONSE FORMAT**

**EVERY response MUST start with:**
- `✅ RDT` - If ALL tenants complied with
- `❌ RDT [violations]` - If ANY tenant violated, list specific violations

**No exceptions. This is the first line of every response.**

---

## **Core Tenants**

### **1. DESIGN COHESION**
All solutions must align with the P1-P13 packet architecture, zero bias principle, and IFCN compliance standards. Preserve the deterministic intelligence + AI enhancement design pattern.

**Enforced by:** Design specifications in DESIGN_SPECIFICATIONS.md

---

### **2. COMPLETE SOLUTIONS**
All solutions must be production-ready implementations, not workarounds or band-aids. Address root causes with proper error handling, logging, and validation.

**Exception:** Explicitly marked TODO items for future work are acceptable if documented.

---

### **3. ALWAYS COMPLIANT**
All solutions must maintain:
- **Zero bias** - No domain whitelisting/blacklisting, structural cues only
- **IFCN compliance** - Methodology-first fact-checking standards
- **Deterministic core** - P1-P13 packets remain deterministic, AI layer is enhancement only

**Enforced by:** Code review against zero bias and IFCN standards

---

### **4. NO ASSUMPTIONS - INVESTIGATION REQUIRED**

**Every response proposing a solution or plan MUST start with:**

```
## 🔍 INVESTIGATION
**Files examined:** [list with specific line ranges read]
**Commands run:** [list actual commands executed]
**Integration points identified:** [list specific functions/files that connect]
```

**Only AFTER providing investigation summary may you propose solutions.**

**Rules:**
- Examine actual code even if context documents claim facts
- Read specific line ranges, don't skim
- Verify integration points by reading actual function calls
- If you haven't read the code, you haven't investigated

**Enforcement:** Any solution proposal without investigation block = automatic ❌ RDT violation

---

### **5. CLARITY ALWAYS**
If any tenant, specification, or instruction is unclear, you MUST ask for clarification before proceeding. Do not guess or assume intent.

**When to ask:**
- Ambiguous specification
- Conflicting requirements
- Unclear success criteria
- Missing information needed for implementation

---

### **6. ASK PERMISSION**
Permission is ALWAYS required to:
- Create ANY new file
- Modify ANY existing file
- Delete ANY file
- Make ANY git commit
- Update ANY documentation

**Permission is NOT required to:**
- Read files
- Run read-only commands (git status, grep, etc.)
- Answer questions
- Present plans or analysis results

**Enforcement:** "May I proceed with these changes?" before executing Write/Edit/Bash commands that modify state

---

### **7. FOLLOW THE SPEC**
Implementation sessions must follow DESIGN_SPECIFICATIONS.md exactly as written. You are executing the design, not reinterpreting it.

**Rules:**
- Implement functions with exact signatures specified
- Use exact file paths specified
- Follow integration contracts as designed
- Do not add "helpful" features not in spec
- Do not optimize or refactor unless specified

**When you may deviate:**
- Spec contains an error (ask permission to fix)
- Spec is ambiguous (ask for clarification)
- Spec is technically impossible (explain why, propose alternative)

**Enforcement:** Code review against design specification

---

## **Quality Gates (Mandatory Before Session End)**

Every session MUST complete these before ending:

- [ ] All tests pass (S6 regression + new tests)
- [ ] Code committed with descriptive message
- [ ] PROGRESS_THREAD.md updated (append entry)
- [ ] IMPLEMENTATION_STATE.md updated (overwrite)
- [ ] NEXT_SESSION_PROMPT.md generated (if work incomplete)
- [ ] ✅ RDT compliance verified

**Violating quality gates = ❌ RDT violation**

---

## **Anti-Patterns to Avoid**

### ❌ "I'll help you build X"
✅ "Building X per DESIGN_SPECIFICATIONS.md lines 234-267"

### ❌ "Let me improve this by also adding Y"
✅ "Implemented X as specified. (Y not in current scope)"

### ❌ "The code looks correct"
✅ "Verified: Tests pass (12/12), matches spec lines 234-267"

### ❌ "I think the issue is Z"
✅ "Reproduced error. Stack trace: [paste]. File: X:Y"

### ❌ "I've reviewed the code"
✅ "Read files: [list with line ranges]"

---

## **When to Stop and Ask**

STOP immediately and ask user if you encounter:

1. **Specification ambiguity** - Unclear what to implement
2. **Specification conflict** - Design says X, existing code says Y
3. **Missing dependency** - Design assumes file/function exists but doesn't
4. **Unexpected test failure** - Tests fail for reasons unrelated to your changes
5. **Token budget approaching 120K** - Ask if should continue or hand off
6. **Scope expansion** - Work discovered outside current step
7. **Technical impossibility** - Spec requires something that can't be done

**Do NOT proceed with assumptions. Ask.**

---

## **Enforcement Summary**

| Tenant | Enforcement Mechanism |
|--------|----------------------|
| 1. Design Cohesion | Design spec review |
| 2. Complete Solutions | Code review, no TODOs without docs |
| 3. Always Compliant | Zero bias check, IFCN review |
| 4. No Assumptions | **Forced investigation block** |
| 5. Clarity Always | Ask before guessing |
| 6. Ask Permission | Explicit approval before state changes |
| 7. Follow the Spec | Implementation matches design exactly |

---

## **RDT Self-Check**

Before marking any response as ✅ RDT, verify:

- [ ] Started response with ✅/❌ RDT
- [ ] If proposing solution: Included investigation block
- [ ] If modifying files: Asked permission
- [ ] If ending session: Completed quality gates
- [ ] If unclear: Asked for clarification rather than assumed
- [ ] Followed design spec exactly (no creative additions)
- [ ] Maintained zero bias and IFCN compliance

**False RDT certification undermines the entire process. Be honest.**

---

**END OF TENANTS v3.0**
