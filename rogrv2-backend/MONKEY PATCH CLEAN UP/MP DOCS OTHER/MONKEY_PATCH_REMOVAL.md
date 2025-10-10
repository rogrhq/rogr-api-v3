# MONKEY PATCH REMOVAL PLAN - CLEAN INTEGRATION

**Purpose:** Replace all 11 monkey-patched files with explicit imports and direct function calls.
**Goal:** Zero `setattr()` usage, no import-order dependency, clean testable code.
**Effort:** 2-3 days
**Status:** Ready to implement

---

## CRITICAL RULES

**NEVER ACCEPTABLE IN PRODUCTION:**
- ❌ `setattr(module, "function", wrapper)` - Runtime function replacement
- ❌ `sys.modules` manipulation - Modifying import system
- ❌ sitecustomize.py - Auto-loading at interpreter startup
- ❌ Wrapper chains - Function wrapping another wrapper
- ❌ Import-time side effects - Code executing on import

**ONLY ACCEPTABLE:**
- ✅ `from module import function` - Explicit imports
- ✅ `result = function(args)` - Direct function calls
- ✅ Dependency injection - Pass functions/objects as parameters
- ✅ Type hints - Clear contracts
- ✅ Testable functions - No hidden dependencies

---

## MONKEY PATCH INVENTORY (11 Files)

### Files Using setattr()

1. **sitecustomize.py** (22 lines)
   - Bootstrap loader
   - Auto-imports p20 + p22 wrappers
   - **Action:** DELETE

2. **intelligence/gather/p19_wrapper.py**
   - Wraps: gather logic
   - **Action:** Extract → `intelligence/gather/enrich.py`

3. **intelligence/content/p20_wrapper.py** (228 lines)
   - Wraps: `pipeline.build_evidence_for_claim`
   - Adds: Finding cards (grade, stance, spans)
   - **Action:** Extract → `intelligence/content/findings.py`

4. **intelligence/content/p21_wrapper.py** (145 lines)
   - Wraps: `pipeline.build_evidence_for_claim`
   - Adds: Full-read evaluation per item
   - **Action:** Extract → `intelligence/content/fullread.py` (already exists)

5. **intelligence/content/p22_ingest.py**
   - Adds: Full-text ingestion
   - **Action:** Extract → `intelligence/content/ingest.py`

6. **intelligence/content/p23_semantic.py**
   - Adds: Semantic alignment (quotes, offsets, stance)
   - **Action:** Extract → `intelligence/content/semantic_read.py`

7. **intelligence/content/p24_semantic_frames.py**
   - Adds: Frame extraction (entity/action/quantity)
   - **Action:** Extract → `intelligence/content/frames.py`

8. **intelligence/content/p25_aggregate.py**
   - Adds: Per-claim aggregation
   - **Action:** Extract → `intelligence/content/aggregation.py`

9. **intelligence/content/p26_dual_researchers.py**
   - Adds: Dual-lane orchestration (R1/R2)
   - **Action:** Extract → `intelligence/consensus/dual.py`

10. **intelligence/content/p27_consensus.py**
    - Adds: Consensus reducer
    - **Action:** Extract → `intelligence/consensus/reducer.py`

11. **intelligence/content/p28_diversify.py + p29_diversify_controls.py**
    - Adds: Lane diversification + telemetry
    - **Action:** Merge → `intelligence/consensus/diversification.py`

---

## DEPENDENCY ORDER (Critical for Safe Removal)

**Removal must proceed in this order to avoid breaking dependencies:**

```
Phase 1: Foundation (Days 1-2)
  1. Extract p22 (ingest) → No dependencies
  2. Extract p23 (semantic) → Depends on p22
  3. Extract p24 (frames) → Depends on p23
  4. Extract p25 (aggregate) → Depends on p23, p24
  5. Extract p19 (gather enrich) → No dependencies

Phase 2: Findings & Grading (Day 2)
  6. Extract p20 (findings) → Depends on p23
  7. Extract p21 (fullread) → Depends on p20

Phase 3: Consensus (Day 3)
  8. Extract p26 (dual-lane) → Depends on all above
  9. Extract p27 (consensus) → Depends on p26
  10. Extract p28+p29 (diversification) → Depends on p26

Phase 4: Cleanup (Day 3)
  11. Delete sitecustomize.py → After all wrappers removed
  12. Delete all p*_wrapper.py files → After logic extracted
```

