# CLEAN INTEGRATION PLAN V2 - P19-P29 Monkey Patch Removal

**Date:** 2025-10-09
**Status:** Ready for execution
**Timeline:** 12-14 days (96-112 hours)
**Validated Against:** Live codebase investigation, no prior bias

---

## EXECUTIVE SUMMARY

### Goal
Remove all monkey patches from P19-P29 and integrate into clean, production-ready pipeline with independent, maintainable modules.

### Current State
- âœ… P1-P18 (core pipeline): Already clean, no monkey patches
- âŒ P19-P29: Monkey-patched wrappers using setattr()
- âŒ Only P20+P22 load in production (deployment bug)
- âŒ P22 has critical memory leak (unbounded cache)
- âŒ 6 packets have embedded logic requiring extraction (1,326 lines)

### Architecture
```
Researcher R1 (Lane 1):
  â”œâ”€ Arm A (support) â†’ P19 counter-frames enhancement
  â””â”€ Arm B (challenge) â†’ P19 counter-frames enhancement
     â†’ P20-P25 enrichment â†’ R1 verdict

Researcher R2 (Lane 2):
  â”œâ”€ Arm A (support) â†’ P19 counter-frames enhancement
  â””â”€ Arm B (challenge) â†’ P19 counter-frames enhancement
     â†’ P20-P25 enrichment â†’ R2 verdict

P28 Diversification: Different provider/query order per lane
P27 Consensus: Combine R1+R2 â†’ Final verdict
P29 Telemetry: Track execution, generate replay_id
```

### Success Criteria
- âœ… No setattr/monkey patches in codebase
- âœ… All P19-P29 as independent modules with clean contracts
- âœ… Memory leaks fixed
- âœ… Dual researchers working with consensus
- âœ… test_s2p30r_audit.py passes
- âœ… Each stage passes standalone + live integration tests

### Key Findings from Investigation
1. **P19 was completely missing from original plan** - must be included
2. **Only 5 of 11 packets have clean modules** - 6 need extraction (not 0)
3. **Module independence is design principle** - don't bundle modules together
4. **Realistic timeline is 12-14 days** - original 8-10 was too optimistic

---

## EXTRACTION STRATEGY

### Core Principle: Preserve Original Files During Integration

**During Days 1-11:** Extract logic to **NEW clean modules** while leaving original wrapper files completely untouched. The old wrappers remain in place but become unused as the pipeline imports shift to the new modules.

**Approach:**
- Create new modules at clean paths (e.g., `intelligence/gather/counter_frames.py`)
- Extract logic from wrappers (e.g., from `p19_wrapper.py`) into new modules
- Update pipeline imports to use new modules (e.g., `from intelligence.gather.counter_frames import ...`)
- Original wrappers stay in place but are no longer imported or executed
- Only after full validation (Day 12) do we archive the old files

**Why This Approach:**
- **Safety**: Old code remains available if rollback needed
- **Clarity**: New modules created in isolation, easy to review
- **Testability**: Can compare old vs new behavior side-by-side
- **Low Risk**: Pipeline switches imports, wrappers become dormant but remain in git

**Target Paths in This Plan:** When the plan specifies "Create `intelligence/gather/counter_frames.py`" - this means create a **NEW file**. The corresponding wrapper (e.g., `p19_wrapper.py`) is the source to extract from, not the file to modify.

---

## PART 1: EXTRACTION REQUIREMENTS

### Packets Needing Extraction (6 total)

| Packet | Current File | Lines | New Module Path | Est. Hours |
|--------|-------------|-------|-----------------|------------|
| P19 | intelligence/gather/p19_wrapper.py | 215 | intelligence/gather/counter_frames.py | 4-6h |
| P22 | intelligence/content/p22_ingest.py | 267 | intelligence/content/fetch_enrichment.py | 6-8h |
| P26 | intelligence/content/p26_dual_researchers.py | 115 | intelligence/orchestration/dual_lane.py | 4-6h |
| P27 | intelligence/content/p27_consensus.py | 164 | intelligence/consensus/dual_lane.py | 2-3h |
| P28 | intelligence/content/p28_diversify.py | 277 | intelligence/planning/diversify.py | 6-8h |
| P29 | intelligence/content/p29_diversify_controls.py | 288 | intelligence/telemetry/collect.py | 4-6h |
| **TOTAL** | | **1,326** | | **26-37h** |

### Packets Already Clean (5 total)

| Packet | Clean Module | Status |
|--------|-------------|---------|
| P20 | intelligence/content/grade.py | âœ… Ready to wire |
| P21 | intelligence/content/fullread.py | âœ… Ready to wire |
| P23 | intelligence/content/semantic_read.py | âœ… Ready to wire |
| P24 | intelligence/content/semantic_frames.py | âœ… Ready to wire |
| P25 | intelligence/content/p25_aggregate.py | âœ… Ready to wire |

---

## PART 2: MODULE CONTRACTS

### P19: Counter-Frames for Arm B

**Module:** `intelligence/gather/counter_frames.py`

**Purpose:** Generate deterministic counter-frame queries for challenge arm (Arm B)

**Exports:**
```python
def generate_counter_frame_queries(
    claim_text: str,
    original_queries: List[str]
) -> List[Tuple[str, str]]:
    """
    Generate counter-frame queries for Arm B.

    Args:
        claim_text: The claim being fact-checked
        original_queries: Base queries for Arm B

    Returns:
        List of (frame_name, query) tuples:
        - ("numeric_dispute", "Austin budget audit revised ...")
        - ("denominator_shift", "Austin general fund enterprise ...")
        - ("timing_change", "Austin rescinded amendment FY ...")
        - ("authority_conflict", "Austin minutes comptroller ...")
        - ("methodology", "Austin methodology baseline ...")
    """

def compute_coverage_metrics(
    candidates: List[Dict[str, Any]],
    queries: List[str],
    providers_used: Set[str]
) -> Dict[str, Any]:
    """
    Compute per-arm coverage metrics.

    Returns:
        {
            "frames_attempted": int,
            "providers_used": int,
            "queries_issued": int,
            "candidates_fetched": int
        }
    """

def reorder_by_anchor_score(
    candidates: List[Dict[str, Any]],
    claim_text: str
) -> List[Dict[str, Any]]:
    """
    Reorder candidates by anchor match (entities, numbers, topics).
    Non-filtering, just stable reordering.
    """
```

**Dependencies:** None (stdlib only)

**Usage in pipeline:**
```python
# In intelligence/gather/online.py or pipeline.py
from intelligence.gather.counter_frames import generate_counter_frame_queries

# For Arm B
if arm["intent"] in ("challenge", "contradict", "refute"):
    counter_queries = generate_counter_frame_queries(claim_text, arm["queries"])
    arm["queries"].extend([q for _, q in counter_queries])
```

**Test command (standalone):**
```bash
python3 -c "
from intelligence.gather.counter_frames import generate_counter_frame_queries
queries = generate_counter_frame_queries('Austin budget increased 8%', ['Austin budget'])
print(f'Generated {len(queries)} counter-frame queries')
for frame, q in queries:
    print(f'  {frame}: {q[:50]}...')
"
```

**Test command (live integration):**
```bash
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' \
  | jq '.claims[0].researchers[0].evidence.coverage_by_arm'
```

---

### P20: Findings Attachment (Grade & Stance)

**Module:** `intelligence/content/grade.py` âœ… (already clean)

**Purpose:** Attach finding card (grade, stance, rationale) to each evidence item

**Exports:**
```python
def attach_finding_to_item(
    claim_text: str,
    arm: str,  # "A" or "B"
    item: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Attach finding card to evidence item.

    Adds to item:
        - grade: float 0-10
        - stance: str ("support", "challenge", "mixed", "unrelated")
        - finding: Dict with grade, stance, matched_spans, rationale, similarity, signals

    Returns:
        Mutated item (same object)
    """
```

**Dependencies:** `intelligence.content.extract_facts`

**Usage in pipeline:**
```python
# After content enrichment (P22)
from intelligence.content.grade import attach_finding_to_item

for arm_key, arm_label in [("arm_A", "A"), ("arm_B", "B")]:
    for item in evidence[arm_key]:
        attach_finding_to_item(claim_text, arm_label, item)
```

**Test command (standalone):**
```bash
python3 -c "
from intelligence.content.grade import attach_finding_to_item
item = {'url': 'test.com', 'snippet': 'Austin budget increased 8% in 2024', 'content': 'Full text...'}
result = attach_finding_to_item('Austin budget increased 8%', 'A', item)
print(f'Grade: {result[\"grade\"]}, Stance: {result[\"stance\"]}')
"
```

**Test command (live integration):**
```bash
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' \
  | jq '.claims[0].evidence.arm_A[0] | {grade, stance, finding}'
```

---

### P21: Full-Read Evaluation

**Module:** `intelligence/content/fullread.py` âœ… (already clean)

**Purpose:** Deeper content analysis with sliding windows, credibility scoring

**Exports:**
```python
def evaluate_full_evidence(
    claim_text: str,
    item: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Full-read evaluation of evidence item.

    Adds to item:
        - grade_full: float 0-10
        - stance_full: str
        - signals_full: Dict (jaccard3, entity_overlap, percent_any, percent_close, year_hit, negation)
        - credibility: float 0-1 (HTTPS, .gov/.edu, authz words)

    Returns:
        Mutated item
    """
```

**Dependencies:** None (stdlib only)

**Usage in pipeline:**
```python
# After P20 findings
from intelligence.content.fullread import evaluate_full_evidence

for arm_key in ("arm_A", "arm_B"):
    for item in evidence[arm_key]:
        if item.get("content"):  # Only if we have full text
            evaluate_full_evidence(claim_text, item)
```

**Test command (standalone):**
```bash
python3 -c "
from intelligence.content.fullread import evaluate_full_evidence
item = {'content': 'Austin city budget increased by 8% in 2024...', 'url': 'https://austintexas.gov/budget'}
result = evaluate_full_evidence('Austin budget increased 8%', item)
print(f'Grade Full: {result[\"grade_full\"]}, Credibility: {result[\"credibility\"]}')
"
```

**Test command (live integration):**
```bash
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' \
  | jq '.claims[0].evidence.arm_A[0] | {grade_full, stance_full, credibility}'
```

---

### P22: Content Enrichment (Fetch & Cache)

**Module:** `intelligence/content/fetch_enrichment.py` (NEW - extract from p22_ingest.py)

**Purpose:** Fetch full-text content for evidence items, manage request-scoped cache

