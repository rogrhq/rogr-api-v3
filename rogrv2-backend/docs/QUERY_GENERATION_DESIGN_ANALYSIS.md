# Query Generation Design Analysis

**Date:** 2025-10-20
**Task:** Understand what query generation was INTENDED to do vs what it ACTUALLY does

---

## Executive Summary

**CRITICAL FINDING:** Query generation has THREE separate implementations with NO CLEAR WINNER:

1. **plan.py (v1)** - Simple template-based with .gov/.edu/.pdf operators
2. **plan_v2.py:build_search_plans_v2** - Sophisticated semantic-preserving design
3. **plan_v2.py:generate_queries_r1/r2** - PHASE 5 addition for lane differentiation

**ROOT CAUSE:** The pipeline uses `build_search_plans_v2()` which has CORRECT DESIGN but the R1/R2 functions (added in Phase 5) are BROKEN and override the good queries with generic ones.

---

## All Versions Found

| File | Function | Purpose | Status |
|------|----------|---------|--------|
| plan.py | `build_search_plans()` | v1: Simple template with domain operators | LEGACY (wrapper only) |
| plan.py | `build()` | v1: Actual implementation | DEPRECATED |
| plan_v2.py | `build_search_plans_v2()` | v2: Semantic-preserving query builder | **CURRENTLY USED** |
| plan_v2.py | `generate_queries_r1()` | Phase 5: Precision queries (quoted) | **BROKEN** |
| plan_v2.py | `generate_queries_r2()` | Phase 5: Recall queries (broad) | **BROKEN** |

**What pipeline actually uses:**
- `intelligence/pipeline/run.py:167` → imports `build_search_plans_v2`
- `intelligence/planning/diversify.py:81` → imports `generate_queries_r1, generate_queries_r2`

---

## Current Version: build_search_plans_v2

**Location:** intelligence/strategy/plan_v2.py:115-179

**Method:** TEMPLATE-BASED with SEMANTIC PRESERVATION

**Sophistication:** MODERATE to SOPHISTICATED

**Uses embeddings:** NO

**Uses ML models:** NO

**Design Philosophy:**
- Preserves claim semantics through `_head_clause()` (quoted full text)
- Enriches with entity/numeric/temporal context
- Two-arm strategy (support vs challenge)
- NO domain operators (learned from v1 mistakes)

### Code Structure

```python
def build_search_plans_v2(claim: Dict[str, Any]) -> Dict[str, Any]:
    # Extract enriched components
    text = claim.get("text") or ""
    entities = _entity_terms(claim.get("entities") or [])
    percents = _percent_terms(claim.get("numbers") or {})
    time = _time_terms(claim.get("scope") or {})
    comps = _comparison_terms(claim.get("cues") or {})
    kind = claim.get("kind_hint") or ""

    # KEY DESIGN: Preserve full claim as quoted "head clause"
    head = _head_clause(text)  # Returns: "Water boils at 100 degrees Celsius"

    # Build common pool of terms
    common_pool = _uniq(entities + percents + time + comps + _norm_words(kind))

    # Arm A: Support-seeking
    a_queries.append(" ".join(_uniq([head] + common_pool + _support_terms(kind))))

    # Arm B: Challenge-seeking
    b_queries.append(" ".join(_uniq([head] + common_pool + _challenge_terms(kind))))
```

**This design is GOOD:** It includes the full quoted claim text to preserve semantic meaning.

---

## Version Comparison

### v1 (plan.py)

**Approach:** Domain-operator based
```python
gov   = [f"{q} site:.gov" for q in base]
edu   = [f"{q} site:.edu" for q in base]
pdf   = [f"{q} filetype:pdf" for q in base]
```

**Problems:**
- Domain operators trigger search engine filters
- Too restrictive for diverse sources
- DEPRECATED and replaced by v2

### v2 (plan_v2.py:build_search_plans_v2)

**Approach:** Semantic preservation with lexical enrichment

**Queries produced for "Water boils at 100 degrees Celsius":**

**Arm A (Support):**
```
"Water boils at 100 degrees Celsius" Water 100 degrees boiling point report press release official statement
Water 100 degrees official statistics
"Water boils at 100 degrees Celsius" 100 degrees explainer
```

