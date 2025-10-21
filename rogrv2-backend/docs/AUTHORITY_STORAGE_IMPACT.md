# Authority Storage Impact Investigation

**Investigation Date:** 2025-10-21
**Location:** `/Users/txtk/Documents/ROGR/github/rogrv2-backend`

This document contains exact facts about where authority is calculated, who reads it, and what changes are required to store it properly.

---

## 1. Current Implementation (Exact Code)

### fuse_module_grades() - Line 275-332

**File:** `intelligence/content/grade.py:275-332`

```python
def fuse_module_grades(features: dict, evidence_item: dict) -> float:
    """
    Fuse P21, P23, P24 features into single item_grade (0-1).

    Weighting:
    - 40% semantic similarity (P23)
    - 30% frame matching (P24)
    - 20% credibility (P21)
    - 10% coverage quality
    """

    # Extract components
    # P23: Semantic similarity
    if features.get('p23_available'):
        semantic_score = features['p23'].get('item_grade', 0.0)
    else:
        semantic_score = 0.0

    # P24: Frame matching
    if features.get('p24_available'):
        frame_score = features['p24'].get('frame_confidence', 0.0)
    else:
        frame_score = 0.0

    # P21: Credibility (for authority calculation)
    if features.get('p21_available'):
        credibility = features['p21'].get('credibility', 0.5)
    else:
        credibility = 0.5

    # PHASE 3.2: Calculate authority from domain + credibility
    url = evidence_item.get('url', '')
    authority = calculate_authority_score(url, credibility)

    # Coverage: full > partial > snippet_only
    coverage = evidence_item.get('coverage', 'snippet_only')
    if coverage == 'full':
        coverage_weight = 1.0
    elif coverage == 'partial':
        coverage_weight = 0.7
    else:  # snippet_only
        coverage_weight = 0.4

    # Fuse with weights (PHASE 3.2: using authority instead of credibility)
    item_grade = (
        0.40 * semantic_score +
        0.30 * frame_score +
        0.20 * authority +       # NEW: Domain-aware authority
        0.10 * coverage_weight
    )

    # Ensure 0-1 range
    item_grade = max(0.0, min(1.0, item_grade))

    # Round to 3 decimals
    item_grade = round(item_grade, 3)

    return item_grade
```

**Currently:**
- Calculates authority: Line 307
- Uses authority in formula: Line 322 (20% weight)
- Returns: `item_grade` (float 0-1)
- Does NOT store authority in features: CONFIRMED
- Does NOT return authority: CONFIRMED

### attach_finding_to_item() - Line 247-266

**File:** `intelligence/content/grade.py:247-266`

```python
def attach_finding_to_item(claim_text: str, arm: str, item: Dict[str, Any]) -> Dict[str, Any]:
    content = item.get("content") or item.get("content_excerpt") or ""
    snippet = item.get("snippet") or ""
    # prefer any upstream best-match window if present
    pre = ""
    pre_sim = -1.0
    for m in item.get("matches") or []:
        # take the highest score match if present
        pre = m.get("sentence") or m.get("text") or pre
        try:
            pre_sim = float(m.get("score", -1.0))
        except Exception:
            pass
        break
    finding = build_finding_v2(claim_text, arm, item)
    # annotate the item
    item["item_grade"] = finding["item_grade"]
    item["stance"] = finding.get("features", {}).get("p23", {}).get("stance", "unrelated")
    item["finding"] = finding
    return item
```

**Currently:**
- Extracts item_grade: Line 263
- Extracts stance: Line 264
- Stores finding dict: Line 265
- Does NOT extract authority: CONFIRMED
- Does NOT store `item["authority"]`: CONFIRMED

### build_finding_v2() - Line 334-410

**File:** `intelligence/content/grade.py:334-410`

Returns:
```python
return {
    'item_grade': item_grade,
    'features': features,
    'orchestrated': True,
}
```

