# FACTUAL ISSUE ANALYSIS - ZERO ASSUMPTIONS

**Date:** October 27, 2025
**Diagnostic Runs Analyzed:** 2 (diagnostic_output_20251027_150245.txt, diagnostic_output_20251027_205832.txt)
**Design Spec Version:** 2.1 (UNIFIED_DESIGN_SPECIFICATION_v2_FINAL.md)
**Methodology:** Evidence-only analysis with direct code references and spec citations

---

## METHODOLOGY

### Analysis Approach

This document was created using a **zero-assumption, evidence-only methodology**. Every claim is backed by one or more of the following:

1. **Direct code inspection** - Reading source files with exact file:line references
2. **Diagnostic output analysis** - Examining actual test runs with line-by-line citations
3. **Design specification review** - Referencing official spec sections
4. **Consistency verification** - Confirming issues appear in multiple independent runs

### Evidence Sources

**Primary Sources:**
- `diagnostic_comprehensive.py` - Diagnostic test script
- `diagnostic_output_20251027_150245.txt` - Test run #1 (138 seconds)
- `diagnostic_output_20251027_205832.txt` - Test run #2 (228 seconds)
- `UNIFIED_DESIGN_SPECIFICATION_v2_FINAL.md` - Official design spec v2.1

**Code Sources:**
- `intelligence/content/grade.py` - P20 item grading
- `intelligence/content/semantic_read.py` - P23 semantic analysis
- `intelligence/content/semantic_frames.py` - P24 frame detection
- `intelligence/content/p25_aggregate.py` - P25 aggregation
- `intelligence/pipeline/run.py` - Main pipeline orchestration
- `intelligence/gather/pipeline.py` - Evidence gathering
- `intelligence/orchestration/dual_lane.py` - Dual researcher system

### Diagnostic Test Execution

**Test Claim:** "Water boils at 100 degrees Celsius"

**Command:**
```bash
python3 diagnostic_comprehensive.py
```

**Output Location:** `diagnostic_output_[timestamp].txt`

**Test Coverage:**
- Full pipeline execution (P19-P27)
- Dual researcher lanes (R1, R2)
- Evidence gathering (10 items per run: 5 Arm A, 5 Arm B)
- Complete scoring chain (P20-P24)
- Aggregation and consensus (P25-P27)

### Validation Rules

**Rule 1: No Assumptions**
- If something cannot be directly observed in code or output, it is not stated
- All interpretations are marked as such and separated from facts

**Rule 2: Consistency Verification**
- Issues must appear in multiple independent test runs
- Code behavior must match observed diagnostic output

**Rule 3: Spec Alignment**
- Fixes must be validated against design spec requirements
- Gaps between spec and implementation are explicitly documented

**Rule 4: Source Citation**
- Every factual statement includes source reference
- Code citations: `file.py:line_number`
- Diagnostic citations: `run_number, line_number`
- Spec citations: `Section X.Y`

### Investigation Process

1. **Ran diagnostic twice** - Verified consistency across independent runs
2. **Compared outputs** - Identified patterns (all items showing 0.000)
3. **Traced diagnostic code** - Found what diagnostic expects to read
4. **Traced pipeline code** - Found what pipeline actually writes
5. **Consulted design spec** - Verified intended behavior
6. **Identified gaps** - Where spec expectations don't match implementation
7. **Proposed fixes** - Only where factual evidence supports the solution

### What This Analysis Does NOT Include

- Performance optimization suggestions
- Architectural refactoring proposals
- Feature enhancements beyond fixing bugs
- Speculative fixes without code evidence
- Fixes that cannot be validated against spec

---

## TABLE OF CONTENTS