**Arm B (Challenge):**
```
"Water boils at 100 degrees Celsius" Water 100 degrees boiling point dispute counterclaim contradict
Water 100 degrees dispute
dispute counterclaim contradict 100 degrees
```

**Assessment:** These queries are GOOD - they preserve semantic meaning while adding context.

**Improvement over v1:** YES
- Removes domain operators
- Preserves full claim text
- More sophisticated term extraction
- Better balance of precision and recall

### v3 or Phase 5 additions (generate_queries_r1/r2)

**Approach:** Lane differentiation (precision vs recall)

**Location:** plan_v2.py:185-272

**Status:** ADDED in Phase 5, but FUNDAMENTALLY BROKEN

---

## Helper Functions Analysis

### _head_clause (line 108-113)
```python
def _head_clause(text: str) -> str:
    # keep a short quoted clause to anchor semantics
    t = text.strip()
    if len(t) > 140:
        t = t[:140]
    return f"\"{t}\""
```

**Purpose:** Preserve full claim as quoted string for semantic anchoring

**Sophistication:** SIMPLE but EFFECTIVE

**Preserves meaning:** YES ✓

### _entity_terms (line 64-89)
```python
def _entity_terms(entities: Union[List[str], List[Dict[str, Any]]]) -> List[str]:
    # Extract entity terms from either format
```

**Purpose:** Extract entity names from enrichment

**Sophistication:** SIMPLE (format normalization only)

**Input:** From `intelligence/claims/interpret.py:_entities()` which uses regex:
```python
_ENTITY = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b")
```

**For "Water boils at 100 degrees Celsius":**
- Extracts: `["Water", "Celsius"]` (capitalized words)
- Does NOT extract: "boils", "100", "degrees" (not capitalized or stored as numbers)

**Preserves meaning:** PARTIAL - only entities, not the relationship

### _percent_terms (line 24-52)
```python
def _percent_terms(numbers: Dict[str, Any]) -> List[str]:
    # Extract percentage terms from enrichment data
```

**Purpose:** Extract and normalize numeric values

**Sophistication:** MODERATE (handles multiple formats)

**For "Water boils at 100 degrees Celsius":**
- Input: `numbers = {"percents": [], "years": [], "number_units": [(100.0, "degrees")]}`
- Output: NOT USED because percents list is empty
- The "100 degrees" IS captured in number_units but NOT by _percent_terms

**Preserves meaning:** PARTIAL - misses temperature values

### _time_terms (line 54-62)
```python
def _time_terms(scope: Dict[str, Any]) -> List[str]:
    # Extract year from scope
```

**Purpose:** Add temporal context

**For "Water boils at 100 degrees Celsius":** None (no year)

### _comparison_terms (line 91-99)
```python
def _comparison_terms(cues: Dict[str, Any]) -> List[str]:
    # Add comparison lexicon if has_comparison flag set
```

**Purpose:** Add comparison vocabulary

**For "Water boils at 100 degrees Celsius":** None (no comparison cues)

### _support_terms / _challenge_terms (line 101-106)
```python
def _support_terms(kind_hint: str) -> List[str]:
    return ["report", "press release", "official", ...]

def _challenge_terms(kind_hint: str) -> List[str]:
    return ["dispute", "counterclaim", "contradict", ...]
```

**Purpose:** Add intent-specific vocabulary for two-arm search

**Sophistication:** SIMPLE but EFFECTIVE

**Preserves meaning:** YES - augments without replacing

---

## Root Cause: Why Phase 5 Queries Are Generic

### Phase 5 Functions: generate_queries_r1 and generate_queries_r2

These functions were added in Phase 5 for "query strategy differentiation" and are called from `intelligence/planning/diversify.py:81`.

### The Bug in generate_queries_r1 (Precision queries)

**Location:** plan_v2.py:185-223

**For claim:** "Water boils at 100 degrees Celsius"

**Step-by-step breakdown:**

1. **Inputs received:**
   ```python
   claim_text = "Water boils at 100 degrees Celsius"
   entities = ["Water", "Celsius"]
   numbers = [{"value": 100.0, "unit": "degrees"}]
   arm = "B"
   ```

2. **Query 1:** Exact claim (GOOD)
   ```python
   queries.append(f'"{claim_text}"')
   # Result: "Water boils at 100 degrees Celsius"
   ```

