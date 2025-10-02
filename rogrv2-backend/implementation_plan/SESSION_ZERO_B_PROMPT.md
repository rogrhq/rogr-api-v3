# SESSION ZERO-B PROMPT - Design Phase 1B Specifications

**Purpose:** Design COMPLETE specifications for Phase 1B (AI Assist Layer - 4 components)

**Instructions:** Copy-paste this entire document into a fresh Claude Code session after Session Zero-A completes.

---

## Overview

This is **Session Zero-B** - the second of three design sessions for ROGRv2 Backend completion.

You will design complete, detailed specifications for:
- **Phase 1B.1:** Query Refinement (AI-enhanced search queries)
- **Phase 1B.2:** Passage Triage (AI-extracts relevant passages from documents)
- **Phase 1B.3:** Contradiction Surfacing (AI-identifies contradictions in evidence)
- **Phase 1B.4:** Explanation Draft (AI-generates human-readable explanations)
- **Phase 1B.5:** Integration (wire all 4 components into pipeline)

**Critical:** These specifications must be COMPLETE. No outlines, no TBDs. Implementation sessions execute your specs exactly.

---

## Your Deliverables

You MUST produce:

1. **DESIGN_SPECIFICATIONS_PHASE_1B.md** (~50-65KB)
   - Complete specifications for all 4 AI components + integration

2. **step_prompts/step03_phase1b1.md** through **step07_phase1b5.md** (5 prompts, ~2-3KB each)
   - Copy-paste ready prompts for each AI component and integration

3. **MASTER_PLAN_UPDATE.md** (~8-10KB)
   - Steps 03-07 breakdown with dependencies, token estimates, risks
   - Merge with partial plan from Zero-A

**Token Budget:** 100-120K (spillover acceptable if needed for completeness)

---

## Required Reading (In Order)

### 1. Previous Design Work
**File:** `implementation_plan/DESIGN_SPECIFICATIONS_PHASE_0_1A.md`
**Why:** Understand integration points from Phase 1A (where AI assist will plug in)

### 2. Source of Truth - Phase 1B Context
**File:** `verification_package/SOURCE_OF_TRUTH_ROGRV2_COMPLETE.md`
**Read:**
- Section 7: Gap Analysis - AI Assist Layer (lines ~475-520)
- Section 8: Completion Plan - Phase 1B description (lines ~640-680)

### 3. Architect Specifications for AI Assist
**File:** `verification_package/architect_answers_session3.md`
**Read:**
- I11: AI model selection and token budgets (lines ~310-380)
- I12: Provider configuration (lines ~385-415)

**Why:** Architect specified model choices, token budgets, and graceful degradation strategy

### 4. User Requirements
**File:** `verification_package/USER_REQUIREMENTS.md`
**Read:**
- AI Assist section (AI assist is MUST HAVE Day 1)

### 5. Behavior Guidelines
**File:** `implementation_plan/TENANTS.md`
**Why:** Zero bias requirement, investigation requirements

---

## PART 0: Investigation (REQUIRED - Tenant 4)

Before designing, investigate existing code for AI/LLM infrastructure.

### Files to Check

**Look for existing patterns:**
- `search_providers/` - Check how external APIs are called
- `infrastructure/` - Check for HTTP client utilities
- Root directory - Check for AI configuration (.env, config files)
- Requirements files - Check for OpenAI/Anthropic dependencies

### Investigation Report Format

```markdown
## 🔍 CODE INVESTIGATION

### Existing AI/LLM Infrastructure
**Found:** [Yes/No]
**Details:**
- OpenAI library installed: [Yes/No, version]
- Configuration management: [How API keys handled]
- HTTP client patterns: [What's used - requests, httpx, etc.]
- Error handling patterns: [Existing retry/fallback strategies]

### Search Provider Patterns (for reference)
**File reviewed:** search_providers/brave/__init__.py
**Pattern observed:**
- Async/sync: [async or sync]
- Error handling: [approach]
- Retry logic: [yes/no]
- Timeout handling: [approach]

**These patterns should be replicated for AI assist calls.**

### Integration Points for AI Assist
**Where to call from:**
- Query refinement: [file:line where queries are generated]
- Passage triage: [file:line where documents are processed]
- Contradiction surfacing: [file:line after P13 runs]
- Explanation draft: [file:line at end of pipeline]

**Integration strategy:** [Describe how to wire in]
```

**Wait for user confirmation after investigation before proceeding.**

---