---

## PHASE 1: FOUNDATION EXTRACTION (Days 1-2)

### Step 1: Extract P22 (Content Ingestion)

**Current State:** p22_ingest.py uses setattr() to inject ingestion

**Goal:** Create standalone `intelligence/content/ingest.py`

**1.1 Read Current Wrapper**
```bash
$ cat intelligence/content/p22_ingest.py | grep -A 20 "def.*ingest"
```

**1.2 Create New Module**

File: `intelligence/content/ingest.py`
```python
"""
Content ingestion: Fetch full text for evidence items.
Replaces p22_ingest.py monkey patch.
"""
from __future__ import annotations
from typing import List, Dict, Any
import logging

from intelligence.content.fetch_sync import fetch_text

logger = logging.getLogger(__name__)

async def ingest_full_text(
    items: List[Dict[str, Any]],
    *,
    max_items: int = 10,
    timeout: float = 5.0
) -> List[Dict[str, Any]]:
    """
    Fetch full text for top N items per arm.
    Adds: content_chars, content_excerpt, content_status

    Args:
        items: Evidence items with url field
        max_items: Max items to fetch per call
        timeout: HTTP timeout per request

    Returns:
        Items enriched with content fields
    """
    enriched = []
    fetched = 0

    for item in items[:max_items]:
        url = item.get("url") or ""
        if not url:
            enriched.append(item)
            continue

        try:
            result = fetch_text(url, timeout=timeout)
            text = result.get("text") or ""
            status = result.get("status") or 0

            item_copy = {**item}
            item_copy["content_chars"] = len(text)
            item_copy["content_excerpt"] = text[:1200] if text else ""
            item_copy["content_status"] = status
            item_copy["content_fetched"] = bool(text)

            enriched.append(item_copy)
            fetched += 1

        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            enriched.append(item)

    logger.info(f"Ingested {fetched}/{min(len(items), max_items)} items")
    return enriched
```

**1.3 Add to Pipeline**

File: `intelligence/pipeline/run.py` (after line 78)
```python
# Add import at top
from intelligence.content.ingest import ingest_full_text

# In run_preview(), after build_evidence_for_claim:
async def run_preview(text: str, test_mode: bool = False) -> Dict[str, Any]:
    # ... existing code ...

    evidence_bundle = await build_evidence_for_claim(
        claim_text=claim["text"],
        plan=plans,
        max_per_arm=3
    )

    # NEW: Explicit ingestion call
    if not test_mode:
        arm_A = evidence_bundle.get("arm_A") or []
        arm_B = evidence_bundle.get("arm_B") or []

        arm_A = await ingest_full_text(arm_A, max_items=3)
        arm_B = await ingest_full_text(arm_B, max_items=3)

        evidence_bundle["arm_A"] = arm_A
        evidence_bundle["arm_B"] = arm_B

    # ... rest of code ...
```

**1.4 Test**
```bash
# Unit test
$ pytest tests/test_content_ingest.py -v

# Integration test
$ python scripts/test_live_pipeline.py --claim "Test claim"

# Should return evidence with content_chars > 0 for some items
```

**1.5 Validation**
- ✅ `ingest.py` created with no setattr()
- ✅ Explicit import in `run.py`
- ✅ Direct function call after gathering
- ✅ Tests pass
- ✅ Live pipeline returns content_chars

---

### Step 2: Extract P23 (Semantic Analysis)

**Current State:** p23_semantic.py uses setattr() for semantic alignment

**Goal:** Create standalone `intelligence/content/semantic_read.py`

**2.1 Create New Module**

