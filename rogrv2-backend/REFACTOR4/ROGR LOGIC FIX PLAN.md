# ROGRv2 Implementation Plan
**Complete the Deterministic Model - Fix Missing Logic**

**Status:** Draft v1.0  
**Date:** 2025-10-15  
**Goal:** Implement all missing features, fix misplaced logic, complete deterministic pipeline before AI assist layer

---

## EXECUTIVE SUMMARY

**Current State:** 62.5% accuracy (5/8 baseline claims correct)
**Target:** 99% accuracy on verifiable claims

**What's Wrong:**
- 26 missing features that were supposed to be there
- Logic in wrong places (stance detection, ranking, authority)
- Scale bugs (0-10 vs 0-1)
- Module overlap creating competing grades
- Consensus comparing labels instead of evidence
- No claim complexity handling
- No unverifiable claim detection
- Insufficient semantic depth
- No confidence calibration

**What We Need:**
1. **Foundation (Phases 0-7):** Fix bugs, add missing logic â†’ 80% accuracy
2. **Quality Amplification (Phase 8):** Source reliability, claim classification, contradiction resolution â†’ 90% accuracy
3. **Precision Handling (Phase 9):** Numeric precision, temporal/geographic context, semantic depth â†’ 95% accuracy
4. **Calibration (Phase 10):** Confidence calibration, edge cases, unverifiable detection â†’ 99% accuracy
5. **Validation (Phase 11):** Comprehensive testing, prove 99% accuracy

**Timeline:** 16 weeks (4 months)

**Success Criteria:**
- 99% accuracy on verifiable factual claims
- 99% accuracy detecting unverifiable claims
- Confidence calibration: 95%+ confidence â†’ 99%+ correct
- <0.5% false positive rate per verdict type

**Risk Management:**
- DO NOT break existing tests
- Keep backward compatibility where possible
- Implement incrementally with validation at each step
- Maintain rollback points
- Conservative confidence thresholds (better to say "mixed" than be wrong)

---

## IMPLEMENTATION PHASES

### Phase 0: Preparation & Safety (Week 1)
**Goal:** Set up for safe implementation

**Tasks:**
1. Create feature branch: `feature/complete-deterministic-model`
2. Snapshot current baseline test results (62.5% accuracy)
3. Create comprehensive test suite for each stage
4. Document current behavior for rollback reference
5. Set up validation checkpoints

**Deliverables:**
- [ ] Feature branch created
- [ ] Baseline results documented
- [ ] Test suite expanded
- [ ] Rollback documentation

---

### Phase 1: Fix Critical Bugs (Week 1-2)
**Goal:** Fix bugs that break everything downstream

#### 1.1: Scale Normalization Bug (P20)
**File:** `intelligence/content/grade.py` line 231

**Current:**
```python
grade = round(min(score, 8.0) * (10.0/8.0), 2)  # 0-10 scale âŒ
```

**Fix:**
```python
grade = round(min(score, 8.0) / 8.0, 3)  # 0-1 scale âœ“
```

**Impact:** Fixes 10x inflation bug when P23 fails
**Risk:** LOW - Simple change, well-understood
**Validation:** Check P25 receives 0-1 values, rerun baseline

---

#### 1.2: Module Grade Consolidation (P20/P21/P23/P24)
**Goal:** ONE canonical item_grade (0-1) per item

**Current Problem:**
- P20: item_grade (0-10) 
- P21: grade_full (0-10)
- P23: item_grade (0-1, overwrites P20)
- P24: best_frame_score (0-1)
- P25: Combines frame + item_grade

**Solution Strategy:**

**Option A: P20 as Orchestrator** (RECOMMENDED)
- P20 calls P21, P23, P24 as helpers
- P20 produces ONE item_grade (0-1)
- P21/P23/P24 return features, not grades
- P20 does final fusion

**Option B: New P20_consolidate Module**
- Keep existing modules as-is
- New module combines their outputs
- Less refactoring but adds complexity

**Recommendation:** Option A

**Implementation:**
1. Refactor P20 to call P21/P23/P24
2. P21/P23/P24 return feature dictionaries
3. P20 fuses features into single item_grade
4. Remove grade_full, best_frame_score as separate outputs
5. Keep credibility as metadata

**Files:**
- `intelligence/content/grade.py` (P20)
- `intelligence/content/full_read.py` (P21)
- `intelligence/content/semantic_read.py` (P23)
- `intelligence/content/frames.py` (P24)

**Impact:** Clean architecture, single source of truth
**Risk:** MEDIUM - Requires coordination across modules
**Validation:** Check item_grade is 0-1, all features present

---

### Phase 2: Evidence Curation Filter (P19) (Week 2-3)
**Goal:** Implement proper filtering BEFORE selection

#### 2.1: Fast Relatedness Filter
**File:** `intelligence/gather/pipeline.py` - new function

**Add:** `filter_unrelated(claim, candidates)` before ranking

**Logic:**
```python
def filter_unrelated(claim_text, claim_entities, claim_numbers, candidates):
    """Fast deterministic filter for obviously unrelated items"""
    filtered = []
    for candidate in candidates:
        # Quick checks (no AI, no embeddings)
        entity_overlap = count_entity_matches(claim_entities, candidate['snippet'])
        number_overlap = count_number_matches(claim_numbers, candidate['snippet'])
        keyword_overlap = lexical_overlap(claim_text, candidate['snippet'])
        
        # If ANY anchor present, keep it
        if entity_overlap >= 1 or number_overlap >= 1 or keyword_overlap > 0.3:
            filtered.append(candidate)
        else:
            candidate['dropped_reason'] = 'no_anchors'
            # Log but don't include
    
    return filtered
```

**Thresholds:**
- At least 1 entity OR 1 number OR 30% keyword overlap
- Conservative (better to keep ambiguous than discard relevant)

**Impact:** Drops obvious junk before ranking
**Risk:** LOW - Conservative thresholds, logged
**Validation:** Check dropped items are truly unrelated

---

#### 2.2: Quality Gate
**File:** `intelligence/gather/pipeline.py` - new function

**Add:** `quality_gate(candidates)` before ranking

**Logic:**
```python
def quality_gate(candidates):
    """Filter out low-quality sources"""
    filtered = []
    for candidate in candidates:
        # Check domain quality
        domain = extract_domain(candidate['url'])
        
        # Block known junk
        if domain in BLOCKED_DOMAINS:
            candidate['dropped_reason'] = 'blocked_domain'
            continue
        
        # Check format
        if candidate['url'].endswith('.pdf') and domain not in WHITELIST_PDF_DOMAINS:
            candidate['dropped_reason'] = 'uncrawlable_pdf'
            continue
        
        # Check language
        if not is_english(candidate['snippet']):
            candidate['dropped_reason'] = 'non_english'
            continue
        
        # Dedup by domain
        if domain_count(filtered, domain) >= 2:
            candidate['dropped_reason'] = 'domain_duplicate'
            continue
        
        filtered.append(candidate)
    
    return filtered
```

**Impact:** Removes junk sources
**Risk:** LOW - Conservative filters
**Validation:** Check filtered items are appropriate

---

#### 2.3: Fix Pipeline Order
**File:** `intelligence/gather/pipeline.py`

**Current Order:**
```
Search â†’ Assign Arm â†’ Rank â†’ Select Top 3
```

**Fixed Order:**
```
Search â†’ Filter Unrelated â†’ Quality Gate â†’ Rank â†’ Select Top 3-5
```

**Note:** Arm still assigned by query source (per SAGPT - full stance detection stays in P20)