Where `features` contains:
```python
features = {
    'p21_available': bool,
    'p21': {
        'grade_full': float,
        'stance_full': str,
        'credibility': float,
        'signals_full': dict,
    },
    'p23_available': bool,
    'p23': {
        'item_grade': float,
        'findings': list,
        'grade_label': str,
        'stance': str,
    },
    'p24_available': bool,
    'p24': {
        'frame_matches': list,
        'frame_confidence': float,
        'item_frame': dict,
    },
}
```

**Currently:**
- Does NOT include 'authority' key in features: CONFIRMED
- Does NOT include 'authority' key in return dict: CONFIRMED

### P25 Confidence Calculation - Line 80-93

**File:** `intelligence/content/p25_aggregate.py:80-93`

```python
# Calculate average authority using credibility (not authority_score which doesn't exist on items)
authorities = [item.get("credibility", 0.5) for item in all_items]
avg_authority = sum(authorities) / len(authorities) if authorities else 0.5

# 6-factor formula (OLD: 3-factor)
conf = (
    0.25 * total +
    0.25 * balance +
    0.15 * count_factor +
    0.15 * avg_authority +
    0.10 * diversity +
    0.10 * consistency
)
return max(0.0, min(1.0, conf))
```

**Currently:**
- Reads: `item.get("credibility", 0.5)` (Line 81)
- Comment explicitly states: "not authority_score which doesn't exist on items"
- Uses credibility (0-0.55 range) instead of authority (0-1 range)

---

## 2. Current Usage of features Dict

### Who WRITES to features:

**File:** `intelligence/content/grade.py`

- Line 364: `features['p21'] = {...}` (stores P21 results)
- Line 372: `features['p21'] = {'error': str(e)}` (error case)
- Line 379: `features['p23'] = {...}` (stores P23 results)
- Line 387: `features['p23'] = {'error': str(e)}` (error case)
- Line 393: `features['p24'] = {...}` (stores P24 results)
- Line 400: `features['p24'] = {'error': str(e)}` (error case)

### Who READS features['p21']:

1. **intelligence/content/grade.py:301** - `fuse_module_grades()`
   ```python
   credibility = features['p21'].get('credibility', 0.5)
   ```

2. **tests/execution_trace.py:92**
   ```python
   print(f"    P21 credibility: {features['p21'].get('credibility', 0):.3f}")
   ```

3. **tests/trace_pipeline_execution.py:166**
   ```python
   p21 = features['p21']
   ```

4. **tests/complete_pipeline_diagnostic.py:227**
   ```python
   p21 = features['p21']
   print(f"    P21 credibility: {p21.get('credibility', 'MISSING')}")
   print(f"    P21 domain_authority: {p21.get('domain_authority', 'MISSING')}")
   ```

5. **tests/complete_pipeline_diagnostic.py:307**
   ```python
   cred = features['p21'].get('credibility', 0)
   ```

### Who READS features['p23']:

1. **intelligence/content/grade.py:264** - `attach_finding_to_item()`
   ```python
   item["stance"] = finding.get("features", {}).get("p23", {}).get("stance", "unrelated")
   ```

2. **intelligence/content/grade.py:289** - `fuse_module_grades()`
   ```python
   semantic_score = features['p23'].get('item_grade', 0.0)
   ```

3. **tests/execution_trace.py:94**
   ```python
   print(f"    P23 semantic: {features['p23'].get('item_grade', 0):.3f}")
   ```

4. **tests/trace_pipeline_execution.py:159**
   ```python
   p23 = features['p23']
   ```

5. **tests/complete_pipeline_diagnostic.py:233**
   ```python
   p23 = features['p23']
   print(f"    P23 item_grade: {p23.get('item_grade', 'MISSING')}")
   ```

### Who READS features['p24']:

1. **intelligence/content/grade.py:295** - `fuse_module_grades()`
   ```python
   frame_score = features['p24'].get('frame_confidence', 0.0)
   ```

2. **tests/execution_trace.py:96**
   ```python
   print(f"    P24 frame: {features['p24'].get('frame_confidence', 0):.3f}")
   ```

