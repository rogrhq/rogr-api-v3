# USER REQUIREMENTS - MVP DEFINITION & PRIORITIES

**Date:** 2025-09-30
**Source:** User clarifications during Session 4
**Context:** Clarifies what "MVP" actually means vs architect's narrower interpretation

---

## 1. MVP DEFINITION (User's Actual Definition)

**MVP = Fully Working Product, NOT Minimal Prototype**

A super smart deterministic fact-checking platform that is:
- Completely unbiased
- Aligned with IFCN compliance
- Uses AI to enhance all deterministic intelligence
- Result: AI-assisted pro journalist-grade research assistant

---

## 2. CORE FEATURES (MUST HAVE DAY 1)

### Input Modalities - Phase 1
**Day 1 Requirements:**
- ✅ **Text input** - MUST WORK
- ✅ **Multi-claim extraction from text** - MUST WORK (NOT deferred to S2P16 as architect suggested)

**Phase 2 (After core works):**
- URL extraction (fetch article, extract text, run P1) - ~2-3 days
- Audio transcription (ASR integration) - ~3-5 days
- Video transcription (ASR + video processing) - ~5-7 days

**User clarification:** "Q1 it may have said that just so the system works with one claim as standard but it must ship with multi claim and it must ship capable of extracting claims from text, URL, audio and video. Stabilizing the live path first may be the build approach but the system must perform with multi-claim day 1"

---

### AI Assist - MUST HAVE DAY 1 (NOT OPTIONAL)

**User clarification:** "Q2 AI Assist is specified in the architect's response to initial 43 questions, please review and report if you still need clarity, this is a MUST HAVE day 1"

From architect's 43 Q&A (I11-29 to I11-31):
1. Query refinement (1.5k in / 300 out tokens)
2. Passage triage (2k in / 300 out tokens)
3. Contradiction surfacing (2k in / 300 out tokens)
4. Explanation draft (4k in / 700 out tokens)

**Critical:** This is NOT optional enhancement. It's core to MVP.

**Estimated effort:** 5-10 days implementation

---

### Claim Extraction & Selection

**Primary/Secondary/Tertiary Tagging:**
- MUST work Day 1
- Required for user tiers and selection

**User Tiers (context for foundation):**
- Free tier: Auto-check primary claims only
- Pro tier: User selects which claims to check
- Enterprise tier: Check all claims

**Usage:**
"When the claims are initially extracted they must be tagged with primary, secondary and tertiary both for the research strategies to be generated but also for user selection. For instance a user may submit a URL from a news article and the claim extraction process pulls out 2 claims in each level but in some user tiers the user will have an option to select which claims they want checked and in some cases the default feature may be to just run all primary claims but report the others with the results so the user can scan them after the initial results are delivered, this flexibility is essential to the user tiers and the user experience."

---

### Trust Capsules

**Definition:** "Trust capsules by definition is the presented result of the fact check."

- Formatted output of fact-check
- IFCN compliant
- Includes: overall score, label, claims list, evidence, methodology
- Shareable format

**Status:** ✅ Already implemented in current codebase

---

## 3. SOCIAL FEATURES (PHASE 2 - After Core Works)

**Social Feed:**
- User posts trust capsules
- Category filtering (user selects interests)
- Engagement algorithms (daily stories, user statistics)
- Example: "Did you know that 20% of your fact checks are science based"

**Purpose:** Drive user engagement with platform

**Status:** API stub exists (`api/feed.py`), implementation deferred to Phase 2

---

## 4. ARCHIVE MODE (PHASE 2 - After Core Works)

**Features:**
- Stored fact checks with smart indexing
- Queryable metadata
- Search across all stored checks
- User's personal archive

**Status:** API stub exists (`api/archive.py`), implementation deferred to Phase 2

---

## 5. CRITICAL ARCHITECTURAL REQUIREMENTS

### 5.1 Zero Bias (IMPERATIVE)

**User statement:** "It is absolutely IMPERATIVE that there is not a single point of bias generated anywhere in this entire system, it must run with flawless un bias, total consistency and accuracy in results and completely aligned with the IFCN core code of principals."