File: `intelligence/content/semantic_read.py`
```python
"""
Semantic reading: Apply claim-to-text alignment with anchored quotes.
Replaces p23_semantic.py monkey patch.
"""
from __future__ import annotations
from typing import List, Dict, Any
import logging

from intelligence.content.align import align_claim_to_text_windowed

logger = logging.getLogger(__name__)

def apply_semantic_analysis(
    claim_text: str,
    items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Apply semantic alignment to items with content.
    Adds: matches (list of anchored quotes), content_score, item_stance

    Args:
        claim_text: The claim being checked
        items: Evidence items (some with content_excerpt)

    Returns:
        Items enriched with semantic signals
    """
    enriched = []
    analyzed = 0

    for item in items:
        excerpt = item.get("content_excerpt") or item.get("snippet") or ""
        if not excerpt or len(excerpt) < 50:
            enriched.append(item)
            continue

        try:
            alignment = align_claim_to_text_windowed(
                claim=claim_text,
                text=excerpt
            )

            item_copy = {**item}
            item_copy["matches"] = alignment.get("matches", [])
            item_copy["content_score"] = alignment.get("content_score", 0.0)
            item_copy["item_stance"] = alignment.get("item_stance", "neutral")
            item_copy["semantic_analyzed"] = True

            enriched.append(item_copy)
            analyzed += 1

        except Exception as e:
            logger.warning(f"Semantic analysis failed for {item.get('url', 'unknown')}: {e}")
            enriched.append(item)

    logger.info(f"Analyzed {analyzed}/{len(items)} items semantically")
    return enriched
```

**2.2 Add to Pipeline**

File: `intelligence/pipeline/run.py`
```python
# Add import at top
from intelligence.content.semantic_read import apply_semantic_analysis

# After ingestion:
    if not test_mode:
        # ... ingestion code ...

        # NEW: Explicit semantic analysis
        arm_A = apply_semantic_analysis(claim["text"], arm_A)
        arm_B = apply_semantic_analysis(claim["text"], arm_B)

        evidence_bundle["arm_A"] = arm_A
        evidence_bundle["arm_B"] = arm_B
```

**2.3 Test & Validate**
```bash
$ pytest tests/test_semantic_read.py -v
$ python scripts/test_live_pipeline.py --claim "Test claim"
# Check for "matches" field with anchored quotes
```

---

### Step 3: Extract P24 (Frame Extraction)

**3.1 Create Module**

File: `intelligence/content/frames.py`
```python
"""
Frame extraction: Extract entity/action/quantity/year/scope from content.
Replaces p24_semantic_frames.py monkey patch.
"""
from __future__ import annotations
from typing import List, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)

_ENTITY_RE = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')
_NUMBER_RE = re.compile(r'\d+(?:\.\d+)?%?')
_YEAR_RE = re.compile(r'\b(19|20)\d{2}\b')

def extract_frame_from_text(text: str) -> Dict[str, Any]:
    """
    Extract simple frame: entities, numbers, years.

    Returns:
        {
            "entities": List[str],
            "quantities": List[str],
            "years": List[int],
            "scope": str (first 100 chars)
        }
    """
    entities = _ENTITY_RE.findall(text)[:5]
    quantities = _NUMBER_RE.findall(text)[:5]
    years = [int(y) for y in _YEAR_RE.findall(text)[:3]]

    return {
        "entities": entities,
        "quantities": quantities,
        "years": years,
        "scope": text[:100]
    }

def extract_frames(
    claim_text: str,
    items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Extract frames from items with semantic analysis.
    Adds: item_frame (entity/action/quantity/year/scope)

    Args:
        claim_text: The claim (for claim frame)
        items: Evidence items with content

    Returns:
        Items enriched with frames
    """
    claim_frame = extract_frame_from_text(claim_text)
    enriched = []
    extracted = 0

    for item in items:
        excerpt = item.get("content_excerpt") or item.get("snippet") or ""
        if not excerpt or len(excerpt) < 50:
            enriched.append(item)
            continue

        try:
            item_frame = extract_frame_from_text(excerpt)

            # Compute frame match
            entity_overlap = len(set(claim_frame["entities"]) & set(item_frame["entities"]))
            year_match = bool(set(claim_frame["years"]) & set(item_frame["years"]))

            match_score = 0.5 * (entity_overlap / max(len(claim_frame["entities"]), 1)) + \
                         0.5 * float(year_match)

            item_copy = {**item}
            item_copy["item_frame"] = item_frame
            item_copy["frame_match_score"] = match_score
            item_copy["frame_extracted"] = True

            enriched.append(item_copy)
            extracted += 1

        except Exception as e:
            logger.warning(f"Frame extraction failed: {e}")
            enriched.append(item)

    logger.info(f"Extracted frames for {extracted}/{len(items)} items")
    return enriched
```

**3.2 Add to Pipeline**
```python
from intelligence.content.frames import extract_frames

# After semantic analysis:
    arm_A = extract_frames(claim["text"], arm_A)
    arm_B = extract_frames(claim["text"], arm_B)
```

