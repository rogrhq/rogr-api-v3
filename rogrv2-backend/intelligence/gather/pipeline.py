from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Tuple

from intelligence.gather import online
from intelligence.gather.normalize import normalize_candidates
from intelligence.rank.select import rank_candidates
from intelligence.analyze.stance import assess_stance
from intelligence.policy.guardrails import apply_guardrails_to_arms
from intelligence.consensus.metrics import compute_overlap_conflict
from intelligence.score.labeling import score_from_evidence, map_score_to_label
from intelligence.util import diag
from intelligence.gather.counter_frames import generate_counter_frame_queries, compute_coverage_metrics
from intelligence.content.fullread import _extract_base_domain


def _canonical_arm_label(arm_def: Dict[str, Any], idx: int) -> str:
    """
    Map arbitrary arm names/intents to canonical labels 'A' or 'B'.
    Priority:
      1) name startswith 'A' or 'B' (case-insensitive)
      2) intent == 'support' -> 'A'; intent == 'challenge' -> 'B'
      3) index: 0 -> 'A', 1 -> 'B'
    """
    name = str(arm_def.get("name") or "").strip()
    intent = str(arm_def.get("intent") or "").strip().lower()
    if name.upper().startswith("A"):
        return "A"
    if name.upper().startswith("B"):
        return "B"
    if intent in ("support", "agree", "for"):
        return "A"
    if intent in ("challenge", "refute", "against"):
        return "B"
    return "A" if idx == 0 else "B"


async def _exec_plan_for_arm(full_plan: Dict[str, Any], arm_def: Dict[str, Any], arm_label: str, *, max_per_query: int) -> List[Dict[str, Any]]:
    """
    Run the provider plan for a single arm (LIVE), then stamp every candidate with canonical arm label.
    Async-only: awaits online.run_plan; NO asyncio.run / run_until_complete (safe in FastAPI event loop).
    """
    sub_plan: Dict[str, Any] = {**full_plan}
    sub_plan["arms"] = [arm_def]

    res = await online.run_plan(sub_plan, max_per_query=max_per_query)
    raw = (res or {}).get("candidates") or []

    # Phase 7: Query validation (ADDED - full retry mode)
    # NOTE: Part D1 implements re-search, so max_retries=2 now works correctly
    claim_text = full_plan.get("claim_text", "")
    claim_entities = full_plan.get("claim_entities", [])
    claim_numbers = full_plan.get("claim_numbers", [])

    queries = arm_def.get("queries", [])
    if queries and raw and claim_text:
        # Validate first query (most important)
        first_query = queries[0]
        refined_query, validated_results, refinement_count = await validate_query_results(
            claim_text, claim_entities, claim_numbers, first_query, raw, max_retries=2,
            arm_label=arm_label,  # Pass actual arm label
            arm_intent=arm_def.get("intent", "support")  # Pass actual intent
        )

        if diag.enabled() and refinement_count > 0:
            diag.log("query_validation", query=first_query, refined=refined_query, needed_refinement=True, refinement_count=refinement_count)

        # Use validated results
        raw = validated_results

    # Continue with original flow
    out: List[Dict[str, Any]] = []
    for c in raw:
        if isinstance(c, dict):
            if "arm" not in c or not c.get("arm"):
                c = {**c, "arm": arm_label}
            else:
                # normalize arm value to canonical 'A'/'B' when possible
                v = str(c.get("arm") or "").upper()
                if v.startswith("A"):
                    c = {**c, "arm": "A"}
                elif v.startswith("B"):
                    c = {**c, "arm": "B"}
                else:
                    c = {**c, "arm": arm_label}
            out.append(c)
    return out