## PART 1: Design DESIGN_SPECIFICATIONS_PHASE_1B.md

### Completeness Standards

Every AI component must specify:

**For each component:**
- Complete function signature with types
- Complete docstring
- System prompt (exact text)
- User prompt template (exact format with variable interpolation)
- API call structure (model, temperature, max_tokens, timeout)
- Response parsing logic (how to extract data from JSON)
- Error handling (timeout, rate limit, malformed response, API failure)
- Fallback behavior (what to return if AI fails)
- Token budget enforcement
- Zero bias verification (how to check no domain whitelisting)
- Test cases (5+ with exact inputs and expected outputs)

---

### Document Structure

```markdown
# DESIGN SPECIFICATIONS - Phase 1B (AI Assist Layer)
**Version:** 1.0
**Created:** [DATE] - Session Zero-B
**Status:** Complete - Ready for implementation

---

## How to Use This Document

**For Steps 03-07:**
- Read relevant component section
- Implement exactly as specified
- No interpretation needed
- If unclear: STOP and ask

---

## Overview: AI Assist Layer Architecture

**Purpose:** Enhance deterministic fact-checking with AI capabilities while maintaining fallback

**Design Principles:**
1. **Non-blocking:** AI failures degrade gracefully, pipeline continues
2. **Token-budgeted:** Each component has max token limit
3. **Zero-bias:** AI must not introduce domain whitelisting
4. **Deterministic core preserved:** P1-P13 remain deterministic, AI enhances

**Components:**
- 1B.1: Query Refinement - Better search queries
- 1B.2: Passage Triage - Extract relevant passages
- 1B.3: Contradiction Surfacing - Identify contradictions
- 1B.4: Explanation Draft - Human-readable explanations
- 1B.5: Integration - Wire all into pipeline

---

## Shared Infrastructure

### AI Configuration

**File to create:** `intelligence/ai_assist/config.py`

```python
"""
AI Assist configuration and shared utilities.
"""

import os
from typing import Optional
from openai import AsyncOpenAI

# Model selection per architect specs (I11)
DEFAULT_MODEL = "gpt-4-turbo"  # Primary model
FALLBACK_MODEL = "gpt-4o-mini"  # Cost-optimized fallback

# Token budgets per component
TOKEN_BUDGETS = {
    "query_refinement": 500,
    "passage_triage": 1000,
    "contradiction_surfacing": 800,
    "explanation_draft": 1500
}

# Timeout settings
DEFAULT_TIMEOUT = 10  # seconds
MAX_RETRIES = 2

# Initialize OpenAI client
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=DEFAULT_TIMEOUT
)


class AIAssistError(Exception):
    """Base exception for AI assist failures."""
    pass


class TokenBudgetExceeded(AIAssistError):
    """Raised when AI response exceeds token budget."""
    pass


async def call_openai(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 300,
    response_format: Optional[dict] = None
) -> dict:
    """
    Shared OpenAI API call with error handling.

    Args:
        system_prompt: System message
        user_prompt: User message
        model: Model to use (default: gpt-4-turbo)
        temperature: Temperature (0.0-1.0)
        max_tokens: Max tokens in response
        response_format: Optional {"type": "json_object"} for JSON mode

    Returns:
        {
            "content": str,  # Response content
            "usage": {  # Token usage
                "prompt_tokens": int,
                "completion_tokens": int,
                "total_tokens": int
            },
            "model": str  # Model used
        }

    Raises:
        AIAssistError: If API call fails after retries
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                timeout=DEFAULT_TIMEOUT
            )

            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model
            }

        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise AIAssistError(f"OpenAI call failed after {MAX_RETRIES} attempts: {e}")
            # Exponential backoff
            await asyncio.sleep(2 ** attempt)
```

**Why this infrastructure:**
- Shared error handling across all components
- Consistent retry logic
- Token tracking
- Configuration centralized

---

## Component 1B.1: Query Refinement

### Purpose
Use GPT-4 to generate 2-3 refined search queries that improve evidence retrieval quality.

### File to Create
**Path:** `intelligence/ai_assist/refine.py`
**Estimated Lines:** 180-220

---

### Complete Function Specification

```python
async def refine_query(
    claim: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Refines search query using GPT-4 to improve evidence retrieval.

    Args:
        claim: Claim dict with keys:
            - text: str (claim text)
            - numbers: List[Dict] (extracted numbers)
            - cues: Dict (negation, comparison, attribution)
            - scope: Dict (year_hint, geo_hint)
            - entities: List[str] (extracted entities)
        context: Optional additional context (unused for now, future extension)

    Returns:
        Dict with:
            - original_query: str (input claim text)
            - refined_queries: List[str] (2-3 refined variants)
            - refinement_reasoning: str (why these refinements)
            - search_hints: Dict (provider preferences, time filters)
            - token_usage: int (total tokens used)
            - fallback_used: bool (True if AI failed, using fallback)

    Raises:
        Never raises - degrades gracefully on failure
    """
