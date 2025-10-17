# ROGRv2 Architecture Documentation

**Version:** 1.0
**Date:** 2025-10-17
**Branch:** post-mp-cleanup
**Purpose:** Comprehensive architectural reference for 11-phase improvement plan

This document provides validated, test-backed documentation of the ROGRv2 fact-checking system architecture to prevent drift across multiple independent Claude Code sessions.

---

## Table of Contents

1. [Section 1: Data Structures](#section-1-data-structures)
2. [Section 2: Module Interfaces](#section-2-module-interfaces)
3. [Section 3: Pipeline Flow](#section-3-pipeline-flow)
4. [Section 4: Known Issues](#section-4-known-issues)
5. [Section 5: Integration Contracts](#section-5-integration-contracts)
6. [Validation Tests](#validation-tests)

---

## Section 1: Data Structures

All data structures documented with validation tests in `tests/architecture/test_data_structures.py`.

### 1.1 Evidence Item Format (Validated ✅)

**Location:** Created by `intelligence/gather/online.py`, modified throughout pipeline

```python
evidence_item = {
    # Base fields (after gather)
    'url': str,                      # Source URL
    'snippet': str,                  # Search result snippet
    'arm': str,                      # 'A' or 'B'
    'score': float,                  # Search relevance (0-1)
    'title': str,                    # Article title
    'provider': str,                 # Search provider name

    # After fetch_enrichment.py (P22)
    'content': str,                  # Full article text
    'content_chars': int,            # Character count
    'content_hash': str,             # SHA256 hash
    'coverage': str,                 # 'full'|'partial'|'snippet_only'

    # After grade.py (P20) ⚠️ BUG: 0-10 scale
    'item_grade': float,             # 0-10 scale (BUG: should be 0-1)
    'stance': str,                   # 'support'|'challenge'|'mixed'|'unrelated'|'contextual_support'
    'finding': {
        'grade': float,              # 0-10 scale
        'stance': str,
        'matched_spans': List[str],
        'rationale': List[str],
        'similarity': float
    },

    # After semantic_read.py (P23) - Fixes P20 scale bug
    'item_grade': float,             # 0-1 scale (overwrites P20)
    'grade_label': str,              # 'high'|'medium'|'low'
    'findings': [
        {
            'quote': str,
            'offset_start': int,
            'offset_end': int,
            'stance': str,
            'signals': List[str],    # ['entity', 'number', ...]
            'score': float           # 0-1
        }
    ],

    # After semantic_frames.py (P24)
    'item_frame': {
        'entity': List[str],
        'action': str,               # 'increase'|'decrease'|'unknown'
        'quantity': List[float],
        'year': List[int],
        'scope': str
    },
    'frame_matches': [
        {
            'label': str,            # 'entail'|'contradict'|'mixed'|'unrelated'
            'score': float,          # 0-1
            'slots': List[str],
            'rules': List[str],
            'quote': str,
            'offset_start': int,
            'offset_end': int
        }
    ],
    'frame_confidence': float,       # 0-1

    # After fullread.py (P21)
    'grade_full': float,             # 0-10 scale
    'stance_full': str,              # 'support'|'challenge'|'mixed'|'unrelated'
    'signals_full': {
        'jaccard3': float,
        'entity_overlap': float,
        'percent_any': bool,
        'percent_close': bool,
        'year_hit': bool,
        'negation': bool
    },
    'credibility': float             # 0-1
}
```

**Validation Test:** `tests/architecture/test_data_structures.py::test_evidence_item_structure`

**Test Result:** ✅ PASSED - Structure confirmed accurate, bug documented

**Known Issues:**
- ⚠️ P20 `item_grade` uses 0-10 scale (should be 0-1) - `intelligence/content/grade.py:231`
- ⚠️ P23 overwrites P20's `item_grade` to fix scale (creates dependency)
- ⚠️ Multiple grades per item: `item_grade` (0-1), `grade_full` (0-10), `frame_confidence` (0-1)

---

### 1.2 Claim Format (Validated ✅)

**Location:** Created by interpret modules, used throughout pipeline

```python
claim = {
    'text': str,                     # Full claim text
    'id': str,                       # Unique claim identifier
    'claim_type': str,               # 'policy'|'scientific'|'generic'
    'entities': List[str] | List[Dict],  # Can be strings or dicts with 'name' key
    'numbers': {
        'percents': List[float | str]  # Can be 8.0 or "8%"
    },
    'scope': {
        'year': int
    },
    'cues': {
        'has_comparison': bool
    },
    'kind_hint': str,                # 'budget'|'scientific'|etc
    'concept': str,
    'dimension': str
}
```

**Validation Test:** `tests/architecture/test_data_structures.py::test_claim_structure`

**Test Result:** ✅ PASSED

**Important:** `entities` can be either `List[str]` (canonical) or `List[Dict]` with `'name'` key (legacy). Use `strategy/plan_v2.py:_entity_terms()` for safe extraction.

---

### 1.3 Verdict Format (Validated ✅)

**Location:** Created by `intelligence/gather/pipeline.py:build_evidence_for_claim`

```python
verdict = {
    'claim_grade_numeric': int,      # 0-100 scale
    'label': str,                    # 'True'|'Mostly True'|'Mixed'|'Mostly False'|'False'
    'evidence_grade_letter': str,    # 'A'-'F'
    'rationale': str,
    'arm_strength': {                # Added by P25
        'support': float,            # 0-1
        'challenge': float,          # 0-1
        'balance': float             # support - challenge
    }
}
```

**Validation Test:** `tests/architecture/test_data_structures.py::test_verdict_structure`

**Test Result:** ✅ PASSED

**Label Mapping (IFCN bands):**
- 90-100: "True"
- 75-89: "Mostly True"
- 55-74: "Mixed"
- 35-54: "Mostly False"
- 0-34: "False"

Location: `intelligence/score/labeling.py:16`

---

### 1.4 Frame Format (Validated ✅)

**Location:** `intelligence/content/shared/frames.py:7`

```python
@dataclass
class Frame:
    phenomenon: Optional[str] = None   # Scientific: "boiling point"
    entity: Optional[str] = None       # Policy: "Austin budget"
    action: Optional[str] = None       # 'increase'|'decrease'|'change'
    number: Optional[float] = None     # Numeric value
    unit: Optional[str] = None         # '°C'|'%'|'dollars'
    condition: Optional[str] = None    # 'sea level'|'room temperature'
    timeframe: Optional[str] = None    # '2024'|'Q1'|'last year'
    direction: Optional[str] = None    # 'up'|'down'|'stable'
    domain: str = "generic"            # 'scientific'|'policy'|'generic'
    confidence: float = 1.0
```

**Validation Test:** `tests/architecture/test_data_structures.py::test_frame_structure`

**Test Result:** ✅ PASSED

---

## Section 2: Module Interfaces

All module interfaces documented with validation tests in `tests/architecture/test_module_interfaces.py`.

### 2.1 grade.py - Evidence Grading (Validated ✅)

**Function:** `build_finding`
**Location:** `intelligence/content/grade.py:176`

```python
def build_finding(
    claim_text: str,
    arm: str,
    content_text: str,
    snippet_text: str = "",
    precomputed_window: str = "",
    precomputed_sim: float = -1.0
) -> Dict[str, Any]:
    """
    Build a finding for one evidence item.

    Returns:
        {
            'grade': float (0-10),  # ⚠️ BUG: Should be 0-1
            'stance': str,
            'matched_spans': List[str],
            'rationale': List[str],
            'similarity': float,
            'signals': {
                'entity': bool,
                'number': bool,
                'year': bool
            }
        }
    """
```

**Validation Test:** `tests/architecture/test_module_interfaces.py::test_grade_build_finding`

**Test Result:** ✅ PASSED

**Known Bug:** Returns 0-10 scale instead of 0-1. Fixed by P23 overwrite.

**Called by:** Evidence processing pipeline after content fetch

---

### 2.2 semantic_read.py - Semantic Analysis (Validated ✅)

**Function:** `analyze_item`
**Location:** `intelligence/content/semantic_read.py:103`

```python
def analyze_item(
    claim_text: str,
    item: Dict[str, Any],
    *,
    window: int = 3
) -> Dict[str, Any]:
    """
    Deterministic semantic pass for a single item.

    Modifies item in place, adding:
        - findings: List[Dict] (quotes, stances, signals)
        - item_grade: float (0-1)  # Overwrites P20's 0-10 value
        - grade_label: str ('high'|'medium'|'low')

    Returns: Updated item dict
    """
```

**Validation Test:** `tests/architecture/test_module_interfaces.py::test_semantic_read_analyze_item`

**Test Result:** ✅ PASSED

**Important:** This function **overwrites** `item_grade` set by P20, fixing the scale bug. Must run after P20.

---

### 2.3 semantic_frames.py - Frame Extraction (Validated ✅)

**Function:** `analyze_frames`
**Location:** `intelligence/content/semantic_frames.py:202`

```python
def analyze_frames(
    claim_text: str,
    content: str,
    *,
    window: int = 3,
    max_windows: int = 500
) -> Dict[str, Any]:
    """
    Extract and compare semantic frames.

    Returns:
        {
            'item_frame': Dict (entity, action, quantity, year, scope),
            'frame_matches': List[Dict] (label, score, slots, rules, quote),
            'frame_confidence': float (0-1)
        }
    """
```

**Validation Test:** `tests/architecture/test_module_interfaces.py::test_semantic_frames_analyze_frames`

**Test Result:** ✅ PASSED

---

### 2.4 fullread.py - Deep Content Analysis (Validated ✅)

**Function:** `evaluate_full_evidence`
**Location:** `intelligence/content/fullread.py:177`

```python
def evaluate_full_evidence(
    claim_text: str,
    item: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deterministic deeper read on best available text.

    Modifies item in place, adding:
        - grade_full: float (0-10)
        - stance_full: str
        - signals_full: Dict (jaccard3, entity_overlap, etc.)
        - credibility: float (0-1)

    Returns: Updated item dict
    """
```

**Validation Test:** `tests/architecture/test_module_interfaces.py::test_fullread_evaluate`

**Test Result:** ✅ PASSED

---

### 2.5 p25_aggregate.py - Verdict Aggregation (Validated ✅)

**Function:** `aggregate_verdict`
**Location:** `intelligence/content/p25_aggregate.py:72`

```python
def aggregate_verdict(
    claim_text: str,
    arm_a_items: List[Dict[str, Any]],
    arm_b_items: List[Dict[str, Any]],
    *,
    delta: float = 0.15
) -> Dict[str, Any]:
    """
    Produce deterministic verdict from arm strengths.

    Returns:
        {
            'label': str ('supports'|'challenges'|'mixed'|'insufficient'),
            'confidence': float (0-1),
            'arm_strength': {
                'support': float (0-1),
                'challenge': float (0-1),
                'balance': float
            }
        }
    """
```

**Formula:**
```python
# Per-item strength
strength = 0.55 * best_frame_score + 0.45 * item_grade * coverage_weight

# Arm strength (top 4 items with diminishing returns)
weights = [1.00, 0.70, 0.50, 0.35]

# Confidence
confidence = 0.4 * total + 0.4 * balance + 0.2 * count_factor

# Verdict decision
if (support_strength - challenge_strength) >= delta: label = "supports"
elif (challenge_strength - support_strength) >= delta: label = "challenges"
elif both_weak: label = "insufficient"
else: label = "mixed"
```

**Validation Test:** `tests/architecture/test_module_interfaces.py::test_p25_aggregate_verdict`

**Test Result:** ✅ PASSED

**Known Issues:**
- Missing source authority weighting (.gov vs .com)
- Missing source diversity consideration
- Missing internal consistency checks
- Missing coverage breadth analysis

---

### 2.6 rank/select.py - Candidate Ranking (Validated ✅)

**Function:** `rank_candidates`
**Location:** `intelligence/rank/select.py:24`

```python
def rank_candidates(
    items: List[Dict[str, Any]] | None = None,
    *,
    candidates: List[Dict[str, Any]] | None = None,
    claim_text: str | None = None,
    query: str | None = None,
    top_k: int | None = None,
    **kwargs: Any
) -> List[Dict[str, Any]]:
    """
    Per-arm ranking for evidence candidates.

    Groups by arm, ranks within each arm by score (desc),
    adds 'rank' field (1..N per arm), optionally truncates to top_k.

    Returns: Flat list [Arm A ranked items, Arm B ranked items]
    """
```

**Validation Test:** `tests/architecture/test_module_interfaces.py::test_rank_candidates`

**Test Result:** ✅ PASSED

---

### 2.7 analyze/stance.py - Stance Assessment (Validated ✅)

**Function:** `assess_stance`
**Location:** `intelligence/analyze/stance.py:44`

```python
def assess_stance(
    claim_text: str,
    item: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Heuristic stance assessment.

    Returns:
        {
            'stance': str ('support'|'refute'|'neutral'),
            'stance_score': int (0-100),
            'contradiction_flags': List[str],
            'notes': str
        }
    """
```

**Validation Test:** `tests/architecture/test_module_interfaces.py::test_assess_stance`

**Test Result:** ✅ PASSED

**Important:** This function is called in pipeline but **not used as a filter**. Items with 'neutral' or 'refute' stance for Arm A are not removed. This is a known issue.

---

### 2.8 strategy/plan_v2.py - Query Planning (Validated ✅)

**Function:** `build_search_plans_v2`
**Location:** `intelligence/strategy/plan_v2.py:115`

```python
def build_search_plans_v2(
    claim: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Input: claim dict with enrichment keys
    Output: normalized plan with two arms (A support, B challenge)

    Returns:
        {
            'version': 'v2',
            'arms': {
                'A': {'intent': 'support', 'queries': List[str]},
                'B': {'intent': 'challenge', 'queries': List[str]}
            },
            'meta': Dict
        }
    """
```

**Validation Test:** `tests/architecture/test_module_interfaces.py::test_plan_v2_build_search_plans`

**Test Result:** ✅ PASSED

---

## Section 3: Pipeline Flow

All pipeline flow documented with validation tests in `tests/architecture/test_pipeline_flow.py`.

### 3.1 Evidence Pipeline Sequence (Validated ✅)

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: Query Planning                                        │
│ strategy/plan_v2.py:build_search_plans_v2()                    │
│ Input: claim dict                                              │
│ Output: plan with Arm A (support) and Arm B (challenge) queries│
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: Evidence Gathering (ASYNC)                           │
│ gather/pipeline.py:build_evidence_for_claim()                 │
│ ├─ gather/online.py:run_plan() - Execute search               │
│ ├─ gather/pipeline.py:_exec_plan_for_arm() - Per arm          │
│ └─ Stamp each candidate with arm label ('A' or 'B')           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: Normalization & Deduplication                        │
│ gather/normalize.py:normalize_candidates()                     │
│ - Remove duplicates by URL                                     │
│ - Clean and standardize fields                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: Ranking                                              │
│ rank/select.py:rank_candidates()                              │
│ - Rank by search relevance score within each arm              │
│ - Add 'rank' field (1..N per arm)                             │
│ - Truncate to top_k per arm (default: 3)                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 5: Stance Enrichment                                    │
│ analyze/stance.py:assess_stance()                             │
│ - Add stance metadata (support/refute/neutral)                │
│ ⚠️  NOT USED AS FILTER (known issue)                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 6: Guardrails                                           │
│ policy/guardrails.py:apply_guardrails_to_arms()               │
│ - Enforce balance/diversity caps                              │
│ - Enforce minimum totals                                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 7: Content Enrichment (ASYNC)                           │
│ content/fetch_enrichment.py:enrich_items_with_content()       │
│ - Fetch full article text for each URL                        │
│ - Add: content, content_chars, content_hash, coverage          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 8: Evidence Analysis (Multiple Modules)                 │
│ ├─ P20: content/grade.py:attach_finding_to_item()            │
│ │   Add: item_grade (0-10 ⚠️ BUG), stance, finding           │
│ ├─ P23: content/semantic_read.py:analyze_item()              │
│ │   Add: findings[], item_grade (0-1, overwrites P20)        │
│ ├─ P24: content/semantic_frames.py:analyze_frames()          │
│ │   Add: frame_matches[], frame_confidence                    │
│ └─ P21: content/fullread.py:evaluate_full_evidence()         │
│     Add: grade_full (0-10), stance_full, credibility         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 9: Arm Aggregation                                      │
│ content/p25_aggregate.py:aggregate_verdict()                  │
│ - Calculate arm strengths (0-1 scale)                         │
│ - Determine verdict label (supports/challenges/mixed/insuff)  │
│ - Calculate confidence (0-1 scale)                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 10: Cross-Arm Consensus                                 │
│ consensus/metrics.py:compute_overlap_conflict()               │
│ - Calculate overlap_ratio (Jaccard on hosts & titles)         │
│ - Calculate conflict_score (opposing stance hints)            │
│ - Calculate stability (1 - conflict_score)                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 11: Final Verdict                                       │
│ score/labeling.py:score_from_evidence() + map_score_to_label()│
│ - Convert to 0-100 numeric score                              │
│ - Map to IFCN label (True/Mostly True/Mixed/etc)              │
└─────────────────────────────────────────────────────────────────┘
```

**Validation Test:** `tests/architecture/test_pipeline_flow.py::test_pipeline_flow_sequence`

**Test Result:** ✅ PASSED

**Key Imports in pipeline.py:**
- `from intelligence.gather import online`
- `from intelligence.gather.normalize import normalize_candidates`
- `from intelligence.rank.select import rank_candidates`
- `from intelligence.analyze.stance import assess_stance`
- `from intelligence.consensus.metrics import compute_overlap_conflict`
- `from intelligence.score.labeling import score_from_evidence, map_score_to_label`

---

## Section 4: Known Issues

All known issues documented with confirmation tests in `tests/architecture/test_known_issues.py`.

### 4.1 Scale Mismatch Bug (CRITICAL) ⚠️

**Issue:** P20 (grade.py) produces 0-10 scale, but P25 expects 0-1 scale

**Location:** `intelligence/content/grade.py:231`

```python
grade = round(min(score, 8.0) * (10.0/8.0), 2)  # Produces 0-10
```

**Impact:**
- If P23 doesn't run, P25 receives wrong scale (8.0 instead of 0.8)
- Verdict calculation severely biased
- Confidence artificially inflated

**Workaround:** P23 (semantic_read.py:196-202) overwrites `item_grade` with 0-1 scale

**Fix Required:** Change P20 to produce 0-1 scale directly:
```python
grade = round(min(score, 8.0) / 8.0, 3)  # Produces 0-1
```

**Validation Test:** `tests/architecture/test_known_issues.py::test_scale_bug_p20`

**Test Result:** ✅ BUG CONFIRMED - grade=6.25 (0-10 scale)

---

### 4.2 P23 Dependency on P20 (HIGH) ⚠️

**Issue:** P23 overwrites P20's `item_grade` to fix scale bug

**Location:** `intelligence/content/semantic_read.py:196-202`

**Impact:**
- Creates hidden dependency: P23 must run after P20
- If P23 is skipped, scale bug manifests
- Unclear which module "owns" item_grade

**Validation Test:** `tests/architecture/test_known_issues.py::test_p23_overwrites_p20_grade`

**Test Result:** ✅ CONFIRMED - P23 overwrites P20 value

---

### 4.3 Multiple Overlapping Grades (HIGH) ⚠️

**Issue:** Three different grades per evidence item

**Grades:**
1. `item_grade` (P23): 0-1 scale, from semantic read
2. `grade_full` (P21): 0-10 scale, from full-text read
3. `frame_confidence` (P24): 0-1 scale, from frame matching

**Location:** Multiple modules (P21, P23, P24)

**Impact:**
- Unclear which represents "evidence strength"
- P25 currently uses: `0.55 * frame_confidence + 0.45 * item_grade`
- `grade_full` is computed but not used in P25

**Question:** What should each grade represent?

**Validation Test:** `tests/architecture/test_known_issues.py::test_multiple_grades_per_item`

**Test Result:** ✅ CONFIRMED - Multiple grades exist

---

### 4.4 Missing Stance Filter (CRITICAL) ⚠️

**Issue:** Stance detection not used as filter during evidence curation

**Location:** Missing in `intelligence/gather/pipeline.py`

**Current Behavior:**
- `assess_stance()` is called and adds stance metadata
- Items marked "neutral" or "refute" for Arm A are NOT filtered out
- Items marked "neutral" or "support" for Arm B are NOT filtered out
- All items proceed to full processing

**Expected Behavior:**
```python
# After ranking, filter by stance alignment
if arm == 'A':
    items = [i for i in items if i['stance'] in ['support']]
elif arm == 'B':
    items = [i for i in items if i['stance'] in ['refute', 'challenge']]
# Discard 'neutral' and 'unrelated'
```

**Impact:**
- Off-mission evidence pollutes arms
- "Unrelated" items waste processing resources
- Arm strength calculations include irrelevant items

**Validation Test:** `tests/architecture/test_known_issues.py::test_missing_stance_filter`

**Test Result:** ✅ CONFIRMED - No stance filter exists

---

### 4.5 P25 Missing Aggregation Factors (HIGH) ⚠️

**Issue:** Arm comparison missing key quality factors

**Location:** `intelligence/content/p25_aggregate.py:45-71`

**Current Factors:**
- ✓ Item grades (item_grade, frame scores)
- ✓ Item count (with diminishing returns)
- ✓ Coverage weighting (full > partial > snippet_only)

**Missing Factors:**
- ✗ Source authority (.gov/.edu vs .com/blog)
- ✗ Source diversity (multiple domains vs single source)
- ✗ Internal consistency (do items agree with each other?)
- ✗ Coverage breadth (different aspects vs repeated point)

**Impact:**
- Blog post weighted same as .gov official document
- Single source repeated 5 times beats 3 diverse sources
- Conflicting evidence within arm not detected

**Validation Test:** `tests/architecture/test_known_issues.py::test_p25_missing_factors`

**Test Result:** ✅ CONFIRMED - .gov and blog treated equally

---

### 4.6 Query Generation Concerns (MEDIUM) ⚠️

**Issue:** Cannot validate if queries return on-mission results without live search

**Location:** `intelligence/strategy/plan_v2.py:115`

**Concerns:**
- Support queries may include challenge terms (e.g., "dispute", "contradict")
- Challenge queries may be too broad/generic
- No validation that queries align with arm objectives

**Mitigation:** Requires stance filter (Issue 4.4) to remove off-mission results

**Validation Test:** `tests/architecture/test_known_issues.py::test_query_generation_issues`

**Test Result:** ✅ DOCUMENTED - Cannot test without live search

---

### 4.7 R1/R2 Minimal Differentiation (MEDIUM) ⚠️

**Issue:** Dual researchers differ only by search provider and seed

**Current Differences:**
- R1: Brave search, seed=0, original query order
- R2: Google search, seed=42, shuffled query order

**Same:**
- Processing pipeline (P20-P25)
- Analysis thresholds
- Aggregation weights
- Interpretation logic

**Impact:**
- Not truly independent analysis
- 37.5% disagreement rate in baseline (why?)
- Unclear if disagreement is good (diverse perspectives) or bad (unreliable system)

**Question:** Should researchers differ in more than just search?

**Validation Test:** `tests/architecture/test_known_issues.py::test_r1_r2_minimal_difference`

**Test Result:** ✅ DOCUMENTED

---

## Section 5: Integration Contracts

Critical interfaces where modules must maintain compatibility.

### 5.1 Evidence Item Contract

**Provider:** `intelligence/gather/online.py`
**Consumer:** All downstream modules

**Guaranteed Fields (after gather):**
```python
{
    'url': str,
    'snippet': str,
    'arm': str,  # Must be 'A' or 'B'
    'score': float
}
```

**Optional Fields:** `title`, `provider`, `content_excerpt`

**Validation:** Must have `url`, `snippet`, and `arm` for downstream processing

---

### 5.2 Grade Scale Contract ⚠️

**Provider:** `intelligence/content/grade.py` (P20)
**Consumer:** `intelligence/content/p25_aggregate.py`

**Current Contract (BROKEN):**
- P20 produces: `item_grade` in 0-10 scale
- P25 expects: `item_grade` in 0-1 scale
- P23 fixes: Overwrites with 0-1 scale

**Required Fix:** P20 must produce 0-1 scale directly

**Validation:** Use `tests/architecture/test_known_issues.py::test_scale_bug_p20`

---

### 5.3 Arm Label Contract

**Provider:** `intelligence/gather/pipeline.py:_canonical_arm_label`
**Consumer:** All modules

**Contract:**
- Arm labels must be exactly 'A' or 'B' (uppercase, single character)
- Arm A = Support-seeking
- Arm B = Challenge-seeking

**Normalization Rules:**
1. If `name` starts with 'A' or 'B' → use that
2. If `intent` is 'support' → 'A'; if 'challenge' → 'B'
3. If index 0 → 'A'; if index 1 → 'B'

**Location:** `intelligence/gather/pipeline.py:16`

---

### 5.4 Plan Format Contract

**Provider:** `intelligence/strategy/plan_v2.py:build_search_plans_v2`
**Consumer:** `intelligence/gather/pipeline.py:build_evidence_for_claim`

**Contract:**
```python
{
    'version': 'v2',
    'arms': {
        'A': {'intent': 'support', 'queries': List[str]},
        'B': {'intent': 'challenge', 'queries': List[str]}
    }
}
```

**Alternative Format (also supported):**
```python
{
    'arms': [
        {'name': 'A', 'intent': 'support', 'queries': [...]},
        {'name': 'B', 'intent': 'challenge', 'queries': [...]}
    ]
}
```

**Validation:** `_extract_arm_defs()` handles both formats (`intelligence/gather/pipeline.py:78`)

---

### 5.5 Stance Values Contract

**Producers:** `grade.py`, `semantic_read.py`, `fullread.py`, `analyze/stance.py`
**Consumers:** P25, consensus modules

**Valid Values:**
- `'support'` - Evidence supports claim
- `'challenge'` / `'refute'` - Evidence contradicts claim
- `'mixed'` - Evidence has both supporting and contradicting elements
- `'unrelated'` - Evidence is not relevant to claim
- `'neutral'` - Evidence is neutral (used by analyze/stance.py)
- `'contextual_support'` - Evidence supports under different conditions (used by grade.py)

**Important:** Different modules use different subsets. Ensure downstream logic handles all values.

---

## Validation Tests

All tests are in `tests/architecture/` directory and can be run independently.

### Run All Tests

```bash
# Individual test files
python tests/architecture/test_data_structures.py
python tests/architecture/test_module_interfaces.py
python tests/architecture/test_pipeline_flow.py
python tests/architecture/test_known_issues.py

# Or use pytest
pytest tests/architecture/ -v
```

### Test Coverage

| Test File | Tests | Purpose |
|-----------|-------|---------|
| `test_data_structures.py` | 5 | Validates format of evidence items, claims, verdicts, frames |
| `test_module_interfaces.py` | 8 | Validates function signatures and return values |
| `test_pipeline_flow.py` | 3 | Validates import chains and call sequences |
| `test_known_issues.py` | 7 | Confirms documented bugs exist |

**Total Tests:** 23
**All tests passing:** ✅ YES

### Validation Philosophy

These tests are **architectural validators**, not unit tests:

1. **Prove documentation accuracy** - Tests fail if docs are wrong
2. **Use real code** - Import and call actual functions, no mocks
3. **Confirm bugs exist** - Known issues tests confirm bugs (not failures)
4. **Executable contracts** - Integration contracts tested with actual data

---

## Usage Notes for 11-Phase Improvement Plan

### Before Making Changes

1. **Read relevant section** in this document
2. **Run validation tests** to confirm current behavior
3. **Check known issues** - your change may fix or be affected by existing bugs

### After Making Changes

1. **Update this document** if data structures or interfaces change
2. **Update validation tests** to match new behavior
3. **Run all tests** to ensure no architectural drift
4. **Document new known issues** if bugs are discovered

### Preventing Architectural Drift

This document is the **single source of truth** for architecture across all Claude Code sessions.

**Session Handoff Protocol:**
1. Load this document at session start
2. Read relevant sections for planned work
3. Make changes
4. Update document and tests
5. Run validation suite
6. Commit with clear message

---

## Document Metadata

**Created:** 2025-10-17
**Last Updated:** 2025-10-17
**Validated Against:** post-mp-cleanup branch
**Test Suite Version:** 1.0
**Total Validation Tests:** 23
**All Tests Passing:** ✅ YES

**Next Review:** After completion of each phase in 11-phase improvement plan

---

**END OF DOCUMENT**
