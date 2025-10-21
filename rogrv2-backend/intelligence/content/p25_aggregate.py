from __future__ import annotations
import sys
from typing import Any, Dict, List, Tuple
import math

def _item_strength(it: Dict[str, Any]) -> float:
    """
    Deterministic per-item strength in [0,1], combining:
      - best frame match score (0..1),
      - item_grade (0..1),
      - coverage weight (full > partial > snippet_only)
    """
    # frame top score
    fms = it.get("frame_matches") or []
    best_frame = 0.0
    for m in fms:
        try:
            sc = float(m.get("score", 0.0))
            if sc > best_frame:
                best_frame = sc
        except Exception as e:
            print(f"⚠️ WARNING in frame score parsing: {e}", file=sys.stderr)
            print(f"   Frame data: {m}", file=sys.stderr)
            # Continue with best_frame unchanged

    # item grade
    try:
        igr = float(it.get("item_grade", 0.0))
    except Exception:
        igr = 0.0

    # coverage factor
    cov = (it.get("coverage") or "unknown").lower()
    if cov == "full":
        cov_w = 1.0
    elif cov == "partial":
        cov_w = 0.75
    elif cov == "snippet_only":
        cov_w = 0.55
    else:
        cov_w = 0.6  # conservative default

    # combine (bounded)
    base = 0.55 * best_frame + 0.45 * igr
    strength = max(0.0, min(1.0, base * cov_w))
    return strength

def _arm_strength(items: List[Dict[str,Any]], top_k: int = 4) -> float:
    """
    Aggregate arm strength from item strengths with diminishing returns.
    """
    vals = sorted((_item_strength(it) for it in items), reverse=True)
    vals = vals[:top_k]
    # diminishing weights (softmax-like but deterministic)
    weights = [1.00, 0.70, 0.50, 0.35]
    total = 0.0
    for i, v in enumerate(vals):
        w = weights[i] if i < len(weights) else weights[-1] * (0.8 ** (i - len(weights) + 1))
        total += v * w
    # normalize by max possible (sum of weights)
    max_possible = sum(weights[:len(vals)]) if vals else 1.0
    return max(0.0, min(1.0, total / max_possible))

def _confidence_from_arms(sa: float, sb: float, n_items_a: int, n_items_b: int,
                         arm_a_items: list, arm_b_items: list, claim_numbers: list = None) -> float:
    """
    Enhanced confidence with quality multipliers (Phase 4).
    NOTE: This violates architecture (p25_aggregate.py importing from grade.py),
    but matches blueprint requirements for quality multipliers.
    """
    total = max(0.0, min(1.0, 0.6 * max(sa, sb) + 0.4 * (sa + sb) / 2.0))
    count_factor = min(1.0, (n_items_a + n_items_b) / 6.0)
    balance = abs(sa - sb)

    # Phase 4: Add quality multipliers
    all_items = arm_a_items + arm_b_items
    diversity = calculate_diversity_score(all_items)
    consistency = calculate_consistency_score(all_items, claim_numbers)

    # Calculate average authority using authority score (now stored on items by grade.py)
    authorities = [item.get("authority", 0.5) for item in all_items]
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

def aggregate_verdict(claim_text: str, arm_a_items: List[Dict[str,Any]], arm_b_items: List[Dict[str,Any]],
                      claim_numbers: list = None, *, delta: float = 0.15) -> Dict[str, Any]:
    """
    Produce deterministic verdict from arm strengths.
    Returns:
      {
        "label": "supports|challenges|mixed|insufficient",
        "confidence": 0..1,
        "arm_strength": {"support": sa, "challenge": sb, "balance": sa - sb}
      }
    """
    sa = _arm_strength(arm_a_items)
    sb = _arm_strength(arm_b_items)

    # Phase 4: Apply quality multipliers to arm strength (ADDED)
    all_items = arm_a_items + arm_b_items
    diversity = calculate_diversity_score(all_items)
    consistency = calculate_consistency_score(all_items, claim_numbers)
    breadth = calculate_breadth_score(all_items)

    # Apply multipliers to arm strength (blueprint specification)
    sa_enhanced = sa * diversity * consistency * breadth
    sb_enhanced = sb * diversity * consistency * breadth

    # Use enhanced strength for verdict calculation
    if sa_enhanced < 0.12 and sb_enhanced < 0.12:
        label = "insufficient"
    else:
        if (sa_enhanced - sb_enhanced) >= delta:
            label = "supports"
        elif (sb_enhanced - sa_enhanced) >= delta:
            label = "challenges"
        else:
            label = "mixed"

    conf = _confidence_from_arms(sa_enhanced, sb_enhanced, len(arm_a_items), len(arm_b_items),
                                arm_a_items, arm_b_items, claim_numbers)
    return {
        "label": label,
        "confidence": float(conf),
        "arm_strength": {
            "support": float(sa_enhanced),
            "challenge": float(sb_enhanced),
            "support_base": float(sa),  # Store base for comparison
            "challenge_base": float(sb),
            "balance": float(sa_enhanced - sb_enhanced)
        },
        "quality_multipliers": {
            "diversity": float(diversity),
            "consistency": float(consistency),
            "breadth": float(breadth)
        }
    }


# ============================================================================
# PHASE 4.1: SOURCE DIVERSITY CHECKING (ADDED)
# ============================================================================

