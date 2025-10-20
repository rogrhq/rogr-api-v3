# ROGRv2 TARGET ARCHITECTURE
**Reference Architecture - Extracted from Source Documents**

**Version:** 1.0
**Date:** 2025-10-19
**Purpose:** Single source of truth for what the NEW system should look like

**Source Documents:**
1. `user_journey_workflow.md` - 13-step target workflow
2. `ROGR LOGIC FIX PLAN.md` - 11-phase implementation plan
3. `ROGR LOGIC REFACTOR EXECUTION GUIDE COMPLETE.md` - Step-by-step implementation
4. `ROGRv2_Feature_Audit_v3_with_SAGPT.xlsx` - Gap analysis

---

## PART 1: TARGET SYSTEM (From workflow.md)

### The 13-Step Pipeline

The target system processes fact-check requests through 13 distinct steps, achieving 99% accuracy through multiple layers of validation and conservative thresholds.

#### STEP 0: Claim Intake & Classification
**Location:** Entry point, Phase 8
**Purpose:** Determine if claim is verifiable before spending resources

**What it does:**
- Classifies claim into 6 categories:
  - SIMPLE_FACTUAL: "Water boils at 100°C"
  - COMPLEX_FACTUAL: "GDP grew 3.2%"
  - HISTORICAL: "WWII ended 1945"
  - SCIENTIFIC: "DNA is double helix"
  - OPINION: "Pizza is best" (STOP)
  - PREDICTION: "Market will crash" (STOP)

**Decision Point:** Is verifiable?
- YES → Continue to Step 1
- NO → Return "Cannot verify" (saves 30 seconds)

**User Experience:** "Analyzing claim type..." spinner

---

#### STEP 1: Understanding the Claim
**Location:** Preprocessing, Phase 9 enhanced
**Purpose:** Extract all key facts with precision awareness

**What it extracts:**
- **Entities:** "Water" (subject)
- **Numbers:** "100" with precision context
- **Units:** "°C" (measurement type)
- **Actions:** "boils" (relationship)
- **Context:** Implied conditions (e.g., "at sea level")

**Phase 9 Improvements:**
- Precision handling: "8%" vs "8.0%" vs "8.00%"
- Context detection: Missing "at sea level"
- Negation detection: "not increasing" ≠ "increasing"
- Hedging detection: "may increase" ≠ "increases"

**User Experience:** "Analyzing: Water (entity), 100°C (number)"

---

#### STEP 2: Dual Research Planning
**Location:** Phase 5 enhanced
**Purpose:** Create TWO independent research strategies

**Researcher 1 (R1) - "The Skeptic":**
- **Strategy:** Precision focused
- **Queries:** Exact quotes, anchored searches
- **Threshold:** Strict (70% stance confidence required)
- **Sources:** Conservative, high-quality only
- **Counter-frames:** Conservative
- **Example:** `"water boils at 100°C"`, `"water" "100°C"`

**Researcher 2 (R2) - "The Explorer":**
- **Strategy:** Recall focused
- **Queries:** Broad, paraphrased, exploratory
- **Threshold:** Lenient (50% stance confidence)
- **Sources:** Permissive, wider range
- **Counter-frames:** Aggressive
- **Example:** `water boiling point`, `H2O temperature boiling`

**Phase 5 Improvements:**
- Truly different query generation strategies
- Different confidence thresholds per researcher
- Different search provider preferences (Brave vs Google)
- Parallel execution (simultaneous, not sequential)

**User Experience:** "Researching claim from multiple angles..."

---

#### STEP 3: Search Execution
**Location:** Each researcher independently, Phase 2 & 7 enhanced
**Purpose:** Gather candidate evidence from web

**Process:**
- R1: 5 precision queries → ~250 candidates
- R2: 8 recall queries → ~400 candidates
- Each query returns ~50 results

**Phase 7 Addition - Query Validation:**
- Sample top 5 results per query
- Check relevance: entities, numbers, keywords
- If <60% relevant → Auto-refine query and retry (max 2 times)
- Refinement strategies: Add quotes, add units, add domain constraints

---

#### STEP 4: Fast Filter
**Location:** Phase 2 added, `intelligence/gather/pipeline.py::filter_unrelated`
**Purpose:** Quick check for obvious mismatches

**Logic:**
- Has entity from claim? ✓
- Has number from claim? ✓
- Has 30%+ keyword overlap? ✓
- If ANY anchor present → Keep
- Else → Drop

**Impact:**
- R1: 250 → 180 candidates (28% dropped)
- R2: 400 → 280 candidates (30% dropped)

**Why:** Like sorting mail - don't open "Car Insurance" when looking for medical bills

---

#### STEP 5: Quality Gate
**Location:** Phase 2 added, `intelligence/gather/pipeline.py::quality_gate`
**Purpose:** Filter by source quality BEFORE deep analysis

**Checks:**
1. **Blocked domains:** pinterest.com, youtube.com (videos), social media
2. **Format:** PDFs (unless .gov/.edu whitelist)
3. **Language:** English only (simple char detection)
4. **Domain duplicates:** Max 2 results per domain

**Impact:**
- R1: 180 → 120 candidates (33% dropped)
- R2: 280 → 200 candidates (29% dropped)

**Why:** Like checking restaurant health ratings before eating

---

#### STEP 6: Query Validation Loop
**Location:** Phase 7 added, between search and ranking
**Purpose:** Ensure search actually found relevant results

**Process:**
1. Sample top 5 results
2. Calculate relevance rate
3. If ≥60% relevant → Proceed
4. If <60% relevant → Refine query and retry

**Refinement Strategies:**
- Add entity quotes if missing
- Add units if numeric claim
- Add domain constraint (site:.gov OR site:.edu)

**Why:** Like asking directions - if 4 out of 5 people don't understand, rephrase question