3. **Query 2:** Entity + number (line 210-215) - **BUG HERE**
   ```python
   for entity in entities[:2]:
       for number in numbers[:2]:
           entity_str = entity if isinstance(entity, str) else entity.get('name', '')
           num_val = number.get('value', '') if isinstance(number, dict) else str(number)
           queries.append(f'"{entity_str}" {num_val}')

   # Result: "Water" 100.0
   # Result: "Celsius" 100.0
   ```

   **SEMANTIC LOSS:** "boils", "degrees", temperature relationship LOST

4. **Query 3:** Conservative counter-frame (line 218-221) - **BROKEN**
   ```python
   if arm == 'B' and entities:
       entity_str = entities[0]
       queries.append(f'"{entity_str}" actual value')
       queries.append(f'"{entity_str}" verify')

   # Result: "Water" actual value
   # Result: "Water" verify
   ```

   **COMPLETE SEMANTIC LOSS:**
   - "actual value" and "verify" are GENERIC TEMPLATES
   - No mention of boiling, temperature, 100 degrees
   - Could apply to ANY claim about water

**Where semantic meaning is lost:**

Line 220-221 are the WORST offenders:
```python
queries.append(f'"{entity_str}" actual value')  # "Water" actual value
queries.append(f'"{entity_str}" verify')        # "Water" verify
```

These are HARDCODED TEMPLATES that:
- Take ONLY the first entity
- Append generic terms "actual value" / "verify"
- Completely IGNORE the claim's meaning
- Produce useless queries

### The Bug in generate_queries_r2 (Recall queries)

**Location:** plan_v2.py:226-271

**Similar problems:**

Line 256-257:
```python
queries.append(f"{entity_str} data statistics")
queries.append(f"{entity_str} report analysis")
```

Line 262:
```python
queries.append(f"{entity_str} trends changes")
```

Line 266-268:
```python
queries.append(f"{entity_str} variation exceptions")
queries.append(f"{entity_str} different conditions")
queries.append(f"{entity_str} context factors")
```

**ALL of these:**
- Take only entity (no relationship, no numeric value)
- Use GENERIC TEMPLATES
- Produce queries like "Water trends changes" instead of "water boiling point temperature"

**Comment at line 252:**
```python
# TODO: Add actual paraphrase generation
```

**This TODO reveals the design intent:** These functions were PLACEHOLDER implementations that were never finished.

---

## Claim Enrichment Analysis

**File:** intelligence/analyze/enrich.py
**File:** intelligence/claims/interpret.py

### What claim enrichment provides

For "Water boils at 100 degrees Celsius":

```python
{
    "text": "Water boils at 100 degrees Celsius",
    "entities": ["Water", "Celsius"],  # Regex: capitalized words
    "numbers": {
        "percents": [],
        "years": [],
        "number_units": [(100.0, "degrees")]  # Captured here!
    },
    "cues": {
        "has_negation": False,
        "has_comparison": False,
        "has_attribution": False
    },
    "scope": {
        # year_hint would go here if present
    },
    "kind_hint": "statement",
    "concept": "water boiling point",      # ADDED in interpret.py:85-87
    "dimension": "temperature"             # ADDED in interpret.py:85-87
}
```

**Key observation:**
- The verb "boils" → "boiling point" IS extracted in `concept`
- The temperature dimension IS detected
- But the Phase 5 query generators (r1/r2) DON'T USE concept or dimension!

### What's captured vs what's used

**Captured by enrichment:**
- ✓ Entities: ["Water", "Celsius"]
- ✓ Numbers: [(100.0, "degrees")]
- ✓ Concept: "water boiling point"
- ✓ Dimension: "temperature"