**3.3 Test & Validate**

---

### Step 4: Extract P25 (Aggregation)

**4.1 Create Module**

File: `intelligence/content/aggregation.py`
```python
"""
Semantic aggregation: Compute per-arm strengths from item-level signals.
Replaces p25_aggregate.py monkey patch.
"""
from __future__ import annotations
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def aggregate_semantic_signals(
    items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate item-level semantic signals into arm-level metrics.

    Returns:
        {
            "avg_content_score": float,
            "avg_frame_match": float,
            "items_with_findings": int,
            "stance_distribution": {"support": N, "refute": N, "neutral": N}
        }
    """
    if not items:
        return {
            "avg_content_score": 0.0,
            "avg_frame_match": 0.0,
            "items_with_findings": 0,
            "stance_distribution": {"support": 0, "refute": 0, "neutral": 0}
        }

    content_scores = []
    frame_matches = []
    findings_count = 0
    stance_counts = {"support": 0, "refute": 0, "neutral": 0}

    for item in items:
        # Content score
        if "content_score" in item:
            content_scores.append(item["content_score"])

        # Frame match
        if "frame_match_score" in item:
            frame_matches.append(item["frame_match_score"])

        # Findings
        if item.get("matches") or item.get("finding"):
            findings_count += 1

        # Stance
        stance = item.get("item_stance") or item.get("stance", "neutral")
        if stance in stance_counts:
            stance_counts[stance] += 1

    return {
        "avg_content_score": sum(content_scores) / len(content_scores) if content_scores else 0.0,
        "avg_frame_match": sum(frame_matches) / len(frame_matches) if frame_matches else 0.0,
        "items_with_findings": findings_count,
        "stance_distribution": stance_counts,
        "total_items": len(items)
    }

def aggregate_arm_strengths(
    arm_A: List[Dict[str, Any]],
    arm_B: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate both arms and return strengths.

    Returns:
        {
            "arm_A_strength": {...},
            "arm_B_strength": {...}
        }
    """
    return {
        "arm_A_strength": aggregate_semantic_signals(arm_A),
        "arm_B_strength": aggregate_semantic_signals(arm_B)
    }
```

**4.2 Add to Pipeline**
```python
from intelligence.content.aggregation import aggregate_arm_strengths

# After frame extraction:
    arm_strengths = aggregate_arm_strengths(arm_A, arm_B)
    evidence_bundle["arm_strengths"] = arm_strengths
```

**4.3 Test & Validate**

---

### Step 5: Extract P19 (Gather Enrichment)

**5.1 Create Module**

File: `intelligence/gather/enrich.py`
```python
"""
Gather enrichment: Post-process gathered evidence.
Replaces p19_wrapper.py monkey patch.
"""
from __future__ import annotations
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def enrich_gather_results(
    evidence: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Post-process gathered evidence (placeholder for p19 logic).

    Args:
        evidence: Raw evidence bundle from gather

    Returns:
        Enriched evidence bundle
    """
    # Extract actual p19 logic here when reading wrapper
    # For now, pass-through
    return evidence
```

**5.2 Add to Pipeline**

File: `intelligence/gather/pipeline.py` (after line 130)
```python
from intelligence.gather.enrich import enrich_gather_results

# After ranking, before returning:
async def build_evidence_for_claim(...):
    # ... existing code ...
    ranked_A = rank_candidates(...)
    ranked_B = rank_candidates(...)

    # NEW: Explicit enrichment
    bundle = {"arm_A": ranked_A, "arm_B": ranked_B}
    bundle = enrich_gather_results(bundle)

    # ... rest of code ...
```

**5.3 Test & Validate**

---

## PHASE 2: FINDINGS & GRADING EXTRACTION (Day 2)

### Step 6: Extract P20 (Findings Attachment)

**6.1 Create Module**