3. **tests/complete_pipeline_diagnostic.py:247**
   ```python
   p24 = features['p24']
   ```

### Who READS features['authority']:

**NONE** - No code currently reads `features['authority']`

---

## 3. Current Usage of item Dict

### Who READS item['authority']:

1. **intelligence/consensus/build.py:55** - `build_trust_capsule()`
   ```python
   auth = item.get('authority', None)
   ```
   Context: Tries to read authority, falls back to calculating it if missing

2. **intelligence/consensus/build.py:293** - `build_trust_capsule()`
   ```python
   authority = item.get('authority', 0.5)
   ```
   Context: Reads for quality scoring

3. **intelligence/consensus/build.py:302** - `build_trust_capsule()`
   ```python
   item['authority'] = authority
   ```
   Context: WRITES authority after calculating it (only place that stores it)

4. **tests/execution_trace.py:98**
   ```python
   print(f"    Authority: {item.get('authority', 0):.3f}")
   ```
   Context: Display only

5. **tests/complete_pipeline_diagnostic.py:251**
   ```python
   print(f"    Authority (combined): {item.get('authority', 'MISSING')}")
   ```
   Context: Display only

6. **tests/complete_pipeline_diagnostic.py:316**
   ```python
   authorities = [item.get('authority', 0) for item in all_items if 'authority' in item]
   ```
   Context: Analysis only

**FACT:** Only `intelligence/consensus/build.py` actually WRITES `item['authority']` (line 302). It calculates it on-demand when building trust capsules.

### Who READS item['credibility']:

1. **intelligence/pipeline/run.py:238-239** - Main pipeline
   ```python
   arm_a_authorities = [item.get("credibility", 0.5) for item in arm_a_items]
   arm_b_authorities = [item.get("credibility", 0.5) for item in arm_b_items]
   ```

2. **intelligence/consensus/build.py:61, 300** - Trust capsule builder
   ```python
   cred = item.get('credibility', 0.5)
   ```
   (Used to calculate authority if not present)

3. **intelligence/content/p25_aggregate.py:81** - Confidence calculation
   ```python
   authorities = [item.get("credibility", 0.5) for item in all_items]
   ```

4. **intelligence/content/fullread.py:204, 285, 303** - P21 module (WRITES)
   ```python
   item["credibility"] = _credibility_from(...)
   item['credibility'] = item['credibility'] * temporal_weight * geographic_weight
   ```

5. **Multiple test files** - Display and verification

### Who READS item['item_grade']:

**CRITICAL:** `item_grade` is read by many modules:

1. **intelligence/consensus/build.py:47, 292** - Trust capsule quality scoring
2. **intelligence/content/semantic_read.py:252** - P23 (WRITES)
3. **intelligence/content/grade.py:263** - P20 (WRITES)
4. **intelligence/content/p25_aggregate.py:28** - Arm strength calculation
   ```python
   igr = float(it.get("item_grade", 0.0))
   ```
   **THIS IS THE CRITICAL PATH TO VERDICT**

5. **Multiple test files** - Display and analysis

---

## 4. Return Structure

### build_finding_v2() returns:

**File:** `intelligence/content/grade.py:406-410`

```python
{
    'item_grade': float,          # 0-1, fused score
    'features': {
        'p21_available': bool,
        'p21': {
            'grade_full': float,
            'stance_full': str,
            'credibility': float,
            'signals_full': dict,
        },
        'p23_available': bool,
        'p23': {
            'item_grade': float,
            'findings': list,
            'grade_label': str,
            'stance': str,
        },
        'p24_available': bool,
        'p24': {
            'frame_matches': list,
            'frame_confidence': float,
            'item_frame': dict,
        },
    },
    'orchestrated': bool,         # True
}
```

**Missing:** No 'authority' key at root level or in features

---

## 5. Serialization

### Where items/findings are serialized:

1. **intelligence/pipeline/run.py:25-44** - `_to_json_primitive()`
   ```python
   def _to_json_primitive(x: Any) -> Any:
       """Deeply coerce nested structures into JSON-safe primitives."""
   ```
   Context: Used for preparing pipeline results for JSON output