**Exports:**
```python
async def enrich_items_with_content(
    items: List[Dict[str, Any]],
    fetch_cache: Dict[str, str]
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Enrich evidence items with full-text content.

    Args:
        items: Evidence items with 'url' field
        fetch_cache: Request-scoped cache {url: content}

    Returns:
        (enriched_items, updated_cache)

    Adds to each item:
        - content: str (full text)
        - content_hash: str (sha256:...)
        - content_chars: int
        - coverage: str ("full", "partial", "snippet_only")
    """

async def fetch_missing_urls(
    urls: List[str],
    fetch_cache: Dict[str, str],
    timeout: float = 8.0
) -> Dict[str, str]:
    """
    Fetch URLs not in cache using asyncio.gather.

    Returns:
        {url: content} for successfully fetched URLs
    """
```

**Dependencies:** `intelligence.content.fetch.fetch_text`

**Critical Fix:** Request-scoped cache (no module-level global)

**Usage in pipeline:**
```python
# After gather, before P20 findings
from intelligence.content.fetch_enrichment import enrich_items_with_content

fetch_cache = {}  # Request-scoped, cleared at end

for arm_key in ("arm_A", "arm_B"):
    items, fetch_cache = await enrich_items_with_content(
        evidence[arm_key],
        fetch_cache
    )
    evidence[arm_key] = items

# Cache cleared when request ends (goes out of scope)
```

**Test command (standalone):**
```bash
python3 -c "
import asyncio
from intelligence.content.fetch_enrichment import enrich_items_with_content

async def test():
    items = [{'url': 'https://www.austintexas.gov/budget', 'snippet': 'test'}]
    cache = {}
    enriched, cache = await enrich_items_with_content(items, cache)
    print(f'Content length: {len(enriched[0].get(\"content\", \"\"))}')
    print(f'Coverage: {enriched[0].get(\"coverage\")}')
    print(f'Hash: {enriched[0].get(\"content_hash\", \"none\")[:20]}...')

asyncio.run(test())
"
```

**Test command (live integration):**
```bash
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' \
  | jq '.claims[0].evidence.arm_A[0] | {content_chars, content_hash, coverage}'
```

---

### P23: Semantic Reading (Findings Extraction)

**Module:** `intelligence/content/semantic_read.py` âœ… (already clean)

**Purpose:** Extract multiple findings from content with scores

**Exports:**
```python
def analyze_item(
    claim_text: str,
    item: Dict[str, Any],
    window: int = 3
) -> Dict[str, Any]:
    """
    Semantic analysis of evidence item.

    Adds to item:
        - findings: List[Dict] with quote, offset_start, offset_end, stance, signals, score
        - item_grade: float 0-1
        - grade_label: str ("high", "medium", "low")

    Returns:
        Mutated item
    """
```

**Dependencies:** None (stdlib only)

**Usage in pipeline:**
```python
# After P20-P22
from intelligence.content.semantic_read import analyze_item

for arm_key in ("arm_A", "arm_B"):
    for item in evidence[arm_key]:
        if item.get("content"):
            analyze_item(claim_text, item, window=3)
```

**Test command (standalone):**
```bash
python3 -c "
from intelligence.content.semantic_read import analyze_item
item = {'content': 'Austin budget increased 8% in 2024. Council approved...'}
result = analyze_item('Austin budget increased 8%', item)
print(f'Findings: {len(result[\"findings\"])}, Grade: {result[\"item_grade\"]}')
"
```

**Test command (live integration):**
```bash
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' \
  | jq '.claims[0].evidence.arm_A[0] | {findings: .findings | length, item_grade, grade_label}'
```

---

### P24: Semantic Frames (Entity/Action/Quantity Extraction)

**Module:** `intelligence/content/semantic_frames.py` âœ… (already clean)

**Purpose:** Extract structured frames (entity, action, quantity, year, scope)

**Exports:**
```python
def analyze_frames(
    claim_text: str,
    content: str,
    window: int = 3,
    max_windows: int = 500
) -> Dict[str, Any]:
    """
    Frame extraction from content.

    Returns:
        {
            "item_frame": {entity[], action, quantity[], year[], scope},
            "frame_matches": [{label, score, slots[], rules[], quote, offset_start, offset_end}],
            "frame_confidence": float
        }
    """
```

**Dependencies:** None (stdlib only)

**Usage in pipeline:**
```python
# After P23
from intelligence.content.semantic_frames import analyze_frames

for arm_key in ("arm_A", "arm_B"):
    for item in evidence[arm_key]:
        content = item.get("content") or item.get("content_excerpt") or ""
        if content:
            frames = analyze_frames(claim_text, content, window=3)
            item.update(frames)
```

**Test command (standalone):**
```bash
python3 -c "
from intelligence.content.semantic_frames import analyze_frames
result = analyze_frames('Austin budget increased 8%', 'Austin city budget increased by 8% in 2024...')
print(f'Frame: {result[\"item_frame\"]}')
print(f'Matches: {len(result[\"frame_matches\"])}, Confidence: {result[\"frame_confidence\"]}')
"
```

**Test command (live integration):**
```bash
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' \
  | jq '.claims[0].evidence.arm_A[0] | {item_frame, frame_confidence}'
```

---

### P25: Arm Aggregation & Verdict

**Module:** `intelligence/content/p25_aggregate.py` âœ… (already clean)

**Purpose:** Aggregate evidence from arms A and B into verdict

**Exports:**
```python
def aggregate_verdict(
    claim_text: str,
    arm_a_items: List[Dict[str, Any]],
    arm_b_items: List[Dict[str, Any]],
    delta: float = 0.15
) -> Dict[str, Any]:
    """
    Compute verdict from arm strengths.

    Returns:
        {
            "label": "supports" | "challenges" | "mixed" | "insufficient",
            "confidence": float 0-1,
            "arm_strength": {"support": float, "challenge": float, "balance": float}
        }
    """
```

**Dependencies:** Expects items to have `frame_matches`, `item_grade`, `coverage` from P23-P24

**Usage in pipeline:**
```python
# After P24
from intelligence.content.p25_aggregate import aggregate_verdict

verdict = aggregate_verdict(
    claim_text,
    evidence["arm_A"],
    evidence["arm_B"],
    delta=0.15
)
```

**Test command (standalone):**
```bash
python3 -c "
from intelligence.content.p25_aggregate import aggregate_verdict
arm_a = [{'item_grade': 0.8, 'frame_matches': [{'score': 0.7}], 'coverage': 'full'}]
arm_b = [{'item_grade': 0.3, 'frame_matches': [{'score': 0.2}], 'coverage': 'partial'}]
result = aggregate_verdict('Test claim', arm_a, arm_b)
print(f'Label: {result[\"label\"]}, Confidence: {result[\"confidence\"]:.2f}')
print(f'Arm Strength: {result[\"arm_strength\"]}')
"
```

**Test command (live integration):**
```bash
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' \
  | jq '.claims[0].researchers[0].verdict | {label, confidence, arm_strength}'
```

---

### P26: Dual-Researcher Orchestration

**Module:** `intelligence/orchestration/dual_lane.py` (NEW - extract from p26_dual_researchers.py)

**Purpose:** Run two independent researchers (R1, R2) and merge results

**Exports:**
```python
async def run_dual_researchers(
    claim_text: str,
    base_plan: Dict[str, Any],
    enrichment_pipeline: Callable,
    diversify_fn: Callable,
    telemetry_class: Type[LaneTelemetry]
) -> Dict[str, Any]:
    """
    Orchestrate R1 and R2 independent runs.

    Args:
        claim_text: Claim being fact-checked
        base_plan: Base search plan (before diversification)
        enrichment_pipeline: Function that runs P19-P25 for one lane
        diversify_fn: Function to diversify plan per lane (from P28)
        telemetry_class: Telemetry tracker (from P29)

    Returns:
        {
            "researchers": [
                {"id": "R1", "verdict": {...}, "evidence": {...}, "lane_config": {...}, "telemetry": {...}},
                {"id": "R2", "verdict": {...}, "evidence": {...}, "lane_config": {...}, "telemetry": {...}}
            ],
            # Backward compatibility:
            "verdict": {...},     # R1 verdict
            "evidence": {...}     # R1 evidence
        }
    """

def merge_r1_r2_results(
    r1_result: Dict[str, Any],
    r2_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge R1 and R2 results, preserving R1 as base for backward compatibility.
    """
```

**Dependencies:** P27 (consensus), P28 (diversify), P29 (telemetry)

**Usage in pipeline:**
```python
# In intelligence/pipeline/run.py
from intelligence.orchestration.dual_lane import run_dual_researchers

result = await run_dual_researchers(
    claim_text=text,
    base_plan=base_plan,
    enrichment_pipeline=run_single_lane_enrichment,  # P19-P25
    diversify_fn=diversify_plan_for_lane,            # P28
    telemetry_class=LaneTelemetry                    # P29
)
```

**Test command (standalone):**
```python
# Create test script: test_p26.py
import asyncio
from intelligence.orchestration.dual_lane import run_dual_researchers

async def mock_enrichment(claim, plan, telemetry):
    return {"verdict": {"label": "supports"}, "evidence": {"arm_A": [], "arm_B": []}}

def mock_diversify(plan, lane_id, claim):
    return plan, {"lane_id": lane_id}

class MockTelemetry:
    def finalize(self):
        return {}

async def test():
    result = await run_dual_researchers(
        "Test claim",
        {"arms": []},
        mock_enrichment,
        mock_diversify,
        MockTelemetry
    )
    print(f"Researchers: {len(result['researchers'])}")
    print(f"R1 label: {result['researchers'][0]['verdict']['label']}")

asyncio.run(test())
```

**Test command (live integration):**
```bash
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' \
  | jq '.claims[0] | {researchers: .researchers | length, r1_label: .researchers[0].verdict.label, r2_label: .researchers[1].verdict.label}'
```

---

### P27: Consensus Mechanism

**Module:** `intelligence/consensus/dual_lane.py` (NEW - extract from p27_consensus.py)

**Purpose:** Combine R1 and R2 verdicts into consensus

**Exports:**
```python
def compute_consensus(
    r1_verdict: Dict[str, Any],
    r2_verdict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute consensus from two researcher verdicts.

    Args:
        r1_verdict: {"label": str, "confidence": float, "arm_strength": {...}}
        r2_verdict: {"label": str, "confidence": float, "arm_strength": {...}}

    Returns:
        {
            "label": "supports" | "challenges" | "mixed" | "insufficient",
            "confidence": float 0-1,
            "rationale": {
                "rule": str,  # "agree_same_label", "disagree_gap_select", "disagree_mixed"
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

    Logic:
        - If R1.label == R2.label: consensus = same, confidence += bonus (max 0.95)
        - If R1.label != R2.label: check arm strength delta
            - If |support - challenge| >= 0.20: pick stronger side
            - Else: label = "mixed"
        - Disagreement: confidence = max(R1, R2) - penalty
    """
```

**Dependencies:** None (pure function)