---

#### STEP 7: Select Top Items
**Location:** Ranking module
**Purpose:** Rank by search relevance, take top 5 per arm

**Output:**
- **ARM A (Support):** Top 5 results supporting claim
- **ARM B (Challenge):** Top 5 results challenging claim
- Total: 10 items per researcher (20 total across R1 & R2)

---

#### STEP 8: Fetch Content
**Location:** Content fetching
**Purpose:** Get full article text for deep analysis

**Coverage Quality:**
- **FULL:** Got entire article (best)
- **PARTIAL:** Got first 50% (good)
- **SNIPPET:** Only got preview (fallback)

**Why:** Full text gives better understanding than book jacket

---

#### STEP 9: Analyze Evidence
**Location:** Phase 1, 3, 9 enhanced - P20 orchestrates P21/P23/P24
**Purpose:** Grade each evidence item 0-1

**Module Structure (Phase 1 Fix):**

**P20 - Orchestrator** (`intelligence/content/grade.py`)
- Calls P21, P23, P24 as helpers
- Produces ONE `item_grade` (0-1) per item
- No more competing grades

**P21 - Authority Checker** (`intelligence/content/fullread.py`)
- Returns: `authority_score` (0-1)
- .gov = 1.0, .edu = 0.9, news = 0.75, blogs = 0.5
- Phase 3: Authority now weighted in final grade

**P23 - Semantic Analyst** (`intelligence/content/semantic_read.py`)
- Returns: `semantic_similarity` (0-1)
- Checks if article SAYS same thing as claim
- Phase 9: Enhanced with negation/hedging detection
- Finds matching sentences, paraphrases

**P24 - Pattern Matcher** (`intelligence/content/frames.py`)
- Returns: `frame_match_score` (0-1)
- Checks if article has same STRUCTURE as claim
- Extracts: [entity][action][number][unit][condition]
- Example: [water][boils][100][°C][sea level]

**P20 Fusion Formula (Phase 1 & 3):**
```
item_grade = (
    40% * semantic_similarity +  # P23
    30% * frame_match +           # P24
    20% * authority +             # P21 (Phase 3)
    10% * coverage_quality        # full > partial > snippet
)
```

**Phase 1 Critical Fix:**
- OLD: Multiple modules produced competing grades (0-10 scale confusion)
- NEW: ONE unified 0-1 grade from P20 orchestrator

**Phase 9 Enhancements:**
- Negation detection: "not increasing" handled correctly
- Hedging penalty: "may increase" reduces confidence
- Precision awareness: "8%" vs "8.00%" context-sensitive
- Temporal weighting: Recent evidence weighted higher for current events
- Geographic matching: US-specific vs global claims

**Result:** Each item gets single `item_grade` (0-1)

**Why:** Like evaluating witness - check WHAT they said (semantic), HOW consistent (structure), WHO they are (authority)

---

#### STEP 10: Arm Aggregation
**Location:** Phase 4 enhanced, P25 (`intelligence/content/p25_aggregate.py`)
**Purpose:** Combine evidence within each arm with quality multipliers

**Process per arm:**

1. **Base Strength** - Weighted sum of top 4 items:
```
strength = (
    item1_grade × 1.00 +
    item2_grade × 0.70 +
    item3_grade × 0.50 +
    item4_grade × 0.35
)
```

2. **Quality Multipliers** (Phase 4):

**Diversity Score** (0-1):
```python
unique_domains / total_items
Bonus if ≥3 unique domains with ≥3 items
```
- 5 unique domains = 1.0
- 3 from same blog = penalized

**Consistency Score** (0-1):
```python
Check if items agree on numbers
High variance in numbers = low consistency
Coefficient of variation: <10% = 1.0, >50% = 0.0
```

**Breadth Score** (0-1):
```python
Measure text similarity between items
High similarity = repetition = low breadth (penalty)
Low similarity = diverse angles = high breadth (reward)
```

3. **Final Arm Strength:**
```
arm_strength = base × diversity × consistency × breadth
```

**Confidence Calculation (Phase 4 Enhanced):**
```
confidence = (
    25% * total_strength +      # Evidence volume
    25% * balance +              # Gap between arms
    15% * item_count +           # Number of items
    15% * avg_authority +        # Source quality (Phase 3)
    10% * diversity +            # Source diversity (Phase 4)
    10% * consistency            # Internal consistency (Phase 4)
)
```

**Verdict Decision:**
- Support - Challenge ≥ 0.15 → SUPPORTS
- Challenge - Support ≥ 0.15 → CHALLENGES
- Difference < 0.15 → MIXED
- Both weak (< 1.0 total) → INSUFFICIENT

**Phase 4 Critical Improvements:**
- OLD: Just averaged grades, volume wins
- NEW: Quality multipliers prevent gaming with low-quality sources
- 1 excellent source > 5 mediocre sources

**Why:** Like jury deliberation - weight ALL evidence, not just count votes

---

#### STEP 11: Consensus Building
**Location:** Phase 6 enhanced, P27 (`intelligence/consensus/build.py`)
**Purpose:** Compare R1 and R2 verdicts using evidence quality

**Process:**

1. **Extract Verdicts:**
- R1: Label + confidence + arm strengths + evidence items
- R2: Label + confidence + arm strengths + evidence items

2. **Evidence Quality Comparison (Phase 6):**
```python
quality_score = (
    40% * avg_item_grade +
    30% * avg_authority +
    20% * diversity +
    10% * consistency
)
```

Calculate `quality_gap = |R1_quality - R2_quality|`

3. **Resolution Logic (Phase 6 Enhanced):**

**Case 1: Agreement**
```
IF R1_label == R2_label:
    consensus_confidence = avg(R1_conf, R2_conf) × 1.10  # +10% boost
    consensus_label = R1_label
    rationale = "Both researchers agree"
```