File: `intelligence/content/findings.py`
```python
"""
Findings attachment: Attach finding cards to evidence items.
Replaces p20_wrapper.py monkey patch.
"""
from __future__ import annotations
from typing import List, Dict, Any
import logging

from intelligence.content.grade import attach_finding_to_item

logger = logging.getLogger(__name__)

def attach_findings(
    claim_text: str,
    evidence: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Attach finding cards (grade, stance, rationale, spans) to each item.

    Args:
        claim_text: The claim being checked
        evidence: Evidence bundle with arm_A, arm_B

    Returns:
        Evidence with findings attached to items
    """
    result = {**evidence}

    for arm_key in ["arm_A", "arm_B"]:
        items = result.get(arm_key) or []
        if not isinstance(items, list):
            continue

        enriched = []
        for item in items:
            try:
                item_with_finding = attach_finding_to_item(
                    claim_text=claim_text,
                    arm_key=arm_key[-1],  # "A" or "B"
                    item=item
                )
                enriched.append(item_with_finding)
            except Exception as e:
                logger.warning(f"Failed to attach finding: {e}")
                enriched.append(item)

        result[arm_key] = enriched

    return result
```

**6.2 Add to Pipeline**
```python
from intelligence.content.findings import attach_findings

# After frame extraction:
    evidence_bundle = attach_findings(claim["text"], evidence_bundle)
```

**6.3 Test & Validate**

---

### Step 7: Extract P21 (Full-Read Evaluation)

**Note:** `intelligence/content/fullread.py` already exists with `evaluate_full_evidence()` function.

**7.1 Verify Function Exists**
```bash
$ grep -n "def evaluate_full_evidence" intelligence/content/fullread.py
```

**7.2 Add to Pipeline**
```python
from intelligence.content.fullread import evaluate_full_evidence

# After findings attachment:
    for arm_key in ["arm_A", "arm_B"]:
        items = evidence_bundle.get(arm_key) or []
        evaluated = []
        for item in items:
            try:
                item_eval = evaluate_full_evidence(claim["text"], item)
                evaluated.append(item_eval)
            except Exception as e:
                logger.warning(f"Full-read eval failed: {e}")
                evaluated.append(item)
        evidence_bundle[arm_key] = evaluated
```

**7.3 Test & Validate**

---

## PHASE 3: CONSENSUS EXTRACTION (Day 3)

### Step 8: Extract P26 (Dual-Lane Orchestration)

**8.1 Create Module**

File: `intelligence/consensus/dual.py`
```python
"""
Dual-researcher orchestration: Run R1/R2 lanes independently.
Replaces p26_dual_researchers.py monkey patch.
"""
from __future__ import annotations
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def run_dual_researchers(
    text: str,
    *,
    test_mode: bool = False,
    diversification_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Run two independent researcher lanes with diversification.

    Args:
        text: Input claim text
        test_mode: Whether to use test mode
        diversification_config: Lane-specific provider orders, timeouts

    Returns:
        {
            "R1": {...},  # Lane 1 results
            "R2": {...},  # Lane 2 results
            "diversification": {...}  # Config used
        }
    """
    from intelligence.pipeline.run import run_preview

    # TODO: Extract actual p26 logic
    # For now, run twice with same config

    r1_result = await run_preview(text, test_mode=test_mode)
    r2_result = await run_preview(text, test_mode=test_mode)

    return {
        "R1": r1_result,
        "R2": r2_result,
        "diversification": diversification_config or {}
    }
```

**8.2 Add to Pipeline (Optional)**
```python
from intelligence.consensus.dual import run_dual_researchers

# Optional dual-lane mode:
async def run_preview(text: str, test_mode: bool = False, dual_lane: bool = False) -> Dict[str, Any]:
    if dual_lane:
        dual_results = await run_dual_researchers(text, test_mode=test_mode)
        # Process dual results...
        return dual_results

    # Standard single-lane path
    # ...
```

**8.3 Test & Validate**

---

### Step 9: Extract P27 (Consensus Reducer)

**9.1 Create Module**