**Usage in pipeline:**
```python
# After R1 and R2 complete
from intelligence.consensus.dual_lane import compute_consensus

consensus = compute_consensus(r1_verdict, r2_verdict)
```

**Test command (standalone):**
```bash
python3 -c "
from intelligence.consensus.dual_lane import compute_consensus

# Agreement case
r1 = {'label': 'supports', 'confidence': 0.7, 'arm_strength': {'support': 0.8, 'challenge': 0.2, 'balance': 0.6}}
r2 = {'label': 'supports', 'confidence': 0.75, 'arm_strength': {'support': 0.85, 'challenge': 0.15, 'balance': 0.7}}
result = compute_consensus(r1, r2)
print(f'Agreement: {result[\"label\"]}, confidence: {result[\"confidence\"]:.2f}')
print(f'Rule: {result[\"rationale\"][\"rule\"]}')

# Disagreement case
r1 = {'label': 'supports', 'confidence': 0.6, 'arm_strength': {'support': 0.65, 'challenge': 0.35, 'balance': 0.3}}
r2 = {'label': 'challenges', 'confidence': 0.65, 'arm_strength': {'support': 0.3, 'challenge': 0.7, 'balance': -0.4}}
result = compute_consensus(r1, r2)
print(f'Disagreement: {result[\"label\"]}, confidence: {result[\"confidence\"]:.2f}')
print(f'Rule: {result[\"rationale\"][\"rule\"]}')
"
```

**Test command (live integration):**
```bash
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' \
  | jq '.claims[0].consensus | {label, confidence, rationale: .rationale.rule, agreement: .agreement | {r1_label, r2_label}}'
```

---

### P28: Lane Diversification

**Module:** `intelligence/planning/diversify.py` (NEW - extract from p28_diversify.py)

**Purpose:** Create lane-specific plans with deterministic diversification

**Exports:**
```python
def diversify_plan_for_lane(
    base_plan: Dict[str, Any],
    lane_id: str,  # "R1" or "R2"
    claim_text: str,
    available_providers: List[str]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Diversify plan for specific lane.

    Args:
        base_plan: Base search plan (same for both lanes)
        lane_id: "R1" or "R2"
        claim_text: Claim text (for deterministic seed)
        available_providers: List of available search providers

    Returns:
        (diversified_plan, lane_config)

    Diversification:
        - R1 provider order: [google, brave, bing]
        - R2 provider order: [brave, google, bing]
        - Queries shuffled deterministically per lane (MD5 seed from lane_id + claim)
        - Same claim always produces same shuffle (reproducible)

    lane_config:
        {
            "lane_id": str,
            "providers": List[str],
            "queries_first3": {"A": [...], "B": [...]}  # For transparency
        }
    """

def get_available_providers() -> List[str]:
    """
    Detect available search providers from environment variables.

    Returns:
        List of provider names: ["google", "brave", "bing"]
    """
```

**Dependencies:** None (stdlib only)

**Usage in pipeline:**
```python
# Before running R1/R2
from intelligence.planning.diversify import diversify_plan_for_lane, get_available_providers

providers = get_available_providers()
r1_plan, r1_config = diversify_plan_for_lane(base_plan, "R1", claim_text, providers)
r2_plan, r2_config = diversify_plan_for_lane(base_plan, "R2", claim_text, providers)

# Run R1 with r1_plan
# Run R2 with r2_plan
```

**Test command (standalone):**
```bash
python3 -c "
from intelligence.planning.diversify import diversify_plan_for_lane

base_plan = {
    'arms': [
        {'name': 'A', 'queries': ['query1', 'query2', 'query3']},
        {'name': 'B', 'queries': ['queryA', 'queryB', 'queryC']}
    ]
}

r1_plan, r1_config = diversify_plan_for_lane(base_plan, 'R1', 'Test claim', ['google', 'brave', 'bing'])
r2_plan, r2_config = diversify_plan_for_lane(base_plan, 'R2', 'Test claim', ['google', 'brave', 'bing'])

print(f'R1 providers: {r1_config[\"providers\"]}')
print(f'R2 providers: {r2_config[\"providers\"]}')
print(f'R1 queries A: {r1_plan[\"arms\"][0][\"queries\"]}')
print(f'R2 queries A: {r2_plan[\"arms\"][0][\"queries\"]}')
print(f'Different orders: {r1_plan[\"arms\"][0][\"queries\"] != r2_plan[\"arms\"][0][\"queries\"]}')
"
```

**Test command (live integration):**
```bash
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' \
  | jq '.claims[0] | {
    r1_providers: .researchers[0].lane_config.providers,
    r2_providers: .researchers[1].lane_config.providers,
    r1_queries_A: .researchers[0].lane_config.queries_first3.A,
    r2_queries_A: .researchers[1].lane_config.queries_first3.A
}'
```

---

### P29: Telemetry & Manifest

**Module:** `intelligence/telemetry/collect.py` (NEW - extract from p29_diversify_controls.py)

**Purpose:** Track execution metrics per lane, generate reproducibility manifest

**Exports:**
```python
class LaneTelemetry:
    """
    Track execution metrics for a single researcher lane.

    Usage:
        telemetry = LaneTelemetry("R1")
        telemetry.record_provider_call("google")
        telemetry.record_provider_call("brave")
        result = telemetry.finalize()
        # {"providers": {"google": 1, "brave": 1}, "duration_ms": 2340}
    """

    def __init__(self, lane_id: str):
        """Initialize telemetry for lane."""

    def record_provider_call(self, provider: str) -> None:
        """Record a search provider call."""

    def finalize(self) -> Dict[str, Any]:
        """
        Finalize telemetry and return metrics.

        Returns:
            {
                "providers": Dict[str, int],  # {provider: count}
                "duration_ms": int
            }
        """

def generate_manifest(
    claim_text: str,
    r1_config: Dict[str, Any],
    r2_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate reproducibility manifest.

    Returns:
        {
            "replay_id": str,  # MD5 hash for reproducibility
            "lanes": {
                "R1": {
                    "providers": List[str],
                    "seed": int,
                    "knobs": {"query_shuffle": bool, ...}
                },
                "R2": {...}
            },
            "claim_text": str,
            "providers_available": List[str]
        }
    """
```

**Dependencies:** None (stdlib only)

**Usage in pipeline:**
```python
# Create telemetry per lane
from intelligence.telemetry.collect import LaneTelemetry, generate_manifest

r1_telemetry = LaneTelemetry("R1")
r2_telemetry = LaneTelemetry("R2")

# During R1 execution
r1_telemetry.record_provider_call("google")  # Each provider call

# After both lanes complete
manifest = generate_manifest(claim_text, r1_config, r2_config)

result = {
    "run_manifest": manifest,
    "researchers": [
        {"id": "R1", "telemetry": r1_telemetry.finalize(), ...},
        {"id": "R2", "telemetry": r2_telemetry.finalize(), ...}
    ]
}
```

**Test command (standalone):**
```bash
python3 -c "
import time
from intelligence.telemetry.collect import LaneTelemetry, generate_manifest

# Test telemetry
t = LaneTelemetry('R1')
t.record_provider_call('google')
t.record_provider_call('google')
t.record_provider_call('brave')
time.sleep(0.1)
result = t.finalize()
print(f'Telemetry: {result}')

# Test manifest
r1_config = {'providers': ['google', 'brave'], 'seed': 12345}
r2_config = {'providers': ['brave', 'google'], 'seed': 67890}
manifest = generate_manifest('Test claim', r1_config, r2_config)
print(f'Replay ID: {manifest[\"replay_id\"]}')
print(f'Lanes: {list(manifest[\"lanes\"].keys())}')
"
```

**Test command (live integration):**
```bash
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' \
  | jq '{
    replay_id: .run_manifest.replay_id,
    r1_telemetry: .claims[0].researchers[0].telemetry,
    r2_telemetry: .claims[0].researchers[1].telemetry
}'
```

---

## PART 3: IMPLEMENTATION SCHEDULE

### Week 1: Item Enrichment (Days 1-5) - 36-42 hours

#### **Day 1: P22 Content Enrichment (6-8 hours)**

**Goal:** Extract P22 fetch/cache logic to clean module, fix memory leak

**Tasks:**
1. Create `intelligence/content/fetch_enrichment.py`
2. Extract functions from p22_ingest.py:
   - `enrich_items_with_content()` - main enrichment function
   - `fetch_missing_urls()` - async fetch with gather
   - Helper functions for hash, coverage detection
3. Remove module-level `_FETCH_CACHE` global
4. Implement request-scoped cache parameter
5. Fix `intelligence/content/fetch_sync.py` cache too (line 21)

**Files to create:**
- `intelligence/content/fetch_enrichment.py` (~200 lines)

**Files to modify:**
- `intelligence/content/fetch_sync.py` (add LRU cache or remove cache)

**Testing:**
```bash
# Standalone
python3 -c "
import asyncio
from intelligence.content.fetch_enrichment import enrich_items_with_content

async def test():
    items = [{'url': 'https://www.austintexas.gov/budget', 'snippet': 'test'}]
    cache = {}
    enriched, cache = await enrich_items_with_content(items, cache)
    print(f'âœ“ Content: {len(enriched[0].get(\"content\", \"\"))} chars')
    print(f'âœ“ Coverage: {enriched[0].get(\"coverage\")}')
    print(f'âœ“ Cache size: {len(cache)} entries')
    assert enriched[0].get('content'), 'Content missing'
    assert enriched[0].get('coverage') in ('full', 'partial', 'snippet_only'), 'Invalid coverage'
    print('âœ“ PASS: Standalone test')

asyncio.run(test())
"

# Live integration (requires wiring first - test after Day 3)
```

**Checkpoint:** Module imports successfully, functions callable, no module-level cache globals

---

#### **Day 2: P19 Counter-Frames (4-6 hours)**

**Goal:** Extract P19 counter-frame logic to clean module

**Tasks:**
1. Create `intelligence/gather/counter_frames.py`
2. Extract functions from p19_wrapper.py:
   - `generate_counter_frame_queries()` - main query generator
   - `_extract_anchors_from_claim()` - entity/number extraction
   - `_build_b_queries()` - frame-based query construction
   - `compute_coverage_metrics()` - per-arm metrics
   - `reorder_by_anchor_score()` - stable reordering
3. Move constants (frame types, regex patterns)
4. Test independently

**Files to create:**
- `intelligence/gather/counter_frames.py` (~180 lines)