**Case 2: Disagreement with Quality Gap**
```
IF R1_label ≠ R2_label AND quality_gap > 0.15:
    trust_better = (R1 if R1_quality > R2_quality else R2)
    consensus_confidence = trust_better.confidence × 0.95  # -5% penalty
    consensus_label = trust_better.label
    rationale = "R{X} has stronger evidence (gap: {quality_gap})"
```

**Case 3: Disagreement, Similar Quality**
```
IF R1_label ≠ R2_label AND quality_gap ≤ 0.15:
    IF abs(R1_balance - R2_balance) < 0.10:
        # Genuinely ambiguous
        consensus_label = "mixed"
        consensus_confidence = avg(R1_conf, R2_conf) × 0.90
    ELSE:
        # One has clearer balance
        trust_clearer = (R1 if |R1_balance| > |R2_balance| else R2)
        consensus_label = trust_clearer.label
        consensus_confidence = trust_clearer.confidence × 0.92
```

4. **Evidence Synthesis (Phase 6):**
```python
# Pool all items from R1 and R2
all_items = R1_items + R2_items

# Deduplicate by URL
unique_items = deduplicate_by_url(all_items)

# Sort by item_grade × authority
sorted_items = sort_by(unique_items, key=lambda x: x.grade * x.authority)

# Take top 5 per arm for display
final_arm_A = sorted_items[arm=="A"][:5]
final_arm_B = sorted_items[arm=="B"][:5]
```

**Phase 6 Critical Improvements:**
- OLD: Just compared labels (supports vs challenges), picked higher confidence
- NEW: Compares evidence quality metrics, resolves intelligently
- Example: If R1 has 3 blogs saying "supports" and R2 has 3 .gov sites saying "challenges", trust R2

**Why:** Like two doctors' opinions - if both agree, confident; if disagree, check whose tests were better

---

#### STEP 12: Confidence Calibration
**Location:** Phase 10 added, `intelligence/calibration/confidence.py`
**Purpose:** Apply conservative thresholds to ensure reliability

**Calibration Process:**

1. **Adjust by Claim Type:**
```python
IF claim_type == HIGHLY_VERIFIABLE:
    confidence × 1.05  # Boost for simple facts
ELIF claim_type == PARTIALLY_VERIFIABLE:
    confidence × 0.90  # Reduce for complex claims
ELIF claim_type == UNVERIFIABLE:
    return "cannot verify"  # Exit early
```

2. **Adjust by Evidence Quality:**
```python
IF avg_authority > 0.90:
    confidence × 1.08  # Boost for high-quality sources
ELIF avg_authority < 0.70:
    confidence × 0.85  # Reduce for low-quality sources
```

3. **Adjust by Arm Balance:**
```python
IF arm_balance > 0.30:
    confidence × 1.10  # Clear winner
ELIF arm_balance < 0.10:
    confidence × 0.80  # Too close
```

4. **Apply Thresholds:**
```python
IF confidence < 0.85:
    # Not confident enough for definitive verdict
    return "mixed"

IF arm_balance < 0.15:
    # Too close to call
    return "mixed"

IF avg_authority < 0.65:
    # Low-quality evidence
    return "insufficient"
```

**Calibration Requirements (Tested in Phase 11):**
- 95-100% confidence → 99%+ actually correct
- 90-95% confidence → 95%+ actually correct
- 85-90% confidence → 90%+ actually correct
- <85% confidence → Force to "mixed"

**Phase 10 Critical Improvement:**
- OLD: Always returned highest confidence verdict (overconfident)
- NEW: Conservative thresholds, forces "mixed" when uncertain
- Better to admit uncertainty than be wrong

**Why:** Like quality control inspector - 98% confident? Ship it. 75% confident? Need more investigation.

---

#### STEP 13: Final Verdict Formatting
**Location:** API response formatting
**Purpose:** Convert to IFCN 5-point scale and prepare user display

**IFCN Scale Mapping:**
- 90-100: TRUE
- 75-89: MOSTLY TRUE
- 55-74: MIXED
- 35-54: MOSTLY FALSE
- 0-34: FALSE

**Evidence Package:**
- Top 3-5 supporting evidence (highest grade × authority)
- Top 2-3 challenging evidence (context/caveats)
- Each with: URL, authority stars, grade, snippet
- Source quality indicators
- Research quality metrics (diversity, consistency, authority)

**User Display Format:**
```
✅ Verdict: TRUE | Confidence: 98%

Supporting Evidence (3):
1. [★★★★★] nih.gov - Grade 95/100
2. [★★★★★] nasa.gov - Grade 93/100
3. [★★★★] chemguide.edu - Grade 91/100

⚠️ Important Context (2):
1. [★★★★★] usgs.gov - Grade 81/100
   "Varies with altitude"

Research Quality:
• Source Diversity: 5 unique domains
• Source Authority: 88% average
• Evidence Consistency: 98% agreement
• Two independent researchers agreed

Processing: 8.3 seconds | 320 candidates → 10 selected
```

---

### User Experience Summary

**What User Submits:** Single sentence claim

**What System Does (Invisibly):**
1. Classifies claim type (1s)
2. Two independent researchers search in parallel (1s)
3. Each finds ~250-400 candidates
4. Filters to ~120-200 quality candidates (1s)
5. Selects top 10 per researcher (20 total)
6. Analyzes each deeply with 3 modules (4s)
7. Aggregates with quality checks
8. Builds consensus comparing evidence quality (1s)
9. Calibrates confidence conservatively
10. Formats for display

**Total Time:** 8-10 seconds

**What User Sees:**
- Clear verdict (TRUE/FALSE/MIXED/etc)
- Confidence score (0-100%)
- Top evidence with links and quality indicators
- Research quality metrics
- Plain English explanation