**Impact:** Proper curation flow
**Risk:** LOW - Additive changes
**Validation:** Check pipeline produces 3-5 quality items per arm

---

### Phase 3: Individual Evidence Grading Enhancement (Week 3-4)
**Goal:** Incorporate authority into item_grade

#### 3.1: Authority Scoring
**File:** `intelligence/content/grade.py` (P20)

**Add:** Authority factor to item_grade calculation

**Logic:**
```python
def calculate_authority_score(url, credibility):
    """Score source authority 0-1"""
    domain = extract_domain(url)
    
    # Domain type scoring
    if domain.endswith('.gov'):
        domain_score = 1.0
    elif domain.endswith('.edu'):
        domain_score = 0.9
    elif is_peer_reviewed(url):  # Check for journal patterns
        domain_score = 0.85
    elif domain in TRUSTED_NEWS:  # Reuters, AP, BBC, etc.
        domain_score = 0.75
    elif domain in TRUSTED_ORGS:  # WHO, CDC, UN, etc.
        domain_score = 0.8
    else:
        domain_score = 0.5  # Default
    
    # Combine with existing credibility score
    authority = 0.6 * domain_score + 0.4 * credibility
    return authority
```

**Integration into item_grade:**
```python
# Current fusion (P25 does this now):
item_strength = 0.55 * frame_score + 0.45 * item_grade

# New fusion (P20 should do this):
item_grade = (
    0.40 * semantic_similarity +  # P23
    0.30 * frame_match +           # P24
    0.20 * authority +             # NEW
    0.10 * coverage_weight         # Existing
)
```

**Impact:** Authority influences evidence strength
**Risk:** MEDIUM - Changes grade calculation
**Validation:** Check .gov sources score higher

---

### Phase 4: Arm Aggregation Intelligence (P25) (Week 4-5)
**Goal:** Add missing factors to arm comparison

#### 4.1: Source Diversity Checking
**File:** `intelligence/content/p25_aggregate.py`

**Add:** Diversity penalty for same-domain clustering

**Logic:**
```python
def calculate_diversity_score(items):
    """Score source diversity 0-1"""
    domains = [extract_domain(item['url']) for item in items]
    unique_domains = len(set(domains))
    total_items = len(items)
    
    diversity = unique_domains / total_items
    
    # Bonus for cross-source corroboration
    if unique_domains >= 3 and total_items >= 3:
        diversity = min(1.0, diversity * 1.1)
    
    return diversity
```

**Integration:**
```python
# Modify arm strength calculation
arm_strength_raw = sum(weighted_items)
diversity_multiplier = 0.8 + (0.2 * diversity_score)  # 0.8 to 1.0 range
arm_strength = arm_strength_raw * diversity_multiplier
```

**Impact:** Penalizes single-source evidence
**Risk:** LOW - Multiplier approach
**Validation:** Check diverse sources score higher

---

#### 4.2: Internal Consistency Checking
**File:** `intelligence/content/p25_aggregate.py`

**Add:** Numeric consistency check within arm

**Logic:**
```python
def calculate_consistency_score(items, claim_numbers):
    """Check if arm items agree on numbers 0-1"""
    if not claim_numbers:
        return 1.0  # N/A for non-numeric claims
    
    # Extract numbers from each item's matched text
    item_numbers = []
    for item in items:
        nums = extract_numbers(item.get('matched_span', ''))
        item_numbers.append(nums)
    
    # Check variance
    if len(item_numbers) < 2:
        return 1.0  # Only one item, no conflict possible
    
    # For each claim number, check item agreement
    conflicts = 0
    for claim_num in claim_numbers:
        item_values = [nums.get(claim_num['type'], None) for nums in item_numbers]
        item_values = [v for v in item_values if v is not None]
        
        if len(item_values) >= 2:
            variance = calculate_variance(item_values)
            if variance > THRESHOLD:  # e.g., >10% variance
                conflicts += 1
    
    consistency = 1.0 - (conflicts / max(len(claim_numbers), 1))
    return max(0.0, consistency)
```

**Integration:**
```python
# Modify arm strength with consistency
arm_strength = arm_strength_raw * diversity_multiplier * consistency_score
```

**Impact:** Penalizes conflicting evidence
**Risk:** MEDIUM - Complex numeric extraction
**Validation:** Check conflicting numbers reduce score

---

#### 4.3: Coverage Breadth Analysis
**File:** `intelligence/content/p25_aggregate.py`

**Add:** Detect repetition vs complementary angles

**Logic:**
```python
def calculate_breadth_score(items):
    """Measure breadth vs repetition 0-1"""
    if len(items) < 2:
        return 1.0
    
    # Use matched spans for comparison
    spans = [item.get('matched_span', '') for item in items]
    
    # Calculate pairwise similarity
    similarities = []
    for i in range(len(spans)):
        for j in range(i+1, len(spans)):
            sim = text_similarity(spans[i], spans[j])  # Trigram overlap
            similarities.append(sim)
    
    avg_similarity = sum(similarities) / len(similarities)
    
    # High similarity = repetition = low breadth
    # Low similarity = diverse angles = high breadth
    breadth = 1.0 - avg_similarity
    return breadth
```

**Integration:**
```python
# Breadth bonus to arm strength
breadth_bonus = 1.0 + (0.1 * breadth_score)  # Up to +10%
arm_strength = arm_strength_raw * diversity_multiplier * consistency_score * breadth_bonus
```

**Impact:** Rewards complementary evidence
**Risk:** LOW - Bonus approach
**Validation:** Check repetitive evidence scores lower

---

#### 4.4: Enhanced Confidence Formula
**File:** `intelligence/content/p25_aggregate.py`

**Current:**
```python
confidence = 0.4 * total + 0.4 * balance + 0.2 * count
```

**Enhanced:**
```python
confidence = (
    0.25 * total_strength +      # Overall evidence volume
    0.25 * balance +              # Gap between arms
    0.15 * count +                # Number of items
    0.15 * avg_authority +        # Source authority
    0.10 * diversity +            # Source diversity
    0.10 * consistency            # Internal consistency
)
```

**Impact:** Confidence reflects all quality factors
**Risk:** LOW - Formula expansion
**Validation:** Check authoritative/diverse evidence increases confidence

---

### Phase 5: Dual Researcher Diversification (Week 5-6)
**Goal:** Make R1 and R2 truly different

#### 5.1: Query Strategy Differentiation
**File:** `intelligence/gather/plan.py`

**Add:** Lane-specific query generation

**R1 Strategy (Precision):**
```python
def generate_queries_r1(claim, entities, numbers):
    """Precision queries - quoted, anchored, exact"""
    queries = []
    
    # Exact quoted phrases
    queries.append(f'"{claim.text}"')
    
    # Anchored entity + number combinations
    for entity in entities:
        for number in numbers:
            queries.append(f'"{entity}" {number.value}{number.unit}')
    
    # Conservative counter-frames (specific)
    queries.append(f'"{entities[0]}" actual value')
    
    return queries
```

**R2 Strategy (Recall):**
```python
def generate_queries_r2(claim, entities, numbers):
    """Recall queries - paraphrased, exploratory, broad"""
    queries = []
    
    # Unquoted, natural language
    queries.append(claim.text)
    
    # Paraphrased versions
    queries.extend(generate_paraphrases(claim.text))
    
    # Broader synonyms
    for entity in entities:
        synonyms = get_synonyms(entity)
        queries.extend([f"{syn} {claim.predicate}" for syn in synonyms])
    
    # Aggressive counter-frames (general)
    queries.append(f"{entities[0]} variation exceptions")
    queries.append(f"{entities[0]} different conditions")
    
    return queries
```