**Testing:**
```bash
# Standalone
python3 -c "
from intelligence.gather.counter_frames import generate_counter_frame_queries, compute_coverage_metrics

# Test query generation
queries = generate_counter_frame_queries('Austin budget increased 8%', ['Austin budget'])
print(f'âœ“ Generated {len(queries)} queries')
assert len(queries) > 0, 'No queries generated'
for frame, q in queries[:3]:
    print(f'  {frame}: {q[:60]}...')
    assert frame in ('numeric_dispute', 'denominator_shift', 'timing_change', 'authority_conflict', 'methodology', 'fallback'), f'Unknown frame: {frame}'

# Test coverage metrics
candidates = [{'provider': 'google'}, {'provider': 'brave'}, {'provider': 'google'}]
coverage = compute_coverage_metrics(candidates, ['q1', 'q2'], {'google', 'brave'})
print(f'âœ“ Coverage: {coverage}')
assert coverage['providers_used'] == 2, 'Wrong provider count'
assert coverage['queries_issued'] == 2, 'Wrong query count'
assert coverage['candidates_fetched'] == 3, 'Wrong candidate count'
print('âœ“ PASS: Standalone test')
"

# Live integration (test after wiring on Day 3)
```

**Checkpoint:** Module imports, generates counter-frame queries, computes coverage

---

#### **Day 3: Wire P19, P20-P22 into Pipeline (8-10 hours)**

**Goal:** Integrate P19, P20, P22 directly into pipeline (no wrappers)

**Tasks:**
1. Modify `intelligence/gather/online.py` or `intelligence/gather/pipeline.py`:
   - Add P19 counter-frame query generation for Arm B
   - Track coverage per arm
2. Modify `intelligence/pipeline/run.py`:
   - Add request-scoped fetch cache
   - Call P22 fetch enrichment
   - Call P20 findings attachment
3. Test execution order: gather â†’ P22 content â†’ P20 findings
4. Verify no wrapper imports

**Files to modify:**
- `intelligence/gather/online.py` or `intelligence/gather/pipeline.py` (+30-40 lines)
- `intelligence/pipeline/run.py` (+50-60 lines)

**Code changes in `intelligence/gather/online.py`:**
```python
from intelligence.gather.counter_frames import generate_counter_frame_queries, compute_coverage_metrics

async def run_plan(plan: Dict[str, Any], max_per_query: int = 10) -> Dict[str, Any]:
    # ... existing gather logic ...

    # Add P19 counter-frames for Arm B
    for arm in plan.get("arms", []):
        intent = arm.get("intent", "").lower()
        if intent in ("challenge", "contradict", "refute") or arm.get("name", "").upper().startswith("B"):
            claim_text = plan.get("claim_text", "")
            counter_queries = generate_counter_frame_queries(claim_text, arm.get("queries", []))
            arm["queries"].extend([q for _, q in counter_queries])

    # ... existing gather execution ...

    # Add coverage tracking
    coverage_by_arm = {}
    for arm_name, candidates in results_by_arm.items():
        coverage_by_arm[arm_name] = compute_coverage_metrics(
            candidates,
            arm_queries[arm_name],
            providers_used[arm_name]
        )

    return {
        "candidates": all_candidates,
        "coverage_by_arm": coverage_by_arm
    }
```

**Code changes in `intelligence/pipeline/run.py`:**
```python
from intelligence.content.fetch_enrichment import enrich_items_with_content
from intelligence.content.grade import attach_finding_to_item

async def run_preview(text: str, test_mode: bool = False) -> Dict[str, Any]:
    # ... existing claim and plan creation ...

    # Initialize request-scoped cache
    fetch_cache = {}

    # Gather evidence (now includes P19 counter-frames)
    evidence = await build_evidence_for_claim(claim["text"], plans, max_per_arm=3)

    # P22: Content enrichment
    for arm_key in ("arm_A", "arm_B"):
        items = evidence.get(arm_key, [])
        items, fetch_cache = await enrich_items_with_content(items, fetch_cache)
        evidence[arm_key] = items

    # P20: Findings attachment
    for arm_key, arm_label in [("arm_A", "A"), ("arm_B", "B")]:
        for item in evidence.get(arm_key, []):
            try:
                attach_finding_to_item(claim["text"], arm_label, item)
            except Exception:
                pass  # Non-critical

    # ... rest of pipeline ...

    # Cache cleared when request ends (goes out of scope)
```

**Testing:**
```bash
# Live integration test
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' > test_output.json

# Verify P19 counter-frames
jq '.claims[0].evidence.coverage_by_arm' test_output.json
# Should show: {"A": {...}, "B": {"frames_attempted": 5, ...}}

# Verify P22 content enrichment
jq '.claims[0].evidence.arm_A[0] | {content_chars, content_hash, coverage}' test_output.json
# Should show: {"content_chars": 5000+, "content_hash": "sha256:...", "coverage": "full"}

# Verify P20 findings
jq '.claims[0].evidence.arm_A[0] | {grade, stance, finding}' test_output.json
# Should show: {"grade": 7.5, "stance": "support", "finding": {...}}

echo "âœ“ PASS: P19, P20, P22 integrated"
```

**Checkpoint:** P19-P22 working in live pipeline, no wrappers loaded

---

#### **Day 4: Wire P21, P23-P25 (6-8 hours)**

**Goal:** Add P21 full-read, P23 semantic, P24 frames, P25 aggregation

**Tasks:**
1. Modify `intelligence/pipeline/run.py`:
   - Add P21 full-read evaluation (after P20)
   - Add P23 semantic reading (after P21)
   - Add P24 frame extraction (after P23)
   - Add P25 verdict aggregation (after P24)
2. Test execution order and data flow

**Files to modify:**
- `intelligence/pipeline/run.py` (+40-50 lines)

**Code changes in `intelligence/pipeline/run.py`:**
```python
from intelligence.content.fullread import evaluate_full_evidence
from intelligence.content.semantic_read import analyze_item
from intelligence.content.semantic_frames import analyze_frames
from intelligence.content.p25_aggregate import aggregate_verdict

async def run_preview(text: str, test_mode: bool = False) -> Dict[str, Any]:
    # ... P19-P22 from Day 3 ...

    # P21: Full-read evaluation
    for arm_key in ("arm_A", "arm_B"):
        for item in evidence.get(arm_key, []):
            if item.get("content"):
                try:
                    evaluate_full_evidence(claim["text"], item)
                except Exception:
                    pass

    # P23: Semantic reading
    for arm_key in ("arm_A", "arm_B"):
        for item in evidence.get(arm_key, []):
            if item.get("content"):
                try:
                    analyze_item(claim["text"], item, window=3)
                except Exception:
                    pass

    # P24: Frame extraction
    for arm_key in ("arm_A", "arm_B"):
        for item in evidence.get(arm_key, []):
            content = item.get("content") or item.get("content_excerpt") or ""
            if content:
                try:
                    frames = analyze_frames(claim["text"], content, window=3)
                    item.update(frames)
                except Exception:
                    pass

    # P25: Aggregate verdict
    try:
        verdict = aggregate_verdict(
            claim["text"],
            evidence.get("arm_A", []),
            evidence.get("arm_B", []),
            delta=0.15
        )
    except Exception:
        verdict = {"label": "insufficient", "confidence": 0.0}

    # ... rest of pipeline ...
```

**Testing:**
```bash
# Live integration test
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' > test_output.json

# Verify P21 full-read
jq '.claims[0].evidence.arm_A[0] | {grade_full, stance_full, credibility}' test_output.json
# Should show: {"grade_full": 7.8, "stance_full": "support", "credibility": 0.4}

# Verify P23 semantic
jq '.claims[0].evidence.arm_A[0] | {findings: .findings | length, item_grade, grade_label}' test_output.json
# Should show: {"findings": 3, "item_grade": 0.75, "grade_label": "high"}

# Verify P24 frames
jq '.claims[0].evidence.arm_A[0] | {item_frame, frame_confidence}' test_output.json
# Should show: {"item_frame": {"entity": [...], "action": "increase", ...}, "frame_confidence": 0.8}

# Verify P25 aggregation
jq '.claims[0].verdict | {label, confidence, arm_strength}' test_output.json
# Should show: {"label": "supports", "confidence": 0.72, "arm_strength": {...}}

echo "âœ“ PASS: P21, P23, P24, P25 integrated"
```

**Checkpoint:** Full item enrichment pipeline (P19-P25) working

---

#### **Day 5: Validation & Memory Leak Testing (6-8 hours)**

**Goal:** Validate item enrichment, confirm memory leak fixed

**Tasks:**
1. Run extended test suite
2. Memory leak test (multiple requests, check memory growth)
3. Compare output to baseline (if available)
4. Document any deviations
5. Performance benchmarks

**Testing:**
```bash
# Memory leak test
cat > test_memory_leak.sh <<'EOF'
#!/bin/bash
echo "Testing memory leak fix..."
for i in {1..100}; do
    curl -s -X POST http://localhost:8000/analyses/preview \
      -H "Content-Type: application/json" \
      -d '{"text":"Austin budget increased 8%"}' > /dev/null
    if [ $((i % 10)) -eq 0 ]; then
        echo "Completed $i requests"
    fi
done
echo "âœ“ Completed 100 requests"
echo "Check memory usage (should be stable):"
ps aux | grep "uvicorn\|gunicorn" | grep -v grep
EOF
chmod +x test_memory_leak.sh
./test_memory_leak.sh

# Performance benchmark
time curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' > /dev/null

# Run test suite
pytest tests/test_s2p30r_audit.py -v
# Should see: api.run_preview is core.run_preview (no wrappers)

echo "âœ“ PASS: Week 1 complete - Item enrichment working"
```

**Deliverables:**
- Item enrichment (P19-P25) working in production
- Memory leak fixed (request-scoped cache)
- No wrappers for P19-P25
- Performance baseline documented

---

### Week 2: Dual Researchers (Days 6-11) - 44-52 hours

#### **Day 6: Extract P27 Consensus (2-3 hours)**

**Goal:** Extract consensus logic to clean module

**Tasks:**
1. Create `intelligence/consensus/dual_lane.py`
2. Extract from p27_consensus.py:
   - `compute_consensus()` - main consensus function
   - `_lane()` - normalize verdict format
   - `_consensus_for_pair()` - agreement/disagreement logic
3. Test standalone with various verdict combinations

**Files to create:**
- `intelligence/consensus/dual_lane.py` (~120 lines)