---

## PART 2: IMPLEMENTATION MAP (From execution guide + plan)

### Function-to-Step Mapping

#### Step 0: Claim Classification
**Files:**
- `intelligence/preprocess/classify.py` (NEW in Phase 8)

**Functions:**
```python
classify_claim(claim_text) -> dict
    Returns: {
        'category': 'SIMPLE_FACTUAL' | 'COMPLEX_FACTUAL' | 'HISTORICAL' |
                   'SCIENTIFIC' | 'OPINION' | 'PREDICTION',
        'verifiability': 'HIGHLY_VERIFIABLE' | 'PARTIALLY_VERIFIABLE' | 'UNVERIFIABLE',
        'confidence_thresholds': {...}
    }

detect_unverifiable_early(claim_text, classification, search_results) -> dict
    Early exit for opinions/predictions
```

**Phase:** 8 (Quality Amplification)

---

#### Step 1: Claim Understanding
**Files:**
- `intelligence/analyze/enrich.py`
- `intelligence/claims/extract.py`

**Functions:**
```python
enrich_claim_obj(claim) -> dict
    Extracts: entities, numbers, units, scope, cues

extract_entities_simple(text) -> List[str]
extract_numbers(text) -> List[dict]
extract_units(text) -> List[str]
```

**Phase 9 Enhancements:**
- `detect_negation(text) -> bool`
- `detect_hedging(text) -> float`
- `extract_precision_context(number) -> dict`

**Phase:** 1 (baseline), 9 (enhanced)

---

#### Step 2: Dual Research Planning
**Files:**
- `intelligence/strategy/plan_v2.py`
- `intelligence/planning/diversify.py` (Phase 5)

**Functions:**
```python
build_search_plans_v2(claim) -> dict
    Base plan with Arm A/B queries

# Phase 5 additions:
generate_queries_r1(claim_text, entities, numbers, arm) -> List[str]
    Precision: quoted, anchored, exact

generate_queries_r2(claim_text, entities, numbers, arm) -> List[str]
    Recall: paraphrased, exploratory, broad

diversify_plan_for_lane(base_plan, lane_id, claim, providers) -> (plan, config)
    R1 vs R2 differentiation
```

**Phase:** 1 (baseline), 5 (enhanced)

---

#### Steps 3-7: Evidence Gathering
**Files:**
- `intelligence/gather/pipeline.py`
- `intelligence/gather/online.py`

**Functions:**
```python
# Step 3: Search
run_plan(plan, max_per_query) -> dict
    Executes queries via search providers

# Step 4: Fast Filter (Phase 2)
filter_unrelated(claim_text, claim_entities, claim_numbers, candidates) -> tuple
    Returns: (filtered, dropped)

# Step 5: Quality Gate (Phase 2)
quality_gate(candidates) -> tuple
    Filters: blocked domains, PDFs, non-English, duplicates

# Step 6: Query Validation (Phase 7)
validate_query_results(claim, query, results, max_retries=2) -> (query, results)
    Auto-refines if <60% relevant

refine_query(claim, original_query, off_topic_results) -> str
    Adds quotes, units, domain constraints

# Step 7: Ranking & Selection
rank_candidates(claim_text, query, candidates, top_k) -> List[dict]
```

**Phases:** 2 (filter/gate), 7 (validation)

---

#### Step 8: Content Fetching
**Files:**
- `intelligence/content/fetch_enrichment.py`
- `intelligence/content/fetch_sync.py`

**Functions:**
```python
enrich_items_with_content(items, fetch_cache) -> (items, cache)
    Fetches full text, tracks coverage (full/partial/snippet)

fetch_text(url, timeout) -> dict
    Returns: {text, status, coverage}
```

**Phase:** Baseline (P22)

---

#### Step 9: Evidence Analysis
**Files:**
- `intelligence/content/grade.py` (P20)
- `intelligence/content/fullread.py` (P21)
- `intelligence/content/semantic_read.py` (P23)
- `intelligence/content/semantic_frames.py` (P24)

**Functions:**

**P20 - Orchestrator:**
```python
build_finding_v2(claim_text, arm, content_text, snippet_text, precomputed_window, precomputed_sim) -> dict
    Returns: complete finding with ONE item_grade

fuse_module_grades(features, evidence_item) -> float
    Combines P21/P23/P24 into single grade:
    = 40% semantic + 30% frame + 20% authority + 10% coverage

attach_finding_to_item(claim_text, arm_label, item) -> None
    Main entry point, adds finding to item dict
```

**P21 - Authority:**
```python
calculate_authority_score(url, credibility) -> float
    Domain scoring: .gov=1.0, .edu=0.9, news=0.75, blog=0.5

get_source_reliability(url) -> float
    (Phase 8 expansion) Comprehensive database of 500+ domains
```

**P23 - Semantic:**
```python
analyze_item(claim_text, item, window) -> None
    Semantic similarity analysis

# Phase 9 enhancements:
detect_negation(text) -> bool
detect_hedging(text) -> float
enhanced_semantic_match(...) -> float
```

**P24 - Frames:**
```python
analyze_frames(claim_text, content, window) -> dict
    Pattern matching: [entity][action][number][unit][condition]

extract_frame(text, domain) -> Frame
compare_frames(frame1, frame2) -> str  # 'exact', 'partial', 'mismatch'
```

**Phases:** 1 (consolidation), 3 (authority), 9 (semantic depth)

---

#### Step 10: Arm Aggregation
**Files:**
- `intelligence/content/p25_aggregate.py`