```

---

### System Prompt (Exact Text)

```python
SYSTEM_PROMPT = """You are a search query optimization expert for fact-checking.

Your task: Generate 2-3 refined search queries that will find the best evidence for verifying a claim.

Consider:
1. Key entities and their variations (official names, acronyms, alternative spellings)
2. Temporal context (specific dates, year ranges, time periods)
3. Negation cues (if claim says "not X", search for both X and evidence of negation)
4. Domain-specific terminology (use technical/scientific terms when appropriate)
5. Authoritative source signals (search for peer-reviewed, government, primary sources)

CRITICAL: Do NOT suggest specific domains or websites. Focus on query terms only.

Output must be valid JSON:
{
    "refined_queries": ["query1", "query2", "query3"],
    "reasoning": "Why these refinements improve search quality",
    "search_hints": {
        "time_filter": "2020-2024" or null,
        "suggested_providers": ["general", "academic", "news"]
    }
}

Suggested providers must be generic categories, NOT specific sites."""
```

---

### User Prompt Template

```python
def build_user_prompt(claim: Dict[str, Any]) -> str:
    """Build user prompt from claim data."""

    numbers_str = ", ".join([
        f"{n['value']} ({n['type']})"
        for n in claim.get("numbers", [])
    ]) or "None"

    entities_str = ", ".join(claim.get("entities", [])) or "None"

    cues_str = []
    if claim.get("cues", {}).get("negation"):
        cues_str.append("Negation detected")
    if claim.get("cues", {}).get("comparison"):
        cues_str.append("Comparison detected")
    if claim.get("cues", {}).get("attribution"):
        cues_str.append(f"Attribution: {claim['cues']['attribution']}")
    cues_final = "; ".join(cues_str) or "None"

    temporal_str = claim.get("scope", {}).get("year_hint") or "None"
    geo_str = claim.get("scope", {}).get("geo_hint") or "None"

    return f"""Claim: {claim['text']}

Numbers in claim: {numbers_str}
Entities: {entities_str}
Cues: {cues_final}
Temporal context: {temporal_str}
Geographic context: {geo_str}

Generate 2-3 refined search queries."""
```

---

### Complete Implementation

```python
import json
import logging
from typing import Dict, Any, Optional, List