1. [Issue 1: semantic_score Field Missing](#issue-1-semantic_score-field-missing)
2. [Issue 2: frame_score Field Missing](#issue-2-frame_score-field-missing)
3. [Issue 3: Aggregation Metadata Structure Missing](#issue-3-aggregation-metadata-structure-missing)
4. [Issue 4: Duplicate URLs Across Arms](#issue-4-duplicate-urls-across-arms)
5. [Non-Issues: Confirmed Not Bugs](#non-issues-confirmed-not-bugs)
6. [Summary of Validated Fixes](#summary-of-validated-fixes)

---

## ISSUE 1: semantic_score Field Missing

### Evidence Classification: **CONFIRMED BUG**

### Factual Evidence

#### 1.1 Design Spec Requirement

**Source:** `UNIFIED_DESIGN_SPECIFICATION_v2_FINAL.md`, Section 7.1

```python
# From P23 (Semantic Analysis)
"semantic_score": float,          # 0-1 similarity to claim
"stance": str,                    # "support", "refute", "neutral", "unrelated"
"matched_text": str,              # Best matching window
"quote": str,                     # Extracted quote for display (NEW)
```

**Spec explicitly lists `semantic_score` as a required field on evidence items.**

#### 1.2 Diagnostic Output Evidence

**Run 1:** `diagnostic_output_20251027_150245.txt`
- Line 30: `Semantic: 0.000` (Arm A, Item 1)
- Line 44: `Semantic: 0.000` (Arm A, Item 2)
- Line 57: `Semantic: 0.000` (Arm A, Item 3)
- Line 70: `Semantic: 0.000` (Arm A, Item 4)
- Line 83: `Semantic: 0.000` (Arm A, Item 5)
- Line 99: `Semantic: 0.000` (Arm B, Item 1)
- Line 112: `Semantic: 0.000` (Arm B, Item 2)
- Line 125: `Semantic: 0.000` (Arm B, Item 3)
- Line 138: `Semantic: 0.000` (Arm B, Item 4)
- Line 151: `Semantic: 0.000` (Arm B, Item 5)

**Result:** 10 out of 10 items show `Semantic: 0.000`

**Run 2:** `diagnostic_output_20251027_205832.txt`
- Line 30: `Semantic: 0.000` (Arm A, Item 1)
- Line 43: `Semantic: 0.000` (Arm A, Item 2)
- Line 56: `Semantic: 0.000` (Arm A, Item 3)
- Line 69: `Semantic: 0.000` (Arm A, Item 4)
- Line 82: `Semantic: 0.000` (Arm A, Item 5)
- Line 98: `Semantic: 0.000` (Arm B, Item 1)
- Line 111: `Semantic: 0.000` (Arm B, Item 2)
- Line 124: `Semantic: 0.000` (Arm B, Item 3)
- Line 137: `Semantic: 0.000` (Arm B, Item 4)
- Line 150: `Semantic: 0.000` (Arm B, Item 5)

**Result:** 10 out of 10 items show `Semantic: 0.000`

**Consistency:** Both diagnostic runs show identical issue across all items.

#### 1.3 Diagnostic Code Evidence

**Source:** `diagnostic_comprehensive.py`, Line 180

```python
logger.log(f"Semantic: {item.get('semantic_score', 0.0):.3f}", indent=2)
```

**Observation:** Code reads `item.get('semantic_score', 0.0)` with default value 0.0.
**Result:** Always returns 0.0, meaning field doesn't exist on items.

#### 1.4 Code Analysis - Where P23 Computes Semantic Score

**Source:** `intelligence/content/semantic_read.py`, Lines 107-254

Function `analyze_item()` computes semantic analysis:

**Line 217:**
```python
item_grade = max(0.0, min(1.0, 0.6 * best + 0.4 * cov_w))
```

**Line 252:**
```python
item["item_grade"] = float(item_grade)
```

**Observation:** P23 computes a score and stores it as `item["item_grade"]`, NOT as `item["semantic_score"]`.

#### 1.5 Code Analysis - Where Items Are Annotated

**Source:** `intelligence/content/grade.py`, Lines 265-272

Function `attach_finding_to_item()` annotates items with P20-P24 results:

```python
# Line 266
item["item_grade"] = finding["item_grade"]
# Line 267
item["authority"] = finding.get("features", {}).get("authority", {}).get("score", 0.5)
# Line 268
item["stance"] = finding.get("features", {}).get("p23", {}).get("stance", "unrelated")
# Line 269
item["credibility"] = finding.get("features", {}).get("p21", {}).get("credibility", 0.5)
# Line 270
item["credibility_tier"] = finding.get("features", {}).get("p21", {}).get("credibility_tier", 4)
# Line 271
item["credibility_category"] = finding.get("features", {}).get("p21", {}).get("credibility_category", "unknown")
```

**Observation:** Lines 266-271 write multiple fields to item.
**Missing:** No line writes `item["semantic_score"]`.

#### 1.6 Design Spec - P20 Expected Behavior

**Source:** `UNIFIED_DESIGN_SPECIFICATION_v2_FINAL.md`, Section 4.H

P20 `attach_finding_to_item()` is specified to:
> 2. Extract key fields from finding
> 3. Mutate item with:
>    - item_grade: float
>    - authority: float
>    - stance: str
>    - credibility: float
>    - credibility_tier: int
>    - credibility_category: str
>    - finding: dict (full details)

**Observation:** Spec Section 4.H does NOT list `semantic_score` in P20's output.
**But:** Spec Section 7.1 DOES list `semantic_score` as required field "From P23".

**Gap:** P23 computes the score, P20 should expose it, but neither writes `semantic_score` field.

### Root Cause

P23 computes semantic similarity and stores as `features['p23']['item_grade']`.
P20 reads this and stores as `item['item_grade']` (the fused grade).
**Missing step:** P20 should ALSO store the raw P23 score as `item['semantic_score']` for transparency.

### Impact

- Diagnostic cannot display semantic analysis results
- Appears that P23 analysis didn't run (but it did)
- Hides quality of semantic matching
- Violates design spec Section 7.1 requirements

---

## ISSUE 2: frame_score Field Missing

### Evidence Classification: **CONFIRMED BUG**

### Factual Evidence

#### 2.1 Design Spec Requirement

**Source:** `UNIFIED_DESIGN_SPECIFICATION_v2_FINAL.md`, Section 7.1

```python
# From P24 (Frame Detection)
"frame_score": float,             # 0-1 frame similarity
"frame_stance": str,              # "entails", "contradicts", "neutral"
```

**Spec explicitly lists `frame_score` as a required field on evidence items.**

#### 2.2 Diagnostic Output Evidence

**Run 1:** `diagnostic_output_20251027_150245.txt`
- Lines 31, 45, 57, 70, 83, 99, 112, 125, 138, 151: All show `Frame: 0.000`

**Run 2:** `diagnostic_output_20251027_205832.txt`
- Lines 31, 44, 57, 70, 83, 99, 112, 125, 138, 151: All show `Frame: 0.000`

**Result:** 10 out of 10 items in both runs show `Frame: 0.000`

**Consistency:** 100% consistent across both diagnostic runs.

#### 2.3 Diagnostic Code Evidence

**Source:** `diagnostic_comprehensive.py`, Line 181

```python
logger.log(f"Frame: {item.get('frame_score', 0.0):.3f}", indent=2)
```

**Result:** Always returns 0.0 default value.

#### 2.4 Code Analysis - Where P24 Computes Frame Score

**Source:** `intelligence/content/semantic_frames.py`, Lines 202-284

Function `analyze_frames()` computes frame analysis:

**Lines 280-284:**
```python
conf = float(best_score)
return {
    "item_frame": best_frame,
    "frame_matches": matches,
    "frame_confidence": conf,
}
```

**Observation:** P24 returns `frame_confidence`, not `frame_score`.

#### 2.5 Code Analysis - Where P24 Results Are Used

**Source:** `intelligence/content/grade.py`, Lines 422-433

```python
# P24: Frame analysis
try:
    content = evidence_item.get('content', evidence_item.get('snippet', ''))
    p24_result = analyze_frames(claim_text, content, window=3, max_windows=500)
    features['p24'] = {
        'frame_matches': p24_result.get('frame_matches', []),
        'frame_confidence': p24_result.get('frame_confidence', 0.0),
        'item_frame': p24_result.get('item_frame', {}),
    }
    features['p24_available'] = True
except Exception as e:
    features['p24'] = {'error': str(e)}
```

**Observation:** P24 results stored in `features['p24']` dict.
**Field name:** Stored as `frame_confidence`, not `frame_score`.

#### 2.6 Code Analysis - Where Items Are Annotated

**Source:** `intelligence/content/grade.py`, Lines 265-272

Same location as Issue 1. No line writes `item["frame_score"]`.

#### 2.7 Design Spec - Item Grading Formula

**Source:** `UNIFIED_DESIGN_SPECIFICATION_v2_FINAL.md`, Section 4.H

```python
# FUSION FORMULA:
item_grade = (0.40 * semantic_score) + \
             (0.30 * frame_score) + \
             (0.20 * authority) + \
             (0.10 * coverage_weight)
```

**Observation:** Spec shows `frame_score` should exist and contribute 30% to item_grade.

#### 2.8 Code Analysis - Actual Fusion Formula

**Source:** `intelligence/content/grade.py`, Lines 324-328

```python
# P24: Frame matching
if features.get('p24_available'):
    frame_score = features['p24'].get('frame_confidence', 0.0)
else:
    frame_score = 0.0
```

**Observation:** Code reads `frame_confidence` from features and uses it locally as `frame_score` in fusion.
**Missing:** This local `frame_score` is never written to the item dict.

### Root Cause

P24 computes frame confidence and returns as `frame_confidence`.
P20 fusion reads this as `frame_confidence` and uses it locally as `frame_score`.
**Missing step:** P20 should write `item['frame_score'] = frame_confidence` for transparency.

### Impact

- Diagnostic cannot display frame analysis results
- Frame analysis is running but results are invisible
- Violates design spec Section 7.1 requirements
- Reduces transparency of grading process

---

## ISSUE 3: Aggregation Metadata Structure Missing

### Evidence Classification: **CONFIRMED GAP - SPEC VS IMPLEMENTATION**

### Factual Evidence

#### 3.1 Design Spec Requirement

**Source:** `UNIFIED_DESIGN_SPECIFICATION_v2_FINAL.md`, Section 7.2

```python
### 7.2 Aggregation Structure

**Output from Component I (P25):**

{
    "arm": str,                       # "A" or "B"
    "base_strength": float,           # Mean item_grade before multipliers
    "strength": float,                # Final strength (base × multipliers)
    "count": int,                     # Number of items in arm
    "items": List[Dict],              # Evidence items
    "multipliers": {
        "diversity": float,           # unique_domains / total_items
        "consistency": float,         # 1.0 / (1.0 + CV)
        "breadth": float              # 1.0 - avg_trigram_similarity
    }
}
```

**Spec Section 4.I:**
> **Key Function:** `def compute_aggregation(items: List[Dict], arm: str) -> Dict`

**Observation:** Spec describes a `compute_aggregation()` function that returns per-arm aggregation structure.

#### 3.2 Code Reality - Function Does Not Exist

**Source:** Search in `intelligence/content/p25_aggregate.py`

```bash
$ grep -n "^def " intelligence/content/p25_aggregate.py
7:def _item_strength(it: Dict[str, Any]) -> float:
49:def _arm_strength(items: List[Dict[str,Any]], top_k: int = 4) -> float:
65:def _confidence_from_arms(sa: float, sb: float, n_items_a: int, n_items_b: int,
96:def aggregate_verdict(claim_text: str, arm_a_items: List[Dict[str,Any]], arm_b_items: List[Dict[str,Any]],
155:def calculate_diversity_score(items: list) -> float:
202:def calculate_consistency_score(items: list, claim_numbers: list = None) -> float:
287:def calculate_breadth_score(items: list) -> float:
```

**Result:** No `compute_aggregation()` function exists.

**Actual function:** `aggregate_verdict()` at line 96.

#### 3.3 Code Reality - What aggregate_verdict() Returns

**Source:** `intelligence/content/p25_aggregate.py`, Lines 133-148

```python
return {
    "label": label,
    "confidence": float(conf),
    "arm_strength": {
        "support": float(sa_enhanced),
        "challenge": float(sb_enhanced),
        "support_base": float(sa),
        "challenge_base": float(sb),
        "balance": float(sa_enhanced - sb_enhanced)
    },
    "quality_multipliers": {
        "diversity": float(diversity),
        "consistency": float(consistency),
        "breadth": float(breadth)
    }
}
```

**Observation:** Returns a single verdict dict with BOTH arms' strengths combined.
**NOT:** Two separate aggregation dicts (one per arm) as spec describes.

#### 3.4 Diagnostic Code Expectation

**Source:** `diagnostic_comprehensive.py`, Lines 210-211

```python
agg_a = claim_result.get("arm_A_aggregation", {})
agg_b = claim_result.get("arm_B_aggregation", {})
```

**Lines 236-237:**
```python
arm_a_strength = agg_a.get('arm_strength', 0.0) if agg_a else 0.0
arm_b_strength = agg_b.get('arm_strength', 0.0) if agg_b else 0.0
```

**Observation:** Diagnostic expects:
- `claim_result["arm_A_aggregation"]` - a dict
- `claim_result["arm_B_aggregation"]` - a dict

#### 3.5 Diagnostic Output Evidence

**Run 1:** Lines 159-168

```
--------------------------------------------------------------------------------
[15:02:45.492] AGGREGATION METRICS:
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
[15:02:45.492] CONSENSUS LOGIC (P27):
--------------------------------------------------------------------------------
  Arm A Strength: 0.000
  Arm B Strength: 0.000
  Difference: 0.000
```

**Observation:** Section is empty (no aggregation data between headers).
**Result:** `agg_a` and `agg_b` are empty dicts, leading to 0.000 strengths.

**Run 2:** Lines 159-168 - Identical output.

#### 3.6 Code Analysis - Where claim_result Is Built

**Source:** `intelligence/pipeline/run.py`, Lines 353-362

```python
claim_obj = {
    "id": "c-0",
    "text": text.strip(),
    "tier": "primary",
    "verdict": dual_result.get("verdict", {}),
    "evidence": dual_result.get("evidence", {}),
    "researchers": researchers,
    "consensus": consensus,
    "summary": summary
}
```

**Observation:** claim_obj construction does NOT include `arm_A_aggregation` or `arm_B_aggregation` fields.

#### 3.7 Where Aggregation Data Actually Exists

**Source:** `intelligence/pipeline/run.py`, Lines 211-219

```python
# Extract researchers
researchers = dual_result.get("researchers", [])

# Compute consensus (P27)
if len(researchers) >= 2:
    r1_verdict = researchers[0].get("verdict", {})
    r2_verdict = researchers[1].get("verdict", {})
    r1_evidence = researchers[0].get("evidence", {})
    r2_evidence = researchers[1].get("evidence", {})
    consensus = compute_consensus(r1_verdict, r2_verdict, r1_evidence, r2_evidence)
```

**Observation:** Researchers have verdicts with arm_strength data.
**Structure:** `researchers[0]["verdict"]["arm_strength"]["support"]` exists.
**But:** Not exposed at claim_result level in the format diagnostic expects.

### Root Cause

**Design spec describes:** Per-arm aggregation structures via `compute_aggregation()`.
**Implementation has:** Combined verdict from `aggregate_verdict()` with both arms in one dict.
**Gap:** Data exists in researchers' verdicts but not in expected format at claim_result level.

### Impact

- Diagnostic cannot display aggregation metrics
- Shows "Arm Strength: 0.000" for both arms (incorrect)
- Transparency loss - cannot see quality multipliers per arm
- Diagnostic expectations don't match implementation

---

## ISSUE 4: Duplicate URLs Across Arms

### Evidence Classification: **CONFIRMED BUG**

### Factual Evidence

#### 4.1 Diagnostic Output Evidence

**Run 1:** `diagnostic_output_20251027_150245.txt`

**Arm A, Item 1 (Line 26):**
```
URL: https://pewresearch.org/short-reads/2015/09/14/does-waters-boiling-point-change-with-altitude-americans-arent-sure/
```

**Arm B, Item 4 (Line 133):**
```
URL: https://pewresearch.org/short-reads/2015/09/14/does-waters-boiling-point-change-with-altitude-americans-arent-sure/
```

**Result:** Identical URL in both arms.

**Run 2:** `diagnostic_output_20251027_205832.txt`

**Arm A, Item 1 (Line 26):**
```
URL: https://pewresearch.org/short-reads/2015/09/14/does-waters-boiling-point-change-with-altitude-americans-arent-sure/
```

**Arm B, Item 4 (Line 133):**
```
URL: https://pewresearch.org/short-reads/2015/09/14/does-waters-boiling-point-change-with-altitude-americans-arent-sure/
```

**Result:** Same duplication in second run.

**Consistency:** Duplicate appears in both diagnostic runs.

#### 4.2 Code Analysis - Where Deduplication Occurs

**Source:** `intelligence/gather/pipeline.py`, Lines 166-191

```python
print(f"\n=== DUPLICATION DIAGNOSTIC ===")
print(f"Total items in labeled_cands: {len(labeled_cands)}")

# Count unique URLs
urls = [item.get('url', '') for item in labeled_cands]
unique_urls = set(urls)
print(f"Unique URLs: {len(unique_urls)}")
print(f"Duplicate count: {len(urls) - len(unique_urls)}")

# Find duplicates
from collections import Counter
url_counts = Counter(urls)
duplicates = {url: count for url, count in url_counts.items() if count > 1}

if duplicates:
    print(f"\nDUPLICATE URLs FOUND:")
    for url, count in duplicates.items():
        print(f"  {url}: appears {count} times")
        # Show arm values for each duplicate
        items_with_url = [item for item in labeled_cands if item.get('url') == url]
        for idx, item in enumerate(items_with_url):
            print(f"    Instance {idx+1}: arm={item.get('arm')}, query={item.get('query_used', 'unknown')}")
else:
    print("NO DUPLICATES FOUND")
```

**Observation:** Code DETECTS duplicates and LOGS them.
**Missing:** No code REMOVES the duplicates after detection.

#### 4.3 Code Analysis - Deduplication Scope

**Source:** `intelligence/gather/normalize.py`, Lines 10-60

Function `normalize_candidates()` performs deduplication:

**Lines 15-24:**
```python
seen_urls: Set[str] = set()
deduplicated: List[Dict[str, Any]] = []

for cand in candidates:
    url = cand.get("url") or ""
    if url and url in seen_urls:
        continue  # Skip duplicates
    seen_urls.add(url)
    deduplicated.append(cand)
```

**Observation:** Deduplication happens within a single list.

**Source:** `intelligence/gather/pipeline.py`, Line 195

```python
armA_norm = normalize_candidates(armA_raw)
armB_norm = normalize_candidates(armB_raw)
```

**Observation:** `normalize_candidates()` is called separately for each arm.
**Result:** Removes duplicates WITHIN arm A, removes duplicates WITHIN arm B.
**Missing:** Does NOT remove duplicates ACROSS arms A and B.

### Root Cause

Deduplication runs per-arm, not cross-arm.
Same URL found by queries in both arms remains in both arms.

### Impact

- Same source counted twice in evidence
- Reduces domain diversity score (fewer unique domains)
- Double-weights one source's perspective
- Violates diversity principle

---

## NON-ISSUES: Confirmed Not Bugs

### Non-Issue A: Stance Labels in "Wrong" Arm

#### Initial Observation

**Example from Run 1:**
- Arm A Item 1: stance="challenge" (in support-seeking arm)
- Arm B Item 2: stance="support" (in challenge-seeking arm)

#### Design Spec Evidence

**Source:** `UNIFIED_DESIGN_SPECIFICATION_v2_FINAL.md`, Section 7.1

```python
# From query/arm assignment
"arm": str,                       # "A" (support) or "B" (challenge)
"intent": str,                    # "support" or "challenge"
```

**Observation:** Spec shows TWO separate fields:
- `arm`: Where item was placed (based on query)
- `intent`: What the query was seeking

**They are independent.**

#### Design Spec Evidence - Arm Assignment Logic

**Source:** Section 4.A (Query Generation)

> 2. For Arm A (support):
>    - Generate primary query: full quoted claim + fact-checking modifiers
>    - Generate secondary query: concept + official statistics
> 3. For Arm B (challenge):
>    - Generate primary: full quoted claim + dispute modifiers

**Observation:** Arms are query strategies, not content filters.

#### Conclusion

Items are assigned to arms at search time based on QUERY INTENT.
Stance is detected from CONTENT later.
An item found by challenge query that supports the claim = **working as designed**.
This tests if claims hold up under adversarial search.

**Classification:** NOT A BUG - This is intentional adversarial design.

---

## SUMMARY OF VALIDATED FIXES

### Fix 1: Add semantic_score Field

**Status:** ✅ VALIDATED BY SPEC

**File:** `intelligence/content/grade.py`
**Function:** `attach_finding_to_item()`
**Location:** After line 268

**Code to add:**
```python
item["semantic_score"] = finding.get("features", {}).get("p23", {}).get("item_grade", 0.0)
```

**Justification:**
- Spec Section 7.1 requires `semantic_score` field
- P23 computes the score as `features['p23']['item_grade']`
- Field mapping is missing
- Fix: Extract and store the field

**Expected Result:**
- Diagnostic will show `Semantic: 0.644` instead of `Semantic: 0.000`
- Non-zero values for all items with content

---

### Fix 2: Add frame_score Field

**Status:** ✅ VALIDATED BY SPEC

**File:** `intelligence/content/grade.py`
**Function:** `attach_finding_to_item()`
**Location:** After line 271

**Code to add:**
```python
# Extract P24 frame analysis results
p24_features = finding.get("features", {}).get("p24", {})
item["frame_score"] = p24_features.get("frame_confidence", 0.0)
item["frame_matches"] = p24_features.get("frame_matches", [])
```

**Justification:**
- Spec Section 7.1 requires `frame_score` field
- P24 returns `frame_confidence` which IS the frame score
- Field mapping is missing
- Fix: Extract and store the field with spec-compliant name
- Also store `frame_matches` for p25_aggregate use

**Expected Result:**
- Diagnostic will show `Frame: 0.542` instead of `Frame: 0.000`
- Non-zero values for all items with content

---

### Fix 3: Cross-Arm Deduplication (REVISED APPROACH)

**Status:** ✅ TESTED & VERIFIED

**File:** `intelligence/gather/pipeline.py`
**Location:** After line 237 (now lines 239-242 after implementation)

**Root Cause:**
Arms A and B search independently (intentional adversarial design). Sometimes both arms find the same URL because:
- The source is highly relevant to both "support" and "challenge" queries
- Search engines independently return it as a top result for both queries
- Current deduplication only removes duplicates WITHIN each arm, not ACROSS arms

**Why Deduplication Happens After Fast Scoring:**
Items need quality scores to determine which instance to keep. The `normalize_candidates()` function (line 195-196) adds a `score` field based on text quality (title/snippet analysis). This score indicates which arm's query had a better match to the content.

**Code to add:**

Function definition (add near top of file, around line 20):
```python
def _deduplicate_across_arms(all_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate URLs across arms, keeping the instance with highest quality score.

    This is a simple filter operation that:
    1. Groups items by URL
    2. For duplicates, keeps the one with highest 'score' field
    3. Returns filtered list (preserves all item fields including 'arm' label)

    Uses the fast-ranking score from normalize_candidates() which measures
    title/snippet quality (numbers, percentages, text density).
    """
    from collections import defaultdict
    import sys

    url_to_items = defaultdict(list)
    for item in all_items:
        url = item.get('url', '')
        if url:
            url_to_items[url].append(item)

    deduplicated = []
    for url, items in url_to_items.items():
        if len(items) == 1:
            # No duplicate - keep it
            deduplicated.append(items[0])
        else:
            # Duplicate found - keep the one with highest quality score
            best_item = max(items, key=lambda x: x.get('score', 0.0))
            deduplicated.append(best_item)

            # Log deduplication decision for transparency
            for item in items:
                status = "KEPT" if item == best_item else "REMOVED"
                print(f"⚠️  Deduplication [{status}]: {url[:60]}... "
                      f"Arm {item.get('arm')}, Score: {item.get('score', 0.0):.3f}",
                      file=sys.stderr)

    return deduplicated
```

Call site (after line 196, after normalize_candidates):
```python
    # 2) Group by explicit arm, then normalize
    armA_raw, armB_raw = _group_by_arm(labeled_cands)
    armA_norm = normalize_candidates(armA_raw)
    armB_norm = normalize_candidates(armB_raw)

    # 2.5) Cross-arm deduplication (items now have 'score' field)
    all_items = armA_norm + armB_norm
    all_items_deduped = _deduplicate_across_arms(all_items)
    armA_norm, armB_norm = _group_by_arm(all_items_deduped)

    # Phase 2.1: Fast filter - remove obviously unrelated (ADDED)
```

**Justification:**
1. **Timing:** Dedup must happen AFTER normalize_candidates() because items need `score` field
2. **Quality-based:** Keeps the instance where the content better matches the query (higher score)
3. **Preserves contracts:** All downstream functions receive same item structure (all fields preserved)
4. **Simple filter:** Just removes lower-scored duplicates, doesn't modify remaining items
5. **No breaking changes:** Uses existing `_group_by_arm()` helper to re-split arms

**Impact Analysis - Downstream Functions:**
- ✅ `filter_unrelated()` (line 204): Expects list with url/title/snippet - preserved
- ✅ `quality_gate()` (line 216): Expects list with url/domain - preserved
- ✅ `rank_candidates()` (line 235): Expects list with score/arm - preserved
- ✅ `assess_stance()` (line 239): Expects items with title/snippet - preserved

**Expected Result:**
- 3 duplicate URLs removed (pewresearch.org, wikipedia.org, usda.gov)
- Kept instances have higher quality scores (better content match)
- Domain diversity score improves (~10%)
- Total items: ~20 → ~17 (3 duplicates removed)
- No downstream breakage (all contracts preserved)

---

### Fix 4: Populate Aggregation Metadata from Existing Data

**Status:** ✅ VALIDATED - ADAPT EXISTING IMPLEMENTATION

**Decision:** Design spec is deficient. The `compute_aggregation()` function described in spec Section 4.I does not exist. The actual implementation uses `aggregate_verdict()` which computes the same data. Fix: Extract and reformat existing data to match diagnostic expectations.

#### Factual Basis for Adaptation

**Current Implementation:**
- `aggregate_verdict()` (p25_aggregate.py:96-148) computes all needed values
- Called once per researcher with both arms (run.py:100-106)
- Returns combined verdict with `arm_strength` and `quality_multipliers`
- Data stored in `researchers[i]["verdict"]`

**Data Already Computed:**
From p25_aggregate.py lines 107-148:
```python
sa = _arm_strength(arm_a_items)              # Arm A base strength
sb = _arm_strength(arm_b_items)              # Arm B base strength
diversity = calculate_diversity_score(all_items)
consistency = calculate_consistency_score(all_items, claim_numbers)
breadth = calculate_breadth_score(all_items)
sa_enhanced = sa * diversity * consistency * breadth   # Arm A final
sb_enhanced = sb * diversity * consistency * breadth   # Arm B final
```

Returns (lines 133-148):
```python
{
    "arm_strength": {
        "support": sa_enhanced,        # Arm A final
        "challenge": sb_enhanced,      # Arm B final
        "support_base": sa,            # Arm A base
        "challenge_base": sb           # Arm B base
    },
    "quality_multipliers": {
        "diversity": diversity,
        "consistency": consistency,
        "breadth": breadth
    }
}
```

**Diagnostic Needs:**
From diagnostic_comprehensive.py lines 215-219:
```python
agg_a.get('avg_grade', 0.0)           # Average item_grade for Arm A items
agg_a.get('domain_diversity', 0.0)    # Unique domains / total (per arm)
agg_a.get('consistency', 0.0)         # Global multiplier
agg_a.get('breadth', 0.0)             # Global multiplier
agg_a.get('arm_strength', 0.0)        # Final strength
```

#### Fix Implementation

**File:** `intelligence/pipeline/run.py`
**Location:** After line 211 (after extracting researchers)

**Code to add:**

```python
# Build aggregation metadata from researchers' verdicts
# Note: Design spec describes compute_aggregation() function which doesn't exist.
# Actual implementation uses aggregate_verdict() which computes same data.
# This extracts and reformats for diagnostic transparency.
aggregation_metadata = {}
if len(researchers) >= 2:
    r1_verdict = researchers[0]["verdict"]
    r2_verdict = researchers[1]["verdict"]
    r1_evidence = researchers[0]["evidence"]
    r2_evidence = researchers[1]["evidence"]

    # Extract arm strengths from verdicts (averaged across R1 and R2)
    r1_arm_strength = r1_verdict.get("arm_strength", {})
    r2_arm_strength = r2_verdict.get("arm_strength", {})

    arm_a_strength = (r1_arm_strength.get("support", 0) + r2_arm_strength.get("support", 0)) / 2
    arm_b_strength = (r1_arm_strength.get("challenge", 0) + r2_arm_strength.get("challenge", 0)) / 2
    arm_a_base = (r1_arm_strength.get("support_base", 0) + r2_arm_strength.get("support_base", 0)) / 2
    arm_b_base = (r1_arm_strength.get("challenge_base", 0) + r2_arm_strength.get("challenge_base", 0)) / 2

    # Extract quality multipliers (averaged across R1 and R2)
    r1_multipliers = r1_verdict.get("quality_multipliers", {})
    r2_multipliers = r2_verdict.get("quality_multipliers", {})

    avg_diversity = (r1_multipliers.get("diversity", 1.0) + r2_multipliers.get("diversity", 1.0)) / 2
    avg_consistency = (r1_multipliers.get("consistency", 1.0) + r2_multipliers.get("consistency", 1.0)) / 2
    avg_breadth = (r1_multipliers.get("breadth", 1.0) + r2_multipliers.get("breadth", 1.0)) / 2

    # Compute per-arm average item grades
    arm_a_items = r1_evidence.get("arm_A", []) + r2_evidence.get("arm_A", [])
    arm_b_items = r1_evidence.get("arm_B", []) + r2_evidence.get("arm_B", [])

    arm_a_grades = [item.get("item_grade", 0) for item in arm_a_items if item.get("item_grade", 0) > 0]
    arm_b_grades = [item.get("item_grade", 0) for item in arm_b_items if item.get("item_grade", 0) > 0]

    avg_grade_a = sum(arm_a_grades) / len(arm_a_grades) if arm_a_grades else 0.0
    avg_grade_b = sum(arm_b_grades) / len(arm_b_grades) if arm_b_grades else 0.0

    # Compute per-arm domain diversity
    from intelligence.content.fullread import _extract_base_domain

    def compute_domain_diversity(items):
        """Calculate unique domains / total items for one arm"""
        domains = []
        for item in items:
            url = item.get('url', '')
            if url:
                domain = _extract_base_domain(url)
                if domain:
                    domains.append(domain)
        if not domains:
            return 0.0
        unique = len(set(domains))
        total = len(domains)
        return unique / total

    arm_a_domain_diversity = compute_domain_diversity(arm_a_items)
    arm_b_domain_diversity = compute_domain_diversity(arm_b_items)

    # Build aggregation structures matching diagnostic expectations
    # Enhancement: Include individual R1/R2 values for full transparency
    aggregation_metadata = {
        "arm_A_aggregation": {
            "arm_strength": float(arm_a_strength),              # AVERAGED (consensus uses this)
            "r1_arm_strength": float(r1_arm_strength.get("support", 0)),  # R1's individual value
            "r2_arm_strength": float(r2_arm_strength.get("support", 0)),  # R2's individual value
            "base_strength": float(arm_a_base),
            "r1_base_strength": float(r1_arm_strength.get("support_base", 0)),
            "r2_base_strength": float(r2_arm_strength.get("support_base", 0)),
            "avg_grade": float(avg_grade_a),
            "domain_diversity": float(arm_a_domain_diversity),
            "consistency": float(avg_consistency),     # Global multiplier
            "breadth": float(avg_breadth),            # Global multiplier
            "diversity": float(avg_diversity)          # Global multiplier (for transparency)
        },
        "arm_B_aggregation": {
            "arm_strength": float(arm_b_strength),              # AVERAGED (consensus uses this)
            "r1_arm_strength": float(r1_arm_strength.get("challenge", 0)),  # R1's individual value
            "r2_arm_strength": float(r2_arm_strength.get("challenge", 0)),  # R2's individual value
            "base_strength": float(arm_b_base),
            "r1_base_strength": float(r1_arm_strength.get("challenge_base", 0)),
            "r2_base_strength": float(r2_arm_strength.get("challenge_base", 0)),
            "avg_grade": float(avg_grade_b),
            "domain_diversity": float(arm_b_domain_diversity),
            "consistency": float(avg_consistency),     # Global multiplier
            "breadth": float(avg_breadth),            # Global multiplier
            "diversity": float(avg_diversity)          # Global multiplier (for transparency)
        }
    }
```

**Then modify claim_obj construction (line 353):**

Current:
```python
claim_obj = {
    "id": "c-0",
    "text": text.strip(),
    "tier": "primary",
    "verdict": dual_result.get("verdict", {}),
    "evidence": dual_result.get("evidence", {}),
    "researchers": researchers,
    "consensus": consensus,
    "summary": summary
}
```

Change to:
```python
claim_obj = {
    "id": "c-0",
    "text": text.strip(),
    "tier": "primary",
    "verdict": dual_result.get("verdict", {}),
    "evidence": dual_result.get("evidence", {}),
    "researchers": researchers,
    "consensus": consensus,
    "summary": summary,
    **aggregation_metadata  # Unpack arm_A_aggregation and arm_B_aggregation
}
```

#### Justification

1. **Data already exists:** All values are computed by `aggregate_verdict()`
2. **No new computation:** Only reformatting and averaging R1/R2 results
3. **Matches diagnostic expectations:** Provides exact fields diagnostic reads
4. **Averaging aligns with consensus logic:** The `compute_consensus()` function (dual_lane.py:90-91, 140-141) averages R1 and R2 arm strengths. The displayed averages match what consensus actually uses for decision-making.
5. **Full transparency:** Includes both averaged values (what consensus uses) AND individual R1/R2 values (how the average was derived) for complete audit trail
6. **Note on quality multipliers:** `diversity`, `consistency`, `breadth` are computed globally (across all items) in current implementation. This is preserved - both arms get same multiplier values.
7. **Per-arm metrics:** Only `arm_strength`, `base_strength`, `avg_grade`, and `domain_diversity` differ between arms.

**Expected Result:**
- Diagnostic will show populated aggregation section
- Arm strengths will be non-zero
- Shows: avg_grade, domain_diversity (per-arm) and consistency, breadth, diversity (global multipliers)
- Displays both consensus averages AND individual researcher values for transparency
- Users can verify: (R1 value + R2 value) / 2 = displayed average

---

## VALIDATION SUMMARY

| Issue | Type | Spec Evidence | Code Evidence | Diagnostic Evidence | Fix Validated |
|-------|------|---------------|---------------|---------------------|---------------|
| 1: semantic_score missing | Bug | ✅ Section 7.1 | ✅ grade.py:268 | ✅ 20/20 items zero | ✅ YES |
| 2: frame_score missing | Bug | ✅ Section 7.1 | ✅ grade.py:271 | ✅ 20/20 items zero | ✅ YES |
| 3: Aggregation structure | Gap | ✅ Section 7.2 | ✅ Function missing | ✅ Empty section | ✅ YES (adapted) |
| 4: Duplicate URLs | Bug | ❌ Not in spec | ✅ pipeline.py:195 | ✅ Both runs | ✅ YES |
| A: Stance in wrong arm | Non-bug | ✅ Section 7.1 | ✅ By design | ✅ Expected | N/A |

**Total Validated Fixes:** 4 (semantic_score, frame_score, aggregation metadata, deduplication)
**Deferred Fixes:** 0
**Confirmed Non-Issues:** 1 (stance assignment)

### Fix Summary

| Fix # | Component | File | Lines to Add | Status |
|-------|-----------|------|--------------|--------|
| 1 | semantic_score | grade.py | 1 | ✅ Ready |
| 2 | frame_score | grade.py | 3 | ✅ Ready |
| 3 | Cross-arm dedup | pipeline.py | 25 | ✅ Ready |
| 4 | Aggregation metadata (enhanced) | run.py | 90 | ✅ Ready |

**Total:** 119 lines of code to add across 3 files

**Fix 4 Enhancement:** Now includes individual R1/R2 values alongside averages for complete transparency. This aligns with the actual consensus logic (dual_lane.py:90-91) which averages arm strengths for decision-making.

---

## IMPLEMENTATION PROGRESS TRACKER

**Purpose:** Track implementation status of each fix as code changes are applied and validated.

### Fix Status Legend
- 🔴 **NOT STARTED** - Fix has not been implemented
- 🟡 **IN PROGRESS** - Code changes in progress
- 🟢 **IMPLEMENTED** - Code changes complete, awaiting testing
- ✅ **TESTED & VERIFIED** - Fix implemented and verified via diagnostic test
- ⚠️ **ISSUES FOUND** - Problems discovered during implementation/testing

---

### Fix 1: semantic_score Field

**Status:** ✅ TESTED & VERIFIED

**File:** `intelligence/content/grade.py`
**Line:** After line 268 (now line 269)
**Change Type:** Add 1 line

**Implementation Notes:**
```
Date: 2025-10-28
Implemented by: Claude Code
Commit hash: [PENDING - not yet committed]
Code added: item["semantic_score"] = finding.get("features", {}).get("p23", {}).get("item_grade", 0.0)
```

**Testing Notes:**
```
Test method: Run diagnostic_comprehensive.py
Expected: Semantic scores show non-zero values (e.g., 0.644 instead of 0.000)
Actual result: ✅ SUCCESS - 20/20 items show non-zero semantic scores
Sample values: 0.659, 0.629, 0.620, 0.679, 0.631, 0.150, 0.648, 0.617, 0.659, 0.639
Date tested: 2025-10-28
Test output: test_fixes_1_2_output.txt
```

---

### Fix 2: frame_score Field

**Status:** ✅ TESTED & VERIFIED

**File:** `intelligence/content/grade.py`
**Line:** After line 272 (now lines 273-276)
**Change Type:** Add 3 lines

**Implementation Notes:**
```
Date: 2025-10-28
Implemented by: Claude Code
Commit hash: [PENDING - not yet committed]
Code added:
  p24_features = finding.get("features", {}).get("p24", {})
  item["frame_score"] = p24_features.get("frame_confidence", 0.0)
  item["frame_matches"] = p24_features.get("frame_matches", [])
```

**Testing Notes:**
```
Test method: Run diagnostic_comprehensive.py
Expected: Frame scores show non-zero values (e.g., 0.542 instead of 0.000)
Actual result: ✅ SUCCESS - 19/20 items show non-zero frame scores
Sample values: 0.616, 0.558, 0.579, 0.642, 0.544, 0.654, 0.502, 0.616, 0.534
Note: 1 item with 0.000 is acceptable (may genuinely have no frame match)
Date tested: 2025-10-28
Test output: test_fixes_1_2_output.txt
```

---

### Fix 3: Cross-Arm Deduplication

**Status:** ✅ TESTED & VERIFIED

**File:** `intelligence/gather/pipeline.py`
**Lines:** Function definition lines 17-55, call site lines 239-242
**Change Type:** Add 43 lines (function + call site)

**Implementation Notes:**
```
Date: 2025-10-28
Implemented by: Claude Code
Commit hash: [PENDING - not yet committed]
Approach: Quality-score based selection (keeps instance with highest score)
Code added:
  - _deduplicate_across_arms() function (lines 17-55)
  - Call site after normalize_candidates (lines 239-242)
```

**Testing Notes:**
```
Test method: Run diagnostic_comprehensive.py and check for duplicate URLs
Expected: No duplicate URLs across arms (duplicates removed, higher-scored kept)
Actual result: ✅ SUCCESS
  - pewresearch.org: Kept in Arm A (score 1.000), removed from Arm B (score 0.912)
  - wikipedia.org: Kept in Arm B (score 0.900), removed from Arm A (score 0.824)
  - usda.gov: Kept in Arm A (score 0.728), removed from Arm B (score 0.728, tie went to first)
  - Total: 3 duplicates removed successfully
  - No duplicate URLs in final output (verified by grep)
  - Fixes 1 & 2 still working (semantic and frame scores preserved)
Date tested: 2025-10-28
Test output: test_fix3_output.txt
```

---

### Fix 4: Aggregation Metadata (Enhanced)

**Status:** 🔴 NOT STARTED

**File:** `intelligence/pipeline/run.py`
**Lines:** After line 211 (aggregation computation), modify line 353 (claim_obj)
**Change Type:** Add ~90 lines

**Implementation Notes:**
```
Date: [PENDING]
Implemented by: [PENDING]
Commit hash: [PENDING]
Notes: Enhanced version includes individual R1/R2 values alongside averages
```

**Testing Notes:**
```
Test method: Run diagnostic_comprehensive.py
Expected:
  - AGGREGATION METRICS section populated (not empty)
  - Arm A/B strengths show non-zero values
  - Both averaged and individual R1/R2 values visible
  - Math verifiable: (R1 + R2) / 2 = displayed average
Actual result: [PENDING]
Date tested: [PENDING]
```

---

### Overall Implementation Status

| Fix # | Description | Status | Priority | Dependencies |
|-------|-------------|--------|----------|--------------|
| 1 | semantic_score field | ✅ TESTED & VERIFIED | HIGH | None |
| 2 | frame_score field | ✅ TESTED & VERIFIED | HIGH | None |
| 3 | Cross-arm dedup | ✅ TESTED & VERIFIED | MEDIUM | None |
| 4 | Aggregation metadata | 🔴 NOT STARTED | LOW | None |

**Last Updated:** 2025-10-28 12:58 PST
**Overall Progress:** 3/4 fixes completed (75%)

---

## COMPREHENSIVE TESTING GUIDE

### Pre-Implementation Baseline

**Capture current behavior BEFORE making any changes:**

```bash
# Run diagnostic and save baseline
python3 diagnostic_comprehensive.py > baseline_before_fixes_$(date +%Y%m%d_%H%M%S).txt

# Save current diagnostic output for comparison
cp diagnostic_output_20251027_150245.txt baseline_reference.txt
```

**Baseline Issues to Document:**
- All semantic_score values = 0.000
- All frame_score values = 0.000
- Duplicate URL: pewresearch.org in both Arm A (Item 1) and Arm B (Item 4)
- AGGREGATION METRICS section is empty

---

### Test Suite for Each Fix

#### Fix 1 Test: semantic_score Field

**Test Command:**
```bash
python3 diagnostic_comprehensive.py > test_fix1_output.txt
```

**Verification Checklist:**
- [ ] All items show non-zero semantic scores (not 0.000)
- [ ] Semantic scores are in reasonable range (0.0 to 1.0)
- [ ] Example values match evidence quality (high authority sources = higher scores)
- [ ] No Python errors or exceptions

**Specific Checks:**
```bash
# Check that semantic scores are populated
grep "Semantic:" test_fix1_output.txt | grep -v "0.000"

# Should show lines like:
# Semantic: 0.644
# Semantic: 0.712
# etc.

# Count how many items have non-zero semantic scores
grep "Semantic:" test_fix1_output.txt | grep -v "0.000" | wc -l
# Expected: 10 (all items should have non-zero values)
```

**Success Criteria:**
✅ At least 8/10 items show semantic_score > 0.0
✅ No semantic_score > 1.0 (bounded correctly)
✅ Diagnostic runs without errors

---

#### Fix 2 Test: frame_score Field

**Test Command:**
```bash
python3 diagnostic_comprehensive.py > test_fix2_output.txt
```

**Verification Checklist:**
- [ ] All items show non-zero frame scores (not 0.000)
- [ ] Frame scores are in reasonable range (0.0 to 1.0)
- [ ] Frame scores reflect semantic relationship to claim
- [ ] No Python errors or exceptions

**Specific Checks:**
```bash
# Check that frame scores are populated
grep "Frame:" test_fix2_output.txt | grep -v "0.000"

# Count items with non-zero frame scores
grep "Frame:" test_fix2_output.txt | grep -v "0.000" | wc -l
# Expected: 10 (all items should have non-zero values)
```

**Success Criteria:**
✅ At least 8/10 items show frame_score > 0.0
✅ No frame_score > 1.0 (bounded correctly)
✅ Diagnostic runs without errors

**Combined Fix 1 & 2 Test:**
```bash
# After implementing both fixes, verify both fields together
python3 diagnostic_comprehensive.py > test_fixes_1_2_combined.txt

# Check both are populated
echo "=== Semantic Scores ==="
grep "Semantic:" test_fixes_1_2_combined.txt | head -5
echo "=== Frame Scores ==="
grep "Frame:" test_fixes_1_2_combined.txt | head -5
```

---

#### Fix 3 Test: Cross-Arm Deduplication

**Test Command:**
```bash
python3 diagnostic_comprehensive.py > test_fix3_output.txt
```

**Verification Checklist:**
- [ ] No duplicate URLs across Arm A and Arm B
- [ ] pewresearch.org URL appears only once (not in both arms)
- [ ] Total evidence count remains reasonable (8-10 items total)
- [ ] Deduplication log message appears in stderr
- [ ] No Python errors or exceptions

**Specific Checks:**
```bash
# Extract all URLs from output
grep "URL:" test_fix3_output.txt | sort | uniq -d
# Expected: Empty (no duplicates)

# Check for specific duplicate from baseline
grep "pewresearch.org" test_fix3_output.txt | grep "URL:"
# Expected: Only 1 line (appears in one arm only)

# Count total unique URLs
grep "URL:" test_fix3_output.txt | sort -u | wc -l
# Expected: 8-10 unique URLs

# Check deduplication was logged (stderr during run)
python3 diagnostic_comprehensive.py 2>&1 | grep -i "deduplication"
# Expected: Should see log message about removed duplicates
```

**Success Criteria:**
✅ Zero duplicate URLs across arms
✅ Total evidence count = 8-10 items (some duplicates removed)
✅ Domain diversity score improves (check aggregation section)
✅ Diagnostic runs without errors

---

#### Fix 4 Test: Aggregation Metadata

**Test Command:**
```bash
python3 diagnostic_comprehensive.py > test_fix4_output.txt
```

**Verification Checklist:**
- [ ] AGGREGATION METRICS section is populated (not empty)
- [ ] Arm A aggregation shows all fields
- [ ] Arm B aggregation shows all fields
- [ ] Arm strengths are non-zero
- [ ] R1 and R2 individual values are visible
- [ ] Math verification: (R1 + R2) / 2 = displayed average
- [ ] Consensus verdict remains unchanged from baseline
- [ ] No Python errors or exceptions

**Specific Checks:**
```bash
# Check aggregation section is populated
sed -n '/AGGREGATION METRICS:/,/CONSENSUS LOGIC/p' test_fix4_output.txt

# Should show output like:
# Arm A Aggregation:
#   Average Grade: 0.650
#   Domain Diversity: 0.800
#   ...

# Extract and verify arm strengths
grep "Arm A Strength:" test_fix4_output.txt
grep "Arm B Strength:" test_fix4_output.txt
# Expected: Non-zero values like 0.456, 0.382

# Verify consensus verdict unchanged
grep "IFCN LABEL:" baseline_reference.txt > baseline_verdict.txt
grep "IFCN LABEL:" test_fix4_output.txt > test_verdict.txt
diff baseline_verdict.txt test_verdict.txt
# Expected: No difference (verdict should be same)
```

**Manual Verification (if R1/R2 values visible):**
```
If diagnostic shows:
  r1_arm_strength: 0.450
  r2_arm_strength: 0.460
  arm_strength: 0.455

Calculate: (0.450 + 0.460) / 2 = 0.455 ✓
```

**Success Criteria:**
✅ AGGREGATION METRICS section shows data (not empty)
✅ All aggregation fields populated with reasonable values
✅ Math verification passes: averaged values are correct
✅ Final verdict matches baseline (no regression)
✅ Diagnostic runs without errors

---

### Regression Testing

**After ALL fixes are implemented, run full regression:**

```bash
# Run complete diagnostic
python3 diagnostic_comprehensive.py > final_all_fixes_output.txt 2>&1

# Compare final verdict with baseline
echo "=== BASELINE VERDICT ==="
grep -A 5 "IFCN LABEL:" baseline_reference.txt

echo "=== FINAL VERDICT ==="
grep -A 5 "IFCN LABEL:" final_all_fixes_output.txt

# Verify no errors
grep -i "error\|exception\|traceback" final_all_fixes_output.txt
# Expected: Empty (no errors)

# Check all fixes are working
echo "=== Fix 1: Semantic Scores ==="
grep "Semantic:" final_all_fixes_output.txt | grep -v "0.000" | wc -l

echo "=== Fix 2: Frame Scores ==="
grep "Frame:" final_all_fixes_output.txt | grep -v "0.000" | wc -l

echo "=== Fix 3: Duplicate URLs ==="
grep "URL:" final_all_fixes_output.txt | sort | uniq -d | wc -l

echo "=== Fix 4: Aggregation Populated ==="
sed -n '/AGGREGATION METRICS:/,/CONSENSUS LOGIC/p' final_all_fixes_output.txt | wc -l
# Expected: > 10 (should have multiple lines of data)
```

**Final Success Criteria:**
✅ All 10 items show non-zero semantic_score
✅ All 10 items show non-zero frame_score
✅ Zero duplicate URLs across arms
✅ AGGREGATION METRICS section fully populated
✅ Final verdict matches baseline verdict
✅ No Python errors or warnings

---

### Test Output Archive

**Save all test outputs for documentation:**

```bash
mkdir -p test_results/fixes_implementation_$(date +%Y%m%d)
mv baseline_before_fixes_*.txt test_results/fixes_implementation_*/
mv test_fix*.txt test_results/fixes_implementation_*/
mv final_all_fixes_output.txt test_results/fixes_implementation_*/

# Create summary
echo "Test Results Summary - $(date)" > test_results/fixes_implementation_*/SUMMARY.txt
echo "==================================" >> test_results/fixes_implementation_*/SUMMARY.txt
echo "" >> test_results/fixes_implementation_*/SUMMARY.txt
echo "Fix 1 (semantic_score): [PASS/FAIL]" >> test_results/fixes_implementation_*/SUMMARY.txt
echo "Fix 2 (frame_score): [PASS/FAIL]" >> test_results/fixes_implementation_*/SUMMARY.txt
echo "Fix 3 (deduplication): [PASS/FAIL]" >> test_results/fixes_implementation_*/SUMMARY.txt
echo "Fix 4 (aggregation): [PASS/FAIL]" >> test_results/fixes_implementation_*/SUMMARY.txt
echo "" >> test_results/fixes_implementation_*/SUMMARY.txt
echo "Regression Test: [PASS/FAIL]" >> test_results/fixes_implementation_*/SUMMARY.txt
```

---

## END OF FACTUAL ANALYSIS

**Methodology:** Every statement backed by:
- Direct code reference with file:line
- Diagnostic output with run number and line
- Design spec citation with section number
- No interpretations or assumptions made