**Functions:**
```python
aggregate_verdict(claim_text, arm_a_items, arm_b_items, delta=0.15) -> dict
    Main aggregation function

# Helper functions:
_item_strength(item) -> float
    Combines frame_matches + item_grade + coverage

_arm_strength(items, top_k=4) -> float
    Weighted sum with diminishing returns

# Phase 4 additions:
calculate_diversity_score(items) -> float
    unique_domains / total_items

calculate_consistency_score(items, claim_numbers) -> float
    Check numeric agreement (coefficient of variation)

calculate_breadth_score(items) -> float
    Trigram similarity (1.0 - avg_pairwise_similarity)

# Phase 4 enhanced confidence:
_confidence_from_arms(sa, sb, n_items_a, n_items_b) -> float
    Factors: total strength, balance, count, (later: authority, diversity, consistency)
```

**Phase:** 4 (enhanced aggregation)

---

#### Step 11: Consensus Building
**Files:**
- `intelligence/consensus/dual_lane.py`
- `intelligence/consensus/build.py` (Phase 6)
- `intelligence/orchestration/dual_lane.py`

**Functions:**
```python
# Orchestration:
run_dual_researchers(claim_text, base_plan, enrichment_pipeline, diversify_fn, telemetry_class) -> dict
    Runs R1 and R2 in parallel

# Phase 6 consensus:
compute_consensus(r1_verdict, r2_verdict) -> dict
    Agreement/disagreement resolution with quality comparison

compare_evidence_quality(r1_items, r2_items) -> dict
    Returns quality metrics per researcher

resolve_disagreement(r1_verdict, r2_verdict, evidence_comparison) -> dict
    Intelligent resolution based on evidence quality

synthesize_evidence(r1_items, r2_items) -> dict
    Deduplicate and combine best evidence
```

**Phase:** 6 (evidence-based consensus)

---

#### Step 12: Confidence Calibration
**Files:**
- `intelligence/calibration/confidence.py` (Phase 10)

**Functions:**
```python
calibrate_confidence(raw_confidence, claim_classification, arm_A_quality, arm_B_quality) -> float
    Adjusts confidence based on:
    - Claim verifiability
    - Evidence quality
    - Arm balance

apply_confidence_thresholds(verdict, confidence, claim_classification) -> dict
    Forces "mixed" or "insufficient" when:
    - confidence < 0.85
    - arm_balance < 0.15
    - avg_authority < 0.65
```

**Phase:** 10 (calibration & edge cases)

---

#### Step 13: Response Formatting
**Files:**
- `api/analyses.py`
- `intelligence/pipeline/run.py`

**Functions:**
```python
run_preview(text, test_mode) -> dict
    Main pipeline entry point

_ensure_preview_shape(res) -> dict
    Ensures consistent response structure

# API endpoint:
@router.post("/analyses/preview")
async def preview(body, _user) -> dict
```

**Phase:** Baseline

---

### Module Structure

```
intelligence/
├── preprocess/
│   └── classify.py          # Step 0: Claim classification (Phase 8)
├── analyze/
│   └── enrich.py            # Step 1: Claim understanding
├── strategy/
│   └── plan_v2.py           # Step 2: Query generation (Phase 5 enhanced)
├── planning/
│   └── diversify.py         # Step 2: R1/R2 diversification (Phase 5)
├── gather/
│   ├── pipeline.py          # Steps 3-7: Evidence gathering (Phase 2, 7)
│   ├── online.py            # Step 3: Search execution
│   └── counter_frames.py    # P19: Counter-frame generation
├── content/
│   ├── grade.py             # Step 9: P20 orchestrator (Phase 1, 3)
│   ├── fullread.py          # Step 9: P21 authority (Phase 3, 8)
│   ├── semantic_read.py     # Step 9: P23 semantic (Phase 9)
│   ├── semantic_frames.py   # Step 9: P24 frames
│   ├── p25_aggregate.py     # Step 10: Arm aggregation (Phase 4)
│   └── fetch_enrichment.py  # Step 8: Content fetching
├── orchestration/
│   └── dual_lane.py         # Runs R1 and R2 (Phase 5)
├── consensus/
│   ├── dual_lane.py         # Step 11: Consensus (Phase 6)
│   └── build.py             # Step 11: Quality comparison (Phase 6)
├── calibration/
│   └── confidence.py        # Step 12: Calibration (Phase 10)
├── sources/
│   └── reliability.py       # Authority database (Phase 8)
└── pipeline/
    └── run.py               # Main orchestration
```

---

## PART 3: INTEGRATION FLOW (From plan + workflow)

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ USER INPUT: "Water boils at 100°C"                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 0: classify_claim()                                    │
│ → category: SIMPLE_FACTUAL                                  │
│ → verifiability: HIGHLY_VERIFIABLE                          │
│ Decision: CONTINUE                                           │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: enrich_claim_obj()                                  │
│ → entities: ["Water"]                                       │
│ → numbers: [{value: 100, unit: "°C", precision: 0}]        │
│ → cues: {has_temperature: true}                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: build_search_plans_v2() + diversify_plan_for_lane()│
│                                                              │
│ ┌──────────────────┐         ┌──────────────────┐          │
│ │ R1 PLAN          │         │ R2 PLAN          │          │
│ │ • 5 queries      │         │ • 8 queries      │          │
│ │ • Precision mode │         │ • Recall mode    │          │
│ │ • Strict thresh  │         │ • Lenient thresh │          │
│ └──────────────────┘         └──────────────────┘          │
└──────────────────┬──────────────────┬──────────────────────┘
                   │                  │
                   ↓                  ↓
         ┌─────────────────┐  ┌─────────────────┐
         │  R1 EXECUTION   │  │  R2 EXECUTION   │  (PARALLEL)
         └─────────┬───────┘  └─────────┬───────┘
                   │                    │
                   ↓                    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: run_plan() - Search execution                       │