**Impact:** Different evidence from each researcher
**Risk:** MEDIUM - Query generation changes
**Validation:** Check R1/R2 find different sources

---

#### 5.2: Analysis Threshold Differentiation
**File:** `intelligence/content/grade.py`, `intelligence/content/p25_aggregate.py`

**Add:** Lane-specific parameters

**Config:**
```python
LANE_CONFIGS = {
    'R1': {
        'stance_threshold': 0.70,      # Strict
        'min_item_grade': 0.60,        # High bar
        'verdict_threshold': 0.20,     # Wide gap required
        'min_confidence': 0.65,        # Conservative
    },
    'R2': {
        'stance_threshold': 0.50,      # Lenient
        'min_item_grade': 0.40,        # Lower bar
        'verdict_threshold': 0.15,     # Narrower gap okay
        'min_confidence': 0.45,        # Exploratory
    }
}
```

**Usage:**
```python
def grade_item(claim, item, lane='R1'):
    config = LANE_CONFIGS[lane]
    # Use lane-specific thresholds
    if stance_score < config['stance_threshold']:
        return None  # Below threshold for this lane
```

**Impact:** R1 strict, R2 permissive
**Risk:** LOW - Config-driven
**Validation:** Check R1 has higher thresholds

---

#### 5.3: Parallel Execution
**File:** `intelligence/orchestrate.py`

**Current:**
```python
r1_result = run_researcher('R1', claim)
r2_result = run_researcher('R2', claim)  # Waits for R1
```

**Fixed:**
```python
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    future_r1 = executor.submit(run_researcher, 'R1', claim)
    future_r2 = executor.submit(run_researcher, 'R2', claim)
    
    r1_result = future_r1.result()
    r2_result = future_r2.result()
```

**Impact:** Faster execution
**Risk:** LOW - Standard concurrency
**Validation:** Check timing, both complete

---

### Phase 6: Evidence-Based Consensus (P27) (Week 6-7)
**Goal:** Compare evidence quality, not just verdicts

#### 6.1: Evidence Quality Comparison
**File:** `intelligence/consensus/build.py`

**Add:** Compare evidence metrics between R1 and R2

**Logic:**
```python
def compare_evidence_quality(r1_items, r2_items):
    """Compare evidence quality across researchers"""
    
    # Calculate aggregate quality metrics
    r1_quality = {
        'avg_grade': mean([item['item_grade'] for item in r1_items]),
        'avg_authority': mean([item.get('authority', 0.5) for item in r1_items]),
        'diversity': calculate_diversity_score(r1_items),
        'consistency': calculate_consistency_score(r1_items),
    }
    
    r2_quality = {
        'avg_grade': mean([item['item_grade'] for item in r2_items]),
        'avg_authority': mean([item.get('authority', 0.5) for item in r2_items]),
        'diversity': calculate_diversity_score(r2_items),
        'consistency': calculate_consistency_score(r2_items),
    }
    
    # Overall quality score
    r1_overall = (
        0.4 * r1_quality['avg_grade'] +
        0.3 * r1_quality['avg_authority'] +
        0.2 * r1_quality['diversity'] +
        0.1 * r1_quality['consistency']
    )
    
    r2_overall = (
        0.4 * r2_quality['avg_grade'] +
        0.3 * r2_quality['avg_authority'] +
        0.2 * r2_quality['diversity'] +
        0.1 * r2_quality['consistency']
    )
    
    return {
        'r1': r1_quality,
        'r2': r2_quality,
        'r1_overall': r1_overall,
        'r2_overall': r2_overall,
        'quality_gap': abs(r1_overall - r2_overall)
    }
```

**Impact:** Evidence-informed consensus
**Risk:** LOW - Additive analysis
**Validation:** Check quality comparison makes sense

---

#### 6.2: Intelligent Disagreement Resolution
**File:** `intelligence/consensus/build.py`

**Current Logic:**
```python
if r1_label == r2_label:
    consensus = r1_label
    confidence_bonus = 0.10
elif arm_balance > 0.20:
    consensus = stronger_label
    confidence_penalty = 0.05
else:
    consensus = 'mixed'
    confidence_penalty = 0.10
```

**Enhanced Logic:**
```python
def resolve_disagreement(r1_verdict, r2_verdict, evidence_comparison):
    """Intelligently resolve disagreement using evidence quality"""
    
    if r1_verdict['label'] == r2_verdict['label']:
        # Agreement - boost confidence
        return {
            'label': r1_verdict['label'],
            'confidence': mean([r1_verdict['confidence'], r2_verdict['confidence']]) * 1.10,
            'rationale': 'Both researchers agree',
        }
    
    # Disagreement - examine evidence quality
    quality_gap = evidence_comparison['quality_gap']
    
    if quality_gap > 0.15:
        # Significant quality difference - trust better evidence
        if evidence_comparison['r1_overall'] > evidence_comparison['r2_overall']:
            better = r1_verdict
            better_researcher = 'R1'
        else:
            better = r2_verdict
            better_researcher = 'R2'
        
        return {
            'label': better['label'],
            'confidence': better['confidence'] * 0.95,  # Slight penalty for disagreement
            'rationale': f'{better_researcher} has stronger evidence (quality gap: {quality_gap:.2f})',
        }
    
    else:
        # Similar quality - genuine ambiguity
        # Check if arm strengths suggest direction
        r1_balance = r1_verdict['arm_A'] - r1_verdict['arm_B']
        r2_balance = r2_verdict['arm_A'] - r2_verdict['arm_B']
        
        if abs(r1_balance - r2_balance) < 0.10:
            # Very close - mixed
            return {
                'label': 'mixed',
                'confidence': mean([r1_verdict['confidence'], r2_verdict['confidence']]) * 0.90,
                'rationale': 'Evidence is genuinely mixed across both researchers',
            }
        else:
            # One has clearer balance
            if abs(r1_balance) > abs(r2_balance):
                return {
                    'label': r1_verdict['label'],
                    'confidence': r1_verdict['confidence'] * 0.92,
                    'rationale': 'R1 shows clearer evidence balance',
                }
            else:
                return {
                    'label': r2_verdict['label'],
                    'confidence': r2_verdict['confidence'] * 0.92,
                    'rationale': 'R2 shows clearer evidence balance',
                }
```

**Impact:** Intelligent consensus based on evidence
**Risk:** MEDIUM - Complex logic
**Validation:** Check consensus makes sense for disagreements

---

#### 6.3: Evidence Synthesis
**File:** `intelligence/consensus/build.py`

**Add:** Combine best evidence from both researchers

**Logic:**
```python
def synthesize_evidence(r1_items, r2_items):
    """Combine best evidence from both researchers"""
    
    # Pool all items
    all_items = r1_items + r2_items
    
    # Deduplicate by URL
    seen_urls = set()
    unique_items = []
    for item in all_items:
        if item['url'] not in seen_urls:
            unique_items.append(item)
            seen_urls.add(item['url'])
    
    # Sort by item_grade * authority
    unique_items.sort(
        key=lambda x: x['item_grade'] * x.get('authority', 0.5),
        reverse=True
    )
    
    # Take top items per arm
    arm_A_items = [item for item in unique_items if item['arm'] == 'A'][:5]
    arm_B_items = [item for item in unique_items if item['arm'] == 'B'][:5]
    
    return {
        'arm_A': arm_A_items,
        'arm_B': arm_B_items,
        'synthesis_note': f'Combined best evidence from R1 and R2',
    }
```

