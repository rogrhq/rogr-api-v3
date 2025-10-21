# Tier-Based Credibility Impact Analysis

**Investigation Date:** 2025-10-21
**Location:** `/Users/txtk/Documents/ROGR/github/rogrv2-backend`

This document analyzes the mathematical and systematic impact of changing from the current credibility model (0-0.55 range) to a tier-based model (0.30-0.90 range).

---

## 1. Current Credibility Scores (Baseline)

### From Execution Trace (docs/EXECUTION_TRACE.md):

```
Item 1 (engineeringtoolbox.com): P21 credibility: 0.120
Item 2 (ask.usda.gov):            P21 credibility: 0.320
Item 3 (masterorganicchemistry):  P21 credibility: 0.150
```

**Distribution:**
- 0.120: HTTPS only (3 occurrences)
- 0.150: HTTPS + keywords (1 occurrence)
- 0.320: HTTPS + .gov/.edu (4 occurrences)

### Current Formula Range:

**File:** `intelligence/content/fullread.py:166-187`

```python
def _credibility_from(url: str, text: str) -> float:
    score = 0.0
    if p.scheme == "https":
        score += 0.15
    if host.endswith(".gov") or host.endswith(".edu"):
        score += 0.25
    if _AUTHZ_WORDS.search(text or ""):
        score += 0.15
    return max(0.0, min(1.0, score))
```

**Score Breakdown:**
- Minimum: 0.0 (no signals)
- HTTPS only: 0.15
- HTTPS + .gov/.edu: 0.40
- Maximum: 0.55 (HTTPS + .gov/.edu + keywords)
- **Typical observed: 0.12-0.32**

---

## 2. Proposed Tier Scores

### Tier Distribution:

- **Tier 1:** 0.85-0.90 (.gov, peer-reviewed journals, fact-checkers)
- **Tier 2:** 0.65-0.75 (.edu, established references, reputable news)
- **Tier 3:** 0.45-0.55 (has credentials, trade publications)
- **Tier 4:** 0.20-0.30 (no signals, unknown sources)

**Comparison:**
- Current max: 0.55 (.gov with all signals)
- Proposed Tier 1: 0.90 (.gov)
- **Increase: +0.35 (64% higher)**

- Current typical: 0.12-0.32
- Proposed Tier 2-4: 0.30-0.75
- **Increase: +0.18 to +0.43**

---

## 3. Mathematical Impact Chain

### Authority Calculation Impact

**Formula:** `authority = 0.6 * domain_score + 0.4 * credibility`

**File:** `intelligence/content/grade.py:532`

#### Example 1: engineeringtoolbox.com (.com domain)

| Model | Credibility | Domain | Authority | Change |
|-------|-------------|--------|-----------|--------|
| Current | 0.12 | 0.50 | 0.348 | baseline |
| Proposed (Tier 2) | 0.70 | 0.50 | 0.580 | +0.232 (+66.7%) |

#### Example 2: usda.gov (.gov domain)

| Model | Credibility | Domain | Authority | Change |
|-------|-------------|--------|-----------|--------|
| Current | 0.32 | 0.95 | 0.698 | baseline |
| Proposed (Tier 1) | 0.90 | 0.95 | 0.930 | +0.232 (+33.2%) |

**FACT:** Authority increases by +0.232 (absolute) regardless of domain, because credibility has 40% weight.

---

### Item Grade Impact

**Formula:** `item_grade = 0.40*semantic + 0.30*frame + 0.20*authority + 0.10*coverage`

**File:** `intelligence/content/grade.py:319-324`

Using real scores from execution trace:
- semantic = 0.62
- frame = 0.58
- coverage = 1.0

#### Example 1: engineeringtoolbox.com

| Model | Authority | Item Grade | Change |
|-------|-----------|------------|--------|
| Current | 0.348 | 0.592 | baseline |
| Proposed | 0.580 | 0.638 | +0.046 (+7.8%) |

#### Example 2: usda.gov