**Requirements:**
- NO domain whitelists/blacklists
- NO hardcoded assumptions
- IFCN alignment mandatory
- Total consistency/accuracy

**Verification needed:** Confirm no bias in ranking, credibility scoring, stance analysis

---

### 5.2 Test Toggle Philosophy

**User clarification:** "The architect originally designed this where there were test toggles all over the place interfering with running the system live with live search and AI assist, this needs to be cleaned up so it doesn't break anything, yes there should be testing toggles but the system needs to work live as a priority and because its not yet in production it doesn't matter if it breaks while in a live environment, if anything that is good."

**Requirements:**
- Live mode is PRIORITY
- Test mode for CI/testing only
- Test toggles must NOT interfere with live operation
- Breaking in dev/staging is ACCEPTABLE and GOOD (find bugs before production)

**Current issue:** Test mode gate bug blocks live mode (pipeline.py line 33)

**User clarification on priority:** "Q3 i mean if they are interfering get them out but if they aren't it is not a priority at all"

---

## 6. SCOPE CONFLICTS RESOLVED

### Multi-Claim Extraction

**Architect said:** "Defer to S2P16" (after live path stable)

**User requirement:** "Must ship Day 1, system must perform with multi-claim day 1"

**Resolution:** Implement multi-claim after fixing integration gaps (Phase 1C in completion plan)

---

### AI Assist

**Architect said:** "Optional enhancement with feature flag"

**User requirement:** "MUST HAVE DAY 1 (not optional)"

**Resolution:** Phase 1B critical path (5-10 days, blocking for MVP)

---

### Input Modalities

**Architect scope:** Text only initially

**User requirement:** "Must ship capable of extracting claims from text, URL, audio and video"

**Resolution:**
- Text: Day 1 (Phase 1)
- Multi-claim from text: Day 1 (Phase 1C)
- URL/audio/video: Phase 2 (after core works)

---

## 7. PHASE 1 vs PHASE 2 SUMMARY

### Phase 1 - Core Fact-Checking (Day 1 / 2-3 weeks)
1. ✅ Text input
2. ✅ Multi-claim extraction (wired up)
3. ✅ Live evidence gathering (integration fixed)
4. ✅ AI assist (4 components) - **CRITICAL PATH**
5. ✅ Primary/secondary/tertiary tagging
6. ✅ Zero bias + IFCN compliance
7. ✅ Trust capsule output

### Phase 2 - Modalities & Social (After Phase 1)
- URL extraction
- Audio/video transcription
- Social feed implementation
- Archive implementation
- User tiers/permissions enforcement

---

## 8. SUCCESS CRITERIA FOR PHASE 1

**When is Phase 1 complete?**
1. User submits text with multiple claims
2. System extracts claims (primary/secondary/tertiary)
3. For each claim:
   - Live evidence gathering from Brave/Google/Bing
   - AI-enhanced query refinement
   - Ranking with zero bias
   - Stance analysis
   - Guardrails (P9-P13)
   - AI-enhanced explanation
4. Returns trust capsule with:
   - Overall verdict (IFCN label)
   - Per-claim verdicts
   - Evidence with sources
   - Natural language explanation (AI-generated)
   - Methodology transparency
5. All of above works with live providers (not test mode)
6. Breaking is acceptable (we want to find bugs)

---

## 9. IMPORTANT CONTEXT FOR FOUNDATION

**User statement:** "I know that many of these features may not be part of the core we're locking down now but they are important in consideration of how this foundation is completed."

**Implication:**
- Don't build Phase 1 in ways that block Phase 2 features
- Keep social feed, archive, user tiers in mind during architecture
- But focus on getting core fact-checking working first

---

## 10. USER'S PHILOSOPHY

**On test toggles:** "If they are interfering get them out but if they aren't it is not a priority at all"

**On breaking in dev:** "It doesn't matter if it breaks while in a live environment, if anything that is good"

**On scope:** "Stabilizing the live path first may be the build approach but the system must perform with multi-claim day 1"

**On AI assist:** "This is a MUST HAVE day 1"

---

**END OF USER REQUIREMENTS**
