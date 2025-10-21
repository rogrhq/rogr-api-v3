# Scoring Model Facts (No Recommendations)

**Investigation Date:** 2025-10-21
**Location:** `/Users/txtk/Documents/ROGR/github/rogrv2-backend`

This document maps the exact implementation of credibility/authority scoring flow based on actual code.

---

## 1. P25 Aggregation Formula

### What P25 Reads From Items

**File:** `intelligence/content/p25_aggregate.py:6-46`

```python
def _item_strength(it: Dict[str, Any]) -> float:
    # frame top score
    fms = it.get("frame_matches") or []
    best_frame = 0.0
    for m in fms:
        sc = float(m.get("score", 0.0))
        if sc > best_frame:
            best_frame = sc

    # item grade
    igr = float(it.get("item_grade", 0.0))

    # coverage factor
    cov = (it.get("coverage") or "unknown").lower()
    if cov == "full": cov_w = 1.0
    elif cov == "partial": cov_w = 0.75
    elif cov == "snippet_only": cov_w = 0.55
    else: cov_w = 0.6

    # combine (bounded)
    base = 0.55 * best_frame + 0.45 * igr
    strength = max(0.0, min(1.0, base * cov_w))
    return strength
```

**Fields P25 _item_strength() READS:**
- `item["frame_matches"]` (list of dicts with "score")
- `item["item_grade"]` (float 0-1)
- `item["coverage"]` (string: "full"/"partial"/"snippet_only")

**Fields P25 _item_strength() DOES NOT READ:**
- `item["credibility"]` - NOT used in item strength calculation
- `item["authority"]` - NOT used in item strength calculation

### Where Credibility IS Used in P25

**File:** `intelligence/content/p25_aggregate.py:64-93`

```python
def _confidence_from_arms(sa: float, sb: float, n_items_a: int, n_items_b: int,
                         arm_a_items: list, arm_b_items: list, claim_numbers: list = None) -> float:
    """Enhanced confidence with quality multipliers (Phase 4)."""
    # ... basic calculation ...

    # Phase 4: Add quality multipliers
    all_items = arm_a_items + arm_b_items
    diversity = calculate_diversity_score(all_items)
    consistency = calculate_consistency_score(all_items, claim_numbers)

    # Calculate average authority using credibility (not authority_score which doesn't exist on items)
    authorities = [item.get("credibility", 0.5) for item in all_items]
    avg_authority = sum(authorities) / len(authorities) if authorities else 0.5

    # 6-factor formula (OLD: 3-factor)
    conf = (
        0.25 * total +
        0.25 * balance +
        0.15 * count_factor +
        0.15 * avg_authority +        # ← credibility used HERE for confidence
        0.10 * diversity +
        0.10 * consistency
    )
    return max(0.0, min(1.0, conf))
```

**Comment in code (line 80):**
> "Calculate average authority using credibility (not authority_score which doesn't exist on items)"

**FACT:** P25 reads `item["credibility"]` and calls it "avg_authority" in confidence calculation, but this field does NOT include the domain-based authority score calculated in grade.py.

---

## 2. Function Call Chain

### Complete Sequence

```
1. evaluate_full_evidence() (fullread.py)
   ├─ Calls: _credibility_from(url, text)
   └─ Stores: item["credibility"] = float (0-1)

2. Pipeline calls attach_finding_to_item() (pipeline/run.py)
   └─ For each evidence item

3. attach_finding_to_item() (grade.py:247)
   ├─ Calls: build_finding_v2(claim_text, arm, item)
   └─ Stores: item["item_grade"] = finding["item_grade"]
   └─ Stores: item["stance"] = ...
   └─ Stores: item["finding"] = finding dict

4. build_finding_v2() (grade.py:334)
   ├─ Calls: evaluate_full_evidence() → P21
   ├─ Calls: analyze_item() → P23
   ├─ Calls: analyze_frames() → P24
   └─ Calls: fuse_module_grades(features, evidence_item)
   └─ Returns: {"item_grade": float, "features": {...}}

5. fuse_module_grades() (grade.py:275)
   ├─ Reads: features['p21']['credibility']
   ├─ Reads: features['p23']['item_grade']
   ├─ Reads: features['p24']['frame_confidence']
   ├─ Calls: calculate_authority_score(url, credibility)
   └─ Formula: 0.40*semantic + 0.30*frame + 0.20*authority + 0.10*coverage
   └─ Returns: item_grade (float 0-1)

6. aggregate_verdict() (p25_aggregate.py:95)
   ├─ Reads: item["item_grade"] for arm strength
   ├─ Reads: item["credibility"] for confidence calculation
   └─ Applies quality multipliers (diversity, consistency, breadth)
   └─ Returns verdict with label + confidence
```

### Critical Finding: Authority Score Loss