**Testing:**
```bash
# Standalone
python3 -c "
from intelligence.consensus.dual_lane import compute_consensus

# Test agreement
r1 = {'label': 'supports', 'confidence': 0.7, 'arm_strength': {'support': 0.8, 'challenge': 0.2, 'balance': 0.6}}
r2 = {'label': 'supports', 'confidence': 0.75, 'arm_strength': {'support': 0.85, 'challenge': 0.15, 'balance': 0.7}}
result = compute_consensus(r1, r2)
print(f'âœ“ Agreement: {result[\"label\"]}, conf={result[\"confidence\"]:.2f}, rule={result[\"rationale\"][\"rule\"]}')
assert result['label'] == 'supports', 'Wrong label'
assert result['confidence'] > 0.7, 'Confidence should increase on agreement'

# Test disagreement
r1 = {'label': 'supports', 'confidence': 0.6, 'arm_strength': {'support': 0.65, 'challenge': 0.35, 'balance': 0.3}}
r2 = {'label': 'challenges', 'confidence': 0.65, 'arm_strength': {'support': 0.3, 'challenge': 0.7, 'balance': -0.4}}
result = compute_consensus(r1, r2)
print(f'âœ“ Disagreement: {result[\"label\"]}, conf={result[\"confidence\"]:.2f}, rule={result[\"rationale\"][\"rule\"]}')
assert result['label'] in ('supports', 'challenges', 'mixed'), 'Invalid label'
assert result['confidence'] < max(0.6, 0.65), 'Confidence should decrease on disagreement'

# Test mixed case
r1 = {'label': 'supports', 'confidence': 0.5, 'arm_strength': {'support': 0.55, 'challenge': 0.45, 'balance': 0.1}}
r2 = {'label': 'challenges', 'confidence': 0.52, 'arm_strength': {'support': 0.48, 'challenge': 0.52, 'balance': -0.04}}
result = compute_consensus(r1, r2)
print(f'âœ“ Mixed: {result[\"label\"]}, conf={result[\"confidence\"]:.2f}')
assert result['label'] == 'mixed', 'Should be mixed when delta < 0.20'

print('âœ“ PASS: Standalone test')
"

# Live integration (test after P26 integration)
```

**Checkpoint:** Consensus module works standalone, handles all verdict combinations

---

#### **Day 7: Extract P28 Diversification (6-8 hours)**

**Goal:** Extract diversification logic to clean module

**Tasks:**
1. Create `intelligence/planning/diversify.py`
2. Extract from p28_diversify.py:
   - `diversify_plan_for_lane()` - main diversification function
   - `get_available_providers()` - detect providers from env
   - `_ordered_providers_for_lane()` - R1 vs R2 provider order
   - `_lane_tweak_plan()` - query shuffle and provider assignment
3. Remove ContextVar usage (pass lane_id as parameter instead)
4. Test deterministic behavior (same input â†’ same output)

**Files to create:**
- `intelligence/planning/diversify.py` (~150 lines)

**Testing:**
```bash
# Standalone
python3 -c "
from intelligence.planning.diversify import diversify_plan_for_lane, get_available_providers

base_plan = {
    'arms': [
        {'name': 'A', 'queries': ['query1', 'query2', 'query3']},
        {'name': 'B', 'queries': ['queryA', 'queryB', 'queryC']}
    ]
}

providers = get_available_providers()
print(f'âœ“ Available providers: {providers}')

# Test R1
r1_plan, r1_config = diversify_plan_for_lane(base_plan, 'R1', 'Test claim', providers)
print(f'âœ“ R1 providers: {r1_config[\"providers\"]}')
print(f'âœ“ R1 queries A: {r1_plan[\"arms\"][0][\"queries\"]}')

# Test R2
r2_plan, r2_config = diversify_plan_for_lane(base_plan, 'R2', 'Test claim', providers)
print(f'âœ“ R2 providers: {r2_config[\"providers\"]}')
print(f'âœ“ R2 queries A: {r2_plan[\"arms\"][0][\"queries\"]}')

# Verify differences
assert r1_config['providers'] != r2_config['providers'], 'Provider order should differ'
assert r1_plan['arms'][0]['queries'] != r2_plan['arms'][0]['queries'], 'Query order should differ'

# Test determinism
r1_plan2, _ = diversify_plan_for_lane(base_plan, 'R1', 'Test claim', providers)
assert r1_plan['arms'][0]['queries'] == r1_plan2['arms'][0]['queries'], 'Should be deterministic'

print('âœ“ PASS: Standalone test')
"

# Live integration (test after P26 integration)
```

**Checkpoint:** Diversification module works, R1 and R2 get different orders deterministically

---

#### **Day 8: Extract P29 Telemetry (4-6 hours)**

**Goal:** Extract telemetry and manifest generation to clean module

**Tasks:**
1. Create `intelligence/telemetry/collect.py`
2. Extract from p29_diversify_controls.py:
   - `LaneTelemetry` class - track provider calls and duration
   - `generate_manifest()` - create reproducibility manifest
3. Remove ContextVar usage (pass telemetry instance explicitly)
4. Test telemetry tracking and manifest generation

**Files to create:**
- `intelligence/telemetry/collect.py` (~100 lines)

**Testing:**
```bash
# Standalone
python3 -c "
import time
from intelligence.telemetry.collect import LaneTelemetry, generate_manifest

# Test telemetry
t = LaneTelemetry('R1')
print('âœ“ Created telemetry for R1')

t.record_provider_call('google')
t.record_provider_call('google')
t.record_provider_call('brave')
print('âœ“ Recorded 3 provider calls')

time.sleep(0.05)
result = t.finalize()
print(f'âœ“ Telemetry: {result}')
assert result['providers']['google'] == 2, 'Wrong google count'
assert result['providers']['brave'] == 1, 'Wrong brave count'
assert result['duration_ms'] >= 50, 'Duration too short'

# Test manifest
r1_config = {'providers': ['google', 'brave'], 'seed': 12345}
r2_config = {'providers': ['brave', 'google'], 'seed': 67890}
manifest = generate_manifest('Test claim', r1_config, r2_config)
print(f'âœ“ Manifest replay_id: {manifest[\"replay_id\"]}')
assert 'replay_id' in manifest, 'Missing replay_id'
assert 'lanes' in manifest, 'Missing lanes'
assert 'R1' in manifest['lanes'], 'Missing R1'
assert 'R2' in manifest['lanes'], 'Missing R2'

# Test determinism
manifest2 = generate_manifest('Test claim', r1_config, r2_config)
assert manifest['replay_id'] == manifest2['replay_id'], 'Should be deterministic'

print('âœ“ PASS: Standalone test')
"

# Live integration (test after P26 integration)
```

**Checkpoint:** Telemetry class works, manifest generation deterministic

---

#### **Day 9: Extract P26 Orchestration Part 1 (6-8 hours)**

**Goal:** Extract dual-researcher orchestration logic to clean module

**Tasks:**
1. Create `intelligence/orchestration/dual_lane.py`
2. Extract from p26_dual_researchers.py:
   - `run_dual_researchers()` - main orchestration function
   - `merge_r1_r2_results()` - combine results preserving backward compatibility
   - Helper functions for researcher payload
3. Design clean interface that takes enrichment pipeline as parameter
4. Test with mock enrichment function

**Files to create:**
- `intelligence/orchestration/dual_lane.py` (~150 lines)

**Testing:**
```bash
# Standalone with mocks
cat > test_p26_standalone.py <<'EOF'
import asyncio
from intelligence.orchestration.dual_lane import run_dual_researchers

async def mock_enrichment_pipeline(claim_text, plan, lane_id, telemetry):
    """Mock enrichment that returns different results per lane."""
    return {
        "verdict": {
            "label": "supports" if lane_id == "R1" else "challenges",
            "confidence": 0.7,
            "arm_strength": {"support": 0.8, "challenge": 0.2, "balance": 0.6}
        },
        "evidence": {
            "arm_A": [{"url": "test.com", "grade": 8}],
            "arm_B": [{"url": "test2.com", "grade": 3}]
        }
    }

def mock_diversify(plan, lane_id, claim_text, providers):
    return plan, {"lane_id": lane_id, "providers": providers}

class MockTelemetry:
    def __init__(self, lane_id):
        self.lane_id = lane_id
    def finalize(self):
        return {"providers": {}, "duration_ms": 100}

async def test():
    result = await run_dual_researchers(
        "Test claim",
        {"arms": []},
        mock_enrichment_pipeline,
        mock_diversify,
        MockTelemetry
    )

    print(f"âœ“ Researchers: {len(result['researchers'])}")
    assert len(result['researchers']) == 2, "Should have 2 researchers"

    print(f"âœ“ R1 label: {result['researchers'][0]['verdict']['label']}")
    assert result['researchers'][0]['verdict']['label'] == 'supports', "R1 should support"

    print(f"âœ“ R2 label: {result['researchers'][1]['verdict']['label']}")
    assert result['researchers'][1]['verdict']['label'] == 'challenges', "R2 should challenge"

    print(f"âœ“ Backward compat verdict: {result['verdict']['label']}")
    assert 'verdict' in result, "Should have backward compat verdict"

    print("âœ“ PASS: Standalone test")

asyncio.run(test())
EOF

python3 test_p26_standalone.py

# Live integration (test after Day 10)
```

**Checkpoint:** P26 orchestration module works with mocks, returns 2 researchers

---

#### **Day 10: Extract P26 Orchestration Part 2 & Integration (6-8 hours)**

**Goal:** Wire P26 into pipeline with real P19-P29 modules

**Tasks:**
1. Modify `intelligence/pipeline/run.py`:
   - Import P26, P27, P28, P29 modules
   - Create enrichment pipeline function (calls P19-P25)
   - Call `run_dual_researchers()` with real modules
   - Add consensus computation
   - Generate manifest
2. Test end-to-end dual-researcher flow

**Files to modify:**
- `intelligence/pipeline/run.py` (+100-120 lines, major refactor)