def _group_by_arm(cands: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split candidates into lists where c['arm'] == 'A' or 'B'."""
    a: List[Dict[str, Any]] = []
    b: List[Dict[str, Any]] = []
    for c in cands or []:
        arm = str(c.get("arm") or "").upper()
        if arm == "A":
            a.append(c)
        elif arm == "B":
            b.append(c)
    return a, b


def _extract_arm_defs(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Accept both list-form and dict-form arms from v2 planner.
    Returns a list of arm dicts with a populated 'name' field.
    Preferred order: A, B, then remaining keys in insertion order.
    """
    arms = plan.get("arms") or []
    out: List[Dict[str, Any]] = []
    if isinstance(arms, dict):
        ordered: List[str] = []
        for k in ("A", "B", "a", "b"):
            if k in arms:
                ordered.append(k)
        for k in arms.keys():
            if k not in ordered:
                ordered.append(k)
        for k in ordered:
            v = arms.get(k)
            if isinstance(v, dict):
                arm = {**v}
                if not arm.get("name"):
                    arm["name"] = str(k)
                out.append(arm)
    elif isinstance(arms, list):
        out = [a for a in arms if isinstance(a, dict)]
    return out


async def build_evidence_for_claim(claim_text: str, plan: Dict[str, Any], claim_entities: list = None, claim_numbers: list = None, max_per_arm: int = 5) -> Dict[str, Any]:
    """
    LIVE evidence pipeline with explicit arm tagging at source (no mocks, no fallbacks).
      1) Execute plan per arm (A, B) and stamp every candidate with canonical arm label.
      2) Normalize & rank within each arm.
      3) Enrich stance metadata.
      4) Apply guardrails (balance/diversity caps, min totals).
      5) Compute cross-arm consensus.
      6) Produce verdict (numeric & label) from evidence.
    """
    # Store claim data in plan for validation
    plan["claim_text"] = claim_text
    plan["claim_entities"] = claim_entities if claim_entities else []
    plan["claim_numbers"] = claim_numbers if claim_numbers else []

    # 1) Execute per arm and tag at source
    arm_defs = _extract_arm_defs(plan)
    labeled_cands: List[Dict[str, Any]] = []
    for idx, arm_def in enumerate(arm_defs):
        label = _canonical_arm_label(arm_def, idx)

        # P19: Add counter-frames for challenge arm (Arm B)
        intent = arm_def.get("intent", "").lower()
        arm_name = arm_def.get("name", "").upper()

        if intent in ("challenge", "contradict", "refute") or arm_name.startswith("B") or label == "B":
            counter_queries = generate_counter_frame_queries(claim_text, arm_def.get("queries", []), plan)

            # Add counter-frame queries to arm
            if "queries" not in arm_def:
                arm_def["queries"] = []
            for frame_name, query in counter_queries:
                arm_def["queries"].append(query)

        labeled_cands.extend(await _exec_plan_for_arm(plan, arm_def, label, max_per_query=2))

    print(f"\n=== DUPLICATION DIAGNOSTIC ===")
    print(f"Total items in labeled_cands: {len(labeled_cands)}")

    # Count unique URLs
    urls = [item.get('url', '') for item in labeled_cands]
    unique_urls = set(urls)
    print(f"Unique URLs: {len(unique_urls)}")
    print(f"Duplicate count: {len(urls) - len(unique_urls)}")

    # Find duplicates
    from collections import Counter
    url_counts = Counter(urls)
    duplicates = {url: count for url, count in url_counts.items() if count > 1}

    if duplicates:
        print(f"\nDUPLICATE URLs FOUND:")
        for url, count in duplicates.items():
            print(f"  {url}: appears {count} times")
            # Show arm values for each duplicate
            items_with_url = [item for item in labeled_cands if item.get('url') == url]
            for idx, item in enumerate(items_with_url):
                print(f"    Instance {idx+1}: arm={item.get('arm')}, query={item.get('query_used', 'unknown')}")
    else:
        print("NO DUPLICATES FOUND")

    print("=== END DIAGNOSTIC ===\n")

    # 2) Group by explicit arm, then normalize
    armA_raw, armB_raw = _group_by_arm(labeled_cands)
    armA_norm = normalize_candidates(armA_raw)
    armB_norm = normalize_candidates(armB_raw)

    # Phase 2.1: Fast filter - remove obviously unrelated (ADDED)
    if claim_entities is None:
        claim_entities = []
    if claim_numbers is None:
        claim_numbers = []

    armA_filtered, armA_dropped = filter_unrelated(claim_text, claim_entities, claim_numbers, armA_norm)
    armB_filtered, armB_dropped = filter_unrelated(claim_text, claim_entities, claim_numbers, armB_norm)

    if diag.enabled():
        diag.log("filter_unrelated_results",
                 armA_kept=len(armA_filtered), armA_dropped=len(armA_dropped),
                 armB_kept=len(armB_filtered), armB_dropped=len(armB_dropped))

    armA_norm = armA_filtered
    armB_norm = armB_filtered

    # Phase 2.2: Quality gate - filter junk domains, PDFs, non-English (ADDED)
    armA_quality, armA_junk = quality_gate(armA_norm)
    armB_quality, armB_junk = quality_gate(armB_norm)

    if diag.enabled():
        diag.log("quality_gate_results",
                 armA_kept=len(armA_quality), armA_junk=len(armA_junk),
                 armB_kept=len(armB_quality), armB_junk=len(armB_junk))

    armA_norm = armA_quality
    armB_norm = armB_quality

    # P19 Reordering: Sort Arm B candidates by anchor match score
    if armB_norm:
        from intelligence.gather.counter_frames import reorder_by_anchor_score
        armB_norm = reorder_by_anchor_score(armB_norm, claim_text)

    if diag.enabled():
        diag.log("gather_counts_pre_rank", armA=len(armA_norm), armB=len(armB_norm))

    ranked_A = rank_candidates(claim_text=claim_text, query=claim_text, candidates=armA_norm, top_k=max_per_arm)
    ranked_B = rank_candidates(claim_text=claim_text, query=claim_text, candidates=armB_norm, top_k=max_per_arm)

    # 3) Stance enrichment
    enr_A = [{**it, **assess_stance(claim_text, it)} for it in ranked_A]
    enr_B = [{**it, **assess_stance(claim_text, it)} for it in ranked_B]

    bundle = {"A": {"intent": "support", "candidates": enr_A}, "B": {"intent": "challenge", "candidates": enr_B}}

    # 4) Guardrails (function may return (bundle, report) or mutate in place)
    gr = apply_guardrails_to_arms(bundle)
    if isinstance(gr, tuple) and len(gr) == 2:
        guarded, report = gr
        guarded["guardrails"] = report
    else:
        guarded = gr
        if "guardrails" not in guarded:
            guarded["guardrails"] = {"status": "applied"}

    # 5) Cross-arm consensus
    a = guarded["A"]["candidates"]
    b = guarded["B"]["candidates"]
    if diag.enabled():
        diag.log("gather_counts_post_guardrails", armA=len(a), armB=len(b))
    guarded["consensus"] = compute_overlap_conflict(a, b)

    # 6) Verdict from evidence
    flat = [*a, *b]
    sv = score_from_evidence(flat)
    score_num = int(sv.get("claim_grade_numeric", 50))
    guarded["verdict"] = {
        "claim_grade_numeric": score_num,
        "label": map_score_to_label(score_num),
        "evidence_grade_letter": sv.get("evidence_grade_letter", "F"),
        "rationale": "Per-arm live gather with explicit arm tags; ranked, guarded, and scored.",
    }
    # Expose Day-1 contract keys expected by API/tests
    guarded["arm_A"] = a
    guarded["arm_B"] = b

    # P19: Track coverage per arm
    coverage_by_arm = {}

    # Coverage for Arm A
    armA_queries = []
    for arm_def in arm_defs:
        label = _canonical_arm_label(arm_def, arm_defs.index(arm_def))
        if label == "A":
            armA_queries.extend(arm_def.get("queries", []))
    armA_providers = set(c.get("provider", "") for c in armA_raw if c.get("provider"))
    coverage_by_arm["A"] = compute_coverage_metrics(armA_raw, armA_queries, armA_providers)

    # Coverage for Arm B
    armB_queries = []
    for arm_def in arm_defs:
        label = _canonical_arm_label(arm_def, arm_defs.index(arm_def))
        if label == "B":
            armB_queries.extend(arm_def.get("queries", []))
    armB_providers = set(c.get("provider", "") for c in armB_raw if c.get("provider"))
    coverage_by_arm["B"] = compute_coverage_metrics(armB_raw, armB_queries, armB_providers)

    guarded["coverage_by_arm"] = coverage_by_arm

    return guarded


# ============================================================================
# PHASE 2.1: FAST RELATEDNESS FILTER (ADDED)
# ============================================================================

def filter_unrelated(claim_text: str, claim_entities: list, claim_numbers: list, candidates: list) -> tuple:
    """
    Fast deterministic filter for obviously unrelated candidates.

    Keeps candidates that have:
    - At least one entity from claim OR
    - At least one number from claim OR
    - At least 30% keyword overlap with claim

    Args:
        claim_text: The claim being fact-checked
        claim_entities: List of entities from claim (strings or dicts with 'name' key)
        claim_numbers: List of numbers from claim (dicts with 'value' key)
        candidates: List of search result dicts

    Returns:
        Tuple of (filtered_candidates, dropped_candidates)
    """

    # Normalize entities (handle both string and dict format)
    entities_normalized = []
    for entity in claim_entities:
        if isinstance(entity, dict):
            entities_normalized.append(entity.get('name', '').lower())
        else:
            entities_normalized.append(str(entity).lower())

    # Normalize numbers
    numbers_normalized = []
    for num in claim_numbers:
        if isinstance(num, dict):
            value = num.get('value', '')
            # Handle both float and string percentages
            if isinstance(value, (int, float)):
                numbers_normalized.append(str(value))
            else:
                # Extract numeric part from strings like "8%"
                import re
                matches = re.findall(r'\d+\.?\d*', str(value))
                numbers_normalized.extend(matches)

    # Claim keywords (for lexical overlap)
    claim_words = set(claim_text.lower().split())
    # Remove common stopwords
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
                 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
                 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
                 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both',
                 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
                 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'just', 'don',
                 'now', 'but', 'and', 'or', 'if', 'because', 'as', 'until', 'while'}
    claim_words = claim_words - stopwords

    filtered = []
    dropped = []

    for candidate in candidates:
        snippet = candidate.get('snippet', '').lower()

        # Check 1: Entity match
        entity_match = any(entity in snippet for entity in entities_normalized if entity)

        # Check 2: Number match
        number_match = any(number in snippet for number in numbers_normalized if number)

        # Check 3: Keyword overlap (>30%)
        snippet_words = set(snippet.split()) - stopwords
        if len(claim_words) > 0:
            overlap = len(claim_words & snippet_words) / len(claim_words)
        else:
            overlap = 0.0
        keyword_match = overlap >= 0.30

        # Keep if ANY anchor present
        if entity_match or number_match or keyword_match:
            filtered.append(candidate)
        else:
            candidate['dropped_reason'] = 'no_anchors'
            candidate['dropped_checks'] = {
                'entity_match': entity_match,
                'number_match': number_match,
                'keyword_overlap': overlap,
            }
            dropped.append(candidate)

    return filtered, dropped