│ R1: 5 queries × ~50 results = ~250 candidates               │
│ R2: 8 queries × ~50 results = ~400 candidates               │
└──────────────────┬──────────────────┬──────────────────────┘
                   │                  │
                   ↓                  ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: filter_unrelated()                                  │
│ R1: 250 → 180 (28% dropped)                                 │
│ R2: 400 → 280 (30% dropped)                                 │
└──────────────────┬──────────────────┬──────────────────────┘
                   │                  │
                   ↓                  ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: quality_gate()                                      │
│ R1: 180 → 120 (33% dropped)                                 │
│ R2: 280 → 200 (29% dropped)                                 │
└──────────────────┬──────────────────┬──────────────────────┘
                   │                  │
                   ↓                  ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: validate_query_results() [optional retry]          │
│ Check relevance, refine if needed                           │
└──────────────────┬──────────────────┬──────────────────────┘
                   │                  │
                   ↓                  ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: rank_candidates()                                   │
│ R1: Select top 5 per arm (10 total)                         │
│ R2: Select top 5 per arm (10 total)                         │
└──────────────────┬──────────────────┬──────────────────────┘
                   │                  │
                   ↓                  ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: enrich_items_with_content()                         │
│ Fetch full text for all 20 items                            │
└──────────────────┬──────────────────┬──────────────────────┘
                   │                  │
                   ↓                  ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 9: FOR EACH ITEM (20 times per researcher)            │
│                                                              │
│   attach_finding_to_item() [P20 orchestrator]              │
│         ├─→ calculate_authority_score() [P21]              │
│         ├─→ analyze_item() [P23 semantic]                  │
│         └─→ analyze_frames() [P24 pattern]                 │
│   fuse_module_grades() → item_grade (0-1)                  │
│                                                              │
│ Output: Each item has item_grade, authority, features       │
└──────────────────┬──────────────────┬──────────────────────┘
                   │                  │
                   ↓                  ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 10: aggregate_verdict() [P25]                         │
│                                                              │
│ R1 Processing:                                               │
│   • Calculate arm_A_strength (diversity×consistency×breadth)│
│   • Calculate arm_B_strength                                │
│   • Balance = arm_A - arm_B                                 │
│   • Confidence (includes authority, diversity, consistency) │
│   • Verdict label (supports/challenges/mixed)              │
│                                                              │
│ R2 Processing: [same]                                       │
│                                                              │
│ Output:                                                      │
│   R1_verdict: {label, confidence, arm_A, arm_B, balance}   │
│   R2_verdict: {label, confidence, arm_A, arm_B, balance}   │
└──────────────────┬──────────────────┬──────────────────────┘
                   │                  │
                   └──────────┬───────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 11: compute_consensus()                                │
│                                                              │
│ 1. compare_evidence_quality(R1_items, R2_items)            │
│    → quality_gap                                             │
│                                                              │
│ 2. resolve_disagreement(R1_verdict, R2_verdict, quality)   │
│    • IF agree → boost confidence +10%                       │
│    • IF disagree + large gap → trust better evidence       │
│    • IF disagree + small gap → check balance or → mixed    │
│                                                              │
│ 3. synthesize_evidence(R1_items, R2_items)                 │
│    • Deduplicate by URL                                     │
│    • Sort by grade × authority                              │
│    • Take top 5 per arm                                     │
│                                                              │
│ Output:                                                      │
│   consensus: {label, confidence, rationale}                 │
│   evidence: {arm_A: [top5], arm_B: [top5]}                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 12: calibrate_confidence()                             │
│                                                              │
│ 1. Adjust by claim type (HIGHLY_VERIFIABLE → +5%)          │
│ 2. Adjust by evidence quality (avg_authority > 0.9 → +8%)  │
│ 3. Adjust by arm balance (balance > 0.3 → +10%)            │
│ 4. apply_confidence_thresholds()                            │
│    • IF confidence < 0.85 → "mixed"                         │
│    • IF balance < 0.15 → "mixed"                            │
│    • IF avg_authority < 0.65 → "insufficient"              │
│                                                              │
│ Output:                                                      │
│   calibrated_verdict: {label, confidence, rationale}        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 13: _ensure_preview_shape() + API formatting          │
│                                                              │
│ • Map to IFCN scale (90-100 → TRUE)                         │
│ • Format evidence with URLs, grades, authority stars        │
│ • Add research quality metrics                              │
│ • Generate plain English explanation                        │
│                                                              │
│ Output:                                                      │
│   {                                                          │
│     verdict: "TRUE", confidence: 98%,                       │
│     evidence: {arm_A: [...], arm_B: [...]},                │
│     research_quality: {...},                                │
│     processing_time: 8.3s                                   │
│   }                                                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ USER SEES: Verdict + Evidence + Quality Metrics             │
└─────────────────────────────────────────────────────────────┘
```

---

### Critical Integration Points

#### 1. Phase 1 Module Consolidation
**Problem:** Multiple modules produced competing grades
**Solution:** P20 orchestrates P21/P23/P24, produces ONE item_grade

**Before:**
```
P20 → item_grade (0-10)
P21 → grade_full (0-10)
P23 → item_grade (0-1, overwrites P20)
P24 → best_frame_score (0-1)
P25 → Confusion, which to use?
```

**After:**
```
P20 [orchestrator]
  ├─→ calls P21 → authority_score
  ├─→ calls P23 → semantic_similarity
  ├─→ calls P24 → frame_match_score
  └─→ fuse_module_grades() → ONE item_grade (0-1)