**Code structure in `intelligence/pipeline/run.py`:**
```python
from intelligence.orchestration.dual_lane import run_dual_researchers
from intelligence.consensus.dual_lane import compute_consensus
from intelligence.planning.diversify import diversify_plan_for_lane, get_available_providers
from intelligence.telemetry.collect import LaneTelemetry, generate_manifest

async def run_single_lane_enrichment(claim_text, plan, lane_id, telemetry):
    """
    Run P19-P25 enrichment for one lane.
    Called by P26 orchestrator.
    """
    # Gather evidence (includes P19 counter-frames)
    evidence = await build_evidence_for_claim(claim_text, plan, max_per_arm=3)

    # Track provider calls in telemetry
    for arm_key in ("arm_A", "arm_B"):
        for item in evidence.get(arm_key, []):
            provider = item.get("provider")
            if provider:
                telemetry.record_provider_call(provider)

    # P22: Content enrichment (request-scoped cache)
    fetch_cache = {}
    for arm_key in ("arm_A", "arm_B"):
        items, fetch_cache = await enrich_items_with_content(
            evidence.get(arm_key, []),
            fetch_cache
        )
        evidence[arm_key] = items

    # P20-P25: Item enrichment
    for arm_key, arm_label in [("arm_A", "A"), ("arm_B", "B")]:
        for item in evidence.get(arm_key, []):
            # P20: Findings
            attach_finding_to_item(claim_text, arm_label, item)

            # P21: Full-read
            if item.get("content"):
                evaluate_full_evidence(claim_text, item)

            # P23: Semantic
            if item.get("content"):
                analyze_item(claim_text, item)

            # P24: Frames
            content = item.get("content") or item.get("content_excerpt") or ""
            if content:
                frames = analyze_frames(claim_text, content)
                item.update(frames)

    # P25: Aggregate verdict
    verdict = aggregate_verdict(
        claim_text,
        evidence.get("arm_A", []),
        evidence.get("arm_B", [])
    )

    return {"verdict": verdict, "evidence": evidence}

async def run_preview(text: str, test_mode: bool = False) -> Dict[str, Any]:
    # Create claim and base plan
    claim = {"id": "c-0", "text": text.strip(), "tier": "primary"}
    base_plan = build_search_plans_v2(claim)

    # Get available providers
    providers = get_available_providers()

    # Run dual researchers (P26)
    result = await run_dual_researchers(
        claim_text=text,
        base_plan=base_plan,
        enrichment_pipeline=run_single_lane_enrichment,
        diversify_fn=diversify_plan_for_lane,
        telemetry_class=LaneTelemetry
    )

    # Compute consensus (P27)
    r1_verdict = result["researchers"][0]["verdict"]
    r2_verdict = result["researchers"][1]["verdict"]
    consensus = compute_consensus(r1_verdict, r2_verdict)

    # Generate manifest (P29)
    r1_config = result["researchers"][0].get("lane_config", {})
    r2_config = result["researchers"][1].get("lane_config", {})
    manifest = generate_manifest(text, r1_config, r2_config)

    # Build final response
    return {
        "claims": [{
            "id": "c-0",
            "text": text,
            "verdict": r1_verdict,  # Backward compat
            "evidence": result["researchers"][0]["evidence"],  # Backward compat
            "consensus": consensus,
            "researchers": result["researchers"]
        }],
        "run_manifest": manifest,
        "diversified": True
    }
```

**Testing:**
```bash
# Live integration test - full dual-researcher flow
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' > test_dual_researchers.json

# Verify dual researchers
jq '.claims[0] | {
    has_researchers: (.researchers | length) == 2,
    r1_id: .researchers[0].id,
    r2_id: .researchers[1].id,
    r1_label: .researchers[0].verdict.label,
    r2_label: .researchers[1].verdict.label
}' test_dual_researchers.json

# Verify diversification (different provider/query order)
jq '.claims[0] | {
    r1_providers: .researchers[0].lane_config.providers,
    r2_providers: .researchers[1].lane_config.providers,
    providers_differ: (.researchers[0].lane_config.providers != .researchers[1].lane_config.providers)
}' test_dual_researchers.json

# Verify consensus
jq '.claims[0].consensus | {
    label,
    confidence,
    rule: .rationale.rule,
    agreement: .agreement | {r1_label, r2_label}
}' test_dual_researchers.json

# Verify manifest
jq '.run_manifest | {
    has_replay_id: .replay_id != null,
    lanes: .lanes | keys
}' test_dual_researchers.json

# Verify telemetry
jq '.claims[0].researchers[0].telemetry' test_dual_researchers.json
jq '.claims[0].researchers[1].telemetry' test_dual_researchers.json

echo "âœ“ PASS: Dual researchers integrated"
```

**Checkpoint:** Full P19-P29 pipeline working, dual researchers producing different results, consensus computed

---

#### **Day 11: Validation & Performance Testing (6-8 hours)**

**Goal:** Validate dual-researcher system, test edge cases

**Tasks:**
1. Test various claim types (agreement, disagreement, mixed)
2. Verify determinism (same claim â†’ same results)
3. Test with different provider availability
4. Performance benchmarks (2x API calls expected)
5. Memory leak check with dual researchers
6. Compare R1 vs R2 results (should differ)

**Testing:**
```bash
# Test agreement case
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Water is wet"}' | \
  jq '.claims[0] | {
    r1_label: .researchers[0].verdict.label,
    r2_label: .researchers[1].verdict.label,
    consensus_label: .consensus.label,
    consensus_rule: .consensus.rationale.rule
  }'
# Expect: R1 and R2 both "supports", consensus "supports", rule "agree_same_label"

# Test disagreement case
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Controversial political claim"}' | \
  jq '.claims[0] | {
    r1_label: .researchers[0].verdict.label,
    r2_label: .researchers[1].verdict.label,
    consensus_label: .consensus.label,
    consensus_rule: .consensus.rationale.rule
  }'
# Expect: R1 and R2 may differ, consensus uses arm strength delta

# Test determinism
for i in {1..3}; do
  curl -X POST http://localhost:8000/analyses/preview \
    -H "Content-Type: application/json" \
    -d '{"text":"Austin budget increased 8%"}' | \
    jq '.run_manifest.replay_id'
done
# All three should show same replay_id

# Test R1 vs R2 differences
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' | \
  jq '.claims[0] | {
    r1_providers: .researchers[0].lane_config.providers,
    r2_providers: .researchers[1].lane_config.providers,
    r1_queries: .researchers[0].lane_config.queries_first3.A,
    r2_queries: .researchers[1].lane_config.queries_first3.A,
    r1_evidence_count: .researchers[0].evidence.arm_A | length,
    r2_evidence_count: .researchers[1].evidence.arm_A | length
  }'
# Should show different provider orders and query orders

# Performance test
echo "Testing dual-researcher performance..."
time curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' > /dev/null
# Expect: ~2x time of single researcher (running sequentially)

# Memory leak test with dual researchers
./test_memory_leak.sh
# Should still show stable memory (request-scoped caches)

echo "âœ“ PASS: Week 2 complete - Dual researchers working"
```

**Deliverables:**
- Dual researchers (R1, R2) working with diversification
- Consensus computed and reasonable
- Manifest generated with replay_id
- Telemetry tracked per lane
- Deterministic results
- No memory leaks

---

### Week 3: Cleanup (Days 12-14) - 16-22 hours

#### **Day 12: Archive Old Wrapper Files (4-6 hours)**

**Goal:** Verify no imports of old wrappers, then archive wrapper files for reference

**Tasks:**
1. **Verify no remaining imports** of wrapper files (critical step):
   ```bash
   # Search for any imports of old wrapper files
   grep -r "p19_wrapper\|p20_wrapper\|p21_wrapper\|p22_ingest\|p23_semantic\|p24_semantic_frames\|p25_semantic_aggregate\|p26_dual_researchers\|p27_consensus\|p28_diversify\|p29_diversify_controls" . --include="*.py"
   # Should return NO RESULTS (if results found, update those imports first)
   ```

2. **Create archive directory** for old wrappers:
   ```bash
   mkdir -p MONKEY_PATCH_ARCHIVE/wrappers
   mkdir -p MONKEY_PATCH_ARCHIVE/wrappers/gather
   mkdir -p MONKEY_PATCH_ARCHIVE/wrappers/content
   ```

3. **Move wrapper files to archive** (not delete - keep in git for reference):
   ```bash
   # Move wrapper files to archive
   git mv intelligence/gather/p19_wrapper.py MONKEY_PATCH_ARCHIVE/wrappers/gather/
   git mv intelligence/content/p20_wrapper.py MONKEY_PATCH_ARCHIVE/wrappers/content/
   git mv intelligence/content/p21_wrapper.py MONKEY_PATCH_ARCHIVE/wrappers/content/
   git mv intelligence/content/p22_ingest.py MONKEY_PATCH_ARCHIVE/wrappers/content/
   git mv intelligence/content/p23_semantic.py MONKEY_PATCH_ARCHIVE/wrappers/content/
   git mv intelligence/content/p24_semantic_frames.py MONKEY_PATCH_ARCHIVE/wrappers/content/
   git mv intelligence/content/p25_semantic_aggregate.py MONKEY_PATCH_ARCHIVE/wrappers/content/
   git mv intelligence/content/p26_dual_researchers.py MONKEY_PATCH_ARCHIVE/wrappers/content/
   git mv intelligence/content/p27_consensus.py MONKEY_PATCH_ARCHIVE/wrappers/content/
   git mv intelligence/content/p28_diversify.py MONKEY_PATCH_ARCHIVE/wrappers/content/
   git mv intelligence/content/p29_diversify_controls.py MONKEY_PATCH_ARCHIVE/wrappers/content/
   git mv sitecustomize.py MONKEY_PATCH_ARCHIVE/
   ```

4. **Verify no monkey patches remain** in active codebase:
   ```bash
   grep -r "setattr.*getattr\|_ORIG.*=.*getattr\|_wrap.*_ORIG" intelligence/ --include="*.py"
   # Should return NO RESULTS
   ```

5. **Create archive README**:
   ```bash
   cat > MONKEY_PATCH_ARCHIVE/README.md <<'EOF'
   # Monkey Patch Archive

   This directory contains the original monkey-patched wrapper files (P19-P29)
   that were replaced during the clean integration (2025-10-09).

   These files are preserved for:
   - Historical reference
   - Rollback capability if needed
   - Understanding original implementation

   **Do not import these files** - they are archived and inactive.
   The clean implementations are now in:
   - intelligence/gather/counter_frames.py (P19)
   - intelligence/content/fetch_enrichment.py (P22)
   - intelligence/orchestration/dual_lane.py (P26)
   - intelligence/consensus/dual_lane.py (P27)
   - intelligence/planning/diversify.py (P28)
   - intelligence/telemetry/collect.py (P29)
   - P20, P21, P23, P24, P25 already had clean modules
   EOF
   ```

**Why Archive Instead of Delete:**
- Preserves git history and original implementations
- Provides rollback option if critical issues found
- Serves as reference for understanding original logic
- Can compare old vs new implementations
- Satisfies audit/compliance requirements

**Verification:**
```bash
# Confirm wrappers archived
ls MONKEY_PATCH_ARCHIVE/wrappers/content/
# Should show 10 wrapper files

ls MONKEY_PATCH_ARCHIVE/wrappers/gather/
# Should show p19_wrapper.py

# Confirm sitecustomize archived
ls MONKEY_PATCH_ARCHIVE/sitecustomize.py
# Should exist

echo "âœ“ All wrappers archived"
```

**Testing:**
```bash
# Verify system still works
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' > test_no_wrappers.json

# Compare to previous test
diff <(jq -S '.claims[0].consensus' test_dual_researchers.json) \
     <(jq -S '.claims[0].consensus' test_no_wrappers.json)
# Should be identical

echo "âœ“ PASS: System works without wrappers"
```

**Checkpoint:** All wrappers deleted, system still working

---

#### **Day 13: Full System Testing (6-8 hours)**

**Goal:** Comprehensive testing of clean pipeline

**Tasks:**
1. Run full test suite
2. Verify test_s2p30r_audit.py passes
3. Test multiple claim types
4. Test error handling (missing providers, network errors, etc.)
5. Load testing
6. Memory leak verification
7. Performance benchmarks