def calculate_diversity_score(items: list) -> float:
    """
    Score source diversity 0-1.

    Higher score = more diverse sources
    Lower score = clustered from few sources

    Args:
        items: List of evidence items (each has 'url')

    Returns:
        Diversity score 0-1
    """
    from urllib.parse import urlparse

    if not items or len(items) == 0:
        return 0.0

    # Extract domains
    domains = []
    for item in items:
        url = item.get('url', '')
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            domains.append(domain)
        except:
            continue

    if not domains:
        return 0.0

    # Calculate diversity
    unique_domains = len(set(domains))
    total_items = len(domains)

    diversity = unique_domains / total_items

    # Bonus for cross-source corroboration
    # If 3+ unique sources with 3+ items, boost diversity
    if unique_domains >= 3 and total_items >= 3:
        diversity = min(1.0, diversity * 1.1)

    return round(diversity, 3)



# ============================================================================
# PHASE 4.2: INTERNAL CONSISTENCY CHECKING (ADDED)
# ============================================================================

def calculate_consistency_score(items: list, claim_numbers: list = None) -> float:
    """
    Check if arm items agree on numbers (0-1).

    Higher score = items agree
    Lower score = items contradict each other

    Args:
        items: List of evidence items
        claim_numbers: List of numbers from claim to check

    Returns:
        Consistency score 0-1 (1.0 = fully consistent)
    """
    import re

    if not items or len(items) < 2:
        return 1.0  # Only one item, can't have conflicts

    if not claim_numbers:
        return 1.0  # Non-numeric claim, consistency N/A

    def extract_numbers(text):
        """Extract all numbers from text"""
        if not text:
            return []
        # Find all numbers (including decimals and percentages)
        numbers = re.findall(r'\d+\.?\d*', text)
        return [float(n) for n in numbers]

    # Extract numbers from each item's content
    item_numbers = []
    for item in items:
        # Check multiple fields for numbers
        text = ''
        text += item.get('snippet', '') + ' '
        text += item.get('content', '')[:500]  # First 500 chars of content

        numbers = extract_numbers(text)
        if numbers:
            item_numbers.append(numbers)

    if len(item_numbers) < 2:
        return 1.0  # Not enough data to check consistency

    # Check variance in numbers
    # If items report similar numbers, consistency is high
    # If items report very different numbers, consistency is low

    all_numbers = []
    for nums in item_numbers:
        all_numbers.extend(nums)

    if not all_numbers:
        return 1.0  # No numbers found

    # Calculate coefficient of variation (std dev / mean)
    import statistics
    if len(all_numbers) >= 2:
        mean = statistics.mean(all_numbers)
        if mean > 0:
            stdev = statistics.stdev(all_numbers)
            coef_var = stdev / mean

            # Convert to consistency score
            # Low variance (< 0.10) = high consistency (1.0)
            # High variance (> 0.50) = low consistency (0.0)
            if coef_var < 0.10:
                consistency = 1.0
            elif coef_var > 0.50:
                consistency = 0.0
            else:
                # Linear interpolation between 0.10 and 0.50
                consistency = 1.0 - ((coef_var - 0.10) / 0.40)

            return round(max(0.0, min(1.0, consistency)), 3)

    return 1.0  # Default: assume consistent



# ============================================================================
# PHASE 4.3: COVERAGE BREADTH ANALYSIS (ADDED)
# ============================================================================

def calculate_breadth_score(items: list) -> float:
    """
    Measure breadth vs repetition 0-1.

    Higher score = diverse angles, complementary coverage
    Lower score = repetitive, same content repeated

    Args:
        items: List of evidence items

    Returns:
        Breadth score 0-1
    """

    if not items or len(items) < 2:
        return 1.0  # Single item, can't measure breadth

    # Extract matched spans or snippets
    texts = []
    for item in items:
        # Prefer matched_span if available, else snippet
        text = ''

        # Check for matched span from various analysis modules
        if 'findings' in item and item['findings']:
            # P23 findings
            for finding in item['findings']:
                text += finding.get('quote', '') + ' '

        if not text:
            text = item.get('snippet', '')

        if text:
            texts.append(text.lower())

    if len(texts) < 2:
        return 1.0

    # Calculate pairwise similarity using trigram overlap
    def trigram_similarity(text1, text2):
        """Calculate trigram similarity between two texts"""
        def get_trigrams(text):
            words = text.split()
            if len(words) < 3:
                return set()
            trigrams = set()
            for i in range(len(words) - 2):
                trigrams.add(' '.join(words[i:i+3]))
            return trigrams

        trigrams1 = get_trigrams(text1)
        trigrams2 = get_trigrams(text2)

        if not trigrams1 or not trigrams2:
            return 0.0

        intersection = len(trigrams1 & trigrams2)
        union = len(trigrams1 | trigrams2)

        if union == 0:
            return 0.0

        return intersection / union

    # Calculate average pairwise similarity
    similarities = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            sim = trigram_similarity(texts[i], texts[j])
            similarities.append(sim)

    if not similarities:
        return 1.0

    avg_similarity = sum(similarities) / len(similarities)

    # High similarity = repetition = low breadth
    # Low similarity = diverse angles = high breadth
    breadth = 1.0 - avg_similarity

    return round(max(0.0, min(1.0, breadth)), 3)