**Impact:** Best evidence from both researchers
**Risk:** LOW - Deduplication + sorting
**Validation:** Check synthesis contains best items

---

### Phase 7: Query Validation Loop (Week 7-8)
**Goal:** Auto-refine queries that return off-topic results

#### 7.1: Query Validation
**File:** `intelligence/gather/pipeline.py`

**Add:** Validation after initial search

**Logic:**
```python
def validate_query_results(claim, query, results, max_retries=2):
    """Check if query returned on-topic results; refine if not"""
    
    if not results:
        return query, results  # No results to validate
    
    # Sample top 5 results
    sample = results[:5]
    
    # Check relevance using fast filter
    relevant_count = 0
    for result in sample:
        if is_related_fast(claim, result):
            relevant_count += 1
    
    relevance_rate = relevant_count / len(sample)
    
    # If >60% relevant, good
    if relevance_rate >= 0.6:
        return query, results
    
    # If <60% relevant and retries remaining, refine
    if max_retries > 0:
        refined_query = refine_query(claim, query, sample)
        new_results = search(refined_query)
        return validate_query_results(claim, refined_query, new_results, max_retries - 1)
    
    # Out of retries, return what we have
    return query, results

def refine_query(claim, original_query, off_topic_results):
    """Refine query to be more targeted"""
    
    # Add anchors if missing
    if not has_quotes(original_query):
        # Add entity quotes
        entities = extract_entities(claim.text)
        if entities:
            return f'"{entities[0]}" {original_query}'
    
    # Add units if numeric claim
    numbers = extract_numbers(claim.text)
    if numbers and not has_units(original_query):
        return f'{original_query} {numbers[0].unit}'
    
    # Add domain constraint
    return f'{original_query} site:.gov OR site:.edu'
```

**Impact:** Fewer off-topic results
**Risk:** MEDIUM - Adds search calls
**Validation:** Check refined queries improve relevance

---

### Phase 8: Quality Amplification (Week 9-10)
**Goal:** Achieve 90% accuracy through source reliability and claim handling

**Current State:** ~80% accuracy after Phase 1-7
**Target:** 90% accuracy
**Strategy:** Strict source filtering, claim classification, contradiction resolution

#### 8.1: Source Reliability Database
**File:** `intelligence/sources/reliability.py` (NEW)

**Create comprehensive source scoring system**

