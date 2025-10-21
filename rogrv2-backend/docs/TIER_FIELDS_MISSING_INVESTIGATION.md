# Tier Fields Missing - Investigation

**Date:** 2025-10-21
**Status:** Root cause identified

## 1. Tier Model Signature

**File:** `intelligence/content/fullread.py`
**Line:** 219

```python
def _credibility_from(url: str, text: str) -> Tuple[int, float, str]:
    """
    Tier-based credibility scoring (IFCN compliant).

    Returns:
        (tier, score, category) where:
        - tier: 1-4 (1=highest, 4=lowest)
        - score: 0.30-0.90 (credibility score)
        - category: Human-readable tier description
    """
```

**Result:** Returns 3-tuple: `(tier, score, category)` ✅

---

## 2. Call Sites

**File:** `intelligence/content/fullread.py`

### Call Site 1 (No text available case)
**Lines:** 315-318
```python
tier, credibility, category = _credibility_from(item.get("url") or "", "")
item["credibility"] = credibility
item["credibility_tier"] = tier
item["credibility_category"] = category
```

**Result:** Properly unpacks tuple, stores all 3 fields ✅

### Call Site 2 (Full text available case)
**Lines:** 399-402
```python
tier, credibility, category = _credibility_from(item.get("url") or "", read)
item["credibility"] = round(credibility, 3)
item["credibility_tier"] = tier
item["credibility_category"] = category
```

**Result:** Properly unpacks tuple, stores all 3 fields ✅

---

## 3. Field Storage in P21

### evaluate_full_evidence return value
**File:** `intelligence/content/fullread.py`
**Line:** 426

```python
return item
```

**Item dict includes at line 400-402:**
```python
item["credibility"] = round(credibility, 3)
item["credibility_tier"] = tier
item["credibility_category"] = category
```

**Result:** P21 returns item with all 3 fields ✅

---

## 4. Build_finding_v2 P21 Handling

**File:** `intelligence/content/grade.py`
**Lines:** 364-370

```python
p21_result = evaluate_full_evidence(claim_text, evidence_item.copy())
features['p21'] = {
    'grade_full': p21_result.get('grade_full', 0.0),
    'stance_full': p21_result.get('stance_full', 'unrelated'),
    'credibility': p21_result.get('credibility', 0.5),
    'signals_full': p21_result.get('signals_full', {}),
}
features['p21_available'] = True
```

**Problem identified:** Only 4 fields extracted from p21_result:
- `grade_full` ✅
- `stance_full` ✅
- `credibility` ✅
- `signals_full` ✅

**Missing fields:**
- `credibility_tier` ❌
- `credibility_category` ❌

---

## 5. Attach_finding_to_item

**File:** `intelligence/content/grade.py`
**Lines:** 247-267

```python
def attach_finding_to_item(claim_text: str, arm: str, item: Dict[str, Any]) -> Dict[str, Any]:
    finding = build_finding_v2(claim_text, arm, item)
    # annotate the item
    item["item_grade"] = finding["item_grade"]
    item["authority"] = finding.get("features", {}).get("authority", {}).get("score", 0.5)
    item["stance"] = finding.get("features", {}).get("p23", {}).get("stance", "unrelated")
    item["finding"] = finding
    return item
```

**What gets copied to item:**
- `item_grade` from finding root ✅
- `authority` from features.authority.score ✅
- `stance` from features.p23.stance ✅
- `finding` (entire finding dict) ✅

**What does NOT get copied:**
- `credibility_tier` from features.p21 ❌
- `credibility_category` from features.p21 ❌

---

## 6. Root Cause

**Two-stage data loss:**

### Stage 1: build_finding_v2() loses tier/category
**Location:** `intelligence/content/grade.py:365-370`

When storing P21 results in `features['p21']`, only extracts:
- `credibility` (score only)
- `grade_full`
- `stance_full`
- `signals_full`

But P21 actually returns on the item:
- `item['credibility']` - the score
- `item['credibility_tier']` - tier (1-4)
- `item['credibility_category']` - human-readable category

**The tier and category are calculated but never extracted into features['p21'].**

### Stage 2: attach_finding_to_item() doesn't expose them
**Location:** `intelligence/content/grade.py:247-267`

Even if tier/category were in `features['p21']`, `attach_finding_to_item()` doesn't copy them to the top-level item dict.

It only copies:
- `item_grade`
- `authority`
- `stance`

---

## 7. Data Flow Diagram