P25 receives clean item_grade per item
```

**Files Changed:**
- `intelligence/content/grade.py` - P20 becomes orchestrator
- `intelligence/content/fullread.py` - P21 returns features, not grades
- `intelligence/content/semantic_read.py` - P23 returns features
- `intelligence/content/semantic_frames.py` - P24 returns features

---

#### 2. Phase 2 Filter Ordering
**Problem:** Expensive analysis before filtering
**Solution:** Filter BEFORE ranking and analysis

**Before:**
```
Search → Assign Arm → Rank → Analyze (expensive) → Select Top 3
```

**After:**
```
Search → Filter Unrelated → Quality Gate → Rank → Analyze → Select Top 5
```

**Performance Impact:**
- 400 candidates → 120 quality candidates before deep analysis
- 70% reduction in expensive operations

**Files Changed:**
- `intelligence/gather/pipeline.py` - Added `filter_unrelated()`, `quality_gate()`

---

#### 3. Phase 5 Parallel Execution
**Problem:** R1 and R2 run sequentially
**Solution:** Parallel execution with `run_dual_researchers()`

**Before:**
```python
r1_result = run_researcher('R1', claim)
r2_result = run_researcher('R2', claim)  # Waits for R1
```

**After:**
```python
await run_dual_researchers(claim, base_plan, ...)
# Internally runs R1 and R2 simultaneously
```

**Performance Impact:** ~40% faster (if I/O bound)

**Files Changed:**
- `intelligence/orchestration/dual_lane.py` - Parallel orchestration

---

#### 4. Phase 6 Consensus Logic
**Problem:** Compared labels only, ignored evidence quality
**Solution:** Evidence-based resolution

**Before:**
```python
if r1_label == r2_label:
    return r1_label
else:
    return label_with_higher_confidence
```

**After:**
```python
quality_gap = |R1_quality - R2_quality|

if r1_label == r2_label:
    boost confidence +10%
elif quality_gap > 0.15:
    trust better evidence
elif quality_gap < 0.15:
    check balance or return "mixed"
```

**Impact:** Resolves disagreements intelligently based on evidence, not just confidence

**Files Changed:**
- `intelligence/consensus/build.py` - Added `compare_evidence_quality()`, `resolve_disagreement()`

---

## PART 4: KNOWN ISSUES (From audit + plan)

### Issues Found in Audit (Excel)

**Summary by Stage:**
| Stage | Good | Needs Mod | Misplaced | Missing | Unknown |
|-------|------|-----------|-----------|---------|---------|
| 1. Query Generation | 0 | 3 | 0 | 2 | 1 |
| 2. Evidence Curation | 1 | 0 | 2 | 4 | 1 |
| 3. Stance Detection | 2 | 4 | 2 | 0 | 0 |
| 4. Semantic Read | 7 | 4 | 0 | 0 | 0 |
| 5. Evidence Grading | 5 | 2 | 1 | 2 | 1 |
| 6. Arm Aggregation | 9 | 1 | 0 | 6 | 0 |
| 7. Dual Researchers | 3 | 2 | 0 | 4 | 0 |
| 8. Consensus | 2 | 2 | 1 | 8 | 0 |

**Total:** 29 Good, 18 Needs Mod, 6 Misplaced, 26 Missing, 3 Unknown

---

### Critical Issues Addressed by Refactor

#### 1. Scale Bug (Phase 1)
**Issue:** P20 line 231 multiplied by (10/8) instead of dividing by 8
**Impact:** 10x grade inflation when P23 failed
**Fix:**
```python
# Before:
grade = round(min(score, 8.0) * (10.0/8.0), 2)  # ❌ 0-10 scale