**Used by build_search_plans_v2:**
- ✓ Entities → added to common_pool
- ✓ Numbers → converted to percent_terms (but doesn't handle "degrees")
- ✗ Concept → NOT USED
- ✗ Dimension → NOT USED
- ✓ Full text → quoted as head clause

**Used by generate_queries_r1/r2:**
- ✓ Entities → used (but only first entity)
- ✗ Numbers → ignored in counter-frame queries
- ✗ Concept → NOT USED
- ✗ Dimension → NOT USED
- ✓ Full text → quoted in first query only

**Diagnosis:** Phase 5 functions have access to rich enrichment data but CHOOSE to use only entity + hardcoded templates.

---

## Design Intent

### Was v2 INTENDED to be sophisticated?

**Evidence from code comments:**

plan_v2.py:108-109:
```python
def _head_clause(text: str) -> str:
    # keep a short quoted clause to anchor semantics
```

plan_v2.py:116-118:
```python
def build_search_plans_v2(claim: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input: claim dict with enrichment keys from S2 Packet 1.
```

**YES - v2 was designed with semantic preservation in mind:**
1. Comment explicitly says "anchor semantics"
2. Uses quoted full text
3. Enrichment data properly extracted
4. Two-arm strategy for balanced search

### Is there a BETTER version we should use?

**NO - build_search_plans_v2 is already the best design.**

The problem is Phase 5 additions (r1/r2) were meant to ENHANCE but actually DEGRADE query quality.

### Or does v2 just have BUGS in its logic?

**build_search_plans_v2:** NO BUGS - working as designed

**generate_queries_r1/r2:** MULTIPLE BUGS - fundamentally broken

**The bugs:**

1. **Hardcoded generic templates** (r1:220-221, r2:256-268)
   - "actual value", "verify", "data statistics", "report analysis"
   - These are TOO GENERIC to find relevant content

2. **Ignores concept/dimension** (both r1 and r2)
   - Enrichment extracts "water boiling point" concept
   - Enrichment detects "temperature" dimension
   - Query generators ignore both

3. **Drops numeric values** (r1:218-221, r2:266-268)
   - Counter-frame queries don't include "100 degrees"
   - Searching "Water actual value" instead of "Water boiling point 100 degrees"

4. **Incomplete implementation** (r2:252)
   - TODO comment: "Add actual paraphrase generation"
   - Functions are PLACEHOLDER implementations

---

## Impact on Pipeline

### Current query flow

1. **pipeline/run.py:167** calls `build_search_plans_v2(claim)`
   - Returns GOOD queries with quoted claim + enrichment

2. **planning/diversify.py:81** calls `generate_queries_r1/r2`
   - Overrides or supplements with BROKEN queries

### What user sees

**For "Water boils at 100 degrees Celsius":**

**Good queries (from build_search_plans_v2):**
```
"Water boils at 100 degrees Celsius" Water Celsius report official
```

**Bad queries (from r1/r2):**
```
"Water" actual value
"Water" verify
Water data statistics
Water report analysis
```

**Result:** Search engine receives mix of good and useless queries, diluting quality.

---

## Recommendations

### Option 1: Fix Phase 5 functions (r1/r2)

**Replace hardcoded templates with semantic composition:**

```python
# Instead of:
queries.append(f'"{entity_str}" actual value')

# Do:
concept = claim.get("concept", "")
dimension = claim.get("dimension", "")
numbers_str = " ".join([str(n.get("value", "")) for n in numbers])
queries.append(f'"{concept}" {numbers_str} {dimension} verify')
# Result: "water boiling point 100 temperature verify"
```

### Option 2: Disable r1/r2, use only build_search_plans_v2

**Simplest fix:**
- Remove calls to generate_queries_r1/r2 from diversify.py
- Use only the queries from build_search_plans_v2
- These already have good semantic preservation

### Option 3: Complete the Phase 5 implementation

**Address the TODO at line 252:**
- Implement actual paraphrase generation (requires LLM or paraphrase model)
- Use concept/dimension fields from enrichment
- Generate semantically equivalent variations

---

## Conclusion

**What was INTENDED:**
- v2: Sophisticated semantic-preserving query generation ✓
- Phase 5: Differentiate precision (r1) vs recall (r2) strategies ✗

**What ACTUALLY happens:**
- build_search_plans_v2: Works correctly, preserves semantics
- generate_queries_r1/r2: Broken placeholder implementations
- Result: Good queries mixed with generic garbage

**Root cause:**
- Phase 5 functions were added with incomplete implementation
- Hardcoded templates replace semantic understanding
- TODO comment at line 252 confirms this was unfinished work

**Immediate fix:**
Use build_search_plans_v2 only, disable r1/r2 until properly implemented.
