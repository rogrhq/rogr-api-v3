# ROGRv2 Pipeline Workflow - Complete Technical Documentation

**Date:** 2025-10-14
**Branch:** post-mp-cleanup
**Purpose:** Document complete data flow from claim input to final verdict

---

## Part 1: Executive Summary

The ROGRv2 fact-checking pipeline processes user claims through a multi-stage enrichment system using two independent AI "researchers" (R1 and R2) that gather evidence, analyze semantic relationships, extract frames, and build consensus verdicts. The pipeline starts at `intelligence/pipeline/run.py:run_preview()`, flows through evidence gathering (P19), content enrichment (P22), and five analysis modules (P20-P25) for each researcher, then combines results through consensus building (P27) to produce a final verdict with confidence score and supporting evidence.

---

## Part 2: High-Level Flow

**Input:** User claim text (string)
**Output:** Final verdict with confidence, evidence items, researcher reports

### Main Stages

1. **Claim Preprocessing** - Parse entities, numbers, detect claim type
2. **Search Planning** - Generate search queries for support/challenge arms
3. **Dual Researcher Orchestration (P26)** - Launch R1 and R2 in sequence
4. **Evidence Gathering (P19)** - Search web, generate counter-frames for challenges
5. **Content Enrichment (P22)** - Fetch full article content
6. **Item Analysis Pipeline (P20-P25)** - Process each evidence item through 6 modules
   - P20: Stance detection (support/challenge/mixed/unrelated)
   - P21: Full-read evaluation with window sliding
   - P23: Semantic analysis with paraphrase matching
   - P24: Frame extraction and comparison
   - P25: Aggregate to per-researcher verdict
7. **Consensus Building (P27)** - Combine R1 and R2 verdicts
8. **Telemetry & Manifest (P29)** - Record reproducibility data
9. **Response Formatting** - Return structured JSON

---

## Part 3: Detailed Stage Breakdown

### Stage 1: Entry Point & Claim Preprocessing

**File:** `intelligence/pipeline/run.py`
**Function:** `run_preview(text: str, test_mode: bool = False)` (lines 121-182)

**Input:**
```python
text: str  # User's claim text
test_mode: bool  # Default False
```

**Processing Steps:**

1. **Create claim object** (lines 124-125)
```python
claim = {"id": "c-0", "text": text.strip(), "tier": "primary"}
```

2. **Enrich with entities/numbers** (lines 127-129)
```python
from intelligence.analyze.enrich import enrich_claim_obj
claim = enrich_claim_obj(claim)
```
Adds fields:
- `entities`: List[str] - Extracted proper nouns
- `numbers`: Dict - Extracted numbers, percentages, years
- `cues`: Dict - Comparison indicators

3. **Detect claim type** (lines 131-133)
```python
from intelligence.claims.interpret import detect_claim_type
claim["claim_type"] = detect_claim_type(claim)
```
Returns: "scientific", "policy_econ", or "generic"

4. **Build search plan** (lines 135-137)
```python
from intelligence.strategy.plan_v2 import build_search_plans_v2
base_plan = build_search_plans_v2(claim)
```

**Output:**
```python
base_plan: Dict[str, Any] = {
    "arms": {
        "A": {"intent": "support", "queries": [...]},
        "B": {"intent": "challenge", "queries": [...]}
    },
    "meta": {
        "claim_type": str,
        "concept": str,
        "dimension": str
    }
}
```

**Next:** Pass to dual researcher orchestration

---

### Stage 2: Dual Researcher Orchestration (P26)

**File:** `intelligence/orchestration/dual_lane.py`
**Function:** `run_dual_researchers()` (lines 4-70)

**Input:**
```python
claim_text: str
base_plan: Dict[str, Any]
enrichment_pipeline: Callable  # run_single_lane_enrichment
diversify_fn: Callable  # diversify_plan_for_lane
telemetry_class: Type  # LaneTelemetry
```

**Processing Steps:**

1. **Diversify plans for R1 and R2** (lines 29-35)
```python
from intelligence.planning.diversify import get_available_providers
providers = get_available_providers()

r1_plan, r1_config = diversify_fn(base_plan, "R1", claim_text, providers)
r2_plan, r2_config = diversify_fn(base_plan, "R2", claim_text, providers)
```

Diversification:
- R1: Uses primary search provider, seed=0
- R2: Uses alternate provider if available, seed=42
- Different query ordering/selection

2. **Run R1 (SEQUENTIAL)** (lines 37-40)
```python
r1_telemetry = telemetry_class("R1")
r1_result = await enrichment_pipeline(claim_text, r1_plan, "R1", r1_telemetry)
r1_telemetry_data = r1_telemetry.finalize()
```

3. **Run R2 (SEQUENTIAL)** (lines 42-45)
```python
r2_telemetry = telemetry_class("R2")
r2_result = await enrichment_pipeline(claim_text, r2_plan, "R2", r2_telemetry)
r2_telemetry_data = r2_telemetry.finalize()
```

**IMPORTANT:** R1 and R2 run SEQUENTIALLY, not in parallel. R2 starts after R1 completes.

4. **Build researcher objects** (lines 47-63)
```python
researchers = [
    {
        "id": "R1",
        "verdict": r1_result.get("verdict", {}),
        "evidence": r1_result.get("evidence", {}),
        "lane_config": r1_config,
        "telemetry": r1_telemetry_data
    },
    {
        "id": "R2",
        "verdict": r2_result.get("verdict", {}),
        "evidence": r2_result.get("evidence", {}),
        "lane_config": r2_config,
        "telemetry": r2_telemetry_data
    }
]
```

**Output:**
```python
{
    "researchers": [R1_obj, R2_obj],
    "verdict": r1_result["verdict"],  # Backward compat
    "evidence": r1_result["evidence"]  # Backward compat
}
```

**Next:** Each researcher runs through complete enrichment pipeline

---

### Stage 3: Single Lane Enrichment Pipeline

**File:** `intelligence/pipeline/run.py`
**Function:** `run_single_lane_enrichment()` (lines 39-118)

**Input:**
```python
claim_text: str
plan: Dict[str, Any]  # Diversified plan for this lane
lane_id: str  # "R1" or "R2"
telemetry: LaneTelemetry
```

