"""
Phase 1 Integration Test
Verifies that build_finding_v2() works end-to-end
"""
import pytest

def test_build_finding_v2_integration():
    """Test new orchestrated grading system"""
    from intelligence.content.grade import build_finding_v2

    # Test claim
    claim_text = "Water boils at 100°C at sea level"

    # Test evidence item
    evidence_item = {
        'url': 'https://en.wikipedia.org/wiki/Boiling_point',
        'snippet': 'Water boils at 100°C (212°F) at standard atmospheric pressure',
        'content': 'Water boils at 100 degrees Celsius at sea level. The boiling point varies with pressure.',
        'arm': 'A',
        'coverage': 'full',
    }

    # Call new function
    result = build_finding_v2(claim_text, 'A', evidence_item)

    # Verify structure
    assert 'item_grade' in result
    assert 'features' in result
    assert 'orchestrated' in result

    # Verify grade is 0-1 scale
    grade = result['item_grade']
    assert 0.0 <= grade <= 1.0, f"Grade {grade} outside 0-1 range"

    # Verify features available
    features = result['features']
    assert features['p23_available'] == True, "P23 should be available"

    print(f"✓ build_finding_v2() works!")
    print(f"  Grade: {grade} (0-1 scale)")
    print(f"  Features: P21={features['p21_available']}, P23={features['p23_available']}, P24={features['p24_available']}")

    return True

if __name__ == '__main__':
    test_build_finding_v2_integration()
    print("\n✓ Phase 1 integration test PASSED")
