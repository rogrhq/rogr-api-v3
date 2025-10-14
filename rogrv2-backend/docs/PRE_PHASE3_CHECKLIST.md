# Pre-Phase 3 Checklist

**Purpose:** Track all items that must be completed before starting Phase 3 (AI Assist Integration)

**Last Updated:** 2025-10-13

**Status:** 🔴 NOT READY

---

## BLOCKING ITEMS

### 🔴 1. Upgrade Paraphrase System to Semantic/Embeddings

**Current State:**
- Dictionary-based with limited vocabulary
- Manual word families in `shared/paraphrases.py`

**Required:**
- Semantic embeddings-based matching
- Unlimited vocabulary support
- Better domain coverage

**Why Blocking:**
- Phase 3 AI Assist depends on robust semantic matching
- Current approach too brittle for production

**Estimated:** 1-2 days

**Completion Criteria:**
- [ ] Semantic embeddings integrated
- [ ] Tests pass
- [ ] Performance acceptable

---

## Instructions

Add new blocking items to this document as they're discovered.
Review this checklist completely before starting Phase 3.

---

## CONTEXTUAL SUPPORT TEST FAILURE

**Date:** 2025-10-13
**Context:** Running Phase 2 test battery - test_contextual_support() failed

### Test Failure Details

**Test:** `test_contextual_support()`
- **Claim:** "Sound travels faster in water than air"
- **Evidence:** "In water, sound speed is higher"
- **Expected:** support/contextual_support/mixed
- **Actual:** unrelated

### Root Cause

P20's contextual support detection is not recognizing the relationship between:
- "travels" ↔ "speed" (semantic relationship not detected)
- "faster" ↔ "higher" (in context of speed/velocity)

This is a **paraphrase/semantic matching limitation** - the dictionary lacks these mappings.

### Status

✅ ACCEPTED as known limitation for Phase 2 completion
⏳ Will be addressed by embeddings upgrade (Blocking Item #1)