**Logic:**
```python
# Source reliability database
SOURCE_SCORES = {
    # Government (0.95-1.0)
    'nih.gov': 1.0,
    'cdc.gov': 1.0,
    'census.gov': 0.98,
    'nasa.gov': 0.98,
    'usgs.gov': 0.97,
    'noaa.gov': 0.97,
    
    # Academic (0.85-0.95)
    'nature.com': 0.95,
    'science.org': 0.95,
    'cell.com': 0.93,
    'nejm.org': 0.95,
    'thelancet.com': 0.94,
    
    # International Organizations (0.90-0.95)
    'who.int': 0.95,
    'un.org': 0.92,
    'worldbank.org': 0.90,
    
    # News - Tier 1 (0.75-0.85)
    'apnews.com': 0.85,
    'reuters.com': 0.85,
    'bbc.com': 0.82,
    'npr.org': 0.80,
    
    # News - Tier 2 (0.65-0.75)
    'nytimes.com': 0.75,
    'washingtonpost.com': 0.75,
    'theguardian.com': 0.72,
    
    # Encyclopedias (0.70-0.80)
    'britannica.com': 0.80,
    'wikipedia.org': 0.70,  # Lower due to editability
    
    # Fact-checkers (0.85-0.95)
    'snopes.com': 0.90,
    'factcheck.org': 0.92,
    'politifact.com': 0.88,
    
    # Default for unknown: 0.50
}

# Domain patterns
DOMAIN_PATTERNS = {
    r'\.gov$': 0.95,        # Any .gov
    r'\.edu$': 0.85,        # Any .edu
    r'\.org$': 0.60,        # Generic .org
}

# Bias/reliability metadata
SOURCE_METADATA = {
    'cnn.com': {'bias': 'left-center', 'reliability': 0.70, 'retraction_rate': 0.02},
    'foxnews.com': {'bias': 'right-center', 'reliability': 0.68, 'retraction_rate': 0.03},
    # ... extensive metadata
}

def get_source_reliability(url):
    """Get comprehensive source reliability score 0-1"""
    domain = extract_domain(url)
    
    # Check direct match
    if domain in SOURCE_SCORES:
        base_score = SOURCE_SCORES[domain]
    else:
        # Check patterns
        base_score = 0.50  # Default
        for pattern, score in DOMAIN_PATTERNS.items():
            if re.search(pattern, domain):
                base_score = score
                break
    
    # Adjust for metadata if available
    if domain in SOURCE_METADATA:
        meta = SOURCE_METADATA[domain]
        # Penalize high retraction rate
        retraction_penalty = meta.get('retraction_rate', 0) * 5  # Up to -0.25
        base_score = max(0.0, base_score - retraction_penalty)
    
    return base_score

def filter_by_reliability(items, min_score=0.65):
    """Filter evidence by source re
## SUCCESS CRITERIA

### Accuracy Targets by Phase
- **Phase 0-7 (Foundation):** 80% accuracy (up from 62.5%)
- **Phase 8 (Quality Amplification):** 90% accuracy
- **Phase 9 (Precision Handling):** 95% accuracy
- **Phase 10 (Calibration):** 99% accuracy on verifiable claims
- **Phase 11 (Validation):** Proven 99% accuracy across 1000+ test claims

### Breakdown by Claim Type (Final Targets)
- Simple factual claims: **99.5% accuracy**
- Complex factual claims: **99% accuracy**
- Historical claims: **99% accuracy**
- Scientific claims: **99% accuracy**
- Policy/causal claims: **95% accuracy** (or correctly mark "insufficient")
- Edge cases: **95% correctly** identified as mixed/insufficient
- Unverifiable detection: **99% accuracy** detecting unprovable claims

### Confidence Calibration Requirements
- **95-100% confidence** â†’ 99%+ correct
- **90-95% confidence** â†’ 95%+ correct
- **85-90% confidence** â†’ 90%+ correct
- **80-85% confidence** â†’ 85%+ correct
- **<80% confidence** â†’ Return "mixed" or "insufficient"

### False Positive/Negative Rates
- False "supports": **<0.5%**
- False "challenges": **<0.5%**
- False "mixed": **<1%**
- Missed "insufficient/unverifiable": **<1%**

### Minimum Viable (Must Have - Foundation)
- [ ] Scale bug fixed (P20 outputs 0-1)
- [ ] Module grades consolidated (ONE item_grade)
- [ ] Evidence curation filter working (P19)
- [ ] Authority in grading (P20) and aggregation (P25)
- [ ] Diversity/consistency in aggregation (P25)
- [ ] Evidence-based consensus (P27)
- [ ] Query validation loop working
- [ ] R1/R2 truly differentiated

### Quality Requirements (Must Have - 99% Accuracy)
- [ ] Source reliability database (500+ domains)
- [ ] Claim classification system working
- [ ] Contradiction resolution logic
- [ ] Numeric precision handling
- [ ] Temporal/geographic context
- [ ] Negation/hedging detection
- [ ] Confidence calibration verified
- [ ] Edge case handlers
- [ ] Unverifiable detection working
- [ ] Accuracy â‰¥ 99% on verifiable claims
- [ ] 99% accuracy detecting unverifiable claims

### Production Ready (Should Have)
- [ ] Parallel execution (R1/R2)
- [ ] Sub-5-second execution time
- [ ] 1000+ test claim suite
- [ ] Adversarial testing passed
- [ ] Comprehensive failure analysis
- [ ] Monitoring and logging
- [ ] Rollback capability

---

## EXECUTION TIMELINE

**Week 1:** Phase 0 - Preparation & Safety (baseline, tests, branch)
**Week 1-2:** Phase 1 - Fix Critical Bugs (scale 0-10â†’0-1, module consolidation)
**Week 2:** Phase 2 - Evidence Curation Filter (relatedness, quality gate, ordering)
**Week 3:** Phase 3 - Evidence Grading Enhancement (authority integration)
**Week 4-5:** Phase 4 - Arm Aggregation Intelligence (diversity, consistency, breadth, confidence formula)
**Week 5-6:** Phase 5 - Dual Researcher Diversification (query strategies, thresholds, parallel)
**Week 6-7:** Phase 6 - Evidence-Based Consensus (quality comparison, disagreement resolution, synthesis)
**Week 7-8:** Phase 7 - Query Validation Loop (validate results, auto-refine)

**FOUNDATION COMPLETE: ~80% Accuracy**

**Week 9-10:** Phase 8 - Quality Amplification (source database, claim classification, contradiction)
**Week 11-12:** Phase 9 - Precision Handling (numeric precision, temporal/geographic, semantic depth)
**Week 13-14:** Phase 10 - Calibration & Edge Cases (confidence calibration, edge cases, unverifiable detection)
**Week 15-16:** Phase 11 - Validation & Stress Testing (1000+ claims, adversarial, calibration verification)

**DETERMINISTIC MODEL COMPLETE: 99% Accuracy**

**Checkpoints:**
- **Week 2:** 65-70% accuracy (critical bugs fixed)
- **Week 4:** 75% accuracy (curation + grading working)
- **Week 7:** 80% accuracy (foundation complete - aggregation + consensus)
- **Week 10:** 90% accuracy (quality amplification - sources + classification)
- **Week 12:** 95% accuracy (precision handling complete)
- **Week 14:** 99% accuracy (calibration complete)
- **Week 16:** 99% validated across 1000+ diverse claims - **PRODUCTION READY**

---

## RISK MITIGATION

**Critical Risks:**
1. **Module consolidation (Phase 1.2)** - High complexity
   - Mitigation: Incremental refactoring, extensive testing
   
2. **Confidence calibration (Phase 10.1)** - Must be perfect
   - Mitigation: Extensive test suite, iterative tuning
   
3. **Claim classification accuracy (Phase 8.2)** - Affects everything downstream
   - Mitigation: Manual review, conservative defaults

**Medium Risks:**
4. Query strategy changes (Phase 5.1) - May change results
5. Consensus logic rewrite (Phase 6.2) - Complex logic
6. Numeric precision (Phase 9.1) - Edge cases

**Mitigation Strategy:**
- **Feature flags** for easy rollback
- **A/B testing** for major changes
- **Comprehensive logging** for debugging
- **Rollback points** at each phase
- **Conservative thresholds** (better "mixed" than wrong)

---

## DEPENDENCIES

**External:** None (all internal refactoring)

**Internal Phase Dependencies:**
- Phase 1 (bugs) **MUST** complete before all others
- Phase 2-7 (foundation) must complete before 8-11
- Phase 8 (classification) blocks Phase 10 (calibration)
- Phase 9 (precision) blocks Phase 10 (calibration)
- Phase 11 (validation) requires all previous phases

**Parallel Work Possible:**
- Phases 2-5 can partially overlap (different files)
- Phase 8-9 can partially overlap
- Test suite building can happen throughout

---

## NEXT STEPS

1. **Review & Approve Plan** âœ“
2. **Create Execution Guide** - Step-by-step implementation prompts
3. **Set Up Feature Branch** - `feature/99-percent-accuracy`
4. **Snapshot Baseline** - Document current 62.5% state
5. **Begin Phase 0** - Preparation & Safety
6. **Execute Phases 1-11** - 16 weeks to 99%
7. **Launch Production** - Deterministic model complete

---

**Plan Status:** COMPLETE - Ready for Execution Guide
**Target:** 99% accuracy on verifiable claims
**Timeline:** 16 weeks (4 months)
**Next Document:** Execution Guide with copy-paste prompts
ugust|September|October|November|December)\s+(\d{4})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, content)
        if match:
            return parse_date_from_match(match)
    
    return None  # Unknown date

def calculate_temporal_weight(item_date, claim_type, current_date=None):
    """Weight evidence by publication date"""
    
    if item_date is None:
        return 0.8  # Unknown date, slight penalty
    
    current_date = current_date or datetime.now()
    age_days = (current_date - item_date).days
    
    # Currency requirements by claim type
    if claim_type in ['SIMPLE_FACTUAL', 'SCIENTIFIC']:
        # Unchanging facts: date doesn't matter much
        if age_days < 365 * 5:  # <5 years
            return 1.0
        elif age_days < 365 * 10:  # <10 years
            return 0.95
        else:
            return 0.9
    
    elif claim_type == 'HISTORICAL':
        # Historical claims: prefer contemporary sources
        claim_year = extract_claim_year(claim)
        if claim_year and item_date.year <= claim_year + 5:
            return 1.0  # Contemporary
        else:
            return 0.85  # Later analysis
    
    elif claim_type in ['POLICY', 'COMPLEX_FACTUAL']:
        # Current data important
        if age_days < 365:  # <1 year
            return 1.0
        elif age_days < 365 * 2:  # <2 years
            return 0.9
        elif age_days < 365 * 5:  # <5 years
            return 0.75
        else:
            return 0.6  # Outdated
    
    return 0.8  # Default

def extract_geographic_scope(text):
    """Extract geographic context from text"""
    
    # Country/region mentions
    locations = []
    
    # Common patterns
    patterns = {
        'USA': r'\b(United States|USA|U\.S\.|America|US)\b',
        'UK': r'\b(United Kingdom|UK|U\.K\.|Britain|British)\b',
        'China': r'\bChina\b',
        'India': r'\bIndia\b',
        'Global': r'\b(world|global|worldwide|international)\b',
        'Europe': r'\bEurope\b',
    }
    
    for location, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            locations.append(location)
    
    return locations if locations else ['Global']  # Default global

def check_geographic_match(claim_scope, item_scope):
    """Check if geographic scopes match"""
    
    # Global matches everything
    if 'Global' in claim_scope or 'Global' in item_scope:
        return 1.0
    
    # Exact match
    overlap = set(claim_scope) & set(item_scope)
    if overlap:
        return 1.0
    
    # Partial match (e.g., USA and North America)
    # TODO: Add geographic hierarchy
    
    return 0.7  # Mismatch penalty
```

**Integration:**
- Add to P20 item grading (temporal weight)
- Add to P25 arm aggregation (prefer recent)
- Add to P24 frame comparison (geographic scope)

**Impact:** Handles "true in 2020" vs "true in 2024" correctly
**Risk:** MEDIUM - Date extraction accuracy
**Validation:** Test with dated claims

---

#### 9.3: Semantic Depth Enhancement
**File:** `intelligence/content/semantic_read.py` (P23 enhancement)

**Better paraphrase detection, implications, negation**