# After:
grade = round(min(score, 8.0) / 8.0, 3)  # ✓ 0-1 scale
```
**Location:** `intelligence/content/grade.py:231`

---

#### 2. Competing Grades (Phase 1)
**Issue:** 4 modules produced different grades on different scales
**Impact:** P25 didn't know which grade to use
**Fix:** P20 orchestrator pattern (see Integration Point 1)

---

#### 3. Missing Evidence Curation (Phase 2)
**Issue:** No filtering before analysis
**Impact:** Wasted computation on junk, reduced accuracy
**Missing Functions:**
- `filter_unrelated()` - Fast relatedness check
- `quality_gate()` - Source quality filtering
**Fix:** Added both functions with deterministic filters
**Location:** `intelligence/gather/pipeline.py`

---

#### 4. No Authority in Grading (Phase 3)
**Issue:** .gov and blogs weighted equally
**Impact:** Volume > quality, easily gamed
**Fix:** Authority factor in item_grade calculation
```python
item_grade = (
    40% semantic +
    30% frame +
    20% authority +  # ← NEW
    10% coverage
)
```
**Location:** `intelligence/content/grade.py::fuse_module_grades()`

---

#### 5. Missing Quality Multipliers (Phase 4)
**Issue:** Arm aggregation just averaged grades
**Impact:** 5 mediocre sources beat 1 excellent source
**Missing:**
- Diversity score
- Consistency score
- Breadth score
**Fix:** Added all three quality multipliers
**Location:** `intelligence/content/p25_aggregate.py`

---

#### 6. R1/R2 Not Diverse (Phase 5)
**Issue:** R1 and R2 used same strategy, just different seeds
**Impact:** Both researchers found same issues, missed others
**Missing:**
- Different query generation strategies
- Different thresholds
**Fix:**
- `generate_queries_r1()` - Precision (quoted, exact)
- `generate_queries_r2()` - Recall (broad, paraphrased)
- Lane-specific thresholds
**Location:** `intelligence/strategy/plan_v2.py`

---

#### 7. Naive Consensus (Phase 6)
**Issue:** Compared labels only, ignored evidence quality
**Impact:** Couldn't resolve disagreements intelligently
**Missing:**
- Evidence quality comparison
- Intelligent disagreement resolution
- Evidence synthesis
**Fix:** Evidence-based consensus with quality metrics
**Location:** `intelligence/consensus/build.py`

---

#### 8. No Query Validation (Phase 7)
**Issue:** Bad queries returned off-topic results, never refined
**Impact:** Wasted results, reduced accuracy
**Missing:**
- Query validation loop
- Auto-refinement
**Fix:** `validate_query_results()` with auto-refine
**Location:** `intelligence/gather/pipeline.py`

---

#### 9. No Claim Classification (Phase 8)
**Issue:** Tried to verify opinions and predictions
**Impact:** Wasted resources, wrong verdicts
**Missing:**
- Claim classification system
- Early unverifiable detection
**Fix:** 6-category classification with verifiability scores
**Location:** `intelligence/preprocess/classify.py`

---

#### 10. No Precision Handling (Phase 9)
**Issue:** "8%" matched "12%", negation missed
**Impact:** Incorrect numeric matches, negation errors
**Missing:**
- Numeric precision context
- Negation detection
- Hedging detection
- Temporal weighting
- Geographic scope matching
**Fix:** Added all precision handlers
**Location:** Various in `intelligence/content/`

---

#### 11. No Confidence Calibration (Phase 10)
**Issue:** System overconfident, no thresholds
**Impact:** High confidence but wrong answers
**Missing:**
- Confidence calibration
- Conservative thresholds
- Edge case handlers
**Fix:** Calibration system with verified thresholds
**Location:** `intelligence/calibration/confidence.py`

---

### Key SAGPT Insights from Audit

**From Excel "KEY SAGPT INSIGHTS" section:**

1. **R1/R2 were meant to have REAL diversity** (precision vs recall strategies), not just seed differences

2. **Stance detection was ALWAYS supposed to be in P20**, not scattered across multiple modules

3. **Authority scores were ALWAYS meant to influence grading**, not just be metadata

4. **Consensus was ALWAYS supposed to compare evidence quality**, not just labels

5. **Scale normalization (0-1) was ALWAYS the intent**, the 0-10 scale was a bug

6. **Evidence filtering was ALWAYS supposed to happen BEFORE analysis**, not after

---

### What Was Wrong vs What Should Be

| Aspect | OLD System (Wrong) | NEW System (Should Be) | Phase Fixed |
|--------|-------------------|------------------------|-------------|
| **Module Grades** | 4 competing grades (0-10 and 0-1 mixed) | ONE grade from P20 (0-1) | Phase 1 |
| **Authority** | Just metadata, not used | 20% weight in item_grade | Phase 3 |
| **Evidence Filter** | After analysis (wasted) | Before analysis (efficient) | Phase 2 |
| **Diversity** | Not checked | Penalizes single-source | Phase 4 |
| **Consistency** | Not checked | Penalizes contradictions | Phase 4 |
| **R1/R2** | Same strategy | Precision vs Recall | Phase 5 |
| **Consensus** | Label comparison | Evidence quality comparison | Phase 6 |
| **Query Validation** | None | Auto-refines if off-topic | Phase 7 |
| **Claim Type** | Treats all same | 6 categories, early exit | Phase 8 |
| **Precision** | "8%" matches "12%" | Context-aware precision | Phase 9 |
| **Negation** | Missed | Detected and handled | Phase 9 |
| **Calibration** | Overconfident | Conservative thresholds | Phase 10 |
| **Confidence** | No verification | Verified: 95% conf → 99% correct | Phase 11 |

---

## SUMMARY

### Target Architecture Principles

1. **One Grade Per Item** (Phase 1)
   - P20 orchestrates P21/P23/P24
   - Single `item_grade` (0-1) from fusion

2. **Filter Before Analysis** (Phase 2)
   - Fast filters remove junk early
   - Quality gate ensures source reliability
   - Saves computation, improves accuracy

3. **Authority Matters** (Phase 3)
   - Source reliability weighted in grading
   - .gov > .edu > news > blogs
   - Volume doesn't beat quality

4. **Quality Multipliers** (Phase 4)
   - Diversity: Penalizes single-source
   - Consistency: Penalizes contradictions
   - Breadth: Rewards complementary angles

5. **True Diversity** (Phase 5)
   - R1 (Precision): Exact, quoted, strict
   - R2 (Recall): Broad, paraphrased, lenient
   - Parallel execution

6. **Evidence-Based Consensus** (Phase 6)
   - Compares evidence quality, not just labels
   - Intelligent disagreement resolution
   - Synthesizes best evidence from both

7. **Query Validation** (Phase 7)
   - Checks relevance, auto-refines
   - Prevents off-topic results

8. **Claim Classification** (Phase 8)
   - Detects unverifiable claims early
   - 6-category classification
   - Early exit for opinions/predictions

9. **Precision Handling** (Phase 9)
   - Context-aware numeric matching
   - Negation and hedging detection
   - Temporal and geographic weighting

10. **Conservative Calibration** (Phase 10)
    - Thresholds: <85% confidence → "mixed"
    - Verified: 95%+ conf → 99%+ correct
    - Better to admit uncertainty than be wrong

---

### Success Metrics

**Accuracy by Claim Type:**
- Simple factual: 99.5%
- Complex factual: 99%
- Historical: 99%
- Scientific: 99%
- Policy: 95% (or marked insufficient)
- Unverifiable detection: 99%

**Confidence Calibration:**
- 95-100% confidence → 99%+ correct
- 90-95% confidence → 95%+ correct
- 85-90% confidence → 90%+ correct
- <85% → Forced to "mixed"

**Performance:**
- Processing time: 8-10 seconds
- Early exits: Unverifiable claims in 1 second

**User Experience:**
- Clear verdict with confidence
- Transparent evidence with quality indicators
- Plain English explanations
- Research quality metrics

---

**Document Status:** COMPLETE
**Next Steps:** Use this as reference for implementation verification and gap analysis

---

*Generated from source documents - no assumptions made, only extracted documented requirements*