| Model | Authority | Item Grade | Change |
|-------|-----------|------------|--------|
| Current | 0.698 | 0.662 | baseline |
| Proposed | 0.930 | 0.708 | +0.046 (+7.0%) |

**FACT:** Item grade increases by ~0.046 (7-8%) because authority has 20% weight in formula.

---

### Arm Strength Impact

**Formula:** Diminishing returns with weights [1.0, 0.7, 0.5, 0.35], normalized by sum

**File:** `intelligence/content/p25_aggregate.py:48-62`

Assuming 4 items with same grade:

| Model | Item Grade | Raw Arm | Normalized | Change |
|-------|------------|---------|------------|--------|
| Current | 0.592 | 1.509 | 0.592 | baseline |
| Proposed | 0.638 | 1.627 | 0.638 | +0.046 (+7.8%) |

---

### After Quality Multipliers

Quality multipliers from execution trace:
- diversity = 0.55
- consistency = 1.0
- breadth = 0.8
- **Combined: 0.44**

| Model | Normalized Arm | After Multipliers | Change |
|-------|----------------|-------------------|--------|
| Current | 0.592 | 0.260 | baseline |
| Proposed | 0.638 | 0.281 | +0.020 (+7.8%) |

**File:** `intelligence/content/p25_aggregate.py:116-118`

```python
sa_enhanced = sa * diversity * consistency * breadth
sb_enhanced = sb * diversity * consistency * breadth
```

---

## 4. Threshold Analysis

### Verdict Determination Thresholds

**File:** `intelligence/content/p25_aggregate.py:120-128`

```python
if sa_enhanced < 0.12 and sb_enhanced < 0.12:
    label = "insufficient"
else:
    if (sa_enhanced - sb_enhanced) >= delta:  # delta = 0.15
        label = "supports"
    elif (sb_enhanced - sa_enhanced) >= delta:
        label = "challenges"
    else:
        label = "mixed"
```

**Thresholds:**
- Insufficient: Both arms < 0.12
- Supports: support_arm - challenge_arm ≥ 0.15
- Challenges: challenge_arm - support_arm ≥ 0.15
- Mixed: Difference < 0.15

### Will Higher Scores Cross Thresholds?

**Current Test Case (Water boils at 100°C):**
- Arm strength (after multipliers): 0.260
- Verdict: **Above 0.12 threshold** (not insufficient)
- Actual verdict from trace: "insufficient"

**Wait - discrepancy found. Checking trace again:**

From `docs/EXECUTION_TRACE.md:129`:
```
Arm strength: {'support': 0.099333, 'challenge': 0.099333, ...}
```

**FACT:** Actual arm strength is 0.099, which is **below 0.12 threshold**.

**Proposed Impact:**
- Current: 0.099 (insufficient)
- Proposed: 0.099 + 0.020 = 0.119 (still insufficient, barely)
- **Verdict: Would still be "insufficient" (below 0.12 by 0.001)**

**To cross threshold to "mixed/supports":**
- Need: 0.12 minimum
- Current: 0.099
- Required increase: +0.021
- Proposed increase: +0.020
- **CONCLUSION: Proposed tier model brings us to edge of threshold but doesn't cross it**

---

### Confidence Score Impact

**Formula:**

**File:** `intelligence/content/p25_aggregate.py:85-92`

```python
conf = (
    0.25 * total +        # max(sa, sb) weighted
    0.25 * balance +      # abs(sa - sb)
    0.15 * count_factor + # min(1.0, (n_items) / 6.0)
    0.15 * avg_authority +  # ← Authority weight
    0.10 * diversity +
    0.10 * consistency
)
```

**Authority contribution: 15% weight**

From execution trace:
- Current confidence: 0.403

Simulating proposed impact:
- Current avg_authority: (0.348 + 0.698) / 2 = 0.523
- Proposed avg_authority: (0.580 + 0.930) / 2 = 0.755
- Change in avg_authority: +0.232

**Confidence change:**
- Change = 0.15 * 0.232 = +0.0348
- Current: 0.403
- Proposed: 0.403 + 0.0348 = **0.438**
- **Increase: +0.035 (+8.7%)**