**Logic:**
```python
def detect_negation(text):
    """Detect if statement is negated"""
    
    negation_patterns = [
        r'\bnot\b',
        r'\bno\b',
        r'\bnever\b',
        r'\bnone\b',
        r'\bneither\b',
        r'\bdoes not\b',
        r'\bdoesn\'t\b',
        r'\bdidn\'t\b',
        r'\bwon\'t\b',
        r'\bcannot\b',
        r'\bcan\'t\b',
        r'\bwithout\b',
    ]
    
    for pattern in negation_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def detect_hedging(text):
    """Detect hedging language that weakens certainty"""
    
    hedging_patterns = [
        r'\bmay\b',
        r'\bmight\b',
        r'\bcould\b',
        r'\bpossibly\b',
        r'\bperhaps\b',
        r'\bprobably\b',
        r'\blikely\b',
        r'\bsuggests\b',
        r'\bindicates\b',
        r'\bappears\b',
        r'\bseems\b',
        r'\bsome evidence\b',
    ]
    
    hedge_count = 0
    for pattern in hedging_patterns:
        hedge_count += len(re.findall(pattern, text, re.IGNORECASE))
    
    # Return confidence penalty (0-1)
    return max(0, 1.0 - (hedge_count * 0.1))

def detect_causal_relationship(claim_text, evidence_text):
    """Detect if evidence explains causal relationship"""
    
    # Claim has causal marker?
    causal_markers = ['causes', 'leads to', 'results in', 'because', 'due to']
    claim_is_causal = any(marker in claim_text.lower() for marker in causal_markers)
    
    if not claim_is_causal:
        return None
    
    # Evidence discusses mechanism?
    mechanism_markers = ['mechanism', 'pathway', 'process', 'through', 'via', 'by']
    evidence_explains = any(marker in evidence_text.lower() for marker in mechanism_markers)
    
    return {
        'claim_is_causal': True,
        'evidence_explains_mechanism': evidence_explains,
        'strength_bonus': 0.1 if evidence_explains else 0.0,
    }

def enhanced_semantic_match(claim_text, evidence_text, claim_entities, claim_numbers):
    """Enhanced semantic matching with negation, hedging, causation"""
    
    # Base semantic similarity (existing)
    base_similarity = calculate_embedding_similarity(claim_text, evidence_text)
    
    # Negation check
    claim_negated = detect_negation(claim_text)
    evidence_negated = detect_negation(evidence_text)
    
    # If negation mismatch, invert similarity
    if claim_negated != evidence_negated:
        # One is negated, other is not = opposite meaning
        base_similarity = 1.0 - base_similarity
    
    # Hedging penalty
    hedging_confidence = detect_hedging(evidence_text)
    
    # Causal relationship bonus
    causal_info = detect_causal_relationship(claim_text, evidence_text)
    causal_bonus = causal_info['strength_bonus'] if causal_info else 0.0
    
    # Final semantic score
    semantic_score = base_similarity * hedging_confidence + causal_bonus
    
    return min(1.0, semantic_score)
```

**Integration:**
- Enhance P23 semantic matching
- Use in P20 stance detection
- Use in P25 consistency checking

**Impact:** Handles negation, hedging, causation correctly
**Risk:** MEDIUM - Complex linguistic patterns
**Validation:** Test with negated claims, hedged evidence

---

**Phase 9 Deliverables:**
- [ ] Numeric precision handling working
- [ ] Unit conversions accurate
- [ ] Temporal weighting by date
- [ ] Geographic scope matching
- [ ] Negation detection working
- [ ] Hedging penalty applied
- [ ] Accuracy reaches 95% on baseline

---

### Phase 10: Calibration & Edge Cases (Week 13-14)
**Goal:** Achieve 99% accuracy through calibration and conservative thresholds

**Current State:** ~95% accuracy after Phase 9
**Target:** 99% accuracy
**Strategy:** Strict confidence calibration, edge case handling, unverifiable detection

#### 10.1: Confidence Calibration
**File:** `intelligence/content/p25_aggregate.py`, `intelligence/consensus/build.py`

**Ensure confidence scores correlate with accuracy**

**Logic:**
```python
def calibrate_confidence(raw_confidence, claim_classification, arm_A_quality, arm_B_quality):
    """Calibrate confidence to ensure 95%+ conf = 99%+ accuracy"""
    
    # Start with raw confidence
    calibrated = raw_confidence
    
    # Adjust by claim verifiability
    if claim_classification['verifiability'] == 'HIGHLY_VERIFIABLE':
        # Boost confidence for simple facts
        calibrated = min(1.0, calibrated * 1.05)
    elif claim_classification['verifiability'] == 'PARTIALLY_VERIFIABLE':
        # Reduce confidence for complex claims
        calibrated = calibrated * 0.90
    elif claim_classification['verifiability'] == 'UNVERIFIABLE':
        # Return "cannot verify"
        return None
    
    # Adjust by evidence quality
    avg_reliability = (arm_A_quality['avg_reliability'] + arm_B_quality['avg_reliability']) / 2
    
    if avg_reliability < 0.70:
        # Low-quality sources, reduce confidence
        calibrated = calibrated * 0.85
    elif avg_reliability > 0.90:
        # High-quality sources, boost confidence
        calibrated = min(1.0, calibrated * 1.08)
    
    # Adjust by arm balance
    arm_balance = abs(arm_A_quality['strength'] - arm_B_quality['strength'])
    
    if arm_balance < 0.10:
        # Very close, reduce confidence significantly
        calibrated = calibrated * 0.80
    elif arm_balance > 0.30:
        # Clear winner, boost confidence
        calibrated = min(1.0, calibrated * 1.10)
    
    # Apply conservative floor
    # Don't return verdict unless confidence meets minimum
    min_confidence = claim_classification['confidence_thresholds']['min_confidence']
    
    if calibrated < min_confidence:
        return None  # Insufficient confidence
    
    return calibrated

def apply_confidence_thresholds(verdict, confidence, claim_classification):
    """Apply strict thresholds, default to 'mixed' or 'insufficient' when uncertain"""
    
    min_conf = claim_classification['confidence_thresholds']['min_confidence']
    mixed_threshold = claim_classification['confidence_thresholds']['mixed_threshold']
    
    # Below minimum = insufficient evidence
    if confidence < min_conf:
        return {
            'label': 'insufficient',
            'confidence': confidence,
            'rationale': f'Confidence {confidence:.2f} below minimum {min_conf:.2f}',
        }
    
    # Check arm balance
    if verdict['arm_balance'] < mixed_threshold:
        # Too close to call
        return {
            'label': 'mixed',
            'confidence': confidence * 0.90,  # Penalty for ambiguity
            'rationale': f'Arm balance {verdict["arm_balance"]:.2f} below threshold {mixed_threshold:.2f}',
        }
    
    # High confidence must be very high
    if verdict['label'] in ['supports', 'challenges']:
        if confidence < 0.85:
            # Not confident enough for definitive verdict
            return {
                'label': 'mixed',
                'confidence': confidence * 0.92,
                'rationale': 'Confidence insufficient for definitive verdict',
            }
    
    return verdict
```