**Testing:**
```bash
# Run test suite
pytest tests/ -v

# Specifically test audit (no wrappers)
pytest tests/test_s2p30r_audit.py -v
# Should PASS: api.run_preview is core.run_preview

# Test various claim types
cat > test_claims.json <<'EOF'
[
  {"text": "Water is wet"},
  {"text": "Austin budget increased 8%"},
  {"text": "The sky is green"},
  {"text": "Ambiguous controversial claim"},
  {"text": "Biden won 2020 election"},
  {"text": "Climate change is real"}
]
EOF

for claim in $(jq -r '.[] | @json' test_claims.json); do
  echo "Testing: $claim"
  curl -X POST http://localhost:8000/analyses/preview \
    -H "Content-Type: application/json" \
    -d "$claim" | \
    jq '.claims[0] | {
      text,
      consensus_label: .consensus.label,
      consensus_confidence: .consensus.confidence,
      r1_label: .researchers[0].verdict.label,
      r2_label: .researchers[1].verdict.label,
      agreement: (.researchers[0].verdict.label == .researchers[1].verdict.label)
    }'
done

# Test error handling - missing provider keys
unset GOOGLE_CSE_API_KEY
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Test claim"}' | \
  jq '.claims[0].researchers[0].lane_config.providers'
# Should show only available providers (not google)

# Load test
echo "Running load test..."
ab -n 100 -c 10 -T application/json -p <(echo '{"text":"Austin budget"}') \
  http://localhost:8000/analyses/preview
# Check for errors, response times

# Memory leak final check
./test_memory_leak.sh
ps aux | grep "uvicorn\|gunicorn" | grep -v grep
# Memory should be stable after 100 requests

# Performance comparison
echo "Performance before (with wrappers):" > performance_comparison.txt
# (If you have baseline timing from before)
echo "Performance after (clean):" >> performance_comparison.txt
time curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' >> performance_comparison.txt 2>&1

echo "âœ“ PASS: Full system testing complete"
```

**Checkpoint:** All tests passing, no wrappers detected, stable performance

---

#### **Day 14: Documentation & Handoff (6-8 hours)**

**Goal:** Document clean architecture and create maintenance guide

**Tasks:**
1. Update architecture documentation
2. Document module contracts
3. Create troubleshooting guide
4. Write deployment notes
5. Document rollback procedure (if needed)
6. Update README with new module structure

**Deliverables:**

**1. Architecture Documentation** (create `docs/CLEAN_ARCHITECTURE.md`):
```markdown
# ROGRv2 Clean Architecture (Post P19-P29 Integration)

## Overview
Clean pipeline P1-P29 with no monkey patches. All modules independently maintainable.

## Module Structure
- P1-P18: Core pipeline (gather, strategy, analysis)
- P19: Counter-frames for Arm B
- P20-P25: Item enrichment (findings, full-read, semantic, frames, aggregation)
- P26: Dual-researcher orchestration
- P27: Consensus mechanism
- P28: Lane diversification
- P29: Telemetry and reproducibility

## Execution Flow
1. Create claim and base plan
2. Diversify plan for R1 and R2 (P28)
3. Run R1: gather (P19) â†’ enrich (P20-P25) â†’ verdict
4. Run R2: gather (P19) â†’ enrich (P20-P25) â†’ verdict
5. Compute consensus (P27)
6. Generate manifest (P29)

## Module Contracts
[Include detailed contracts from PART 2]

## Testing
[Include test commands for each module]
```

**2. Troubleshooting Guide** (create `docs/TROUBLESHOOTING.md`):
```markdown
# Troubleshooting Guide

## No Results Returned
- Check provider API keys are set
- Verify network connectivity
- Check logs for errors in gather phase

## Consensus Always "Mixed"
- R1 and R2 disagreeing on most claims
- Check diversification is working (different provider orders)
- Verify evidence quality (enough candidates gathered)

## Memory Leak
- Verify sitecustomize.py deleted
- Check no module-level cache globals
- Monitor memory over 100+ requests

## Performance Degradation
- Dual researchers = 2x API calls (expected)
- Check provider rate limits
- Consider parallel R1/R2 execution (future enhancement)

## Determinism Issues
- Same claim should produce same replay_id
- Check diversification seed generation
- Verify no randomness without seed
```

**3. Deployment Notes** (create `docs/DEPLOYMENT.md`):
```markdown
# Deployment Notes

## Environment Variables Required
- GOOGLE_CSE_API_KEY (optional)
- GOOGLE_CSE_ENGINE_ID (optional)
- BRAVE_API_KEY (optional)
- BING_API_KEY (optional)
- At least one provider required

## Configuration
- No sitecustomize.py needed
- No wrapper imports needed
- Clean module imports only

## Monitoring
- Track memory usage (should be stable)
- Track response times (expect ~2x vs single researcher)
- Track consensus agreement rate (R1 vs R2)
- Track replay_id usage (reproducibility)

## Rollback Procedure
If issues arise:
1. Restore wrappers from git
2. Restore sitecustomize.py
3. Restart service
4. Wrappers auto-load
Note: This should not be necessary if testing was thorough
```

**4. Update README** (modify `README.md`):
```markdown
## Architecture

ROGRv2 uses a clean, modular pipeline (P1-P29) with no monkey patches:

### Modules
- **P19**: Counter-frame query generation for challenge arm
- **P20**: Findings attachment (grade, stance, rationale)
- **P21**: Full-read evaluation with credibility scoring
- **P22**: Content enrichment and fetch management
- **P23**: Semantic reading (multiple findings extraction)
- **P24**: Semantic frame extraction (entity/action/quantity)
- **P25**: Arm aggregation and verdict computation
- **P26**: Dual-researcher orchestration (R1, R2)
- **P27**: Consensus mechanism (combine R1 + R2)
- **P28**: Lane diversification (different provider/query orders)
- **P29**: Telemetry and reproducibility manifest

### Design Principles
- **Module Independence**: Each module is independently maintainable
- **Clean Contracts**: Clear input/output contracts between modules
- **No Monkey Patches**: Direct function calls, no setattr/getattr
- **Request-Scoped State**: No module-level globals, no memory leaks
- **Deterministic**: Same claim â†’ same results (via replay_id)

### Testing
Each module has standalone and live integration tests.
See `docs/TESTING.md` for details.
```

**5. Create Migration Log** (create `docs/MIGRATION_LOG.md`):
```markdown
# Migration Log - Monkey Patch Removal

## Date: 2025-10-09

## Changes Made
1. Extracted P19 logic â†’ intelligence/gather/counter_frames.py
2. Extracted P22 logic â†’ intelligence/content/fetch_enrichment.py
3. Extracted P26 logic â†’ intelligence/orchestration/dual_lane.py
4. Extracted P27 logic â†’ intelligence/consensus/dual_lane.py
5. Extracted P28 logic â†’ intelligence/planning/diversify.py
6. Extracted P29 logic â†’ intelligence/telemetry/collect.py
7. Wired P20-P25 (already had clean modules)
8. Deleted all wrapper files (p19-p29_wrapper.py)
9. Deleted sitecustomize.py
10. Fixed memory leaks (P22, fetch_sync.py caches)

## Testing Results
- All standalone module tests: PASS
- All live integration tests: PASS
- test_s2p30r_audit.py: PASS (no wrappers detected)
- Memory leak test (100 requests): PASS (stable memory)
- Consensus agreement rate: [XX]%
- Average response time: [XX]ms

## Performance Impact
- Single researcher (P1-P25): [baseline]ms
- Dual researcher (P1-P29): [XX]ms (~2x expected)
- Memory usage: Stable (no growth over 100 requests)

## Known Issues
[None or list any minor issues]

## Follow-up Items
- [ ] Consider parallel R1/R2 execution (reduce latency)
- [ ] Add configurable diversification parameters
- [ ] Optimize provider call batching
```

**Testing:**
```bash
# Verify documentation exists
ls docs/CLEAN_ARCHITECTURE.md
ls docs/TROUBLESHOOTING.md
ls docs/DEPLOYMENT.md
ls docs/MIGRATION_LOG.md

# Verify README updated
grep "P19.*Counter-frame" README.md

echo "âœ“ PASS: Documentation complete"
echo "âœ“ PASS: Week 3 complete - Clean integration done"
```

**Checkpoint:** Full documentation, ready for production

---

## PART 4: ROLLBACK PROCEDURES

### Emergency Rollback (< 5 minutes)

If critical issues discovered in production:

```bash
# Step 1: Checkout previous commit (before wrapper removal)
git log --oneline | head -5
git checkout [commit-hash-before-cleanup]  # From Day 12

# Step 2: Restore wrappers and sitecustomize.py
git checkout HEAD -- intelligence/gather/p19_wrapper.py
git checkout HEAD -- intelligence/content/p20_wrapper.py
git checkout HEAD -- intelligence/content/p21_wrapper.py
git checkout HEAD -- intelligence/content/p22_ingest.py
git checkout HEAD -- intelligence/content/p23_semantic.py
git checkout HEAD -- intelligence/content/p24_semantic_frames.py
git checkout HEAD -- intelligence/content/p25_semantic_aggregate.py
git checkout HEAD -- intelligence/content/p26_dual_researchers.py
git checkout HEAD -- intelligence/content/p27_consensus.py
git checkout HEAD -- intelligence/content/p28_diversify.py
git checkout HEAD -- intelligence/content/p29_diversify_controls.py
git checkout HEAD -- sitecustomize.py

# Step 3: Restart service
systemctl restart rogrv2
# or
pkill -f "uvicorn\|gunicorn" && ./start.sh

# Step 4: Verify wrappers loaded
curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Test"}' | jq '.claims[0]' > /dev/null

echo "âœ“ Rollback complete - wrappers restored"
```

### Partial Rollback Options

**Option 1: Keep P19-P25 clean, rollback P26-P29:**
```bash
# Keep clean item enrichment, restore dual-researcher wrappers
git checkout HEAD -- intelligence/content/p26_dual_researchers.py
git checkout HEAD -- intelligence/content/p27_consensus.py
git checkout HEAD -- intelligence/content/p28_diversify.py
git checkout HEAD -- intelligence/content/p29_diversify_controls.py

# Modify run.py to not call dual-researcher orchestration
# Fall back to single researcher with P19-P25 clean modules
```

**Option 2: Keep clean modules, restore sitecustomize.py:**
```bash
# Restore sitecustomize but wrappers now import clean modules
git checkout HEAD -- sitecustomize.py
# Update sitecustomize to only load critical wrappers (P20, P22)
```

### Gradual Rollback Testing

Before full rollback, test specific components:

```bash
# Test only P19-P25 without dual researchers
# Modify run.py to skip P26-P29 calls

# Test with only one researcher (R1)
# Comment out R2 execution in run_dual_researchers()

# Test with different provider combinations
# Verify no issues with specific providers
```