**Processing Steps:**

#### Step 3.1: Evidence Gathering (P19)

**Line 58:**
```python
evidence = await build_evidence_for_claim(claim_text, plan, max_per_arm=3)
```

**File:** `intelligence/gather/pipeline.py`
**Function:** `build_evidence_for_claim()` (lines 105-150+)

**Sub-steps:**

1. **Extract arm definitions** (line 116)
```python
arm_defs = _extract_arm_defs(plan)  # Returns [arm_A_def, arm_B_def]
```

2. **For each arm, execute search** (lines 117-134)
```python
for idx, arm_def in enumerate(arm_defs):
    label = _canonical_arm_label(arm_def, idx)  # "A" or "B"

    # P19: Add counter-frame queries for Arm B
    if label == "B":
        counter_queries = generate_counter_frame_queries(
            claim_text,
            arm_def.get("queries", []),
            plan
        )
        arm_def["queries"].extend([query for _, query in counter_queries])

    labeled_cands.extend(
        await _exec_plan_for_arm(plan, arm_def, label, max_per_query=2)
    )
```

**P19 Counter-Frames:** (intelligence/gather/counter_frames.py)
Generates 5 frame types for challenges:
- numeric_dispute
- denominator_shift
- timing_change
- authority_conflict
- methodology

3. **Group and normalize candidates** (lines 136-139)
```python
armA_raw, armB_raw = _group_by_arm(labeled_cands)
armA_norm = normalize_candidates(armA_raw)
armB_norm = normalize_candidates(armB_raw)
```

4. **Rank candidates** (lines 149-150)
```python
ranked_A = rank_candidates(claim_text, claim_text, armA_norm, top_k=3)
ranked_B = rank_candidates(claim_text, claim_text, armB_norm, top_k=3)
```

**Output:**
```python
evidence = {
    "arm_A": [  # Support evidence (top 3)
        {
            "url": str,
            "title": str,
            "snippet": str,
            "arm": "A",
            "provider": str,
            "score": float
        },
        ...
    ],
    "arm_B": [  # Challenge evidence (top 3)
        {...}
    ]
}
```

#### Step 3.2: Content Enrichment (P22)

**Lines 67-73:**
```python
fetch_cache = {}
for arm_key in ("arm_A", "arm_B"):
    items = evidence.get(arm_key, [])
    if items:
        items, fetch_cache = await enrich_items_with_content(items, fetch_cache)
        evidence[arm_key] = items
```

**File:** `intelligence/content/fetch_enrichment.py`
**Function:** `enrich_items_with_content()`

Fetches full article content and adds:
- `content`: str (full article text, 2,000-20,000+ chars)
- `content_hash`: str (MD5 hash)
- `coverage`: "full" | "partial" | "snippet_only"
- `content_excerpt`: str (truncated if >12,000 chars)

**CRITICAL BUG FIX:** Lines 63-64 use keyword argument:
```python
result = await fetch_text(url, timeout=timeout)  # Must be keyword
content = result.get('text', '')  # Extract text from dict
```

**Evidence Item After P22:**
```python
{
    "url": str,
    "title": str,
    "snippet": str,
    "arm": "A" | "B",
    "provider": str,
    "score": float,
    "content": str,  # NEW - Full article text
    "content_hash": str,  # NEW
    "coverage": str,  # NEW
    "content_excerpt": str  # NEW
}
```

#### Step 3.3: Item Analysis Loop (P20-P25)

**Lines 75-105:** For each item in each arm:

##### P20: Stance Detection

**Lines 78-82:**
```python
try:
    attach_finding_to_item(claim_text, arm_label, item)
except:
    pass
```

**File:** `intelligence/content/grade.py`
**Function:** `attach_finding_to_item()` (lines 247-267)

Calls `build_finding()` (lines 176-245):

1. **Select best window** (lines 182-191)
```python
if not window:
    from intelligence.content.extract_facts import best_window_for_text
    window, sim = best_window_for_text(claim_text, content_text or "", win=4)
    if not window:
        window = snippet_text or content_text or ""
if sim is None or sim < 0:
    sim = jaccard_trigrams(claim_text, window)
```

2. **Extract signals** (lines 193-200)
```python
ents = claim_entities(claim_text)  # Entities from claim
nums = claim_numbers(claim_text)  # Numbers from claim
yrs  = claim_years(claim_text)  # Years from claim

has_ent = has_any(window, ents)  # Entity in window?
has_num = has_any(window, nums)  # Number in window?
has_yr  = has_any(window, yrs)  # Year in window?
```

3. **Determine stance** (line 203)
```python
stance = _stance_for_window(window, arm, claim_text=claim_text)
```

**Function:** `_stance_for_window()` (lines 60-157)

Uses frame-based reasoning:
- Extracts frames from claim and evidence
- Compares frames (exact/partial/none)
- Checks paraphrase scores
- Checks condition equivalence
- Returns: "support", "challenge", "contextual_support", "mixed", or "unrelated"

4. **Calculate score** (lines 206-228)
```python
score = 0.0
rationale: List[str] = []

if has_ent:
    score += W_ENTITY  # 2.0
    rationale.append("entity matched")
if has_num:
    score += W_NUMBER  # 2.0
    rationale.append("number matched")
if has_yr:
    score += W_YEAR  # 1.0
    rationale.append("year matched")

if sim >= 0.35:
    score += W_SIM_HI  # 2.0
    rationale.append(f"similarity high ({sim:.2f})")
elif sim >= 0.25:
    score += W_SIM_LO  # 1.0
    rationale.append(f"similarity moderate ({sim:.2f})")

if arm.upper()=="A" and stance=="support":
    score += W_STANCE  # 1.0
    rationale.append("stance supports claim")
if arm.upper()=="B" and stance=="challenge":
    score += W_STANCE  # 1.0
    rationale.append("stance challenges claim")

penalty = _modality_penalty(window)
if penalty > 0:
    score -= penalty
    rationale.append("modality hedged")

score = max(0.0, score)
```

5. **Normalize to grade** (lines 229-231)
```python
# normalize to 0..10 (max theoretical ~8); scale gently
grade = round(min(score, 8.0) * (10.0/8.0), 2)
```