---

## 5. Breaking Points Identified

### Code That Expects Low Credibility:

**NONE FOUND**

Search results:
```bash
grep -r "credibility.*<\|credibility.*>\|if.*credibility" intelligence/ --include="*.py" -n
```

Found only:
- Line 166: Function definition
- Line 302: Check if key exists (not comparison)
- Line 430: Function parameter default

**FACT:** No code compares credibility to thresholds.

### Hardcoded Thresholds:

**NONE FOUND**

No code checks if credibility is above/below specific values.

### Comparisons That Could Break:

**NONE FOUND**

### Credibility Multipliers:

**FOUND:** Temporal and geographic weights multiply credibility.

**File:** `intelligence/content/fullread.py:298-307`

```python
temporal_weight = calculate_temporal_weight(pub_date, claim_category)
geographic_weight = check_geographic_match(claim_scope, item_scope)

if 'credibility' in item:
    item['credibility'] = item['credibility'] * temporal_weight * geographic_weight
```

**RISK:** If temporal/geographic weights < 1.0, they reduce credibility. With higher base credibility, the reduced value might still be high enough.

**Example:**
- Current: cred=0.12 * temporal=0.5 = 0.06 (very low)
- Proposed: cred=0.70 * temporal=0.5 = 0.35 (still moderate)

**FACT:** Multipliers affect proportionally, but higher base means higher floor.

---

## 6. Risk Assessment

### LOW RISK:

1. **No hardcoded thresholds** - Code doesn't check credibility ranges
2. **Authority formula handles full range** - Takes 0-1 input, produces 0-1 output
3. **Item grade bounded** - Always clamped to [0, 1]
4. **Arm strength normalized** - Divided by max possible weights
5. **Confidence bounded** - Always clamped to [0, 1]

### MEDIUM RISK:

1. **Verdict threshold proximity** - Proposed increase (+0.020) brings arm strength from 0.099 to 0.119, just below "insufficient" threshold (0.12)
   - Risk: Small changes in other factors could push across threshold
   - Mitigation: This is desired behavior (better evidence = stronger verdict)

2. **Temporal/geographic multipliers** - Higher base credibility means multipliers have less proportional effect
   - Current: 0.12 * 0.5 = 0.06 (50% reduction)
   - Proposed: 0.70 * 0.5 = 0.35 (50% reduction)
   - Risk: Old/distant evidence still gets moderate credibility
   - Mitigation: May need to adjust multiplier weights

3. **Confidence score inflation** - Confidence increases by ~8.7%
   - Current: 0.403
   - Proposed: 0.438
   - Risk: Confidence might be overstated for low-quality evidence
   - Mitigation: Tier 4 (0.30) keeps floor reasonable

### HIGH RISK:

**NONE IDENTIFIED**

---

## 7. Expected Verdict Changes

### Current Test Case (Water boils at 100°C):

**Current State (from execution trace):**
- Credibility: 0.120-0.320
- Authority: 0.348-0.698
- Item grades: 0.240-0.591
- Arm strength: 0.099 (after multipliers)
- Verdict: **insufficient** (< 0.12 threshold)
- Confidence: 0.403

**Proposed State (calculated):**
- Credibility: 0.30-0.90 (Tier 4 to Tier 1)
- Authority: 0.580-0.930 (+0.232)
- Item grades: 0.286-0.637 (+0.046)
- Arm strength: 0.119 (after multipliers) (+0.020)
- Verdict: **still insufficient** (< 0.12 by 0.001)
- Confidence: 0.438 (+0.035)

### Verdict Change Prediction:

**insufficient → insufficient** (no change, but very close to threshold)

**Why no change:**
- Threshold: 0.12
- Current: 0.099 (21% below threshold)
- Proposed: 0.119 (0.8% below threshold)
- **Need +0.021, getting +0.020**

**FACT:** Tier model brings verdict to edge of threshold but doesn't cross it for this specific test case.