**Calibration Testing:**
```python
def test_confidence_calibration(test_claims):
    """Verify confidence correlates with accuracy"""
    
    results_by_confidence = {
        '95-100': {'correct': 0, 'total': 0},
        '90-95': {'correct': 0, 'total': 0},
        '85-90': {'correct': 0, 'total': 0},
        '80-85': {'correct': 0, 'total': 0},
        '75-80': {'correct': 0, 'total': 0},
    }
    
    for claim in test_claims:
        result = run_pipeline(claim)
        confidence = result['consensus']['confidence']
        correct = (result['consensus']['label'] == claim['ground_truth'])
        
        # Bin by confidence
        if confidence >= 0.95:
            bin_key = '95-100'
        elif confidence >= 0.90:
            bin_key = '90-95'
        elif confidence >= 0.85:
            bin_key = '85-90'
        elif confidence >= 0.80:
            bin_key = '80-85'
        else:
            bin_key = '75-80'
        
        results_by_confidence[bin_key]['total'] += 1
        if correct:
            results_by_confidence[bin_key]['correct'] += 1
    
    # Check calibration
    for bin_key, stats in results_by_confidence.items():
        if stats['total'] > 0:
            accuracy = stats['correct'] / stats['total']
            print(f"Confidence {bin_key}%: {accuracy*100:.1f}% accurate")
            
            # Assert calibration requirements
            if bin_key == '95-100':
                assert accuracy >= 0.99, f"95-100% confidence must be 99%+ accurate, got {accuracy*100:.1f}%"
            elif bin_key == '90-95':
                assert accuracy >= 0.95, f"90-95% confidence must be 95%+ accurate"
```

**Impact:** Confidence scores reliable
**Risk:** HIGH - Calibration is critical
**Validation:** Extensive testing with ground truth

---

#### 10.2: Edge Case Handling
**File:** Throughout pipeline

**Handle special cases that break normal logic**

**Cases to Handle:**

**1. Ambiguous Claims**
```python
def detect_ambiguous_claim(claim_text, entities, numbers):
    """Detect claims that are inherently ambiguous"""
    
    # Vague quantifiers
    vague_terms = ['many', 'most', 'some', 'few', 'often', 'rarely', 'usually']
    if any(term in claim_text.lower() for term in vague_terms):
        return {'ambiguous': True, 'reason': 'vague_quantifier'}
    
    # Missing context
    if not entities and not numbers:
        return {'ambiguous': True, 'reason': 'no_anchors'}
    
    # Comparative without baseline
    if 'more' in claim_text.lower() and 'than' not in claim_text.lower():
        return {'ambiguous': True, 'reason': 'incomplete_comparison'}
    
    return {'ambiguous': False}
```

**2. Satirical/Opinion Content**
```python
def detect_satire_or_opinion(evidence_text, url):
    """Detect satirical or opinion content"""
    
    # Known satire sites
    satire_domains = ['theonion.com', 'babylonbee.com', 'clickhole.com']
    if any(domain in url for domain in satire_domains):
        return {'satire': True, 'filter': True}
    
    # Opinion markers in text
    opinion_markers = ['opinion:', 'editorial:', 'commentary:', 'in my view', 'i believe']
    if any(marker in evidence_text.lower() for marker in opinion_markers):
        return {'opinion': True, 'reliability_penalty': 0.5}
    
    return {'satire': False, 'opinion': False}
```

**3. Conflicting Expert Opinion**
```python
def handle_conflicting_experts(arm_A_items, arm_B_items):
    """Handle cases where experts disagree"""
    
    # Check if both arms have high-authority sources
    arm_A_experts = [i for i in arm_A_items if i.get('source_reliability', 0) > 0.85]
    arm_B_experts = [i for i in arm_B_items if i.get('source_reliability', 0) > 0.85]
    
    if len(arm_A_experts) >= 2 and len(arm_B_experts) >= 2:
        # Genuine expert disagreement
        return {
            'conflicting_experts': True,
            'verdict': 'mixed',
            'confidence': 0.75,  # High-ish confidence in "mixed"
            'rationale': 'High-quality sources disagree - genuine scientific debate',
        }
    
    return {'conflicting_experts': False}
```

**4. Emerging/Breaking News**
```python
def detect_breaking_news(evidence_items):
    """Detect if this is breaking/emerging news"""
    
    # Check publication dates
    recent_count = 0
    for item in evidence_items:
        pub_date = extract_publication_date(item)
        if pub_date and (datetime.now() - pub_date).days < 7:
            recent_count += 1
    
    if recent_count >= len(evidence_items) * 0.8:  # 80%+ very recent
        return {
            'breaking_news': True,
            'confidence_penalty': 0.9,  # Slight penalty, situation evolving
            'note': 'Claim relates to very recent events - information may be incomplete',
        }
    
    return {'breaking_news': False}
```

**Impact:** Handles edge cases gracefully
**Risk:** MEDIUM - Must not over-filter
**Validation:** Test with edge case suite

---

#### 10.3: Unverifiable Claim Detection
**File:** `intelligence/preprocess/classify.py`, `intelligence/gather/pipeline.py`

**Early detection of claims that cannot be verified**

**Logic:**
```python
def detect_unverifiable_early(claim_text, claim_classification, search_results):
    """Detect unverifiable claims before full processing"""
    
    # 1. Classification-based
    if claim_classification['verifiability'] == 'UNVERIFIABLE':
        return {
            'unverifiable': True,
            'reason': 'opinion_or_prediction',
            'message': 'This appears to be an opinion or prediction, not a factual claim',
        }
    
    # 2. No search results
    if not search_results or len(search_results) < 3:
        return {
            'unverifiable': True,
            'reason': 'no_evidence_found',
            'message': 'No relevant evidence found to verify this claim',
        }
    
    # 3. All results unrelated
    related_count = sum(1 for r in search_results if is_related_fast(claim_text, r))
    if related_count < 2:
        return {
            'unverifiable': True,
            'reason': 'all_results_unrelated',
            'message': 'Search returned no relevant results - claim may be too obscure or fictional',
        }
    
    # 4. Contradictory claim structure
    if has_contradictory_structure(claim_text):
        return {
            'unverifiable': True,
            'reason': 'contradictory_structure',
            'message': 'Claim contains contradictory elements',
        }
    
    return {'unverifiable': False}

def has_contradictory_structure(claim_text):
    """Detect claims with self-contradictory structure"""
    
    # "X but also not X"
    if re.search(r'\bbut\b.*\bnot\b', claim_text, re.IGNORECASE):
        return True
    
    # "all X are Y except X"
    if re.search(r'\ball\b.*\bexcept\b', claim_text, re.IGNORECASE):
        return True
    
    return False

def return_unverifiable_verdict(reason, message):
    """Return structured unverifiable verdict"""
    
    return {
        'verdict': {
            'label': 'insufficient',
            'confidence': 0.95,  # High confidence in "cannot verify"
            'rationale': message,
        },
        'evidence': {
            'arm_A': [],
            'arm_B': [],
        },
        'metadata': {
            'unverifiable': True,
            'reason': reason,
            'processing_time_saved': True,
        }
    }
```

**Integration:**
- Check after claim classification (Phase 8.2)
- Check after initial search (Phase 2)
- Return early, save computation

**Impact:** Handles unverifiable claims correctly
**Risk:** LOW - Conservative detection
**Validation:** Test with unverifiable claim set

---

**Phase 10 Deliverables:**
- [ ] Confidence calibration tested and verified
- [ ] Edge case handlers implemented
- [ ] Unverifiable detection working
- [ ] Accuracy reaches 99% on verifiable claims
- [ ] 99% accuracy on detecting unverifiable claims
- [ ] Confidence 95%+ â†’ 99%+ correct

---

### Phase 11: Validation & Stress Testing (Week 15-16)
**Goal:** Prove 99% accuracy across diverse test suite

**Target:** Comprehensive validation proving 99% accuracy

#### 11.1: Comprehensive Test Suite
**File:** `tests/test_comprehensive.py`

**Build 1000+ claim test suite**

**Test Categories:**