---

## PART 5: SUCCESS METRICS

### Pre-Implementation Baseline

**Capture before starting Day 1:**

```bash
# Memory usage baseline
ps aux | grep "uvicorn\|gunicorn" | grep -v grep > baseline_memory.txt

# Performance baseline
time curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' > baseline_response.json 2> baseline_time.txt

# Output structure baseline
jq '.claims[0] | keys' baseline_response.json > baseline_keys.txt

# Wrapper detection baseline
pytest tests/test_s2p30r_audit.py -v > baseline_audit.txt 2>&1
# Should FAIL: wrappers detected
```

### Post-Implementation Metrics

**Measure after Day 14:**

```bash
# Memory usage after
ps aux | grep "uvicorn\|gunicorn" | grep -v grep > final_memory.txt
diff baseline_memory.txt final_memory.txt

# Performance after
time curl -X POST http://localhost:8000/analyses/preview \
  -H "Content-Type: application/json" \
  -d '{"text":"Austin budget increased 8%"}' > final_response.json 2> final_time.txt

# Compare times
echo "Baseline:" && cat baseline_time.txt
echo "Final:" && cat final_time.txt

# Output structure after
jq '.claims[0] | keys' final_response.json > final_keys.txt
comm -3 baseline_keys.txt final_keys.txt
# Should show added keys: consensus, researchers, run_manifest

# Wrapper detection after
pytest tests/test_s2p30r_audit.py -v > final_audit.txt 2>&1
# Should PASS: no wrappers detected
```

### Key Performance Indicators

| Metric | Baseline | Target | Actual |
|--------|----------|--------|--------|
| Memory leak | Growing | Stable | [measure] |
| Response time (single) | [XX]ms | <[XX*1.1]ms | [measure] |
| Response time (dual) | N/A | ~2x single | [measure] |
| Wrapper count | 11 | 0 | [verify] |
| Test pass rate | [XX]% | 100% | [measure] |
| Consensus agreement rate | N/A | [XX]% | [measure] |
| Module independence | 0 | 11 | [verify] |

### Quality Metrics

```bash
# Code quality
grep -r "setattr\|getattr.*_ORIG\|monkey" intelligence/ --include="*.py" | wc -l
# Should be 0

# Module-level globals (cache leaks)
grep -r "^[A-Z_]*CACHE.*=.*\{\}" intelligence/ --include="*.py" | wc -l
# Should be 0

# Import cleanliness
grep -r "from.*wrapper import" . --include="*.py" | wc -l
# Should be 0

# Test coverage
pytest --cov=intelligence --cov-report=term
# Should show high coverage for new modules
```

---

## PART 6: RISK MITIGATION

### High-Risk Areas

**1. P26-P29 Integration (Days 9-11)**
- **Risk:** Never run in production before
- **Mitigation:**
  - Extensive standalone testing with mocks (Day 9)
  - Gradual integration (Day 10)
  - Full validation (Day 11)
  - Feature flag for rollback
- **Contingency:** Can rollback to single researcher (P19-P25 only)

**2. Memory Leak Fix (Day 1)**
- **Risk:** Request-scoped cache might have edge cases
- **Mitigation:**
  - Test with 100+ requests
  - Monitor memory continuously
  - Validate cache clearing
- **Contingency:** Can use LRU cache with maxsize instead

**3. Execution Order Change (Day 3)**
- **Risk:** P22 before P20 might affect quality
- **Mitigation:**
  - A/B test both orders
  - Compare outputs
  - Measure quality metrics
- **Contingency:** Can restore old order if quality degrades

**4. Wrapper Removal (Day 12)**
- **Risk:** Unexpected import dependencies
- **Mitigation:**
  - Search for all wrapper imports first
  - Test immediately after deletion
  - Keep git history clean
- **Contingency:** Quick git restore

### Medium-Risk Areas

**1. P28 Diversification (Day 7)**
- **Risk:** ContextVar removal might break async behavior
- **Mitigation:**
  - Pass lane_id explicitly
  - Test async execution
  - Verify determinism
- **Contingency:** Keep ContextVar if needed (isolated to P28)

**2. Performance Impact (Day 11)**
- **Risk:** 2x API calls might cause timeout/rate limits
- **Mitigation:**
  - Test with various claims
  - Monitor provider responses
  - Validate sequential execution
- **Contingency:** Can parallelize R1/R2 if sequential too slow

**3. Provider Availability (Day 10)**
- **Risk:** What if only one provider available?
- **Mitigation:**
  - Test with single provider
  - Verify graceful degradation
  - Diversification still uses query order
- **Contingency:** Falls back to query-order-only diversification

### Low-Risk Areas

**1. P20-P25 Wiring (Days 3-4)**
- **Risk:** Minimal (already have clean modules)
- **Mitigation:** Direct function calls, already tested
- **Contingency:** Trivial to unwire

**2. P27 Consensus (Day 6)**
- **Risk:** Minimal (pure function, well-defined logic)
- **Mitigation:** Extensive standalone tests
- **Contingency:** Can use simple average if consensus fails

**3. P29 Telemetry (Day 8)**
- **Risk:** Minimal (additive only, non-critical)
- **Mitigation:** Optional parameter, graceful failures
- **Contingency:** Can skip telemetry if issues

---

## PART 7: TESTING CHECKLIST

### Daily Testing Checklist

Use this checklist at end of each day:

**Day 1: P22 Content Enrichment**
- [ ] Standalone test passes (enrich_items_with_content)
- [ ] No module-level cache globals
- [ ] fetch_sync.py cache fixed
- [ ] Module imports successfully

**Day 2: P19 Counter-Frames**
- [ ] Standalone test passes (generate_counter_frame_queries)
- [ ] Coverage metrics computed correctly
- [ ] Module imports successfully
- [ ] No dependencies on wrappers

**Day 3: Wire P19, P20-P22**
- [ ] P19 counter-frames added to Arm B queries
- [ ] P22 content enrichment working
- [ ] P20 findings attached
- [ ] Live integration test passes
- [ ] Coverage tracking working

**Day 4: Wire P21, P23-P25**
- [ ] P21 full-read working
- [ ] P23 semantic findings extracted
- [ ] P24 frames extracted
- [ ] P25 verdict aggregated
- [ ] Live integration test passes

**Day 5: Validation**
- [ ] Memory leak test passes (100 requests, stable memory)
- [ ] Performance acceptable
- [ ] All item enrichment working
- [ ] No errors in logs

**Day 6: Extract P27**
- [ ] Standalone test passes (compute_consensus)
- [ ] Agreement case works
- [ ] Disagreement case works
- [ ] Module imports successfully

**Day 7: Extract P28**
- [ ] Standalone test passes (diversify_plan_for_lane)
- [ ] R1 and R2 get different orders
- [ ] Deterministic (same input â†’ same output)
- [ ] Module imports successfully

**Day 8: Extract P29**
- [ ] Standalone test passes (LaneTelemetry)
- [ ] Manifest generation works
- [ ] Replay_id deterministic
- [ ] Module imports successfully

**Day 9: Extract P26 Part 1**
- [ ] Standalone test with mocks passes
- [ ] Returns 2 researchers
- [ ] Backward compatibility preserved
- [ ] Module imports successfully

**Day 10: Extract P26 Part 2 & Integration**
- [ ] Dual researchers working
- [ ] R1 and R2 produce different results
- [ ] Consensus computed
- [ ] Manifest generated
- [ ] Live integration test passes

**Day 11: Validation**
- [ ] Dual researcher test passes
- [ ] Determinism verified
- [ ] Performance acceptable
- [ ] Memory stable
- [ ] Agreement/disagreement cases work

**Day 12: Remove Wrappers**
- [ ] All 11 wrappers deleted
- [ ] sitecustomize.py deleted
- [ ] No wrapper imports remain
- [ ] No setattr patterns remain
- [ ] System still works

**Day 13: Full Testing**
- [ ] test_s2p30r_audit.py PASSES
- [ ] All test suite passes
- [ ] Multiple claim types work
- [ ] Error handling works
- [ ] Load test passes
- [ ] Memory stable

**Day 14: Documentation**
- [ ] Architecture documentation complete
- [ ] Troubleshooting guide complete
- [ ] Deployment notes complete
- [ ] README updated
- [ ] Migration log complete

---

## PART 8: FINAL VALIDATION

### Pre-Production Checklist

Before deploying to production:

**Code Quality:**
- [ ] No setattr/getattr monkey patches in codebase
- [ ] No module-level cache globals
- [ ] No wrapper imports
- [ ] All modules have clean contracts
- [ ] All modules independently testable

**Testing:**
- [ ] All standalone module tests pass
- [ ] All live integration tests pass
- [ ] test_s2p30r_audit.py passes (no wrappers)
- [ ] Memory leak test passes (100+ requests)
- [ ] Load test passes (100 concurrent)
- [ ] Multiple claim types tested
- [ ] Error handling verified

**Functionality:**
- [ ] P19 counter-frames working
- [ ] P20-P25 item enrichment working
- [ ] P26 dual researchers working
- [ ] P27 consensus reasonable
- [ ] P28 diversification working (different R1/R2)
- [ ] P29 telemetry and manifest generated
- [ ] Backward compatibility preserved

**Performance:**
- [ ] Response time acceptable (~2x single researcher)
- [ ] Memory usage stable
- [ ] No memory leaks
- [ ] Provider rate limits respected

**Documentation:**
- [ ] Architecture documented
- [ ] Module contracts documented
- [ ] Testing procedures documented
- [ ] Troubleshooting guide complete
- [ ] Deployment notes complete
- [ ] Rollback procedure documented

**Rollback Readiness:**
- [ ] Rollback procedure tested
- [ ] Git history clean
- [ ] Can restore wrappers in < 5 minutes
- [ ] Team trained on rollback

---

## CONCLUSION

This plan provides a complete, executable roadmap to remove all monkey patches from P19-P29 and integrate them cleanly into the production pipeline.

**Key Principles:**
1. **Module Independence** - Each P19-P29 stays separate, independently maintainable
2. **Testing at Every Stage** - Both standalone and live integration tests required
3. **Gradual Integration** - Week 1 item enrichment, Week 2 dual researchers, Week 3 cleanup
4. **Risk Mitigation** - Extensive testing, rollback procedures, gradual rollout
5. **Clean Contracts** - Clear input/output for each module

**Timeline:** 12-14 days (96-112 hours)

**Confidence:** HIGH - based on actual codebase investigation, realistic estimates, and thorough testing strategy

**Next Steps:**
1. Review this plan with team
2. Set up development environment
3. Capture baseline metrics (memory, performance, output structure)
4. Begin Day 1: P22 content enrichment extraction

**Questions/Issues:** Escalate immediately if any step takes significantly longer than estimated or if unexpected dependencies discovered.