**⚠️ CRITICAL SCALE ISSUE:** `grade` is on **0-10 scale** but P25 expects **0-1 scale**

6. **Build finding object** (lines 233-245)
```python
finding = {
    "grade": grade,  # 0-10 scale
    "stance": stance,
    "matched_spans": [window][:1] if window else [],
    "rationale": rationale,
    "similarity": round(sim, 3),
    "signals": {
        "entity": bool(has_ent),
        "number": bool(has_num),
        "year": bool(has_yr),
    }
}
```

7. **Attach to item** (lines 261-266)
```python
item["item_grade"] = finding["grade"]  # 0-10 scale assigned here!
item["stance"] = finding["stance"]
item["finding"] = finding
return item
```

**Evidence Item After P20:**
```python
{
    ...(all previous fields),
    "item_grade": float,  # 0-10 scale (BUG: should be 0-1)
    "stance": str,  # "support", "challenge", "mixed", "unrelated", "contextual_support"
    "finding": {
        "grade": float,  # 0-10 scale
        "stance": str,
        "matched_spans": [str],
        "rationale": [str],
        "similarity": float,
        "signals": {"entity": bool, "number": bool, "year": bool}
    }
}
```

##### P21: Full-Read Evaluation

**Lines 84-89:**
```python
if item.get("content"):
    try:
        evaluate_full_evidence(claim_text, item)
    except:
        pass
```

**File:** `intelligence/content/fullread.py`
**Function:** `evaluate_full_evidence()` (lines 177-269)

1. **Read content** (lines 181-193)
```python
read = item.get("content") or item.get("content_excerpt") or item.get("snippet") or ""
if len(read) > 12000:
    read = read[:12000]  # Clamp to 12KB

if not read.strip():
    item["grade_full"] = float(item.get("grade") or 0.0)
    item["stance_full"] = item.get("finding", {}).get("stance") or "unrelated"
    item["signals_full"] = {"reason": "no_text"}
    item["credibility"] = _credibility_from(item.get("url") or "", "")
    return item
```

2. **Slide windows, find best match** (lines 195-244)
```python
best = {"score": -1.0, "stance": "unrelated", "jacc": 0.0, ...}
claim_tri = _ngrams(_tokens(claim), 3)

for chunk in _window_sentences(read, win=4, max_sents=80):
    txt = " ".join(chunk)
    tri = _ngrams(_tokens(txt), 3)
    j = _jaccard(claim_tri, tri)
    stance = _stance_for_chunk(claim, txt)
    neg = bool(_NEG.search(txt))
    ent = _entity_overlap(claim, txt)
    pct_any, pct_close = _percent_hits(claim, txt)
    yh = _year_hit(claim, txt)

    # Weighted score for window
    score = 0.0
    score += 2.0 * (1.0 if pct_close else 0.0) + 0.8 * (1.0 if pct_any else 0.0)
    score += 1.2 * (1.0 if yh else 0.0)
    score += 2.0 * min(ent, 1.0)
    score += 3.0 * j  # tri-gram overlap

    # Paraphrase matching (NEW)
    para_score = paraphrase_match_score(claim, txt)
    if para_score > 0.3:
        score += 0.6 * para_score

    # Condition awareness
    if cond_match:
        score += 0.4
    elif cond_mismatch:
        score -= 0.3

    if stance in ("support", "challenge"):
        score += 0.8

    if score > best["score"]:
        best = {all metrics}
```

3. **Map to grade_full** (lines 246-255)
```python
base = max(0.0, best["score"])
# Squashing to 0..10 with diminishing returns
grade_full = 10.0 * (1.0 - math.exp(-base / 6.0))

# Stance adjustments
stance_full = best["stance"]
if best["neg"] and stance_full == "challenge":
    grade_full = min(10.0, grade_full + 0.5)
if best["neg"] and stance_full == "support":
    grade_full = max(0.0, grade_full - 0.5)
```

4. **Attach to item** (lines 257-268)
```python
item["grade_full"] = round(grade_full, 2)  # 0-10 scale
item["stance_full"] = stance_full
item["signals_full"] = {
    "jaccard3": round(best["jacc"], 3),
    "entity_overlap": round(best["entity_overlap"], 3),
    "percent_any": bool(best["pct_any"]),
    "percent_close": bool(best["pct_close"]),
    "year_hit": bool(best["year_hit"]),
    "negation": bool(best["neg"]),
}
item["credibility"] = round(_credibility_from(item.get("url") or "", read), 3)
return item
```

**Evidence Item After P21:**
```python
{
    ...(all previous fields),
    "grade_full": float,  # 0-10 scale (consistent with P20)
    "stance_full": str,
    "signals_full": {
        "jaccard3": float,
        "entity_overlap": float,
        "percent_any": bool,
        "percent_close": bool,
        "year_hit": bool,
        "negation": bool
    },
    "credibility": float  # 0-1 scale
}
```

##### P23: Semantic Analysis

**Lines 91-96:**
```python
if item.get("content"):
    try:
        analyze_item(claim_text, item, window=3)
    except:
        pass
```

**File:** `intelligence/content/semantic_read.py`
**Function:** `analyze_item()` (lines 103-203+)

1. **Slide windows, compute findings** (lines 109-201)
```python
content = item.get("content") or ""
if not content:
    item.setdefault("findings", [])
    item.setdefault("item_grade", 0.15)  # 0-1 scale (CORRECT)
    item.setdefault("grade_label", "low")
    return item

# Window processing...
for win in windows:
    # Calculate trigram overlap
    # Calculate paraphrase score
    # Extract entities
    # Check percentages, years
    # Compute weighted score

    findings.append(finding_obj)

# Select best finding
best = max(findings, key=lambda f: f.get("score", 0))
```

2. **Compute item_grade** (lines 195-203)
```python
# Best finding score (0-10 range typically)
best_score = best.get("score", 0)

# Coverage factor
cov = item.get("coverage", "unknown").lower()
if cov == "full":
    cov_w = 1.0
elif cov == "partial":
    cov_w = 0.8
elif cov == "snippet_only":
    cov_w = 0.6
else:
    cov_w = 0.7

# Combine and normalize to 0-1
item_grade = max(0.0, min(1.0, 0.6 * best + 0.4 * cov_w))
item["item_grade"] = float(item_grade)  # 0-1 scale (CORRECT)
item["grade_label"] = "high" if item_grade >= 0.67 else ("medium" if item_grade >= 0.4 else "low")
```