# ============================================================================
# PHASE 2.2: QUALITY GATE FILTER (ADDED)
# ============================================================================

def quality_gate(candidates: list) -> tuple:
    """
    Filter out low-quality sources.

    Filters:
    - Blocked domains
    - Uncrawlable PDFs (except from whitelist)
    - Non-English content
    - Domain duplicates (max 2 per domain)

    Returns:
        Tuple of (filtered_candidates, dropped_candidates)
    """
    from urllib.parse import urlparse

    # Blocked domains (known junk sites)
    BLOCKED_DOMAINS = {
        'pinterest.com',
        'youtube.com',  # Video, not crawlable text
        'instagram.com',
        'facebook.com',
        'twitter.com',  # Social media, not authoritative
        'reddit.com',
        'quora.com',
    }

    # Whitelist for PDFs (these are OK to include)
    WHITELIST_PDF_DOMAINS = {
        '.gov',
        '.edu',
        'nih.gov',
        'cdc.gov',
        'census.gov',
        'who.int',
    }

    def extract_domain(url):
        """Extract base domain from URL using tldextract."""
        return _extract_base_domain(url)

    def is_english(text):
        """Simple English detection - filters out obviously non-English content"""
        if not text:
            return False

        # Check for accented characters and non-Latin scripts
        # These indicate Spanish, French, German, Chinese, Arabic, etc.
        non_english_chars = set('áéíóúñüàèìòùäöößçåæø中国日本한국اللغة')

        # If text contains non-English characters, it's not English
        text_lower = text.lower()
        if any(char in text_lower for char in non_english_chars):
            return False

        # Otherwise, assume English (simple, permissive)
        return True

    def is_whitelisted_pdf(url):
        """Check if PDF is from whitelisted domain"""
        domain = extract_domain(url)
        return any(wl in domain for wl in WHITELIST_PDF_DOMAINS)

    filtered = []
    dropped = []
    domain_counts = {}

    for candidate in candidates:
        url = candidate.get('url', '')
        snippet = candidate.get('snippet', '')
        domain = extract_domain(url)

        # Check 1: Blocked domain
        if domain in BLOCKED_DOMAINS:
            candidate['dropped_reason'] = 'blocked_domain'
            dropped.append(candidate)
            continue

        # Check 2: PDF check
        if url.endswith('.pdf'):
            if not is_whitelisted_pdf(url):
                candidate['dropped_reason'] = 'uncrawlable_pdf'
                dropped.append(candidate)
                continue

        # Check 3: Language check
        if not is_english(snippet):
            candidate['dropped_reason'] = 'non_english'
            dropped.append(candidate)
            continue

        # Check 4: Domain duplicate limit (max 2 per domain)
        current_count = domain_counts.get(domain, 0)
        if current_count >= 2:
            candidate['dropped_reason'] = 'domain_duplicate'
            dropped.append(candidate)
            continue

        # Passed all checks
        filtered.append(candidate)
        domain_counts[domain] = current_count + 1

    return filtered, dropped