**File:** `intelligence/content/grade.py:275-332`

The `calculate_authority_score()` function is called in `fuse_module_grades()`:

```python
def fuse_module_grades(features: dict, evidence_item: dict) -> float:
    # ...extract credibility...
    credibility = features['p21'].get('credibility', 0.5)

    # PHASE 3.2: Calculate authority from domain + credibility
    url = evidence_item.get('url', '')
    authority = calculate_authority_score(url, credibility)

    # Fuse with weights (PHASE 3.2: using authority instead of credibility)
    item_grade = (
        0.40 * semantic_score +
        0.30 * frame_score +
        0.20 * authority +       # NEW: Domain-aware authority
        0.10 * coverage_weight
    )
    return item_grade  # ← Authority affects item_grade
```

**BUT:** The `authority` value is NOT stored on the item dict. Only `item_grade` (the result) is stored.

**File:** `intelligence/content/grade.py:261-266`

```python
def attach_finding_to_item(claim_text: str, arm: str, item: Dict[str, Any]) -> Dict[str, Any]:
    finding = build_finding_v2(claim_text, arm, item)
    # annotate the item
    item["item_grade"] = finding["item_grade"]
    item["stance"] = finding.get("features", {}).get("p23", {}).get("stance", "unrelated")
    item["finding"] = finding
    return item
```

**FACT:** Authority score affects `item_grade` calculation but is NOT preserved as `item["authority"]`.

---

## 3. Authority Calculation

### Implementation Details

**File:** `intelligence/content/grade.py:418-526`

```python
def calculate_authority_score(url: str, credibility: float = 0.5) -> float:
    """
    Score source authority 0-1 based on domain.

    Authority tiers:
    - Government (.gov): 1.0
    - Education (.edu): 0.9
    - Peer-reviewed journals: 0.85
    - International organizations: 0.90-0.95
    - Trusted news (Tier 1): 0.85 (Reuters, AP)
    - Trusted news (Tier 2): 0.75 (NYT, BBC)
    - Default: 0.5
    """
    domain = extract_domain(url)

    # Check direct match in DOMAIN_SCORES dict (90+ domains)
    if domain in DOMAIN_SCORES:
        domain_score = DOMAIN_SCORES[domain]
    else:
        # Check domain patterns
        if domain.endswith('.gov'):
            domain_score = 0.95
        elif domain.endswith('.edu'):
            domain_score = 0.85
        elif domain.endswith('.org'):
            domain_score = 0.60
        else:
            domain_score = 0.50  # Default

    # Combine domain score with existing credibility
    # Domain = 60%, Credibility = 40%
    authority = 0.6 * domain_score + 0.4 * credibility

    return round(authority, 3)
```

**Called By:**
- `fuse_module_grades()` in `intelligence/content/grade.py:307`

**Parameters:**
- `url`: Source URL (string)
- `credibility`: P21 credibility score (float 0-1, default 0.5)

**Returns:**
- Authority score (float 0-1, rounded to 3 decimals)

**Formula:**
```
authority = 0.6 * domain_score + 0.4 * credibility

Where domain_score is:
- Exact match: DOMAIN_SCORES[domain] (e.g., nih.gov → 1.0)
- .gov pattern: 0.95
- .edu pattern: 0.85
- .org pattern: 0.60
- Default: 0.50
```

---

## 4. Credibility Calculation (P21)

### Implementation Details

**File:** `intelligence/content/fullread.py:166-187`

```python
def _credibility_from(url: str, text: str) -> float:
    """
    Structural-only credibility in [0,1], no whitelists:
      + HTTPS scheme
      + TLD .gov/.edu bonus
      + presence of authz words in body
    """
    score = 0.0

    # HTTPS bonus
    p = urlparse(url or "")
    if p.scheme == "https":
        score += 0.15

    # TLD bonus
    host = (p.hostname or "").lower()
    if host.endswith(".gov") or host.endswith(".edu"):
        score += 0.25

    # Authoritative words in text
    if _AUTHZ_WORDS.search(text or ""):
        score += 0.15

    return max(0.0, min(1.0, score))
```

**Where:** `_AUTHZ_WORDS = re.compile(r"\b(report|press\s+release|statement|dataset|methodology|audit|budget)\b", re.I)`

**Called By:**
- `evaluate_full_evidence()` in `intelligence/content/fullread.py:204,285`

**Stored In:**
- `item["credibility"]` (float 0-1)

**Formula:**
```
credibility = 0.0
+ 0.15 if HTTPS
+ 0.25 if .gov or .edu
+ 0.15 if text contains authz words
= max score 0.55, min 0.0
```

---

## 5. Quality Multipliers

**File:** `intelligence/content/p25_aggregate.py:109-147`

### In aggregate_verdict()