2. **intelligence/util/diag.py:21** - Diagnostic logging
   ```python
   _LOGGER.info(json.dumps(payload, ensure_ascii=False))
   ```

3. **intelligence/content/align.py:53, 389** - Event logging
   ```python
   print(json.dumps(rec, ensure_ascii=False))
   ```

4. **tests/comprehensive/diagnostic_pipeline.py:112**
   ```python
   print(json.dumps(result, indent=2, default=str))
   ```

5. **tests/test_e2e_trust_capsule.py:43**
   ```python
   print(json.dumps(data, indent=indent, default=str))
   ```

**Format:** All use `json.dumps()` with `default=str` fallback

**Impact:** Adding `authority` field will serialize cleanly (it's a float)

---

## 6. Impact Assessment

### Adding features['authority']:

**Implementation:**
```python
# In build_finding_v2() after calling fuse_module_grades()
authority = calculate_authority_score(evidence_item.get('url', ''), credibility)
features['authority'] = {
    'score': authority,
    'credibility': credibility,
    'url': evidence_item.get('url', ''),
}
```

**Who would see it:**
- Any code that iterates through `features` dict keys
- JSON serialization (would include it automatically)

**Who would NOT see it:**
- Code that specifically checks `features['p21']`, `features['p23']`, `features['p24']` only
- No existing code reads `features['authority']`, so NO impact on existing logic

**Breaking changes:**
- **NONE** - Adding a new key to a dict is backward compatible
- Existing code that doesn't look for 'authority' will continue working

**Backward compatibility:**
- **YES** - No code currently depends on authority being absent
- Adding new keys to dicts is always backward compatible in Python

### Adding item['authority']:

**Implementation:**
```python
# In attach_finding_to_item() after line 263
item["item_grade"] = finding["item_grade"]
item["authority"] = finding.get("features", {}).get("authority", {}).get("score", 0.5)
item["stance"] = finding.get("features", {}).get("p23", {}).get("stance", "unrelated")
```

**Who would see it:**

1. **intelligence/consensus/build.py:55** - Would read stored value instead of None
   - Current: `auth = item.get('authority', None)` → Falls through to calculate
   - New: `auth = item.get('authority', None)` → Uses stored value
   - **SAFE** - Code already expects authority to exist, has fallback

2. **intelligence/consensus/build.py:293** - Would read stored value
   - Current: `authority = item.get('authority', 0.5)` → Gets 0.5 default
   - New: `authority = item.get('authority', 0.5)` → Gets stored value
   - **SAFE** - Already expects this field

3. **intelligence/consensus/build.py:302** - Would skip calculation
   - Current: Line 296 check `if 'authority' not in item:` → Always True, calculates
   - New: Line 296 check → False, skips calculation
   - **SAFE** - Uses stored value instead of recalculating (more efficient)

4. **tests/execution_trace.py:98** - Would display actual value
   - Current: `item.get('authority', 0)` → Gets 0
   - New: `item.get('authority', 0)` → Gets stored value
   - **SAFE** - Display only, expects this field

5. **tests/complete_pipeline_diagnostic.py:251** - Would display actual value
   - Current: Shows "MISSING"
   - New: Shows actual authority score
   - **SAFE** - Display only

**Who would NOT see it:**
- `intelligence/content/p25_aggregate.py` - Reads `credibility`, not `authority`
- Pipeline verdict calculation - Would need separate change (see below)

**Breaking changes:**
- **NONE** - All existing readers have safe fallback defaults
- `consensus/build.py` already expects this field and handles missing case

**Backward compatibility:**
- **YES** - All code that reads `item['authority']` uses `.get()` with defaults
- Code is defensive and handles missing field

### Changing P25 to read authority instead of credibility:

**Current behavior (Line 81):**
```python
authorities = [item.get("credibility", 0.5) for item in all_items]
avg_authority = sum(authorities) / len(authorities) if authorities else 0.5

conf = (
    0.25 * total +
    0.25 * balance +
    0.15 * count_factor +
    0.15 * avg_authority +      # Using credibility (0-0.55 range)
    0.10 * diversity +
    0.10 * consistency
)
```

**New behavior:**
```python
authorities = [item.get("authority", 0.5) for item in all_items]
avg_authority = sum(authorities) / len(authorities) if authorities else 0.5

conf = (
    0.25 * total +
    0.25 * balance +
    0.15 * count_factor +
    0.15 * avg_authority +      # Using authority (0-1 range)
    0.10 * diversity +
    0.10 * consistency
)
```

**If item['authority'] doesn't exist:**
- Fallback: `item.get("authority", 0.5)` → Returns 0.5
- **SAFE** - Has default value

**Breaking changes:**
- **NONE** - Backward compatible with safe default
- Will change confidence scores (EXPECTED BEHAVIOR - this is the fix)

**Numeric Impact:**
- Old: avg_authority typically 0.15-0.40 (credibility range 0-0.55)
- New: avg_authority typically 0.50-0.95 (authority range with domain scores)
- Confidence will increase by ~0.05-0.15 for high-authority sources
- **This is the intended fix** - credibility was artificially low

---

## 7. Required Changes Summary

### File 1: intelligence/content/grade.py

**Change 1 - build_finding_v2() at line ~404:**

**Before:**
```python
    item_grade = fuse_module_grades(features, evidence_item)

    return {
        'item_grade': item_grade,
        'features': features,
        'orchestrated': True,
    }
```

**After:**
```python
    item_grade = fuse_module_grades(features, evidence_item)

    # Store authority score in features (used in fuse_module_grades)
    credibility = features.get('p21', {}).get('credibility', 0.5) if features.get('p21_available') else 0.5
    url = evidence_item.get('url', '')
    authority = calculate_authority_score(url, credibility)

    features['authority'] = {
        'score': authority,
        'credibility': credibility,
        'domain': url,
    }

    return {
        'item_grade': item_grade,
        'features': features,
        'orchestrated': True,
    }
```

**Purpose:** Store calculated authority in features dict for transparency

**Change 2 - attach_finding_to_item() at line ~263:**

**Before:**
```python
    finding = build_finding_v2(claim_text, arm, item)
    # annotate the item
    item["item_grade"] = finding["item_grade"]
    item["stance"] = finding.get("features", {}).get("p23", {}).get("stance", "unrelated")
    item["finding"] = finding
    return item
```

**After:**
```python
    finding = build_finding_v2(claim_text, arm, item)
    # annotate the item
    item["item_grade"] = finding["item_grade"]
    item["authority"] = finding.get("features", {}).get("authority", {}).get("score", 0.5)
    item["stance"] = finding.get("features", {}).get("p23", {}).get("stance", "unrelated")
    item["finding"] = finding
    return item
```

**Purpose:** Store authority on item dict so P25 can access it

### File 2: intelligence/content/p25_aggregate.py

**Change 1 - _confidence_from_arms() at line ~81:**

**Before:**
```python
    # Calculate average authority using credibility (not authority_score which doesn't exist on items)
    authorities = [item.get("credibility", 0.5) for item in all_items]
    avg_authority = sum(authorities) / len(authorities) if authorities else 0.5
```

**After:**
```python
    # Calculate average authority using authority score (now available on items from grade.py)
    authorities = [item.get("authority", 0.5) for item in all_items]
    avg_authority = sum(authorities) / len(authorities) if authorities else 0.5
```

**Purpose:** Use proper authority score (0-1 with domain weighting) instead of credibility (0-0.55 simple)

**Alternative (if backward compatibility required):**
```python
    # Prefer authority, fall back to credibility for old items
    authorities = [item.get("authority", item.get("credibility", 0.5)) for item in all_items]
    avg_authority = sum(authorities) / len(authorities) if authorities else 0.5
```

---

## 8. Test Requirements

Based on who reads these fields, tests needed:

### Unit Tests:

1. **test_build_finding_v2_includes_authority()**
   - Verify `features['authority']` exists in return dict
   - Verify `features['authority']['score']` is float 0-1
   - Verify matches `calculate_authority_score()` output

2. **test_attach_finding_stores_authority()**
   - Verify `item['authority']` is set after attach_finding_to_item()
   - Verify value matches features['authority']['score']

3. **test_p25_uses_authority_not_credibility()**
   - Mock items with both 'authority' and 'credibility'
   - Verify P25 reads 'authority' field
   - Verify confidence calculation uses authority value

### Integration Tests:

4. **test_authority_flows_to_verdict()**
   - Run full pipeline with high-authority source (.gov)
   - Verify `item['authority']` > 0.9
   - Verify verdict confidence reflects high authority

5. **test_backward_compatibility_missing_authority()**
   - Mock old-format items without 'authority' field
   - Verify P25 falls back to default 0.5
   - Verify no crashes

### Regression Tests:

6. **test_consensus_build_uses_stored_authority()**
   - Verify consensus/build.py uses stored authority
   - Verify doesn't recalculate unnecessarily

7. **test_json_serialization_includes_authority()**
   - Run pipeline, serialize to JSON
   - Verify 'authority' field present in output
   - Verify valid float value

---

## 9. Rollback Plan

### If changes cause issues:

**Step 1: Revert P25 change**
```bash
# Revert p25_aggregate.py line 81 to read credibility
git checkout HEAD -- intelligence/content/p25_aggregate.py
```
This restores old behavior. Items will have authority stored but P25 won't use it.

**Step 2: Revert attach_finding_to_item() change**
```bash
# Revert grade.py to not store item['authority']
git diff intelligence/content/grade.py
# Manually revert line where item["authority"] is set
```
This stops storing authority on item dict.

**Step 3: Revert build_finding_v2() change**
```bash
# Revert features['authority'] storage
# Manually remove the features['authority'] block from build_finding_v2()
```
This stops storing authority in features dict.

### Minimal Fix (if full rollback not needed):

If authority calculation is correct but causing issues downstream:

**Option A:** Keep storing authority, but don't use it in P25
- Keep changes to grade.py (stores authority)
- Revert p25_aggregate.py (reads credibility)
- Net effect: Authority visible for debugging, but not affecting verdicts

**Option B:** Use authority but with fallback
```python
# In p25_aggregate.py
authorities = [item.get("authority", item.get("credibility", 0.5)) for item in all_items]
```
- If authority exists: use it
- If missing: fall back to credibility
- Allows gradual migration

---

## 10. Dependencies and Order

### Required Change Order:

1. **FIRST:** Add authority to features in `build_finding_v2()`
   - No dependencies
   - No breaking changes
   - Enables downstream changes

2. **SECOND:** Add authority to item dict in `attach_finding_to_item()`
   - Depends on: features['authority'] existing
   - No breaking changes (safe fallbacks exist)

3. **THIRD:** Change P25 to read authority in `_confidence_from_arms()`
   - Depends on: item['authority'] being populated
   - Changes verdict confidence scores (INTENDED)

### Can be deployed separately if needed:
- Step 1 alone: Authority calculated and visible in features, not used
- Steps 1+2: Authority stored on items, consensus/build.py benefits, P25 unchanged
- Steps 1+2+3: Full fix, P25 uses proper authority scores

---

## 11. Verification Checklist

After implementing changes, verify:

- [ ] `features['authority']` exists in finding dict
- [ ] `item['authority']` exists on evidence items
- [ ] `item['authority']` value is float 0-1
- [ ] High-authority sources (.gov) have authority > 0.9
- [ ] Low-authority sources have authority ~0.5-0.6
- [ ] P25 confidence calculation reads item['authority']
- [ ] consensus/build.py stops recalculating authority
- [ ] JSON output includes authority field
- [ ] Existing tests still pass
- [ ] Display code shows actual authority values (not 0 or MISSING)

---

**END OF IMPACT ASSESSMENT**
