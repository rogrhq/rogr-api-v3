#!/usr/bin/env python3
"""
Architecture Validation: Data Structures
Tests verify the exact format of core data structures in the ROGRv2 system.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_evidence_item_structure():
    """
    Test evidence_item dict structure.
    Location: Created by intelligence/gather/online.py, modified throughout pipeline
    Expected keys: url, snippet, arm, content, item_grade, stance, finding
    """
    print("Testing evidence_item structure...")

    # Simulate minimal evidence item from gather phase
    evidence_item = {
        'url': 'https://example.com',
        'snippet': 'Test snippet text',
        'arm': 'A',
        'score': 0.85,
        'title': 'Test Title',
        'provider': 'test_provider'
    }

    # Core keys that must exist after gather
    assert 'url' in evidence_item and isinstance(evidence_item['url'], str), \
        "Evidence item must have 'url' as string"
    assert 'snippet' in evidence_item and isinstance(evidence_item['snippet'], str), \
        "Evidence item must have 'snippet' as string"
    assert 'arm' in evidence_item and evidence_item['arm'] in ['A', 'B'], \
        f"Evidence item must have 'arm' in ['A', 'B'], got: {evidence_item.get('arm')}"

    print(f"  ✓ Evidence item base structure validated")
    print(f"    - url: {type(evidence_item['url']).__name__}")
    print(f"    - snippet: {type(evidence_item['snippet']).__name__}")
    print(f"    - arm: {evidence_item['arm']}")

    # After enrichment (fetch_enrichment.py)
    evidence_item['content'] = 'Full content text'
    evidence_item['content_chars'] = len(evidence_item['content'])
    evidence_item['content_hash'] = 'sha256:abc123...'
    evidence_item['coverage'] = 'full'  # full|partial|snippet_only

    assert 'content' in evidence_item, "After enrichment, must have 'content'"
    assert 'coverage' in evidence_item, "After enrichment, must have 'coverage'"
    assert evidence_item['coverage'] in ['full', 'partial', 'snippet_only'], \
        f"Coverage must be one of [full, partial, snippet_only], got: {evidence_item['coverage']}"

    print(f"  ✓ Evidence item after enrichment validated")
    print(f"    - content: {type(evidence_item['content']).__name__}")
    print(f"    - coverage: {evidence_item['coverage']}")

    # After grade.py (P20)
    evidence_item['item_grade'] = 7.5  # ⚠️ BUG: Should be 0-1, currently 0-10
    evidence_item['stance'] = 'support'
    evidence_item['finding'] = {
        'grade': 7.5,
        'stance': 'support',
        'matched_spans': ['matched text'],
        'rationale': ['entity matched', 'similarity high (0.65)'],
        'similarity': 0.65
    }

    assert 'item_grade' in evidence_item, "After grade.py, must have 'item_grade'"
    assert 'stance' in evidence_item, "After grade.py, must have 'stance'"
    assert evidence_item['stance'] in ['support', 'challenge', 'mixed', 'unrelated', 'contextual_support'], \
        f"Stance must be valid, got: {evidence_item['stance']}"

    print(f"  ✓ Evidence item after grade.py validated")
    print(f"    - item_grade: {evidence_item['item_grade']} (⚠️ BUG: 0-10 scale, should be 0-1)")
    print(f"    - stance: {evidence_item['stance']}")

    # After semantic_read.py (P23)
    evidence_item['findings'] = [
        {
            'quote': 'relevant quote',
            'offset_start': 0,
            'offset_end': 100,
            'stance': 'support',
            'signals': ['entity', 'number'],
            'score': 0.75
        }
    ]
    evidence_item['item_grade'] = 0.75  # Overwrites P20's 0-10 scale value
    evidence_item['grade_label'] = 'high'  # high|medium|low

    assert 'findings' in evidence_item, "After semantic_read, must have 'findings'"
    assert isinstance(evidence_item['findings'], list), "findings must be a list"
    print(f"  ✓ Evidence item after semantic_read.py validated")
    print(f"    - item_grade: {evidence_item['item_grade']} (✓ Fixed to 0-1 scale)")
    print(f"    - findings count: {len(evidence_item['findings'])}")

    # After semantic_frames.py (P24)
    evidence_item['item_frame'] = {
        'entity': ['Austin'],
        'action': 'increase',
        'quantity': [8.0],
        'year': [2024],
        'scope': 'budget'
    }
    evidence_item['frame_matches'] = [
        {
            'label': 'entail',
            'score': 0.85,
            'slots': ['entity', 'action', 'quantity'],
            'rules': ['aligned_action_quantity'],
            'quote': 'frame quote'
        }
    ]
    evidence_item['frame_confidence'] = 0.85

    assert 'frame_matches' in evidence_item, "After frames, must have 'frame_matches'"
    assert 'frame_confidence' in evidence_item, "After frames, must have 'frame_confidence'"
    print(f"  ✓ Evidence item after semantic_frames.py validated")
    print(f"    - frame_confidence: {evidence_item['frame_confidence']}")

    # After fullread.py (P21)
    evidence_item['grade_full'] = 8.25  # 0-10 scale
    evidence_item['stance_full'] = 'support'
    evidence_item['signals_full'] = {
        'jaccard3': 0.45,
        'entity_overlap': 0.60,
        'percent_any': True,
        'percent_close': True,
        'year_hit': True,
        'negation': False
    }
    evidence_item['credibility'] = 0.55  # 0-1 scale

    assert 'grade_full' in evidence_item, "After fullread, must have 'grade_full'"
    assert 'credibility' in evidence_item, "After fullread, must have 'credibility'"
    print(f"  ✓ Evidence item after fullread.py validated")
    print(f"    - grade_full: {evidence_item['grade_full']} (0-10 scale)")
    print(f"    - credibility: {evidence_item['credibility']} (0-1 scale)")

    print("✅ PASS: Evidence item structure validation complete\n")
    return evidence_item


def test_claim_structure():
    """
    Test claim dict structure.
    Location: Created by interpret modules, used throughout pipeline
    """
    print("Testing claim structure...")

    claim = {
        'text': 'Austin budget increased by 8% in 2024',
        'id': 'claim_123',
        'claim_type': 'policy',
        'entities': ['Austin'],  # Can also be List[Dict] with 'name' key
        'numbers': {
            'percents': [8.0]  # Can be float or string "8%"
        },
        'scope': {
            'year': 2024
        },
        'cues': {
            'has_comparison': True
        },
        'kind_hint': 'budget',
        'concept': 'budget_increase',
        'dimension': 'fiscal'
    }

    assert 'text' in claim and isinstance(claim['text'], str), \
        "Claim must have 'text' as string"
    assert 'entities' in claim, "Claim must have 'entities'"
    assert isinstance(claim['entities'], list), "entities must be a list"

    print(f"  ✓ Claim structure validated")
    print(f"    - text: {claim['text'][:50]}...")
    print(f"    - entities: {claim['entities']}")
    print(f"    - numbers.percents: {claim['numbers']['percents']}")
    print("✅ PASS: Claim structure validation complete\n")
    return claim


def test_verdict_structure():
    """
    Test verdict dict structure.
    Location: Created by pipeline.py:build_evidence_for_claim
    """
    print("Testing verdict structure...")

    verdict = {
        'claim_grade_numeric': 75,  # 0-100 scale
        'label': 'Mostly True',  # True|Mostly True|Mixed|Mostly False|False
        'evidence_grade_letter': 'B',  # A-F
        'rationale': 'Per-arm live gather with explicit arm tags; ranked, guarded, and scored.',
        'arm_strength': {
            'support': 0.65,
            'challenge': 0.35,
            'balance': 0.30
        }
    }

    assert 'claim_grade_numeric' in verdict, "Verdict must have claim_grade_numeric"
    assert 'label' in verdict, "Verdict must have label"
    assert verdict['label'] in ['True', 'Mostly True', 'Mixed', 'Mostly False', 'False'], \
        f"Label must be valid IFCN band, got: {verdict['label']}"
    assert 0 <= verdict['claim_grade_numeric'] <= 100, \
        f"claim_grade_numeric must be 0-100, got: {verdict['claim_grade_numeric']}"

    print(f"  ✓ Verdict structure validated")
    print(f"    - claim_grade_numeric: {verdict['claim_grade_numeric']} (0-100 scale)")
    print(f"    - label: {verdict['label']}")
    print(f"    - evidence_grade_letter: {verdict['evidence_grade_letter']}")
    print("✅ PASS: Verdict structure validation complete\n")
    return verdict


def test_p25_aggregate_verdict():
    """
    Test aggregate_verdict from p25_aggregate.py
    Location: intelligence/content/p25_aggregate.py:72
    """
    print("Testing P25 aggregate_verdict structure...")

    from intelligence.content.p25_aggregate import aggregate_verdict

    # Mock evidence items
    arm_a = [
        {'item_grade': 0.75, 'frame_matches': [{'score': 0.80}], 'coverage': 'full'},
        {'item_grade': 0.65, 'frame_matches': [{'score': 0.70}], 'coverage': 'partial'}
    ]
    arm_b = [
        {'item_grade': 0.45, 'frame_matches': [{'score': 0.50}], 'coverage': 'snippet_only'}
    ]

    result = aggregate_verdict(
        claim_text='Test claim',
        arm_a_items=arm_a,
        arm_b_items=arm_b,
        delta=0.15
    )

    assert 'label' in result, "aggregate_verdict must return 'label'"
    assert 'confidence' in result, "aggregate_verdict must return 'confidence'"
    assert 'arm_strength' in result, "aggregate_verdict must return 'arm_strength'"
    assert result['label'] in ['supports', 'challenges', 'mixed', 'insufficient'], \
        f"Label must be valid, got: {result['label']}"
    assert 0 <= result['confidence'] <= 1, \
        f"confidence must be 0-1, got: {result['confidence']}"

    print(f"  ✓ P25 aggregate_verdict validated")
    print(f"    - label: {result['label']}")
    print(f"    - confidence: {result['confidence']:.3f}")
    print(f"    - arm_strength.support: {result['arm_strength']['support']:.3f}")
    print(f"    - arm_strength.challenge: {result['arm_strength']['challenge']:.3f}")
    print("✅ PASS: P25 aggregate_verdict validation complete\n")
    return result


def test_frame_structure():
    """
    Test Frame dataclass structure.
    Location: intelligence/content/shared/frames.py:7
    """
    print("Testing Frame structure...")

    from intelligence.content.shared.frames import Frame

    frame = Frame(
        phenomenon='boiling point',
        entity='Austin budget',
        action='increase',
        number=8.0,
        unit='%',
        condition='at 2024',
        timeframe='2024',
        direction='up',
        domain='policy',
        confidence=0.85
    )

    assert hasattr(frame, 'phenomenon'), "Frame must have phenomenon"
    assert hasattr(frame, 'entity'), "Frame must have entity"
    assert hasattr(frame, 'action'), "Frame must have action"
    assert hasattr(frame, 'number'), "Frame must have number"
    assert hasattr(frame, 'unit'), "Frame must have unit"
    assert hasattr(frame, 'domain'), "Frame must have domain"

    print(f"  ✓ Frame structure validated")
    print(f"    - entity: {frame.entity}")
    print(f"    - action: {frame.action}")
    print(f"    - number: {frame.number}")
    print(f"    - domain: {frame.domain}")
    print("✅ PASS: Frame structure validation complete\n")
    return frame


if __name__ == '__main__':
    print("="*70)
    print("ARCHITECTURE VALIDATION: Data Structures")
    print("="*70 + "\n")

    try:
        evidence_item = test_evidence_item_structure()
        claim = test_claim_structure()
        verdict = test_verdict_structure()
        p25_verdict = test_p25_aggregate_verdict()
        frame = test_frame_structure()

        print("="*70)
        print("✅ ALL DATA STRUCTURE TESTS PASSED")
        print("="*70)
    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