```python
def aggregate_verdict(...):
    sa = _arm_strength(arm_a_items)
    sb = _arm_strength(arm_b_items)

    # Phase 4: Apply quality multipliers to arm strength (ADDED)
    all_items = arm_a_items + arm_b_items
    diversity = calculate_diversity_score(all_items)
    consistency = calculate_consistency_score(all_items, claim_numbers)
    breadth = calculate_breadth_score(all_items)

    # Apply multipliers to arm strength (blueprint specification)
    sa_enhanced = sa * diversity * consistency * breadth
    sb_enhanced = sb * diversity * consistency * breadth

    # Use enhanced strength for verdict calculation
    # ... label determination ...

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

### Diversity Score

**File:** `intelligence/content/p25_aggregate.py:154-199`

```python
def calculate_diversity_score(items: list) -> float:
    """
    Score source diversity 0-1.
    Higher score = more diverse sources
    """
    # Extract domains from URLs
    domains = [extract_domain(item.get('url', '')) for item in items]

    # Calculate diversity
    unique_domains = len(set(domains))
    total_items = len(domains)
    diversity = unique_domains / total_items

    # Bonus for cross-source corroboration
    # If 3+ unique sources with 3+ items, boost diversity
    if unique_domains >= 3 and total_items >= 3:
        diversity = min(1.0, diversity * 1.1)

    return round(diversity, 3)
```

### Consistency Score

**File:** `intelligence/content/p25_aggregate.py:207-284`

```python
def calculate_consistency_score(items: list, claim_numbers: list = None) -> float:
    """
    Check if arm items agree on numbers (0-1).
    Higher score = items agree
    """
    if not items or len(items) < 2:
        return 1.0  # Only one item, can't have conflicts

    if not claim_numbers:
        return 1.0  # Non-numeric claim, consistency N/A

    # Extract numbers from item snippets/content
    item_numbers = [extract_numbers(item) for item in items]

    # Calculate coefficient of variation (std dev / mean)
    all_numbers = flatten(item_numbers)
    if len(all_numbers) >= 2:
        mean = statistics.mean(all_numbers)
        stdev = statistics.stdev(all_numbers)
        coef_var = stdev / mean if mean > 0 else 0

        # Convert to consistency score
        # Low variance (< 0.10) = high consistency (1.0)
        # High variance (> 0.50) = low consistency (0.0)
        if coef_var < 0.10:
            consistency = 1.0
        elif coef_var > 0.50:
            consistency = 0.0
        else:
            consistency = 1.0 - ((coef_var - 0.10) / 0.40)

        return round(max(0.0, min(1.0, consistency)), 3)

    return 1.0  # Default: assume consistent
```

### Breadth Score

**File:** `intelligence/content/p25_aggregate.py:292-373`

```python
def calculate_breadth_score(items: list) -> float:
    """
    Measure breadth vs repetition 0-1.
    Higher score = diverse angles, complementary coverage
    """
    if not items or len(items) < 2:
        return 1.0  # Single item, can't measure breadth

    # Extract matched spans or snippets
    texts = [extract_text_for_comparison(item) for item in items]

    # Calculate pairwise similarity using trigram overlap
    similarities = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            sim = trigram_similarity(texts[i], texts[j])
            similarities.append(sim)

    avg_similarity = sum(similarities) / len(similarities)

    # High similarity = repetition = low breadth
    # Low similarity = diverse angles = high breadth
    breadth = 1.0 - avg_similarity

    return round(max(0.0, min(1.0, breadth)), 3)
```

---

## 6. Current Display Output

### execution_trace.py

**File:** `tests/execution_trace.py:80-98`

```python
for idx, item in enumerate(items[:2], 1):
    print(f"\n  Item {idx}:")
    print(f"    Title: {item.get('title', '')[:60]}")
    print(f"    URL: {item.get('url', '')[:60]}")
    print(f"    Stance: {item.get('stance')}")
    print(f"    Grade: {item.get('item_grade', 0):.3f}")

    # Show grading breakdown
    finding = item.get('finding', {})
    features = finding.get('features', {})

    if 'p21' in features:
        print(f"    P21 credibility: {features['p21'].get('credibility', 0):.3f}")
    if 'p23' in features:
        print(f"    P23 semantic: {features['p23'].get('item_grade', 0):.3f}")
    if 'p24' in features:
        print(f"    P24 frame: {features['p24'].get('frame_confidence', 0):.3f}")

    print(f"    Authority: {item.get('authority', 0):.3f}")
```

**Output Shows:**
- `item_grade` (final fused grade)
- `features['p21']['credibility']` (P21 credibility)
- `features['p23']['item_grade']` (P23 semantic)
- `features['p24']['frame_confidence']` (P24 frame)
- `item.get('authority', 0)` ← **This reads from item dict, but authority is never stored there**

### complete_pipeline_diagnostic.py

**File:** `tests/complete_pipeline_diagnostic.py:211-251`

```python
print(f"    Item grade: {item.get('item_grade', 'MISSING')}")