File: `intelligence/consensus/reducer.py`
```python
"""
Consensus reducer: Combine R1/R2 verdicts into consensus.
Replaces p27_consensus.py monkey patch.
"""
from __future__ import annotations
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def reduce_consensus(
    r1_result: Dict[str, Any],
    r2_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Combine two lane results into consensus verdict.

    Args:
        r1_result: Lane 1 verdict
        r2_result: Lane 2 verdict

    Returns:
        Consensus verdict with agreement metrics
    """
    # Extract verdicts
    v1 = r1_result.get("verdict", {})
    v2 = r2_result.get("verdict", {})

    label1 = v1.get("label", "Mixed")
    label2 = v2.get("label", "Mixed")
    score1 = v1.get("claim_grade_numeric", 50)
    score2 = v2.get("claim_grade_numeric", 50)

    # Simple consensus rules
    if label1 == label2:
        # Full agreement
        consensus_label = label1
        confidence = 0.9
    elif abs(score1 - score2) <= 10:
        # Close agreement
        consensus_label = label1  # Prefer R1
        confidence = 0.7
    else:
        # Disagreement
        consensus_label = "Mixed"
        confidence = 0.5

    consensus_score = (score1 + score2) / 2

    return {
        "consensus_label": consensus_label,
        "consensus_score": consensus_score,
        "confidence": confidence,
        "r1_label": label1,
        "r2_label": label2,
        "agreement": label1 == label2
    }
```

**9.2 Add to Pipeline**
```python
from intelligence.consensus.reducer import reduce_consensus

# After dual researchers:
    if dual_lane:
        dual_results = await run_dual_researchers(text, test_mode=test_mode)
        consensus = reduce_consensus(dual_results["R1"], dual_results["R2"])
        dual_results["consensus"] = consensus
        return dual_results
```

**9.3 Test & Validate**

---

### Step 10: Extract P28+P29 (Diversification)

**10.1 Create Module**

File: `intelligence/consensus/diversification.py`
```python
"""
Lane diversification: Apply provider order and config diversity per lane.
Replaces p28_diversify.py + p29_diversify_controls.py monkey patches.
"""
from __future__ import annotations
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def apply_lane_diversification(
    lane_id: str,
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate lane-specific configuration for diversification.

    Args:
        lane_id: "R1" or "R2"
        config: Base config

    Returns:
        Lane-specific config with provider order, timeouts, etc.
    """
    base_providers = ["google", "brave", "bing"]

    if lane_id == "R1":
        # R1: Standard order
        providers = base_providers
        timeout = 5.0
    elif lane_id == "R2":
        # R2: Reversed order for diversity
        providers = list(reversed(base_providers))
        timeout = 6.0
    else:
        providers = base_providers
        timeout = 5.0

    return {
        "lane_id": lane_id,
        "providers": providers,
        "timeout": timeout,
        "diversification_applied": True
    }

def get_telemetry(lane_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract telemetry from lane results.

    Returns:
        Run telemetry and audit fields
    """
    return {
        "lanes_run": len(lane_results),
        "diversification_configs": [
            lane_results.get("R1", {}).get("diversification", {}),
            lane_results.get("R2", {}).get("diversification", {})
        ]
    }
```

**10.2 Add to Dual Orchestration**
```python
from intelligence.consensus.diversification import apply_lane_diversification, get_telemetry

async def run_dual_researchers(...):
    # Apply diversification
    r1_config = apply_lane_diversification("R1")
    r2_config = apply_lane_diversification("R2")

    # Run with configs
    r1_result = await run_preview(text, test_mode=test_mode)  # Pass r1_config
    r2_result = await run_preview(text, test_mode=test_mode)  # Pass r2_config

    results = {
        "R1": {**r1_result, "diversification": r1_config},
        "R2": {**r2_result, "diversification": r2_config}
    }

    # Add telemetry
    results["telemetry"] = get_telemetry(results)

    return results
```

**10.3 Test & Validate**

---

## PHASE 4: CLEANUP (Day 3 Afternoon)

### Step 11: Delete sitecustomize.py

**Prerequisites:**
- All 10 wrappers extracted and logic moved to clean modules
- All tests pass without sitecustomize.py

**11.1 Verify No Dependency**
```bash
# Test without sitecustomize.py
$ mv sitecustomize.py sitecustomize.py.bak
$ pytest tests/ -v
# All tests should pass

$ python scripts/test_live_pipeline.py --claim "Test claim"
# Should work with explicit imports
```

**11.2 Delete**
```bash
$ rm sitecustomize.py
$ git add sitecustomize.py
$ git commit -m "Remove sitecustomize.py bootstrap (P30)"
```

---

### Step 12: Delete All Wrapper Files