```
evaluate_full_evidence (P21)
  ├─ Calculates: tier, credibility, category
  ├─ Stores on item:
  │    ├─ item['credibility'] = 0.520
  │    ├─ item['credibility_tier'] = 2
  │    └─ item['credibility_category'] = 'technical reference'
  └─ Returns: item
       ↓
build_finding_v2()
  ├─ Calls: p21_result = evaluate_full_evidence(...)
  ├─ Extracts to features['p21']:
  │    ├─ credibility: 0.520 ✅
  │    ├─ grade_full: 2.210 ✅
  │    ├─ stance_full: 'support' ✅
  │    └─ signals_full: {...} ✅
  └─ DROPS:
       ├─ credibility_tier: 2 ❌
       └─ credibility_category: 'technical reference' ❌
       ↓
attach_finding_to_item()
  ├─ Receives: finding from build_finding_v2()
  ├─ Copies to item:
  │    ├─ item_grade ✅
  │    ├─ authority ✅
  │    └─ stance ✅
  └─ Does NOT copy:
       ├─ credibility_tier ❌
       └─ credibility_category ❌
```

---

## 8. Evidence from Diagnostic Output

**File:** `docs/pipeline_diagnostics/diagnostic_20251021_143424.md`

```
Item 1:
  CREDIBILITY:
    Score: 0.000      ← Top-level field missing
    Tier: N/A         ← Top-level field missing
    Category: N/A     ← Top-level field missing

  GRADING BREAKDOWN:
    P21 (Full Read):
      Credibility: 0.520   ← Available in features['p21']
```

**Observation:**
- Top-level `item['credibility_tier']` shows "N/A" (field doesn't exist)
- Top-level `item['credibility_category']` shows "N/A" (field doesn't exist)
- P21 credibility score (0.520) IS available in `features['p21']['credibility']`

This confirms tier/category never make it to the final item dict.

---

## 9. Required Fixes

### Fix 1: Store tier/category in features['p21']
**File:** `intelligence/content/grade.py`
**Lines:** 365-370

**Current:**
```python
features['p21'] = {
    'grade_full': p21_result.get('grade_full', 0.0),
    'stance_full': p21_result.get('stance_full', 'unrelated'),
    'credibility': p21_result.get('credibility', 0.5),
    'signals_full': p21_result.get('signals_full', {}),
}
```

**Required:**
```python
features['p21'] = {
    'grade_full': p21_result.get('grade_full', 0.0),
    'stance_full': p21_result.get('stance_full', 'unrelated'),
    'credibility': p21_result.get('credibility', 0.5),
    'credibility_tier': p21_result.get('credibility_tier', 4),       # ADD
    'credibility_category': p21_result.get('credibility_category', 'unknown'),  # ADD
    'signals_full': p21_result.get('signals_full', {}),
}
```

### Fix 2: Copy tier/category to top-level item
**File:** `intelligence/content/grade.py`
**Lines:** 263-266

**Current:**
```python
item["item_grade"] = finding["item_grade"]
item["authority"] = finding.get("features", {}).get("authority", {}).get("score", 0.5)
item["stance"] = finding.get("features", {}).get("p23", {}).get("stance", "unrelated")
item["finding"] = finding
```

**Required:**
```python
item["item_grade"] = finding["item_grade"]
item["authority"] = finding.get("features", {}).get("authority", {}).get("score", 0.5)
item["stance"] = finding.get("features", {}).get("p23", {}).get("stance", "unrelated")
item["credibility"] = finding.get("features", {}).get("p21", {}).get("credibility", 0.5)           # ADD
item["credibility_tier"] = finding.get("features", {}).get("p21", {}).get("credibility_tier", 4)   # ADD
item["credibility_category"] = finding.get("features", {}).get("p21", {}).get("credibility_category", "unknown")  # ADD
item["finding"] = finding
```

---

## 10. Summary

**Tier model implementation:** ✅ Working correctly
**Tier calculation:** ✅ Happens in P21
**Tier storage in P21 output:** ✅ Stored on item
**Tier extraction to features['p21']:** ❌ **NOT extracted** (Fix 1 required)
**Tier exposure on final item:** ❌ **NOT copied** (Fix 2 required)

**Root cause:** Two-stage data loss in the grade.py pipeline. The tier/category fields are calculated and stored by P21, but never extracted into the features dict, and never copied to the final item dict.

**Impact:** Users cannot see tier assignments in diagnostic output or final results, despite tier model working correctly behind the scenes.

**Fixes required:** 2 code changes in `intelligence/content/grade.py`