**⚠️ SCALE CONFLICT:** P23 produces `item_grade` on **0-1 scale**, but P20 produced it on **0-10 scale**

**Evidence Item After P23:**
```python
{
    ...(all previous fields),
    "findings": [  # List of window findings
        {
            "window": str,
            "score": float,
            "signals": {...}
        },
        ...
    ],
    "item_grade": float,  # NOW ON 0-1 SCALE (overwrites P20's 0-10 value)
    "grade_label": str  # "high", "medium", "low"
}
```

##### P24: Frame Analysis

**Lines 98-105:**
```python
content = item.get("content") or ""
if content:
    try:
        frames = analyze_frames(claim_text, content, window=3)
        item.update(frames)
    except:
        pass
```

**File:** `intelligence/content/semantic_frames.py`
**Function:** `analyze_frames()` (lines 160-250+)

1. **Extract claim frame** (lines 111-121)
```python
def extract_claim_frame(claim_text: str) -> Dict[str, Any]:
    ctoks = _tokens(claim_text)
    frame = {
        "entity": _entities_from_claim_tokens(ctoks),
        "action": _detect_action(ctoks) or "increase",
        "quantity": _percent_numbers(claim_text)[:1],
        "year": _years(claim_text)[:1],
        "scope": "budget" if any(...) else "unknown"
    }
    return frame
```

2. **Slide windows, extract and compare frames** (lines 200-235)
```python
claim_frame = extract_claim_frame(claim_text)
sents = _split_sentences(content)

for i in range(len(sents) - win + 1):
    win_text = " ".join(sents[i:i+win])
    win_frame = extract_window_frame(win_text)

    # Compare frames
    action_compatible = _action_compatible(
        claim_frame["action"],
        win_frame["action"],
        win_frame.get("neg", False)
    )

    entity_compatible = _entities_overlap(...)
    quantity_compatible = _quantity_compatible(...)
    year_compatible = _year_compatible(...)

    # Check paraphrases
    paraphrase_score = paraphrase_match_score(claim_text, win_text)

    # Compute match score
    score = 0.0
    if action_compatible:
        score += 3.0
    if entity_compatible:
        score += 2.5
    if quantity_compatible:
        score += 2.0
    if year_compatible:
        score += 1.5
    if paraphrase_score > 0.3:
        score += 1.0 * paraphrase_score

    if score > 3.0:  # Threshold
        frame_matches.append({
            "window": win_text,
            "score": score / 10.0,  # Normalize to 0-1
            "action": win_frame["action"],
            "compatible": {...}
        })
```

3. **Attach to item** (lines 240+)
```python
return {
    "frame_matches": frame_matches[:10],  # Top 10 matches
    "best_frame_score": max(m["score"] for m in frame_matches) if frame_matches else 0.0
}
```

**Evidence Item After P24:**
```python
{
    ...(all previous fields),
    "frame_matches": [  # Top 10 frame matches
        {
            "window": str,
            "score": float,  # 0-1 scale
            "action": str,
            "compatible": {...}
        },
        ...
    ],
    "best_frame_score": float  # 0-1 scale
}
```

##### P25: Aggregate Verdict

**Lines 107-116:**
```python
try:
    verdict = aggregate_verdict(
        claim_text,
        evidence.get("arm_A", []),
        evidence.get("arm_B", []),
        delta=0.15
    )
except:
    verdict = {"label": "insufficient", "confidence": 0.0}
```

**File:** `intelligence/content/p25_aggregate.py`
**Function:** `aggregate_verdict()` (lines 72-103)

1. **Calculate arm strengths** (lines 83-84)
```python
sa = _arm_strength(arm_a_items)  # Support arm strength
sb = _arm_strength(arm_b_items)  # Challenge arm strength
```

**Function:** `_arm_strength()` (lines 45-59)
```python
def _arm_strength(items: List[Dict[str,Any]], top_k: int = 4) -> float:
    vals = sorted((_item_strength(it) for it in items), reverse=True)
    vals = vals[:top_k]  # Top 4 items

    # Diminishing returns
    weights = [1.00, 0.70, 0.50, 0.35]
    total = 0.0
    for i, v in enumerate(vals):
        w = weights[i] if i < len(weights) else weights[-1] * (0.8 ** (i - len(weights) + 1))
        total += v * w

    # Normalize by max possible
    max_possible = sum(weights[:len(vals)]) if vals else 1.0
    return max(0.0, min(1.0, total / max_possible))
```

**Function:** `_item_strength()` (lines 5-43)
```python
def _item_strength(it: Dict[str, Any]) -> float:
    # Frame match score
    fms = it.get("frame_matches") or []
    best_frame = 0.0
    for m in fms:
        sc = float(m.get("score", 0.0))
        if sc > best_frame:
            best_frame = sc

    # Item grade (EXPECTS 0-1 SCALE!)
    igr = float(it.get("item_grade", 0.0))

    # Coverage factor
    cov = (it.get("coverage") or "unknown").lower()
    if cov == "full":
        cov_w = 1.0
    elif cov == "partial":
        cov_w = 0.75
    elif cov == "snippet_only":
        cov_w = 0.55
    else:
        cov_w = 0.6

    # Combine (⚠️ CRITICAL: Assumes igr is 0-1 scale)
    base = 0.55 * best_frame + 0.45 * igr
    strength = max(0.0, min(1.0, base * cov_w))
    return strength
```

**⚠️ CRITICAL BUG:**
- Line 25: `igr = float(it.get("item_grade", 0.0))`
- Comment on line 9 says "item_grade (0..1)"
- But P20 produces item_grade on **0-10 scale**
- P23 overwrites it with **0-1 scale**
- If P23 doesn't run (error), item_grade is still 0-10
- Result: P25 treats 0-10 value as 0-1, inflating strength by 10x

2. **Determine label** (lines 86-95)
```python
if sa < 0.12 and sb < 0.12:
    label = "insufficient"
else:
    if (sa - sb) >= delta:  # delta = 0.15
        label = "supports"
    elif (sb - sa) >= delta:
        label = "challenges"
    else:
        label = "mixed"
```