# ============================================================================
# PHASE 7.1: QUERY VALIDATION LOOP
# ============================================================================

async def validate_query_results(claim_text: str, claim_entities: list, claim_numbers: list,
                          query: str, results: list, max_retries: int = 2,
                          arm_label: str = "A", arm_intent: str = "support") -> tuple:
    """
    Check if query returned on-topic results; refine if not.

    Validation:
    - Sample top 5 results
    - Check relevance using fast filter (from Phase 2)
    - If <60% relevant and retries remaining, refine and retry

    Args:
        claim_text: The claim
        claim_entities: Entities from claim
        claim_numbers: Numbers from claim
        query: Original query string
        results: Search results
        max_retries: Max refinement attempts (default 2)

    Returns:
        Tuple of (final_query, final_results, refinement_count)
    """

    if not results:
        return query, results, 0  # No results to validate

    # Sample top 5 results
    sample_size = min(5, len(results))
    sample = results[:sample_size]

    # Check relevance using Phase 2 filter logic
    relevant_count = 0
    for result in sample:
        snippet = result.get('snippet', '').lower()

        # Entity match
        entity_match = False
        for entity in claim_entities:
            entity_str = entity if isinstance(entity, str) else entity.get('name', '')
            if entity_str.lower() in snippet:
                entity_match = True
                break

        # Number match
        number_match = False
        for number in claim_numbers:
            num_val = number.get('value', '') if isinstance(number, dict) else str(number)
            if str(num_val) in snippet:
                number_match = True
                break

        # Keyword overlap
        claim_words = set(claim_text.lower().split())
        snippet_words = set(snippet.split())
        overlap = len(claim_words & snippet_words) / len(claim_words) if claim_words else 0
        keyword_match = overlap >= 0.30

        # Relevant if any anchor present
        if entity_match or number_match or keyword_match:
            relevant_count += 1

    relevance_rate = relevant_count / sample_size if sample_size > 0 else 0.0

    # If >60% relevant, good
    if relevance_rate >= 0.6:
        return query, results, 0

    # If <60% relevant and retries remaining, refine
    if max_retries > 0:
        refined_query = refine_query(claim_text, claim_entities, claim_numbers, query, sample)

        # Execute refined search

        # Build mini-plan with refined query
        refined_plan = {
            "version": "v2",
            "arms": [{
                "name": arm_label,      # Use actual arm label (A or B)
                "intent": arm_intent,   # Use actual intent (support or challenge)
                "queries": [refined_query]
            }]
        }

        # Execute search (use same max_per_query)
        new_res = await online.run_plan(refined_plan, max_per_query=len(results))
        new_results = (new_res or {}).get("candidates", [])

        if new_results and len(new_results) > 0:
            if diag.enabled():
                diag.log("query_refinement_search",
                         refined_query=refined_query,
                         new_result_count=len(new_results))

            # Recursive call with refined query and new results
            final_query, final_results, child_count = await validate_query_results(
                claim_text, claim_entities, claim_numbers,
                refined_query, new_results, max_retries - 1,
                arm_label=arm_label, arm_intent=arm_intent  # Preserve arm info in recursion
            )
            return (final_query, final_results, child_count + 1)
        else:
            # Refinement failed, return original
            return (refined_query, results, 1)

    # Out of retries, return what we have
    return query, results, 0