**For stronger evidence:**
- Current: 0.11 (insufficient)
- Proposed: 0.11 + 0.020 = 0.13 (mixed/supports)
- **FACT:** Cases near threshold will flip verdicts

---

## 8. Backward Compatibility

### Items With Old Credibility Scores:

**Scenario:** Pipeline has mix of items with old credibility (0-0.55) and new tier scores (0.30-0.90)

**Impact:**
- Authority calculation accepts any 0-1 value
- No range checks in code
- **FACT:** Old and new scores can coexist

**Issue:**
- Old scores will produce lower authority/grades
- Mixed-score arms will have inconsistent weighting
- **Risk:** Transitional period might have unfair comparisons

### Fallback Behavior:

**File:** `intelligence/content/grade.py:301-303`

```python
if features.get('p21_available'):
    credibility = features['p21'].get('credibility', 0.5)
else:
    credibility = 0.5
```

**Default:** 0.5 if credibility missing

**Tier Model Default:**
- Should default to Tier 3 (0.55) or Tier 4 (0.30)?
- Current 0.5 default is between Tier 3 and Tier 4
- **FACT:** Default stays reasonable in tier model

---

## 9. Required Changes for Tier Model

### Files That Must Change:

#### 1. intelligence/content/fullread.py

**Function:** `_credibility_from()` (line 166)

**Current signature:**
```python
def _credibility_from(url: str, text: str) -> float:
```

**Proposed signature:**
```python
def _credibility_from(url: str, text: str) -> Tuple[int, float, str]:
    # Returns: (tier, score, rationale)
```

**Impact:** Both call sites must unpack tuple

**Call sites:**
- Line 204: `item["credibility"] = _credibility_from(...)`
- Line 285: `item["credibility"] = round(_credibility_from(...), 3)`

**Proposed changes:**
```python
# Line 204
tier, score, rationale = _credibility_from(item.get("url") or "", "")
item["credibility"] = score
item["credibility_tier"] = tier
item["credibility_rationale"] = rationale

# Line 285
tier, score, rationale = _credibility_from(item.get("url") or "", read)
item["credibility"] = round(score, 3)
item["credibility_tier"] = tier
item["credibility_rationale"] = rationale
```

#### 2. intelligence/content/fullread.py (context weights)

**Function:** `evaluate_full_evidence()` (line 303)

**Current:**
```python
item['credibility'] = item['credibility'] * temporal_weight * geographic_weight
```

**Issue:** Multiplying tier score might drop it below tier boundary

**Options:**
- A) Multiply score, recalculate tier from result
- B) Keep tier fixed, only multiply score
- C) Adjust tier down if score drops significantly

**FACT:** Decision needed on how temporal/geographic weights affect tiers

### Files That DON'T Need Changes:

- `intelligence/content/grade.py` - Reads credibility as float, range-agnostic
- `intelligence/content/p25_aggregate.py` - Reads authority, not credibility directly
- `intelligence/consensus/build.py` - Reads credibility with .get() fallback
- All test files - Display only, no logic changes needed

**FACT:** Most code is already compatible with new credibility range.

---

## 10. Testing Requirements

### Unit Tests Needed:

1. **test_credibility_tier_calculation()**
   - Verify each tier produces correct score range
   - Verify rationale matches tier assignment

2. **test_credibility_tier_gov_sources()**
   - Verify .gov sources get Tier 1 (0.85-0.90)
   - Verify .edu sources get Tier 2 (0.65-0.75)

3. **test_credibility_tier_unknown_sources()**
   - Verify unknown sources get Tier 4 (0.20-0.30)

4. **test_authority_with_tier_scores()**
   - Verify authority calculation with tier scores
   - Verify authority stays in [0, 1] range

5. **test_temporal_weight_on_tier_scores()**
   - Verify temporal multiplier affects tier score correctly
   - Verify tier assignment updates or stays fixed (based on decision)

### Integration Tests Needed:

6. **test_tier_scores_through_pipeline()**
   - Run full pipeline with tier model
   - Verify item grades increase as expected
   - Verify arm strength increases as expected
   - Verify verdict logic still works