from intelligence.ai_assist.config import (
    call_openai,
    TOKEN_BUDGETS,
    TokenBudgetExceeded,
    AIAssistError
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """[exact text from above]"""


async def refine_query(
    claim: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """[docstring from above]"""

    original_query = claim["text"]

    try:
        # Build prompts
        user_prompt = build_user_prompt(claim)

        # Call OpenAI
        response = await call_openai(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model="gpt-4-turbo",
            temperature=0.3,
            max_tokens=300,
            response_format={"type": "json_object"}
        )

        # Check token budget
        if response["usage"]["total_tokens"] > TOKEN_BUDGETS["query_refinement"]:
            logger.warning(
                f"Query refinement exceeded token budget: "
                f"{response['usage']['total_tokens']} > {TOKEN_BUDGETS['query_refinement']}"
            )
            raise TokenBudgetExceeded("Token budget exceeded")

        # Parse response
        ai_output = json.loads(response["content"])

        # Validate structure
        if "refined_queries" not in ai_output or not isinstance(ai_output["refined_queries"], list):
            raise ValueError("Invalid AI response structure")

        if len(ai_output["refined_queries"]) < 2:
            raise ValueError("AI returned fewer than 2 queries")

        # Zero bias check: Ensure no specific domains in queries
        for query in ai_output["refined_queries"]:
            if any(domain in query.lower() for domain in [
                ".com", ".org", ".gov", ".edu", "site:", "domain:"
            ]):
                logger.warning(f"AI query contains domain reference: {query}")
                raise ValueError("AI introduced domain bias")

        # Return successful refinement
        return {
            "original_query": original_query,
            "refined_queries": ai_output["refined_queries"][:3],  # Max 3
            "refinement_reasoning": ai_output.get("reasoning", ""),
            "search_hints": ai_output.get("search_hints", {}),
            "token_usage": response["usage"]["total_tokens"],
            "fallback_used": False
        }

    except Exception as e:
        # Log error and fall back
        logger.error(f"Query refinement failed: {e}. Using fallback.")

        # Fallback: Return original query + simple variants
        return {
            "original_query": original_query,
            "refined_queries": [
                original_query,  # Original
                original_query + " evidence",  # Simple variant 1
                original_query + " fact check"  # Simple variant 2
            ],
            "refinement_reasoning": f"AI refinement failed ({type(e).__name__}). Using fallback queries.",
            "search_hints": {},
            "token_usage": 0,
            "fallback_used": True
        }
```

---

### Integration Point

**Where to call:** `intelligence/gather/pipeline.py` or `intelligence/pipeline/run.py`, BEFORE calling strategy planner (P3)

**Pattern:**
```python
# After P2 (interpret) runs
if not test_mode:
    from intelligence.ai_assist.refine import refine_query

    # Refine query with AI
    refinement = await refine_query(claim)

    # Use refined queries for strategy planning
    queries_for_search = refinement["refined_queries"]

    # Log if fallback used
    if refinement["fallback_used"]:
        logger.info(f"Query refinement fallback for claim {claim['id']}")
else:
    # Test mode: use original claim text
    queries_for_search = [claim["text"]]
```

---

### Test Cases

**Test 1: Simple factual claim**
```python
async def test_refine_simple_claim():
    """Test query refinement with simple factual claim."""
    claim = {
        "id": "c-0",
        "text": "The Eiffel Tower is 330 meters tall.",
        "numbers": [{"value": 330, "type": "number"}],
        "entities": ["Eiffel Tower"],
        "cues": {},
        "scope": {}
    }

    result = await refine_query(claim)

    # Validate structure
    assert "original_query" in result
    assert "refined_queries" in result
    assert isinstance(result["refined_queries"], list)
    assert len(result["refined_queries"]) >= 2
    assert len(result["refined_queries"]) <= 3

    # Validate zero bias (no domains)
    for query in result["refined_queries"]:
        assert ".com" not in query.lower()
        assert ".org" not in query.lower()
        assert "site:" not in query.lower()

    # Validate token budget
    if not result["fallback_used"]:
        assert result["token_usage"] <= TOKEN_BUDGETS["query_refinement"]

    print(f"Refined queries: {result['refined_queries']}")
```

**Test 2: Claim with temporal context**
```python
async def test_refine_with_temporal():
    """Test refinement includes temporal context."""
    claim = {
        "id": "c-1",
        "text": "US GDP grew 3.2% in Q4 2023.",
        "numbers": [
            {"value": 3.2, "type": "percent"},
            {"value": 2023, "type": "year"}
        ],
        "entities": ["US", "GDP"],
        "cues": {},
        "scope": {"year_hint": "2023"}
    }

    result = await refine_query(claim)

    # Check queries include temporal context
    queries_str = " ".join(result["refined_queries"]).lower()
    assert "2023" in queries_str or "q4" in queries_str

    # Check search hints
    if "search_hints" in result and "time_filter" in result["search_hints"]:
        assert "2023" in result["search_hints"]["time_filter"]
```

**Test 3: Negation cue**
```python
async def test_refine_with_negation():
    """Test refinement handles negation cues."""
    claim = {
        "id": "c-2",
        "text": "Vaccines do not cause autism.",
        "numbers": [],
        "entities": ["vaccines", "autism"],
        "cues": {"negation": "not"},
        "scope": {}
    }

    result = await refine_query(claim)

    # Check queries address negation
    queries_str = " ".join(result["refined_queries"]).lower()
    assert "vaccine" in queries_str
    assert "autism" in queries_str
    # Should search for both the claim and counter-evidence
```

**Test 4: Fallback on API failure**
```python
async def test_refine_fallback():
    """Test graceful fallback when AI fails."""
    # Mock API failure
    import intelligence.ai_assist.config as config
    original_call = config.call_openai

    async def mock_fail(*args, **kwargs):
        raise AIAssistError("Simulated failure")

    config.call_openai = mock_fail

    try:
        claim = {
            "id": "c-3",
            "text": "Test claim",
            "numbers": [],
            "entities": [],
            "cues": {},
            "scope": {}
        }

        result = await refine_query(claim)

        # Should not raise, should use fallback
        assert result["fallback_used"] is True
        assert len(result["refined_queries"]) == 3
        assert result["refined_queries"][0] == "Test claim"
        assert "evidence" in result["refined_queries"][1]

    finally:
        config.call_openai = original_call
```

**Test 5: Token budget enforcement**
```python
async def test_token_budget():
    """Test token budget is enforced."""
    claim = {
        "id": "c-4",
        "text": "Complex claim with many entities and numbers.",
        "numbers": [{"value": 100, "type": "number"}],
        "entities": ["entity1", "entity2", "entity3"],
        "cues": {},
        "scope": {}
    }

    result = await refine_query(claim)

    # If not fallback, must be within budget
    if not result["fallback_used"]:
        assert result["token_usage"] <= TOKEN_BUDGETS["query_refinement"], \
            f"Token usage {result['token_usage']} exceeds budget {TOKEN_BUDGETS['query_refinement']}"
```

---

### Success Criteria for 1B.1

Component complete when:
- [ ] `refine.py` created with complete implementation
- [ ] All 5 test cases pass
- [ ] Token budget enforced (≤500 tokens)
- [ ] Zero bias verified (no domain whitelisting)
- [ ] Graceful fallback works (tested)
- [ ] Integration point wired
- [ ] Code committed: "[Session 03] Phase 1B.1: Query refinement"

---

## Component 1B.2: Passage Triage

[Continue with COMPLETE specification for passage triage following same pattern as 1B.1]

**Purpose:** Extract 2-3 most relevant passages from fetched documents

**File:** `intelligence/ai_assist/triage.py` (180-220 lines)

**Token Budget:** 1000 per document

**Model:** gpt-4o-mini (cost-optimized for batch processing)

[Complete function signature, system prompt, user prompt, implementation, test cases...]

---

## Component 1B.3: Contradiction Surfacing

[Complete specification following same pattern]

**Purpose:** Identify contradictions between evidence items using LLM

**File:** `intelligence/ai_assist/contradict.py` (160-200 lines)

**Token Budget:** 800 per comparison

**Model:** gpt-4-turbo

[Complete specs...]

---

## Component 1B.4: Explanation Draft

[Complete specification following same pattern]

**Purpose:** Generate human-readable explanation of fact-check result

**File:** `intelligence/ai_assist/explain.py` (200-240 lines)

**Token Budget:** 1500 per explanation

**Model:** gpt-4-turbo

[Complete specs...]

---

## Component 1B.5: Integration

[Complete integration specifications]

**Purpose:** Wire all 4 AI components into pipeline

**Modifications needed:**
- intelligence/gather/pipeline.py: Call refine_query, triage_passages
- intelligence/pipeline/run.py: Call contradict, explain at appropriate points

**Error handling strategy:** Each component failure is non-blocking

[Complete integration code...]

---

**END OF DESIGN_SPECIFICATIONS_PHASE_1B.md**
```

---

## PART 2: Create Step Prompts (Steps 03-07)

Create 5 complete step prompts following the pattern from Zero-A, each referencing specific sections of DESIGN_SPECIFICATIONS_PHASE_1B.md.

---

## PART 3: Update Master Plan

Merge with MASTER_PLAN_PARTIAL.md from Zero-A, add steps 03-07 with complete breakdown.

---

## Your Execution Plan

1. ✅ Read required documents
2. ✅ Investigate code for AI infrastructure (REQUIRED - Tenant 4)
3. ✅ Report investigation - **WAIT FOR USER CONFIRMATION**
4. ✅ Design complete 1B.1 specifications
5. ✅ Design complete 1B.2 specifications
6. ✅ Design complete 1B.3 specifications
7. ✅ Design complete 1B.4 specifications
8. ✅ Design complete 1B.5 integration
9. ✅ Create step03-step07 prompts
10. ✅ Update master plan
11. ✅ Update PROGRESS_THREAD.md
12. ✅ Update IMPLEMENTATION_STATE.md
13. ✅ Report completion

---

## Important Reminders

- **Complete specifications only** - No outlines
- **Investigation required** - Check for existing AI infrastructure
- **Ask permission** - Before creating files
- **Zero bias** - AI must not introduce domain whitelisting
- **Graceful degradation** - All AI failures non-blocking

---

**Token Budget:** 100-120K (spillover acceptable if needed)

---

**Ready to begin Session Zero-B?**

**Confirm you understand: Complete Phase 1B specs (all 4 AI components + integration).**