3. **Calculate confidence** (line 97)
```python
conf = _confidence_from_arms(sa, sb, len(arm_a_items), len(arm_b_items))
```

**Function:** `_confidence_from_arms()` (lines 61-70)
```python
def _confidence_from_arms(sa: float, sb: float, n_items_a: int, n_items_b: int) -> float:
    total = max(0.0, min(1.0, 0.6 * max(sa, sb) + 0.4 * (sa + sb) / 2.0))
    count_factor = min(1.0, (n_items_a + n_items_b) / 6.0)
    balance = abs(sa - sb)

    # Weights: 40% total, 40% balance, 20% count
    conf = 0.4 * total + 0.4 * balance + 0.2 * count_factor
    return max(0.0, min(1.0, conf))
```

4. **Return verdict** (lines 98-102)
```python
return {
    "label": label,  # "supports", "challenges", "mixed", "insufficient"
    "confidence": float(conf),  # 0-1 scale
    "arm_strength": {
        "support": float(sa),
        "challenge": float(sb),
        "balance": float(sa - sb)
    }
}
```

**Researcher Result After P25:**
```python
{
    "verdict": {
        "label": str,  # "supports", "challenges", "mixed", "insufficient"
        "confidence": float,  # 0-1 scale
        "arm_strength": {
            "support": float,  # 0-1 scale
            "challenge": float,  # 0-1 scale
            "balance": float  # -1 to +1 scale
        }
    },
    "evidence": {
        "arm_A": [items with all enrichments],
        "arm_B": [items with all enrichments]
    }
}
```

**Return to Stage 2:** Both R1 and R2 complete enrichment, return to orchestrator

---

### Stage 4: Consensus Building (P27)

**File:** `intelligence/pipeline/run.py` (lines 151-157)
```python
if len(researchers) >= 2:
    r1_verdict = researchers[0].get("verdict", {})
    r2_verdict = researchers[1].get("verdict", {})
    consensus = compute_consensus(r1_verdict, r2_verdict)
else:
    consensus = dual_result.get("verdict", {})
```

**File:** `intelligence/consensus/dual_lane.py`
**Function:** `compute_consensus()` (lines 4-118)

**Input:**
```python
r1_verdict: {
    "label": str,
    "confidence": float,
    "arm_strength": {"support": float, "challenge": float, "balance": float}
}
r2_verdict: {same structure}
```

**Decision Rules:**

#### Rule 1: Agreement (lines 52-73)
```python
if r1_label == r2_label:
    base_conf = max(r1_conf, r2_conf)
    bonus = 0.10  # Agreement bonus
    final_conf = min(base_conf + bonus, 0.95)

    support_mean = (r1_arm["support"] + r2_arm["support"]) / 2
    challenge_mean = (r1_arm["challenge"] + r2_arm["challenge"]) / 2

    return {
        "label": r1_label,  # Same label
        "confidence": final_conf,
        "rationale": {
            "rule": "agree_same_label",
            "support_mean": support_mean,
            "challenge_mean": challenge_mean,
            "delta": abs(support_mean - challenge_mean),
            "base_conf": base_conf,
            "bonus_or_penalty": bonus
        },
        "agreement": {...}
    }
```

#### Rule 2: Disagreement with Clear Gap (lines 75-100)
```python
support_mean = (r1_arm["support"] + r2_arm["support"]) / 2
challenge_mean = (r1_arm["challenge"] + r2_arm["challenge"]) / 2
delta = abs(support_mean - challenge_mean)

if delta >= 0.20:  # Clear gap
    label = "supports" if support_mean > challenge_mean else "challenges"
    penalty = -0.05  # Disagreement penalty
    final_conf = max(base_conf + penalty, 0.0)

    return {
        "label": label,  # Pick stronger side
        "confidence": final_conf,
        "rationale": {
            "rule": "disagree_gap_select",
            ...
        }
    }
```

#### Rule 3: Disagreement Too Close (lines 102-118)
```python
# delta < 0.20 (too close to call)
penalty = -0.10  # Higher penalty for unclear
final_conf = max(base_conf + penalty, 0.0)

return {
    "label": "mixed",  # Default to mixed
    "confidence": final_conf,
    "rationale": {
        "rule": "disagree_mixed",
        ...
    }
}
```

**Output:**
```python
consensus = {
    "label": str,
    "confidence": float,
    "rationale": {
        "rule": str,
        "support_mean": float,
        "challenge_mean": float,
        "delta": float,
        "base_conf": float,
        "bonus_or_penalty": float
    },
    "agreement": {
        "r1_label": str,
        "r2_label": str,
        "r1_conf": float,
        "r2_conf": float,
        "delta_balance": float
    }
}
```

---

### Stage 5: Telemetry & Manifest (P29)

**File:** `intelligence/pipeline/run.py` (lines 159-165)
```python
if len(researchers) >= 2:
    r1_config = researchers[0].get("lane_config", {})
    r2_config = researchers[1].get("lane_config", {})
    manifest = generate_manifest(text, r1_config, r2_config)
else:
    manifest = {"replay_id": "error", "lanes": {}}
```

**File:** `intelligence/telemetry/collect.py`
**Function:** `generate_manifest()`

Records:
- Query configurations for R1 and R2
- Search providers used
- Seeds for reproducibility
- Timestamps

**Output:**
```python
manifest = {
    "replay_id": str,  # Unique ID for replay
    "lanes": {
        "R1": {...},
        "R2": {...}
    }
}
```

---

### Stage 6: Response Formatting

**File:** `intelligence/pipeline/run.py` (lines 167-182)
```python
claim_obj = {
    "id": "c-0",
    "text": text.strip(),
    "tier": "primary",
    "verdict": dual_result.get("verdict", {}),  # R1 verdict (backward compat)
    "evidence": dual_result.get("evidence", {}),  # R1 evidence (backward compat)
    "researchers": researchers,  # [R1_obj, R2_obj]
    "consensus": consensus  # Combined verdict
}

return {
    "claims": [claim_obj],
    "run_manifest": manifest,
    "diversified": True
}
```

