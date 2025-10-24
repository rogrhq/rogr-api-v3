"""
Unit tests for failed item handling.

Tests that items with fetch_status='failed' are skipped in scoring.
"""
import pytest
from intelligence.content.grade import fuse_module_grades


def test_failed_item_returns_zero():
    """Test that failed items return 0.0 grade without scoring."""
    # Create a failed item
    evidence_item = {
        'url': 'https://failed.example.com',
        'fetch_status': 'failed',
        'fetch_error': 'Empty content returned',
        'content': ''
    }

    # Create mock features (these should be ignored)
    features = {
        'p23_available': True,
        'p23': {'item_grade': 0.8},
        'p24_available': True,
        'p24': {'frame_confidence': 0.7},
        'p21_available': True,
        'p21': {'credibility': 0.9}
    }

    # Call fuse_module_grades
    item_grade = fuse_module_grades(features, evidence_item)

    # Should return 0.0 for failed items
    assert item_grade == 0.0
    print(f"✓ Failed item returned 0.0 grade (skipped scoring)")


def test_successful_item_uses_scoring():
    """Test that successful items use normal scoring."""
    # Create a successful item
    evidence_item = {
        'url': 'https://success.example.com',
        'fetch_status': 'success',
        'fetch_error': None,
        'content': 'x' * 200,
        'coverage': 'full'
    }

    # Create mock features
    features = {
        'p23_available': True,
        'p23': {'item_grade': 0.8},
        'p24_available': True,
        'p24': {'frame_confidence': 0.7},
        'p21_available': True,
        'p21': {'credibility': 0.9}
    }

    # Call fuse_module_grades
    item_grade = fuse_module_grades(features, evidence_item)

    # Should return non-zero grade using normal scoring
    assert item_grade > 0.0
    assert item_grade <= 1.0
    print(f"✓ Successful item used normal scoring: {item_grade:.3f}")


def test_minimal_item_uses_scoring():
    """Test that minimal items (not failed) still get scored."""
    # Create a minimal item (low content but not failed)
    evidence_item = {
        'url': 'https://minimal.example.com',
        'fetch_status': 'minimal',
        'fetch_error': 'Content length below threshold (100 chars)',
        'content': 'short content',
        'coverage': 'partial'
    }

    # Create mock features
    features = {
        'p23_available': True,
        'p23': {'item_grade': 0.5},
        'p24_available': True,
        'p24': {'frame_confidence': 0.4},
        'p21_available': True,
        'p21': {'credibility': 0.6}
    }

    # Call fuse_module_grades
    item_grade = fuse_module_grades(features, evidence_item)

    # Should return non-zero grade (minimal items still get scored)
    assert item_grade > 0.0
    assert item_grade <= 1.0
    print(f"✓ Minimal item still scored: {item_grade:.3f}")


def test_item_without_fetch_status_field():
    """Test backward compatibility - items without fetch_status field."""
    # Create item without fetch_status (old format)
    evidence_item = {
        'url': 'https://legacy.example.com',
        'content': 'some content',
        'coverage': 'full'
    }

    # Create mock features
    features = {
        'p23_available': True,
        'p23': {'item_grade': 0.7},
        'p24_available': True,
        'p24': {'frame_confidence': 0.6},
        'p21_available': True,
        'p21': {'credibility': 0.8}
    }

    # Call fuse_module_grades
    item_grade = fuse_module_grades(features, evidence_item)

    # Should work normally (backward compatible)
    assert item_grade > 0.0
    assert item_grade <= 1.0
    print(f"✓ Legacy item (no fetch_status) scored normally: {item_grade:.3f}")


if __name__ == "__main__":
    print("Running failed item handling tests...")
    test_failed_item_returns_zero()
    test_successful_item_uses_scoring()
    test_minimal_item_uses_scoring()
    test_item_without_fetch_status_field()
    print("✓ All tests passed!")