**12.1 Verify Logic Extracted**
```bash
# Check each wrapper has corresponding clean module
$ ls intelligence/content/ingest.py         # Replaces p22
$ ls intelligence/content/semantic_read.py  # Replaces p23
$ ls intelligence/content/frames.py         # Replaces p24
$ ls intelligence/content/aggregation.py    # Replaces p25
$ ls intelligence/content/findings.py       # Replaces p20
$ ls intelligence/consensus/dual.py         # Replaces p26
$ ls intelligence/consensus/reducer.py      # Replaces p27
$ ls intelligence/consensus/diversification.py  # Replaces p28+p29
$ ls intelligence/gather/enrich.py          # Replaces p19
```

**12.2 Delete Wrappers**
```bash
$ rm intelligence/gather/p19_wrapper.py
$ rm intelligence/content/p20_wrapper.py
$ rm intelligence/content/p21_wrapper.py
$ rm intelligence/content/p22_ingest.py
$ rm intelligence/content/p23_semantic.py
$ rm intelligence/content/p24_semantic_frames.py
$ rm intelligence/content/p25_aggregate.py
$ rm intelligence/content/p25_semantic_aggregate.py
$ rm intelligence/content/p26_dual_researchers.py
$ rm intelligence/content/p27_consensus.py
$ rm intelligence/content/p28_diversify.py
$ rm intelligence/content/p29_diversify_controls.py

$ git add intelligence/
$ git commit -m "Remove all monkey patch wrappers (P30)"
```

---

## VALIDATION CHECKLIST

### After Each Phase

**Code Quality:**
- ✅ No `setattr()` usage in new modules
- ✅ All imports explicit at top of file
- ✅ Type hints on all functions
- ✅ Docstrings with Args/Returns
- ✅ Error handling with try/except + logging

**Functionality:**
- ✅ Unit tests pass for new module
- ✅ Integration tests pass end-to-end
- ✅ Live pipeline returns valid trust capsule
- ✅ Output equivalent to monkey-patched version

**Integration:**
- ✅ New module imported in `run.py` or `pipeline.py`
- ✅ Function called explicitly at correct point
- ✅ Parameters passed clearly
- ✅ Return value used correctly

### Final Validation (After Phase 4)

**Clean Code:**
```bash
# 1. No setattr usage
$ grep -r "setattr" intelligence/
# Should return empty (or only in tests)

# 2. No sitecustomize
$ ls sitecustomize.py
# Should not exist

# 3. No wrapper files
$ ls intelligence/**/*wrapper*.py
# Should return empty
```

**Functionality:**
```bash
# 4. All tests pass
$ pytest tests/ -v
# 100% pass rate

# 5. Live pipeline works
$ python scripts/test_live_pipeline.py --claim "Vaccines are safe and effective"
# Returns valid trust capsule with:
#   - Evidence items (arm_A, arm_B)
#   - Content fields (content_chars > 0 for some)
#   - Semantic signals (matches, item_stance)
#   - Frames (item_frame with entities)
#   - Verdict (label, confidence, score)

# 6. Import order doesn't matter
$ PYTHONDONTWRITEBYTECODE=1 python -c "from intelligence.pipeline.run import run_preview; print('OK')"
# Should work regardless of import order
```

**Performance:**
```bash
# 7. No performance regression
$ time python scripts/test_live_pipeline.py --claim "Test claim"
# Should be <= monkey-patched version time
```

---

## ROLLBACK PLAN

If something breaks during removal:

**1. Rollback Git:**
```bash
$ git checkout HEAD~1  # Go back one commit
$ git log --oneline    # Verify state
```

**2. Restore sitecustomize.py:**
```bash
$ git checkout main -- sitecustomize.py
```

**3. Restore Specific Wrapper:**
```bash
$ git checkout main -- intelligence/content/p20_wrapper.py
```

**4. Test Restored State:**
```bash
$ pytest tests/ -v
$ python scripts/test_live_pipeline.py
```

**5. Identify Issue:**
- Check error logs
- Compare output with/without wrapper
- Fix issue in new module
- Try removal again

---

## TESTING STRATEGY

### Unit Tests (Per Module)

**tests/test_content_ingest.py:**
```python
import pytest
from intelligence.content.ingest import ingest_full_text

@pytest.mark.asyncio
async def test_ingest_full_text():
    items = [
        {"url": "https://example.com/article1", "title": "Test"},
        {"url": "https://example.com/article2", "title": "Test2"}
    ]

    enriched = await ingest_full_text(items, max_items=2, timeout=5.0)

    assert len(enriched) == 2
    assert "content_chars" in enriched[0]
    assert "content_excerpt" in enriched[0]
```

