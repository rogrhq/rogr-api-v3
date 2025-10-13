# Priority Items Before AI Assist

## CRITICAL: Upgrade Paraphrase System to Semantic Matching

**Current State:**
- Dictionary-based paraphrase matching (limited to PARAPHRASE_FAMILIES)
- "rose" only matches "increased" if both in same dictionary
- Cannot handle unlimited vocabulary

**Why This Blocks AI Assist:**
- AI generates diverse natural language
- Cannot rely on predefined dictionaries
- Semantic understanding is foundational

**Solution Required:**
Replace with semantic embeddings (sentence-transformers, etc.)
- True semantic similarity
- Unlimited vocabulary
- Context-aware matching

**Estimated Effort:** 1-2 days
**Priority:** CRITICAL before AI Assist
**Status:** Documented for post-Phase 2 work