**1. Simple Factual Claims (200 claims)**
- Basic facts with clear evidence
- Target: 99.5% accuracy
- Examples:
  - "Water boils at 100Â°C at sea level"
  - "Earth has one moon"
  - "Speed of light is 299,792,458 m/s"

**2. Complex Factual Claims (200 claims)**
- Multi-part claims, statistics
- Target: 99% accuracy
- Examples:
  - "US GDP grew 3.2% in Q4 2023"
  - "COVID-19 vaccines are 95% effective against severe disease"

**3. Historical Claims (150 claims)**
- Events, dates, figures
- Target: 99% accuracy
- Examples:
  - "WWII ended in 1945"
  - "Moon landing occurred in 1969"

**4. Scientific Claims (150 claims)**
- Scientific facts, study results
- Target: 99% accuracy
- Examples:
  - "DNA has a double helix structure"
  - "Antibiotics treat bacterial infections"

**5. Policy Claims (100 claims)**
- Laws, regulations, impacts
- Target: 95% accuracy (or mark unverifiable)
- Examples:
  - "Seatbelt laws reduced traffic deaths by 45%"

**6. Edge Cases (100 claims)**
- Ambiguous, satirical, conflicting experts
- Target: 95% correctly identified as mixed/insufficient

**7. Unverifiable Claims (100 claims)**
- Opinions, predictions, subjective
- Target: 99% correctly identified as unverifiable

**Test Implementation:**
```python
def run_comprehensive_test_suite():
    """Run all 1000 claims through pipeline"""
    
    test_suite = load_test_claims('tests/comprehensive_1000.json')
    
    results = {
        'total': 0,
        'correct': 0,
        'by_category': {},
        'by_confidence': {},
        'failures': [],
    }
    
    for claim in test_suite:
        result = run_pipeline(claim['text'])
        
        # Check correctness
        correct = check_verdict(result, claim['ground_truth'])
        
        results['total'] += 1
        if correct:
            results['correct'] += 1
        else:
            results['failures'].append({
                'claim': claim,
                'result': result,
                'expected': claim['ground_truth'],
            })
        
        # Track by category
        category = claim['category']
        if category not in results['by_category']:
            results['by_category'][category] = {'correct': 0, 'total': 0}
        results['by_category'][category]['total'] += 1
        if correct:
            results['by_category'][category]['correct'] += 1
        
        # Track by confidence
        conf_bin = get_confidence_bin(result['confidence'])
        if conf_bin not in results['by_confidence']:
            results['by_confidence'][conf_bin] = {'correct': 0, 'total': 0}
        results['by_confidence'][conf_bin]['total'] += 1
        if correct:
            results['by_confidence'][conf_bin]['correct'] += 1
    
    # Calculate accuracy
    overall_accuracy = results['correct'] / results['total']
    
    # Assert requirements
    assert overall_accuracy >= 0.99, f"Overall accuracy {overall_accuracy*100:.2f}% < 99%"
    
    for category, stats in results['by_category'].items():
        category_accuracy = stats['correct'] / stats['total']
        print(f"{category}: {category_accuracy*100:.1f}% ({stats['correct']}/{stats['total']})")
    
    return results
```

---

#### 11.2: Adversarial Testing
**File:** `tests/test_adversarial.py`

**Test deliberately tricky claims**

**Adversarial Cases:**

**1. Misleading Context**
- Claim: "Water boils at 100Â°C"
- Evidence: Article about water boiling at different temperatures on mountains
- Expected: System recognizes "at sea level" is implied/missing

**2. Subtle Negation**
- Claim: "Vaccines cause autism"
- Evidence: "Studies show vaccines do not cause autism"
- Expected: Correctly identifies challenge

**3. Numeric Precision Traps**
- Claim: "Pi is 3.14"
- Evidence: "Pi is 3.14159..."
- Expected: Recognizes as approximate match (contextual precision)

**4. Temporal Confusion**
- Claim: "US President is Joe Biden"
- Evidence from 2020: "US President is Donald Trump"
- Expected: Prefers recent evidence

**5. Geographic Confusion**
- Claim: "Minimum wage is $15"
- Evidence: Mix of US ($7.25 federal) and California ($15)
- Expected: Recognizes geographic scope issue

**6. Cherry-Picked Evidence**
- Claim: "Coffee cures cancer"
- Evidence: Single low-quality study
- Expected: Rejects due to low authority, lack of consensus

**7. Correlation vs Causation**
- Claim: "Ice cream causes drowning"
- Evidence: "Ice cream sales and drowning both peak in summer"
- Expected: Recognizes correlation, not causation

**8. False Equivalence**
- Claim: "Evolution is just a theory"
- Evidence: Scientific definition of "theory"
- Expected: Recognizes semantic difference (colloquial vs scientific "theory")

---

#### 11.3: Calibration Verification
**File:** `tests/test_calibration.py`

**Verify confidence â†’ accuracy mapping**

**Calibration Requirements:**
```python
CALIBRATION_REQUIREMENTS = {
    (0.95, 1.00): 0.99,  # 95-100% confidence â†’ 99%+ accurate
    (0.90, 0.95): 0.95,  # 90-95% confidence â†’ 95%+ accurate
    (0.85, 0.90): 0.90,  # 85-90% confidence â†’ 90%+ accurate
    (0.80, 0.85): 0.85,  # 80-85% confidence â†’ 85%+ accurate
}

def verify_calibration(test_results):
    """Verify confidence bands meet accuracy requirements"""
    
    for (conf_min, conf_max), required_accuracy in CALIBRATION_REQUIREMENTS.items():
        # Get results in this confidence band
        band_results = [
            r for r in test_results 
            if conf_min <= r['confidence'] < conf_max
        ]
        
        if not band_results:
            print(f"WARNING: No results in confidence band {conf_min}-{conf_max}")
            continue
        
        # Calculate accuracy
        correct = sum(1 for r in band_results if r['correct'])
        accuracy = correct / len(band_results)
        
        print(f"Confidence {conf_min*100:.0f}-{conf_max*100:.0f}%: {accuracy*100:.1f}% accurate ({correct}/{len(band_results)})")
        
        # Assert requirement
        assert accuracy >= required_accuracy, \
            f"Confidence {conf_min*100:.0f}-{conf_max*100:.0f}% requires {required_accuracy*100:.0f}% accuracy, got {accuracy*100:.1f}%"
```

**Failure Analysis:**
```python
def analyze_failures(failures):
    """Analyze patterns in failures"""
    
    patterns = {
        'scale_bugs': [],
        'stance_errors': [],
        'authority_issues': [],
        'context_misses': [],
        'other': [],
    }
    
    for failure in failures:
        # Classify failure type
        if failure['result']['confidence'] > 0.95:
            # High confidence, wrong answer = serious bug
            patterns['scale_bugs'].append(failure)
        elif failure['result']['verdict'] != failure['expected']['stance']:
            patterns['stance_errors'].append(failure)
        # ... more classification
    
    # Report
    print("\nFAILURE ANALYSIS:")
    for pattern_type, items in patterns.items():
        if items:
            print(f"{pattern_type}: {len(items)} failures")
            for item in items[:3]:  # Show first 3
                print(f"  - {item['claim']['text']}")
```

---

**Phase 11 Deliverables:**
- [ ] 1000-claim test suite built
- [ ] Adversarial test suite passed
- [ ] Calibration verified (95%+ conf â†’ 99%+ accuracy)
- [ ] Failure analysis documented
- [ ] 99% overall accuracy achieved
- [ ] Ready for production

---