**tests/test_semantic_read.py:**
```python
from intelligence.content.semantic_read import apply_semantic_analysis

def test_semantic_analysis():
    claim = "Vaccines are safe and effective"
    items = [
        {"content_excerpt": "Vaccines have been proven safe through extensive testing", "url": "test.com"}
    ]

    result = apply_semantic_analysis(claim, items)

    assert len(result) == 1
    assert "matches" in result[0]
    assert "content_score" in result[0]
    assert result[0]["semantic_analyzed"] is True
```

### Integration Tests

**tests/test_pipeline_clean.py:**
```python
import pytest
from intelligence.pipeline.run import run_preview

@pytest.mark.asyncio
async def test_clean_pipeline_no_monkey_patches():
    """Test that pipeline works without sitecustomize.py"""
    result = await run_preview("Test claim", test_mode=False)

    assert "overall" in result
    assert "claims" in result
    assert len(result["claims"]) > 0

    claim = result["claims"][0]
    assert "evidence" in claim
    assert "verdict" in claim

    # Check semantic enrichment happened
    evidence = claim.get("evidence", [])
    if evidence:
        item = evidence[0]
        # Should have semantic fields if content was fetched
        # (may be None if fetch failed, but fields should exist)
        assert "content_chars" in item or "snippet" in item
```

---

## ESTIMATED EFFORT BREAKDOWN

### Day 1: Foundation (6-8 hours)
- Morning: P22 (ingest) - 1.5h
- Morning: P23 (semantic) - 2h
- Afternoon: P24 (frames) - 2h
- Afternoon: P25 (aggregate) - 1.5h
- Evening: P19 (enrich) - 1h

### Day 2: Findings & Grading (6-8 hours)
- Morning: P20 (findings) - 3h
- Afternoon: P21 (fullread) - 2h
- Afternoon: Testing & fixes - 2h

### Day 3: Consensus & Cleanup (6-8 hours)
- Morning: P26 (dual-lane) - 2h
- Morning: P27 (consensus) - 1.5h
- Midday: P28+P29 (diversification) - 2h
- Afternoon: Delete sitecustomize + wrappers - 0.5h
- Afternoon: Final validation - 2h

**Total: 18-24 hours (2-3 days)**

---

## SUCCESS CRITERIA

**Code Quality:**
- ✅ Zero `setattr()` in production code
- ✅ Zero import-time side effects
- ✅ All functions have type hints
- ✅ All functions have docstrings
- ✅ Clear module organization

**Functionality:**
- ✅ All existing tests pass
- ✅ Live pipeline produces equivalent output
- ✅ No performance regression
- ✅ Semantic fields present in output
- ✅ Dual-lane mode works (if enabled)

**Maintainability:**
- ✅ Can read `run.py` and understand execution flow
- ✅ Can test modules independently
- ✅ Can add new features without wrappers
- ✅ Clear contracts between modules
- ✅ No hidden dependencies

**Documentation:**
- ✅ This removal plan completed
- ✅ CLEAN_WIRING_SPEC.md updated with actual paths
- ✅ Comments in code explaining integration points

---

## POST-CLEANUP VERIFICATION

After completing all phases, run full verification:

```bash
# 1. Code scan
$ python scripts/verify_no_monkey_patches.py
# Checks: no setattr, no sitecustomize, no wrappers

# 2. Test suite
$ pytest tests/ -v --cov=intelligence
# 100% pass, >80% coverage

# 3. Live test
$ python scripts/test_live_pipeline.py --claim "Climate change is caused by human activity"
# Returns valid trust capsule with semantic enrichment

# 4. Performance benchmark
$ python scripts/benchmark_pipeline.py
# Compare before/after times

# 5. Integration check
$ python scripts/check_integration.py
# Verifies all modules properly integrated
```

---

## END OF MONKEY PATCH REMOVAL PLAN

**Status:** Ready to implement
**Effort:** 2-3 days
**Blocking:** No dependencies (can start immediately)
**Next:** After completion, proceed to Phase 1B (AI Assist implementation)

**Key Principle:** Replace runtime modifications with explicit imports and direct calls. No shortcuts, no band-aids, only clean maintainable code.
