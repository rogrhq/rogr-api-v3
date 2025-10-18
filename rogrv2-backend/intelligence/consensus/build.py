"""
Phase 6: Evidence-Based Consensus Building

Compares R1 and R2 evidence quality and resolves disagreements intelligently.
"""

def compare_evidence_quality(r1_items_a: list, r1_items_b: list,
                             r2_items_a: list, r2_items_b: list) -> dict:
    """
    Compare evidence quality across researchers.

    Compares:
    - Average evidence grade (item_grade)
    - Average authority score
    - Source diversity
    - Internal consistency

    Args:
        r1_items_a: R1's Arm A evidence
        r1_items_b: R1's Arm B evidence
        r2_items_a: R2's Arm A evidence
        r2_items_b: R2's Arm B evidence

    Returns:
        Dict with quality comparison
    """

    def calculate_arm_quality(items):
        """Calculate aggregate quality for one arm"""
        if not items:
            return {
                'avg_grade': 0.0,
                'avg_authority': 0.5,
                'diversity': 0.0,
                'item_count': 0,
            }

        # Import functions from Phase 4
        try:
            from intelligence.content.p25_aggregate import calculate_diversity_score
        except ImportError:
            # Fallback if not available
            def calculate_diversity_score(items):
                return 0.5

        # Average grade
        grades = [item.get('item_grade', 0.0) for item in items]
        avg_grade = sum(grades) / len(grades) if grades else 0.0

        # Average authority (if available)
        # Authority might be in features from Phase 3
        authorities = []
        for item in items:
            # Try to get authority from multiple places
            auth = item.get('authority', None)
            if auth is None:
                # Try to calculate from URL + credibility
                try:
                    from intelligence.content.grade import calculate_authority_score
                    url = item.get('url', '')
                    cred = item.get('credibility', 0.5)
                    auth = calculate_authority_score(url, cred)
                except:
                    auth = 0.5
            authorities.append(auth)

        avg_authority = sum(authorities) / len(authorities) if authorities else 0.5

        # Diversity
        diversity = calculate_diversity_score(items)

        return {
            'avg_grade': round(avg_grade, 3),
            'avg_authority': round(avg_authority, 3),
            'diversity': round(diversity, 3),
            'item_count': len(items),
        }

    # Calculate quality for each arm for each researcher
    r1_quality_a = calculate_arm_quality(r1_items_a)
    r1_quality_b = calculate_arm_quality(r1_items_b)
    r2_quality_a = calculate_arm_quality(r2_items_a)
    r2_quality_b = calculate_arm_quality(r2_items_b)

    # Calculate overall quality score for each researcher
    # Weighted combination of metrics
    def overall_quality(arm_a_qual, arm_b_qual):
        """Calculate overall quality across both arms"""
        total_items = arm_a_qual['item_count'] + arm_b_qual['item_count']
        if total_items == 0:
            return 0.0

        # Weight by item count
        weight_a = arm_a_qual['item_count'] / total_items
        weight_b = arm_b_qual['item_count'] / total_items

        overall = (
            0.4 * (weight_a * arm_a_qual['avg_grade'] + weight_b * arm_b_qual['avg_grade']) +
            0.3 * (weight_a * arm_a_qual['avg_authority'] + weight_b * arm_b_qual['avg_authority']) +
            0.2 * (weight_a * arm_a_qual['diversity'] + weight_b * arm_b_qual['diversity']) +
            0.1 * min(total_items / 6, 1.0)  # Item count factor (max 6)
        )
        return round(overall, 3)

    r1_overall = overall_quality(r1_quality_a, r1_quality_b)
    r2_overall = overall_quality(r2_quality_a, r2_quality_b)

    quality_gap = abs(r1_overall - r2_overall)

    return {
        'r1': {
            'arm_A': r1_quality_a,
            'arm_B': r1_quality_b,
            'overall': r1_overall,
        },
        'r2': {
            'arm_A': r2_quality_a,
            'arm_B': r2_quality_b,
            'overall': r2_overall,
        },
        'quality_gap': round(quality_gap, 3),
        'better_researcher': 'R1' if r1_overall > r2_overall else 'R2' if r2_overall > r1_overall else 'tied',
    }



# ============================================================================
# PHASE 6.2: INTELLIGENT DISAGREEMENT RESOLUTION
# ============================================================================