**Final Output Structure:**
```python
{
    "claims": [
        {
            "id": "c-0",
            "text": str,
            "tier": "primary",
            "verdict": {...},  # R1 (legacy)
            "evidence": {...},  # R1 (legacy)
            "researchers": [
                {
                    "id": "R1",
                    "verdict": {...},
                    "evidence": {...},
                    "lane_config": {...},
                    "telemetry": {...}
                },
                {
                    "id": "R2",
                    "verdict": {...},
                    "evidence": {...},
                    "lane_config": {...},
                    "telemetry": {...}
                }
            ],
            "consensus": {
                "label": str,
                "confidence": float,
                "rationale": {...},
                "agreement": {...}
            }
        }
    ],
    "run_manifest": {...},
    "diversified": True
}
```

---

## Part 4: Grade/Score Flow (CRITICAL)

### Creation Points

#### Point 1: P20 Creates item_grade (0-10 scale)

**File:** `intelligence/content/grade.py`
**Line:** 231
```python
grade = round(min(score, 8.0) * (10.0/8.0), 2)
```

**Scale:** 0-10 (max theoretical: 10.0)

**Assignment:** Line 263
```python
item["item_grade"] = finding["grade"]  # Assigns 0-10 value
```

**Formula Breakdown:**
```python
# Possible score components:
W_ENTITY = 2.0  # If entity matched
W_NUMBER = 2.0  # If number matched
W_YEAR = 1.0    # If year matched
W_SIM_HI = 2.0  # If similarity >= 0.35
W_SIM_LO = 1.0  # If similarity >= 0.25
W_STANCE = 1.0  # If stance aligns with arm
P_MODAL = 1.0   # Penalty for hedging

# Max score = 2.0 + 2.0 + 1.0 + 2.0 + 1.0 = 8.0
# Normalization: min(score, 8.0) * (10.0/8.0)
# Result range: 0.0 - 10.0
```

**Example:**
- Entity match: +2.0
- Number match: +2.0
- High similarity: +2.0
- Stance support: +1.0
- Total: 7.0
- Grade: 7.0 * 1.25 = **8.75** (on 0-10 scale)

#### Point 2: P23 Overwrites item_grade (0-1 scale)

**File:** `intelligence/content/semantic_read.py`
**Lines:** 201-202
```python
item_grade = max(0.0, min(1.0, 0.6 * best + 0.4 * cov_w))
item["item_grade"] = float(item_grade)  # Assigns 0-1 value
```

**Scale:** 0-1 (correctly normalized)

**Formula:**
```python
# best = best finding score (varies)
# cov_w = coverage weight (1.0 for full, 0.8 for partial, 0.6 for snippet)
item_grade = 0.6 * best + 0.4 * cov_w
# Clamped to [0, 1]
```

**Example:**
- Best score: 0.8
- Coverage: full (1.0)
- Grade: 0.6 * 0.8 + 0.4 * 1.0 = 0.48 + 0.40 = **0.88** (on 0-1 scale)

**⚠️ CRITICAL ISSUE:** If P23 fails or is skipped, item_grade remains at P20's 0-10 scale value!

### Usage Points

#### Point 3: P25 Reads item_grade (EXPECTS 0-1 scale)

**File:** `intelligence/content/p25_aggregate.py`
**Line:** 25
```python
igr = float(it.get("item_grade", 0.0))
```

**Comment on Line 9:** "item_grade (0..1)"
**Expected Scale:** 0-1

**Formula:** Line 41
```python
base = 0.55 * best_frame + 0.45 * igr
strength = max(0.0, min(1.0, base * cov_w))
```

**Bug Impact:**

**Scenario A: P23 Runs Successfully**
- P20 assigns: item_grade = 8.75 (0-10 scale)
- P23 overwrites: item_grade = 0.88 (0-1 scale)
- P25 reads: igr = 0.88 (CORRECT)
- Calculation: base = 0.55 * 0.5 + 0.45 * 0.88 = 0.275 + 0.396 = 0.671
- Result: CORRECT

**Scenario B: P23 Fails (exception caught)**
- P20 assigns: item_grade = 8.75 (0-10 scale)
- P23 skipped due to error
- P25 reads: igr = 8.75 (WRONG SCALE - interprets as 875%!)
- Calculation: base = 0.55 * 0.5 + 0.45 * 8.75 = 0.275 + 3.9375 = 4.2125
- Clamped: strength = min(1.0, 4.2125 * 1.0) = 1.0
- Result: **MAXIMUM STRENGTH despite weak evidence**

**Scenario C: No Content (P21/P23 skip)**
- P20 assigns: item_grade = 1.25 (0-10 scale, low score)
- P21/P23 skipped (no content)
- P25 reads: igr = 1.25 (interprets as 125%)
- Calculation: base = 0.55 * 0.0 + 0.45 * 1.25 = 0.5625
- Clamped: strength = min(1.0, 0.5625 * 0.55) = 0.309
- Result: Weak evidence gets **30.9% strength** (should be ~5%)

### Scale Inconsistency Summary

| Module | Field | Scale | Line |
|--------|-------|-------|------|
| P20 | item_grade | 0-10 | grade.py:263 |
| P21 | grade_full | 0-10 | fullread.py:257 |
| P23 | item_grade | 0-1 | semantic_read.py:202 |
| P24 | best_frame_score | 0-1 | semantic_frames.py:240+ |
| P25 | (reads item_grade) | **Expects 0-1** | p25_aggregate.py:25 |

**Conflict:**
- P20 produces 0-10
- P23 produces 0-1 (overwrites P20)
- P25 expects 0-1
- If P23 doesn't run, P25 gets 0-10 value → **10x inflation**

---

## Part 5: Evidence Item Evolution

### After P19 (Evidence Gathering)

```python
{
    "url": "https://example.com/article",
    "title": "Article Title",
    "snippet": "Short excerpt...",
    "arm": "A",  # or "B"
    "provider": "brave",
    "score": 0.85  # Search relevance
}
```

### After P22 (Content Enrichment)