# ... module breakdown ...
if 'p21' in features:
    p21 = features['p21']
    print(f"    P21 credibility: {p21.get('credibility', 'MISSING')}")
    print(f"    P21 domain_authority: {p21.get('domain_authority', 'MISSING')}")

if 'p23' in features:
    p23 = features['p23']
    print(f"    P23 item_grade: {p23.get('item_grade', 'MISSING')}")

# ... etc ...

print(f"    Authority (combined): {item.get('authority', 'MISSING')}")
```

**Output Shows:**
- `item_grade` (final)
- `p21['credibility']` (P21)
- `p21['domain_authority']` ← **Field does not exist in P21 output**
- `p23['item_grade']` (P23)
- `item['authority']` ← **Field does not exist on item dict**

---

## 7. Item Dict Structure

### What Actually Exists

Based on code inspection:

```python
item = {
    # Search/fetch fields
    'url': str,
    'title': str,
    'snippet': str,
    'content': str,                      # from fetch_enrichment
    'coverage': str,                      # "full"/"partial"/"snippet_only"

    # P21 fields (from evaluate_full_evidence)
    'credibility': float,                 # 0-1, from _credibility_from()
    'grade_full': float,                  # 0-10
    'stance_full': str,                   # "support"/"challenge"/"mixed"/"unrelated"
    'signals_full': dict,

    # P20 fields (from attach_finding_to_item)
    'item_grade': float,                  # 0-1, from fuse_module_grades()
    'stance': str,                        # from P23
    'finding': {                          # from build_finding_v2()
        'item_grade': float,
        'features': {
            'p21': {
                'credibility': float,
                'grade_full': float,
                'stance_full': str,
                'signals_full': dict,
            },
            'p23': {
                'item_grade': float,
                'stance': str,
                'findings': list,
            },
            'p24': {
                'frame_confidence': float,
                'frame_matches': list,
            },
        },
        'orchestrated': True,
    },

    # P24 fields (from analyze_frames)
    'frame_matches': list,               # List of frame match dicts
}
```

### What Does NOT Exist

```python
item = {
    # These fields are NEVER stored:
    'authority': ???,           # ❌ Calculated in fuse_module_grades() but NOT stored
    'domain_authority': ???,    # ❌ Does not exist anywhere
}
```

### Where Authority Goes

**Fact:** The `authority` score calculated by `calculate_authority_score()` is used ONLY in the `fuse_module_grades()` formula:

```python
item_grade = 0.40*semantic + 0.30*frame + 0.20*authority + 0.10*coverage
```

After this calculation, `authority` is discarded. Only `item_grade` is stored on the item dict.

---

## 8. P25 Confidence Calculation Uses Wrong Field

**File:** `intelligence/content/p25_aggregate.py:80-82`

```python
# Calculate average authority using credibility (not authority_score which doesn't exist on items)
authorities = [item.get("credibility", 0.5) for item in all_items]
avg_authority = sum(authorities) / len(authorities) if authorities else 0.5
```

**Code Comment Confirms:**
> "Calculate average authority using credibility (not authority_score which doesn't exist on items)"

**What This Means:**
- P25 wants to use `authority` in confidence calculation
- But `authority` does not exist on items (only in intermediate calculation)
- So P25 falls back to reading `credibility` instead
- This means confidence formula uses **credibility** (0-0.55 range with simple HTTPS/.gov/.edu checks)
- NOT **authority** (0-1 range with domain-specific scores and 60/40 blend)

**Formula in confidence:**
```python
conf = (
    0.25 * total +
    0.25 * balance +
    0.15 * count_factor +
    0.15 * avg_authority +        # ← This is actually avg_credibility
    0.10 * diversity +
    0.10 * consistency
)
```

---

## Summary of Facts

1. **Authority Score Exists** - `calculate_authority_score()` is implemented with 90+ domains and sophisticated scoring
2. **Authority Affects item_grade** - Used in `fuse_module_grades()` with 20% weight
3. **Authority Is Not Stored** - The value is discarded after `item_grade` calculation
4. **P25 Uses Wrong Field** - Reads `credibility` instead of `authority` for confidence calculation
5. **Credibility Is Simple** - Max 0.55 based on HTTPS + .gov/.edu + keywords
6. **Authority Is Sophisticated** - 0-1 scale with domain-specific scores (e.g., nih.gov=1.0, nytimes.com=0.75)
7. **Quality Multipliers Work** - Diversity, consistency, breadth are calculated and applied to arm strength
8. **Display Code Expects Authority** - Both test files try to print `item['authority']` but it doesn't exist

**End of Facts Report**