def refine_query(claim_text: str, claim_entities: list, claim_numbers: list,
                original_query: str, off_topic_results: list) -> str:
    """
    Refine query to be more targeted.

    Refinement strategies:
    1. Add entity quotes if missing
    2. Add units if numeric claim
    3. Add domain constraint (.gov OR .edu)

    Args:
        claim_text: The claim
        claim_entities: Entities
        claim_numbers: Numbers
        original_query: Original query that failed
        off_topic_results: Off-topic results (for analysis)

    Returns:
        Refined query string
    """

    # Strategy 1: Add entity quotes if missing
    if '"' not in original_query and claim_entities:
        entity = claim_entities[0]
        entity_str = entity if isinstance(entity, str) else entity.get('name', '')
        return f'"{entity_str}" {original_query}'

    # Strategy 2: Add units if numeric
    if claim_numbers:
        # Check if query has units
        units = ['percent', '%', 'million', 'billion', 'degrees', '°']
        has_units = any(unit in original_query.lower() for unit in units)

        if not has_units:
            # Try to infer unit from claim
            if '%' in claim_text or 'percent' in claim_text.lower():
                return f'{original_query} percent'

    # Strategy 3: Add domain constraint
    if 'site:' not in original_query:
        return f'{original_query} site:.gov OR site:.edu'

    # Fallback: Return original
    return original_query