```python
{
    "url": "https://example.com/article",
    "title": "Article Title",
    "snippet": "Short excerpt...",
    "arm": "A",
    "provider": "brave",
    "score": 0.85,

    # NEW FIELDS FROM P22:
    "content": "Full article text (2,000-20,000 chars)...",
    "content_hash": "abc123def456",
    "coverage": "full",  # or "partial", "snippet_only"
    "content_excerpt": "Truncated if >12KB..."
}
```

### After P20 (Stance Detection)

```python
{
    ...(all P22 fields),

    # NEW FIELDS FROM P20:
    "item_grade": 8.75,  # ⚠️ 0-10 SCALE
    "stance": "support",  # or "challenge", "mixed", "unrelated", "contextual_support"
    "finding": {
        "grade": 8.75,  # ⚠️ 0-10 SCALE
        "stance": "support",
        "matched_spans": ["relevant sentence from article"],
        "rationale": ["entity matched", "number matched", "similarity high (0.62)", "stance supports claim"],
        "similarity": 0.620,
        "signals": {
            "entity": true,
            "number": true,
            "year": false
        }
    }
}
```

### After P21 (Full-Read)

```python
{
    ...(all P20 fields),

    # NEW FIELDS FROM P21:
    "grade_full": 9.23,  # 0-10 SCALE (consistent with P20)
    "stance_full": "support",
    "signals_full": {
        "jaccard3": 0.485,
        "entity_overlap": 0.750,
        "percent_any": true,
        "percent_close": true,
        "year_hit": true,
        "negation": false
    },
    "credibility": 0.550  # 0-1 SCALE (based on URL domain)
}
```

### After P23 (Semantic Read)

```python
{
    ...(all P21 fields),

    # NEW FIELDS FROM P23:
    "findings": [
        {
            "window": "Three sentence window from article...",
            "score": 7.8,
            "signals": {
                "trigram_overlap": 0.45,
                "entity_overlap": 0.80,
                "paraphrase_score": 0.62,
                "percent_match": true,
                "year_match": true
            },
            "stance": "support"
        },
        ...  // More windows
    ],

    # OVERWRITES item_grade:
    "item_grade": 0.88,  # ✅ 0-1 SCALE (CORRECTED)
    "grade_label": "high"  # or "medium", "low"
}
```

### After P24 (Frame Analysis)

```python
{
    ...(all P23 fields),

    # NEW FIELDS FROM P24:
    "frame_matches": [
        {
            "window": "Frame-matched sentence...",
            "score": 0.85,  # 0-1 SCALE
            "action": "increase",
            "compatible": {
                "action": true,
                "entity": true,
                "quantity": true,
                "year": true
            }
        },
        ...  // Top 10 matches
    ],
    "best_frame_score": 0.85  # 0-1 SCALE
}
```

### After P25 (Aggregation)

**Individual Item:** (unchanged, all enrichments preserved)

**Aggregated Verdict:**
```python
{
    "label": "supports",  # or "challenges", "mixed", "insufficient"
    "confidence": 0.538,  # 0-1 SCALE
    "arm_strength": {
        "support": 0.599,  # 0-1 SCALE
        "challenge": 0.292,  # 0-1 SCALE
        "balance": 0.307  # -1 to +1 SCALE
    }
}
```

**Complete Researcher Object:**
```python
{
    "id": "R1",
    "verdict": {
        "label": "supports",
        "confidence": 0.538,
        "arm_strength": {
            "support": 0.599,
            "challenge": 0.292,
            "balance": 0.307
        }
    },
    "evidence": {
        "arm_A": [item1_with_all_enrichments, item2, item3],
        "arm_B": [item4, item5, item6]
    },
    "lane_config": {...},
    "telemetry": {...}
}
```

---

## Part 6: Dual Researcher System

### How R1 and R2 Work

**File:** `intelligence/orchestration/dual_lane.py`
**Function:** `run_dual_researchers()` (lines 4-70)

### Execution Model: SEQUENTIAL

**Lines 37-45:**
```python
# Run R1
r1_telemetry = telemetry_class("R1")
r1_result = await enrichment_pipeline(claim_text, r1_plan, "R1", r1_telemetry)
r1_telemetry_data = r1_telemetry.finalize()

# Run R2 (starts AFTER R1 completes)
r2_telemetry = telemetry_class("R2")
r2_result = await enrichment_pipeline(claim_text, r2_plan, "R2", r2_telemetry)
r2_telemetry_data = r2_telemetry.finalize()
```

**Execution Order:**
1. R1 starts
2. R1 completes (gathers evidence, runs P20-P25)
3. R2 starts
4. R2 completes (gathers evidence, runs P20-P25)
5. Results combined

**NOT parallel** - R2 waits for R1 to finish

### Differences Between R1 and R2

#### Diversification (intelligence/planning/diversify.py)

**R1 Configuration:**
- Primary search provider (Brave)
- Seed: 0
- Query ordering: Original

**R2 Configuration:**
- Alternate provider if available (Google CSE, Bing)
- Seed: 42
- Query ordering: Shuffled/diversified
- May skip some queries or add variations

**Purpose:** Reduce bias, increase coverage, find different evidence

#### Same Modules (P20-P25)

**Both use identical processing:**
- P20: `attach_finding_to_item()`
- P21: `evaluate_full_evidence()`
- P23: `analyze_item()`
- P24: `analyze_frames()`
- P25: `aggregate_verdict()`

**No code differences** - only input data differs (different evidence sources)

### How Results Are Combined

**File:** `intelligence/consensus/dual_lane.py`
**Function:** `compute_consensus()` (lines 4-118)

**Input:**
```python
r1_verdict = {
    "label": "supports",
    "confidence": 0.503,
    "arm_strength": {"support": 0.611, "challenge": 0.428, "balance": 0.183}
}

r2_verdict = {
    "label": "mixed",
    "confidence": 0.394,
    "arm_strength": {"support": 0.356, "challenge": 0.428, "balance": -0.072}
}
```

**Consensus Logic:**

1. **Check Agreement** (line 53)
```python
if r1_label == r2_label:
    # Agreement: Use same label, boost confidence by +0.10
    final_conf = min(max(r1_conf, r2_conf) + 0.10, 0.95)
```

2. **Calculate Mean Arm Strengths** (lines 76-78)
```python
support_mean = (r1_arm["support"] + r2_arm["support"]) / 2
challenge_mean = (r1_arm["challenge"] + r2_arm["challenge"]) / 2
delta = abs(support_mean - challenge_mean)
```