def resolve_disagreement(r1_verdict: dict, r2_verdict: dict,
                        evidence_comparison: dict) -> dict:
    """
    Intelligently resolve disagreement using evidence quality.

    Resolution strategy:
    1. Agreement → boost confidence
    2. Large quality gap (>0.15) → trust better evidence
    3. Small quality gap → check arm balance
    4. Very close → genuine mixed

    Args:
        r1_verdict: R1's verdict dict with label, confidence, arm_strength
        r2_verdict: R2's verdict dict
        evidence_comparison: Quality comparison from compare_evidence_quality()

    Returns:
        Consensus verdict dict
    """

    r1_label = r1_verdict.get('label', 'insufficient')
    r2_label = r2_verdict.get('label', 'insufficient')
    r1_conf = r1_verdict.get('confidence', 0.5)
    r2_conf = r2_verdict.get('confidence', 0.5)

    # Case 1: Agreement
    if r1_label == r2_label:
        # Both researchers agree - boost confidence
        avg_conf = (r1_conf + r2_conf) / 2
        consensus_conf = min(1.0, avg_conf * 1.10)  # 10% boost for agreement

        return {
            'label': r1_label,
            'confidence': round(consensus_conf, 3),
            'rationale': 'Both researchers agree',
            'agreement': True,
            'r1_verdict': r1_label,
            'r2_verdict': r2_label,
        }

    # Case 2: Disagreement - examine evidence quality
    quality_gap = evidence_comparison['quality_gap']
    better_researcher = evidence_comparison['better_researcher']

    # Case 2a: Significant quality difference (>0.15)
    if quality_gap > 0.15:
        # Trust the researcher with better evidence
        if better_researcher == 'R1':
            better_verdict = r1_verdict
            better_label_name = 'R1'
        else:
            better_verdict = r2_verdict
            better_label_name = 'R2'

        # Use better verdict but apply penalty for disagreement
        consensus_conf = better_verdict['confidence'] * 0.95  # 5% penalty

        return {
            'label': better_verdict['label'],
            'confidence': round(consensus_conf, 3),
            'rationale': f'{better_label_name} has stronger evidence (quality gap: {quality_gap:.2f})',
            'agreement': False,
            'quality_resolution': True,
            'better_evidence': better_label_name,
            'r1_verdict': r1_label,
            'r2_verdict': r2_label,
        }

    # Case 2b: Similar quality - check arm balance
    else:
        # Extract arm strengths
        r1_arm_a = r1_verdict.get('arm_strength', {}).get('support', 0.0)
        r1_arm_b = r1_verdict.get('arm_strength', {}).get('challenge', 0.0)
        r2_arm_a = r2_verdict.get('arm_strength', {}).get('support', 0.0)
        r2_arm_b = r2_verdict.get('arm_strength', {}).get('challenge', 0.0)

        r1_balance = r1_arm_a - r1_arm_b
        r2_balance = r2_arm_a - r2_arm_b

        # If balances are very close, genuinely mixed
        if abs(r1_balance - r2_balance) < 0.10:
            avg_conf = (r1_conf + r2_conf) / 2
            return {
                'label': 'mixed',
                'confidence': round(avg_conf * 0.90, 3),  # 10% penalty for ambiguity
                'rationale': 'Evidence is genuinely mixed across both researchers',
                'agreement': False,
                'quality_resolution': False,
                'r1_verdict': r1_label,
                'r2_verdict': r2_label,
            }

        # One has clearer balance
        else:
            if abs(r1_balance) > abs(r2_balance):
                return {
                    'label': r1_label,
                    'confidence': round(r1_conf * 0.92, 3),
                    'rationale': 'R1 shows clearer evidence balance',
                    'agreement': False,
                    'balance_resolution': True,
                    'r1_verdict': r1_label,
                    'r2_verdict': r2_label,
                }
            else:
                return {
                    'label': r2_label,
                    'confidence': round(r2_conf * 0.92, 3),
                    'rationale': 'R2 shows clearer evidence balance',
                    'agreement': False,
                    'balance_resolution': True,
                    'r1_verdict': r1_label,
                    'r2_verdict': r2_label,
                }



# ============================================================================
# PHASE 6.3: EVIDENCE SYNTHESIS
# ============================================================================

def synthesize_evidence(r1_items_a: list, r1_items_b: list,
                       r2_items_a: list, r2_items_b: list) -> dict:
    """
    Combine best evidence from both researchers.

    Strategy:
    1. Pool all items
    2. Deduplicate by URL
    3. Sort by quality (item_grade * authority)
    4. Take top 5 per arm

    Args:
        r1_items_a: R1 Arm A items
        r1_items_b: R1 Arm B items
        r2_items_a: R2 Arm A items
        r2_items_b: R2 Arm B items

    Returns:
        Dict with synthesized arm_A and arm_B items
    """

    def synthesize_arm(r1_items, r2_items):
        """Synthesize items for one arm"""
        # Pool all items
        all_items = r1_items + r2_items

        if not all_items:
            return []

        # Deduplicate by URL
        seen_urls = set()
        unique_items = []
        for item in all_items:
            url = item.get('url', '')
            if url and url not in seen_urls:
                unique_items.append(item)
                seen_urls.add(url)

        # Calculate quality score for sorting
        for item in unique_items:
            grade = item.get('item_grade', 0.0)
            authority = item.get('authority', 0.5)

            # Try to calculate authority if not present
            if 'authority' not in item:
                try:
                    from intelligence.content.grade import calculate_authority_score
                    url = item.get('url', '')
                    cred = item.get('credibility', 0.5)
                    authority = calculate_authority_score(url, cred)
                    item['authority'] = authority
                except:
                    authority = 0.5

            # Quality score = grade * authority
            item['_quality_score'] = grade * authority

        # Sort by quality score (descending)
        unique_items.sort(key=lambda x: x.get('_quality_score', 0.0), reverse=True)

        # Take top 5
        top_items = unique_items[:5]

        # Remove temporary quality score
        for item in top_items:
            if '_quality_score' in item:
                del item['_quality_score']

        return top_items

    # Synthesize each arm
    synthesized_a = synthesize_arm(r1_items_a, r2_items_a)
    synthesized_b = synthesize_arm(r1_items_b, r2_items_b)

    return {
        'arm_A': synthesized_a,
        'arm_B': synthesized_b,
        'synthesis_note': f'Combined best evidence from R1 and R2',
        'total_items': len(synthesized_a) + len(synthesized_b),
    }