7. **test_tier_scores_cross_threshold()**
   - Test case where tier model pushes arm strength from 0.11 to 0.13
   - Verify verdict changes from "insufficient" to "mixed/supports"

8. **test_mixed_credibility_scores()**
   - Mix old credibility items (0.12) with new tier items (0.70)
   - Verify both score types process correctly
   - Verify no crashes or range errors

### Regression Tests Needed:

9. **test_baseline_verdict_unchanged()**
   - Run water boiling point test with tier model
   - Expected: insufficient (but at 0.119 vs 0.099)
   - Verify confidence increases to ~0.44

10. **test_high_authority_sources_boosted()**
    - Test with .gov source
    - Verify authority increases from 0.698 to 0.930
    - Verify item grade increases accordingly

11. **test_confidence_formula_bounded()**
    - Test that confidence stays ≤ 1.0 with high tier scores
    - Test edge case: all Tier 1 sources

---

## 11. Numerical Summary

### Impact Magnitudes:

| Metric | Current | Proposed | Absolute Change | Relative Change |
|--------|---------|----------|-----------------|-----------------|
| Credibility (.com) | 0.12 | 0.70 | +0.58 | +483% |
| Credibility (.gov) | 0.32 | 0.90 | +0.58 | +181% |
| Authority (.com) | 0.348 | 0.580 | +0.232 | +67% |
| Authority (.gov) | 0.698 | 0.930 | +0.232 | +33% |
| Item Grade (.com) | 0.592 | 0.638 | +0.046 | +7.8% |
| Item Grade (.gov) | 0.662 | 0.708 | +0.046 | +7.0% |
| Arm Strength | 0.099 | 0.119 | +0.020 | +20% |
| Confidence | 0.403 | 0.438 | +0.035 | +8.7% |

### Formula Attenuation:

Credibility increase flows through formulas with diminishing effect:
- Credibility: +483% (base input)
- Authority: +67% (40% weight in formula)
- Item Grade: +7.8% (20% weight in formula)
- Arm Strength: +20% (complex aggregation)
- Confidence: +8.7% (15% weight in formula)

**FACT:** High initial increase (483%) is attenuated to reasonable increases in final scores (8-20%) due to weighted formulas and normalization.

---

## 12. Verdict Threshold Sensitivity

### Current Thresholds:

- Insufficient: < 0.12
- Mixed: ≥ 0.12, difference < 0.15
- Supports/Challenges: difference ≥ 0.15

### Sensitivity Analysis:

**At threshold boundary (current = 0.099):**
- To cross insufficient→mixed: need +0.021
- Tier model provides: +0.020
- **Result:** Stays insufficient (99.5% of needed increase)**

**At 110% of threshold (current = 0.108):**
- To cross insufficient→mixed: need +0.012
- Tier model provides: +0.020
- **Result:** Crosses to mixed**

**At 120% of threshold (current = 0.118):**
- To cross insufficient→mixed: need +0.002
- Tier model provides: +0.020
- **Result:** Crosses to mixed**

**FACT:** Cases within 20% of threshold will flip verdicts with tier model.

### Distribution Estimate:

If threshold is at 0.12:
- Current below: 0.08-0.11 (33% of range)
- Proposed: 0.10-0.13 (some cross threshold)

**Without actual distribution data, estimate:**
- ~30-40% of "insufficient" verdicts near threshold may flip to "mixed"
- Exact percentage depends on real evidence quality distribution

---

## 13. Rollout Strategy Considerations

### Phase 1: Compatibility Layer
- Add tier fields alongside existing credibility
- Both old and new scores coexist
- No breaking changes

### Phase 2: Monitor Metrics
- Track verdict distribution changes
- Identify threshold sensitivity
- Adjust if needed

### Phase 3: Full Cutover
- Remove old credibility calculation
- Tier model only

**FACT:** Gradual rollout is safe because code accepts full 0-1 range.

---

**END OF IMPACT ANALYSIS**