3. **Handle Disagreement**

**Clear Gap (delta >= 0.20):** (lines 82-100)
```python
label = "supports" if support_mean > challenge_mean else "challenges"
penalty = -0.05  # Small penalty for disagreement
final_conf = max(base_conf + penalty, 0.0)
rule = "disagree_gap_select"
```

**Too Close (delta < 0.20):** (lines 102-118)
```python
label = "mixed"  # Default to mixed when unclear
penalty = -0.10  # Larger penalty
final_conf = max(base_conf + penalty, 0.0)
rule = "disagree_mixed"
```

**Output:**
```python
{
    "label": "mixed",  # Final consensus label
    "confidence": 0.403,  # Adjusted confidence
    "rationale": {
        "rule": "disagree_mixed",
        "support_mean": 0.484,
        "challenge_mean": 0.428,
        "delta": 0.056,  # Too small for clear verdict
        "base_conf": 0.503,
        "bonus_or_penalty": -0.10
    },
    "agreement": {
        "r1_label": "supports",
        "r2_label": "mixed",
        "r1_conf": 0.503,
        "r2_conf": 0.394,
        "delta_balance": 0.255  # R1 balance - R2 balance
    }
}
```

### Benefits of Dual System

1. **Diversity:** Different sources reduce single-provider bias
2. **Robustness:** If one researcher finds weak evidence, other may find strong
3. **Confidence Calibration:** Agreement boosts, disagreement lowers confidence
4. **Transparency:** Users see both perspectives

---

## Part 7: Final Output Structure

### Complete Response

```python
{
    "claims": [
        {
            "id": "c-0",
            "text": "Water boils at 100 degrees Celsius at sea level",
            "tier": "primary",

            # Legacy (R1 for backward compatibility):
            "verdict": {
                "label": "supports",
                "confidence": 0.503,
                "arm_strength": {
                    "support": 0.611,
                    "challenge": 0.428,
                    "balance": 0.183
                }
            },
            "evidence": {
                "arm_A": [...R1 evidence items...],
                "arm_B": [...R1 evidence items...]
            },

            # Full dual researcher data:
            "researchers": [
                {
                    "id": "R1",
                    "verdict": {...},
                    "evidence": {
                        "arm_A": [3 items with all P20-P25 enrichments],
                        "arm_B": [3 items with all P20-P25 enrichments]
                    },
                    "lane_config": {
                        "lane_id": "R1",
                        "provider": "brave",
                        "seed": 0
                    },
                    "telemetry": {
                        "providers": {"brave": 6},
                        "duration_ms": 8234
                    }
                },
                {
                    "id": "R2",
                    "verdict": {...},
                    "evidence": {...},
                    "lane_config": {...},
                    "telemetry": {...}
                }
            ],

            # Consensus verdict:
            "consensus": {
                "label": "mixed",
                "confidence": 0.403,
                "rationale": {
                    "rule": "disagree_mixed",
                    "support_mean": 0.484,
                    "challenge_mean": 0.428,
                    "delta": 0.056,
                    "base_conf": 0.503,
                    "bonus_or_penalty": -0.10
                },
                "agreement": {
                    "r1_label": "supports",
                    "r2_label": "mixed",
                    "r1_conf": 0.503,
                    "r2_conf": 0.394,
                    "delta_balance": 0.255
                }
            }
        }
    ],

    "run_manifest": {
        "replay_id": "abc123-def456-ghi789",
        "lanes": {
            "R1": {...config...},
            "R2": {...config...}
        }
    },

    "diversified": true
}
```

---

## Appendix A: Module Reference Quick Lookup

| Module | File | Function | Lines | Purpose |
|--------|------|----------|-------|---------|
| **Entry** | intelligence/pipeline/run.py | run_preview() | 121-182 | Main entry point |
| **P19** | intelligence/gather/counter_frames.py | generate_counter_frame_queries() | 5-150 | Generate challenge queries |
| **P19** | intelligence/gather/pipeline.py | build_evidence_for_claim() | 105-150+ | Gather evidence from web |
| **P20** | intelligence/content/grade.py | attach_finding_to_item() | 247-267 | Stance detection |
| **P21** | intelligence/content/fullread.py | evaluate_full_evidence() | 177-269 | Full-read analysis |
| **P22** | intelligence/content/fetch_enrichment.py | enrich_items_with_content() | - | Fetch article content |
| **P23** | intelligence/content/semantic_read.py | analyze_item() | 103-203+ | Semantic analysis |
| **P24** | intelligence/content/semantic_frames.py | analyze_frames() | 160-250+ | Frame extraction |
| **P25** | intelligence/content/p25_aggregate.py | aggregate_verdict() | 72-103 | Verdict aggregation |
| **P26** | intelligence/orchestration/dual_lane.py | run_dual_researchers() | 4-70 | Dual orchestration |
| **P27** | intelligence/consensus/dual_lane.py | compute_consensus() | 4-118 | Consensus building |
| **P29** | intelligence/telemetry/collect.py | generate_manifest() | - | Reproducibility data |

---

## Appendix B: Data Scale Summary

| Field | Module | Scale | Correct? |
|-------|--------|-------|----------|
| item_grade | P20 (creates) | 0-10 | ❌ Wrong |
| item_grade | P23 (overwrites) | 0-1 | ✅ Correct |
| item_grade | P25 (reads) | Expects 0-1 | ⚠️ Depends on P23 |
| grade_full | P21 | 0-10 | ⚠️ Not used by P25 |
| best_frame_score | P24 | 0-1 | ✅ Correct |
| arm_strength | P25 | 0-1 | ✅ Correct |
| confidence | P25 | 0-1 | ✅ Correct |
| credibility | P21 | 0-1 | ✅ Correct |
| similarity | P20 | 0-1 | ✅ Correct |
| paraphrase_score | Embeddings | 0-1 | ✅ Correct |

**Critical Issue:** P20's item_grade on 0-10 scale causes 10x inflation in P25 if P23 doesn't run.

---

**Document Complete**
**Last Updated:** 2025-10-14
**Version:** 1.0
