P19-P29 Module Status Investigation Report

  Executive Summary

  All 11 packet files (P19-P29) exist and are production code. However, only 2 packets load in 
  production via sitecustomize.py (P20, P22). The remaining 9 packets (P19, P21, P23-P29) are
  installed but not loading, creating a critical gap between what exists and what runs. The
  monkey-patching pattern is pervasive across all packets, with P22 containing a confirmed memory 
  leak (_FETCH_CACHE grows unbounded). Clean modules exist for 5 packets and work standalone; the
  remaining 6 have logic embedded in wrappers.

  File Inventory

  | Packet | Wrapper File                                   | Clean Module
      | Logic Location       |
  |--------|------------------------------------------------|-------------------------------------
  ----|----------------------|
  | P19    | intelligence/gather/p19_wrapper.py             | None
      | Embedded (215 lines) |
  | P20    | intelligence/content/p20_wrapper.py            | intelligence/content/grade.py
      | Separated            |
  | P21    | intelligence/content/p21_wrapper.py            | intelligence/content/fullread.py
      | Separated            |
  | P22    | intelligence/content/p22_ingest.py             | None
      | Embedded (267 lines) |
  | P23    | intelligence/content/p23_semantic.py           |
  intelligence/content/semantic_read.py   | Separated            |
  | P24    | intelligence/content/p24_semantic_frames.py    |
  intelligence/content/semantic_frames.py | Separated            |
  | P25    | intelligence/content/p25_semantic_aggregate.py |
  intelligence/content/p25_aggregate.py   | Separated            |
  | P26    | intelligence/content/p26_dual_researchers.py   | None
      | Embedded (115 lines) |
  | P27    | intelligence/content/p27_consensus.py          | None
      | Embedded (164 lines) |
  | P28    | intelligence/content/p28_diversify.py          | None
      | Embedded (277 lines) |
  | P29    | intelligence/content/p29_diversify_controls.py | None
      | Embedded (288 lines) |

  Production vs Test Split

  Production (sitecustomize.py)

  _try("intelligence.content.p20_wrapper")
  _try("intelligence.content.p22_ingest")
  Only P20 and P22 are loaded at import time in production.

  Not Loaded in Production

  P19, P21, P23, P24, P25, P26, P27, P28, P29 - these 9 packets exist but are never imported by
  sitecustomize.py.

  Test Files

  - tests/test_s2p30r_audit.py exists but does not import any P19-P29 packets
  - Test checks that wrappers are not active (expects api.run_preview is core.run_preview)

  Critical Finding

  The fact that packets appear test-only is itself a problem - all packets are production code but
   some are orphaned due to missing imports.

  Standalone Import Test Results

  All clean modules work standalone without wrappers loaded:

  ✓ intelligence.content.grade               (P20 clean module)
  ✓ intelligence.content.fullread            (P21 clean module)
  ✓ intelligence.content.semantic_read       (P23 clean module)
  ✓ intelligence.content.semantic_frames     (P24 clean module)
  ✓ intelligence.content.p25_aggregate       (P25 clean module)

  Confidence: HIGH - tested imports succeed without errors.

  Per-Packet Analysis

  P19: Arm-B Counter-Frame Queries + Coverage Tracking

  File: intelligence/gather/p19_wrapper.py (215 lines)Clean Module: NoneLogic: Embedded (challenge
   query generation, anchor extraction, counter-frames)Target:
  intelligence.gather.online.run_planWhat it does:
  - Wraps online.run_plan with setattr(online, "run_plan", _p19_run_plan)
  - Adds deterministic counter-frame queries for arm_B (numeric_dispute, denominator_shift,
  timing_change, authority_conflict, methodology)
  - Extracts anchors (entities, numbers, topic) from claim text
  - Tracks per-arm coverage: frames_attempted, providers_used, queries_issued, candidates_fetched
  - Reorders candidates in-arm by tiny anchor score
  - Returns original shape + coverage_by_arm

  Dependencies:
  - intelligence.gather.online module
  - Regex patterns for entity/number extraction (module-level constants)

  Loaded in: NOT LOADED (missing from sitecustomize.py)Global State: Module-level regex compiles
  (_WORD, _PERCENT_WORDS) and constant lists (_COUNTER_FRAMES) - safe (immutable)

  ---
  P20: Deterministic Reading & Grading (Finding Cards)

  File: intelligence/content/p20_wrapper.py (228 lines)Clean Module: intelligence/content/grade.py
   (134 lines)Logic: Separated (grading logic in clean module, wrapping in wrapper)Target:
  intelligence.gather.pipeline.build_evidence_for_claimWhat it does:
  - Wraps pipeline.build_evidence_for_claim at import via _install()
  - For each evidence item (arm_A/arm_B), calls attach_finding_to_item(claim_text, arm_key, item)
  - Attaches Finding Card: grade (0-10), stance, rationale[], matched_spans[], similarity, signals
  - Uses heuristics: entity match, number match, year match, similarity, stance, modality penalty
  - Handles both evidence[arm_A] = list and evidence[arm_A] = {"candidates": list} shapes
  - Propagates wrapper to other modules via sys.modules iteration (line 217-224)

  Dependencies:
  - intelligence.content.grade.attach_finding_to_item (clean function)
  - intelligence.content.extract_facts (for entity/number/year extraction)
  - Async-aware (detects coroutine and wraps appropriately)

  Loaded in: PRODUCTION (sitecustomize.py line 19)Global State: None in wrapper or clean module

  ---
  P21: Full-Read Evaluation

  File: intelligence/content/p21_wrapper.py (145 lines)Clean Module:
  intelligence/content/fullread.py (200 lines)Logic: Separated (evaluation logic in clean
  module)Target: intelligence.gather.pipeline.build_evidence_for_claimWhat it does:
  - Wraps pipeline.build_evidence_for_claim at import via _install()
  - For each evidence item, calls evaluate_full_evidence(claim_text, item)
  - Attaches: grade_full (0-10), stance_full, signals_full, credibility
  - Slides 4-sentence windows over content (up to 80 sentences, 12KB limit)
  - Computes jaccard trigrams, entity overlap, percent hits, year hits
  - Stance detection via regex (support/challenge/mixed/unrelated)
  - Credibility from URL structure (HTTPS, .gov/.edu, authz words)
  - Propagates wrapper to other modules via sys.modules iteration (line 134-141)

  Dependencies:
  - intelligence.content.fullread.evaluate_full_evidence (clean function)
  - Regex patterns for percent/year/negation/support/challenge

  Loaded in: NOT LOADED (missing from sitecustomize.py)Global State: Clean module has regex
  compiles at module level - safe (immutable)

  ---
  P22: Full-Text Ingestion & Integrity

  File: intelligence/content/p22_ingest.py (267 lines)Clean Module: NoneLogic: Embedded (fetch
  caching, enrichment, wrapping all in one file)Target: intelligence.content.fetch.fetch_text +
  intelligence.pipeline.run.run_preview + api.analysesWhat it does:
  - Wraps fetch_text to cache full-text by URL (line 119-168)
  - Wraps run_preview or build_evidence_for_claim to enrich evidence items (line 190-237)
  - Collects missing URLs and performs fallback async fetch (line 65-98)
  - Attaches: content, content_hash (sha256), coverage (full/partial/snippet_only)
  - Rebinds api.analyses module globals so preview route uses wrapped functions (line 239-256)

  Dependencies:
  - intelligence.content.fetch module
  - intelligence.pipeline.run module
  - api.analyses module

  Loaded in: PRODUCTION (sitecustomize.py line 21)Global State: CRITICAL MEMORY LEAK at line 29:
  _FETCH_CACHE: Dict[str, str] = {}
  This unbounded dictionary grows with every unique URL fetched and is never cleaned. Each entry
  stores full-text content (potentially megabytes per URL).

  ---
  P23: Deterministic Semantic Reading

  File: intelligence/content/p23_semantic.py (94 lines)Clean Module:
  intelligence/content/semantic_read.py (194 lines)Logic: Separated (analysis in clean
  module)Target: intelligence.pipeline.run.run_previewWhat it does:
  - Wraps run_preview at import via _install()
  - For each evidence item (arm_A/arm_B), calls analyze_item(claim_text, item)
  - Attaches: findings[] (quote, offsets, stance, signals, score), item_grade (0-1), grade_label
  - Slides 3-sentence windows over content (up to 500 sentences)
  - Detects entity/number/year hits, computes trigram jaccard
  - Imports P22 first to ensure it runs after ingestion (line 54-58)
  - Rebinds api.analyses.run_preview to wrapped version (line 77-85)

  Dependencies:
  - intelligence.content.semantic_read.analyze_item (clean function)
  - Explicitly imports P22 first

  Loaded in: NOT LOADED (missing from sitecustomize.py)Global State: Clean module has
  regex/constant sets at module level - safe (immutable)

  ---
  P24: Deterministic Semantic Frames

  File: intelligence/content/p24_semantic_frames.py (106 lines)Clean Module:
  intelligence/content/semantic_frames.py (278 lines)Logic: Separated (frame analysis in clean
  module)Target: intelligence.pipeline.run.run_previewWhat it does:
  - Wraps run_preview at import via _install()
  - For each evidence item, calls analyze_frames(claim_text, content, window=3)
  - Attaches: item_frame {entity[], action, quantity[], year[], scope}, frame_matches[],
  frame_confidence
  - Extracts claim frame (entity/action/quantity/year/scope) and matches against content windows
  - Detects budget context, increase/decrease actions, negation
  - Determines entailment/contradiction via rule-based logic
  - Imports P22 and P23 first to ensure proper ordering (line 64-71)
  - Rebinds api.analyses.run_preview to wrapped version (line 89-97)

  Dependencies:
  - intelligence.content.semantic_frames.analyze_frames (clean function)
  - Explicitly imports P22, P23 first

  Loaded in: NOT LOADED (missing from sitecustomize.py)Global State: Clean module has lexicon sets
   (BUDGET_CONTEXT, INC_VERBS, DEC_VERBS, NEG_WORDS) - safe (immutable)

  ---
  P25: Arm Aggregation & Verdict

  File: intelligence/content/p25_semantic_aggregate.py (90 lines)Clean Module:
  intelligence/content/p25_aggregate.py (103 lines)Logic: Separated (aggregation logic in clean
  module)Target: intelligence.pipeline.run.run_previewWhat it does:
  - Wraps run_preview at import via _install()
  - For each claim, calls aggregate_verdict(claim_text, arm_A_items, arm_B_items, delta=0.15)
  - Computes per-item strength from frame_matches, item_grade, coverage
  - Aggregates arm strengths with diminishing returns (top-k=4)
  - Determines verdict label: supports/challenges/mixed/insufficient
  - Updates claims[i].verdict with: label, confidence, arm_strength
  - Imports P22/P23/P24 first to ensure proper ordering (line 53-58)
  - Rebinds api.analyses.run_preview to wrapped version (line 72-81)

  Dependencies:
  - intelligence.content.p25_aggregate.aggregate_verdict (clean function)
  - Explicitly imports P22, P23, P24 first

  Loaded in: NOT LOADED (missing from sitecustomize.py)Global State: None

  ---
  P26: Dual-Researcher Orchestrator

  File: intelligence/content/p26_dual_researchers.py (115 lines)Clean Module: NoneLogic: Embedded
  (orchestration logic in wrapper)Target: intelligence.pipeline.run.run_previewWhat it does:
  - Wraps run_preview at import via _install()
  - Runs the existing pipeline twice (R1, R2) sequentially (line 63-70)
  - Merges results: base output is R1, attaches researchers[] array with R1 + R2 per claim
  - Each researcher entry: {id: "R1"/"R2", verdict, evidence}
  - Preserves top-level verdict from R1 for backward compatibility
  - Imports P22/P23/P24/P25 first to ensure full pipeline runs in each lane (line 73-83)
  - Rebinds api.analyses.run_preview to wrapped version (line 98-106)

  Dependencies:
  - Explicitly imports P22, P23, P24, P25 first
  - Calls original run_preview twice

  Loaded in: NOT LOADED (missing from sitecustomize.py)Global State: None

  ---
  P27: Deterministic Consensus

  File: intelligence/content/p27_consensus.py (164 lines)Clean Module: NoneLogic: Embedded
  (consensus logic in wrapper)Target: intelligence.pipeline.run.run_previewWhat it does:
  - Wraps run_preview at import via _install()
  - For each claim, reads researchers[0] (R1) and researchers[1] (R2) verdicts
  - Computes consensus from dual lanes:
    - Agreement: adopt label, add consistency bonus (≤0.95 confidence cap)
    - Disagreement: check aggregate strengths (gap ≥ 0.20), pick side or mixed, apply penalty
  - Attaches: consensus {label, confidence, rationale, agreement}
  - Fallback: if no researchers, derives from top-level verdict with 0.8x penalty
  - Imports P26 first to ensure dual-researchers is installed (line 129-132)
  - Rebinds api.analyses.run_preview to wrapped version (line 148-155)

  Dependencies:
  - Explicitly imports P26 first
  - Module-level constant: _ALLOWED = {"supports","challenges","mixed","insufficient"} - safe

  Loaded in: NOT LOADED (missing from sitecustomize.py)Global State: One module-level constant set
   - safe (immutable)

  ---
  P28: Lane Diversification Knobs

  File: intelligence/content/p28_diversify.py (277 lines)Clean Module: NoneLogic: Embedded
  (diversification, lane context, plan tweaking all in wrapper)Target: Multiple: p26._run_once,
  intelligence.gather.online.run_plan, intelligence.pipeline.run.run_preview, api.analysesWhat it 
  does:
  - Patches P26's _run_once to set lane context (R1/R2) via ContextVar (line 202-217)
  - Wraps online.run_plan to apply lane-specific tweaks: provider order (R1: google/brave/bing,
  R2: brave/google/bing), query shuffle (line 127-137, 234-247)
  - Wraps run_preview to inject lane_config into researchers[] in returned object (line 174-182,
  249-263)
  - Uses MD5-derived seed per lane+claim for deterministic shuffle
  - Rebinds api.analyses module to wrapped run_preview (line 184-200)
  - Sets ROGR_LANE_ID environment variable for downstream probes (line 48)

  Dependencies:
  - Imports and patches P26 module
  - Uses contextvars.ContextVar for lane tracking

  Loaded in: NOT LOADED (missing from sitecustomize.py)Global State: ContextVar for LANE_ID and
  LANE_POS - safe (thread-local, async-safe)

  ---
  P29: Diversification Controls, Manifest & Telemetry

  File: intelligence/content/p29_diversify_controls.py (288 lines)Clean Module: NoneLogic:
  Embedded (telemetry, manifest, enrichment all in wrapper)Target:
  intelligence.gather.online.run_plan, intelligence.pipeline.run.run_preview, api.analysesWhat it 
  does:
  - Wraps online.run_plan to collect per-lane telemetry: provider counts, duration_ms (line
  132-146)
  - Wraps run_preview to inject top-level run_manifest + replay_id + diversified flag (line
  210-231)
  - Builds stable manifest with lane seeds, provider orders, knobs
  - Attaches lane_config.knobs {query_shuffle, timeout_jitter_ms, max_per_provider, seed} and
  telemetry {providers, duration_ms} to each researchers[*]
  - Adds parity check: parity.providers_equal to assert provider sets are identical across lanes
  - Rebinds api.analyses module to wrapped run_preview (line 233-248)

  Dependencies:
  - Reads ROGR_LANE_ID environment variable (set by P28)
  - Uses MD5 hash for replay_id

  Loaded in: NOT LOADED (missing from sitecustomize.py)Global State: ContextVar for _TELEM with
  default dict - potential issue (accumulates telemetry across calls, but ContextVar is better
  than module-level)

  ---
  Global State Found

  Critical Memory Leak

  File: intelligence/content/p22_ingest.py:29
  _FETCH_CACHE: Dict[str, str] = {}
  - Unbounded dictionary that grows with every unique URL fetched
  - Each entry stores full-text content (potentially megabytes)
  - Never cleaned or limited
  - Impact: Memory usage grows indefinitely in long-running processes

  Related Cache Issue

  File: intelligence/content/fetch_sync.py:21
  _CACHE: dict[str, Dict[str, Any]] = {}
  - Similar unbounded cache pattern (not directly used by P19-P29 but in same module)

  Safe Global State

  These are not memory leaks (immutable constants):
  - Regex compiles at module level (e.g., _WORD = re.compile(...))
  - Constant sets/dicts (e.g., BUDGET_CONTEXT = {...}, _ALLOWED = {...})
  - ContextVar usage in P28/P29 (thread-safe, async-safe, but still stateful)

  ---
  Critical Findings

  1. Production Loading Gap

  Only 2 of 11 packets load in production:
  - ✓ P20 (loaded via sitecustomize.py)
  - ✓ P22 (loaded via sitecustomize.py)
  - ✗ P19, P21, P23, P24, P25, P26, P27, P28, P29 (exist but never imported)

  Impact: 9 packets worth of functionality are dead code in production despite being marked
  "LIVE".

  2. Memory Leak in P22

  - _FETCH_CACHE grows unbounded
  - Production-loaded packet (runs on every request)
  - High risk in long-running services

  3. Chain-Wrapping Pattern

  Each packet re-wraps the same function:
  - P20, P21, P22 wrap build_evidence_for_claim
  - P23, P24, P25, P26, P27, P28, P29 wrap run_preview
  - Each wrapper captures previous _ORIG and creates closure
  - 9 layers deep if all loaded: P22 → P23 → P24 → P25 → P26 → P27 → P28 → P29
  - Creates deep call stack and makes debugging nearly impossible

  4. API Module Rebinding

  8 packets explicitly rebind api.analyses.run_preview or api.analyses.build_evidence_for_claim:
  - P22, P23, P24, P25, P26, P27, P28, P29
  - Uses setattr(api_mod, "run_preview", wrapped) to force API routes through wrappers
  - Import order dependency: last wrapper wins
  - Currently only P22 rebinds because others aren't loaded

  5. sys.modules Propagation

  P20 and P21 iterate over sys.modules to replace function references in already-imported modules
  (lines 217-224 in P20, 134-141 in P21). This is extremely fragile and makes wrapper installation
   order critical.

  6. Idempotency Flags Missing

  Most wrappers check for idempotency flags (e.g., _ROGR_P20_INSTALLED), but:
  - P19 checks _ROGR_P19_INSTALLED but doesn't set it until after wrapping
  - P22 uses __p22_fetch_wrapped__ and __p22_run_wrapped__
  - Mixed naming conventions make auditing difficult

  7. Logic Embedded in Wrappers

  6 packets (P19, P22, P26, P27, P28, P29) have substantial logic embedded:
  - P19: 215 lines (query generation, anchor extraction, counter-frames)
  - P22: 267 lines (fetch caching, enrichment, fallback fetch)
  - P26: 115 lines (dual-orchestrator, merging)
  - P27: 164 lines (consensus logic)
  - P28: 277 lines (lane context, plan tweaking, provider ordering)
  - P29: 288 lines (telemetry, manifest, replay_id)

  Cannot be tested independently without importing wrapper.

  ---
  Confidence Assessment

  | Area                            | Confidence | Evidence
        |
  |---------------------------------|------------|------------------------------------------------
  ------|
  | File inventory                  | HIGH       | Files found, read, counted
        |
  | Production loading              | HIGH       | sitecustomize.py explicitly lists P20, P22
        |
  | Clean module standalone imports | HIGH       | All 5 tested successfully
        |
  | Memory leak in P22              | HIGH       | Code inspection confirms unbounded dict
        |
  | Logic separation                | HIGH       | Read all files, identified patterns
        |
  | Wrapper functionality           | MEDIUM     | Read code, not executed in test environment
        |
  | P26-P29 integration             | MEDIUM     | Understand logic, but not loaded so untested in
   prod |

  ---
  Unknowns

  1. Why are P19, P21, P23-P29 not in sitecustomize.py?
    - Were they intentionally excluded?
    - Did they fail integration tests?
    - Deployment/rollout not complete?
  2. Does P19 load anywhere else?
    - It's in intelligence/gather/ (different dir than others)
    - No evidence of alternative loading mechanism found
  3. What's the intended load order?
    - P23-P29 explicitly import earlier packets
    - But sitecustomize only loads P20, P22
    - Missing 7 packets breaks dependency chain
  4. Are there other entry points besides sitecustomize.py?
    - Could be environment-specific loading
    - Could be conditional imports in other modules
    - Did not find evidence in this investigation
  5. Why does P25 have two files?
    - p25_aggregate.py (clean module, 103 lines)
    - p25_semantic_aggregate.py (wrapper, 90 lines)
    - This is the only packet split this way
    - Suggests it was refactored but others weren't
  6. What's the performance impact of 9-layer wrapping?
    - If all loaded, every preview request goes through 9 async wrappers
    - Each wrapper has try/except overhead
    - Telemetry/logging in each layer
    - Not measured quantitatively

  ---
  Recommendations

  1. Fix Memory Leak Immediately
    - Add LRU cache with max size to P22 _FETCH_CACHE
    - Or implement TTL-based expiration
    - Or move to external cache (Redis)
  2. Document Intended Load Order
    - Create manifest listing all packets and dependencies
    - Specify which should load in production vs dev/test
    - Update sitecustomize.py to match intent
  3. Refactor All Wrappers to Separate Logic
    - Follow P20-P25 pattern: clean module + thin wrapper
    - Extract P19, P22, P26, P27, P28, P29 embedded logic into clean modules
    - Enable independent testing
  4. Eliminate setattr() Pattern
    - Replace with proper dependency injection or middleware pattern
    - Use decorators or class inheritance instead of runtime rebinding
    - Remove sys.modules iteration
  5. Add Integration Tests
    - Test each packet independently
    - Test full chain P20→P21→...→P29
    - Verify memory doesn't leak over repeated runs
    - Check that all 11 packets actually work together
  6. Create Clean Integration Points
    - Instead of wrapping run_preview 9 times, create plugin/middleware system
    - Single entry point that calls packets in sequence
    - Clear state passing between stages