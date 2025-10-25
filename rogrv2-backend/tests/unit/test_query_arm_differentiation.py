"""
Unit tests for query generation arm differentiation fix.

Tests that Arm A (support) and Arm B (challenge) generate different queries.

Spec: Section 5.2.5
"""

import pytest
from intelligence.strategy.plan_v2 import generate_queries_r1, generate_queries_r2


def test_r1_arm_differentiation():
    """Test that R1 generates different queries for each arm."""

    claim = {
        "text": "Water boils at 100 degrees Celsius",
        "concept": "water boiling point",
        "dimension": "temperature",
        "entities": ["Water"],
        "numbers": {"number_units": [[100, "degrees Celsius"]]}
    }

    base_plan = {
        "meta": {
            "concept": "water boiling point",
            "dimension": "temperature"
        }
    }

    # Generate queries for both arms
    queries_a = generate_queries_r1(claim, "A", base_plan)
    queries_b = generate_queries_r1(claim, "B", base_plan)

    # Assert both arms generated queries
    assert len(queries_a) > 0, "Arm A should generate queries"
    assert len(queries_b) > 0, "Arm B should generate queries"

    # Assert queries are different
    assert set(queries_a) != set(queries_b), "Arm A and B queries should be different"

    # Assert less than 30% overlap (spec requirement)
    identical = set(queries_a) & set(queries_b)
    overlap_ratio = len(identical) / len(queries_a)
    assert overlap_ratio < 0.3, f"Query overlap {overlap_ratio:.1%} exceeds 30% threshold"


def test_r2_arm_differentiation():
    """Test that R2 generates different queries for each arm."""

    claim = {
        "text": "Water boils at 100 degrees Celsius",
        "concept": "water boiling point",
        "dimension": "temperature",
        "entities": ["Water"],
        "numbers": {"number_units": [[100, "degrees Celsius"]]}
    }

    base_plan = {
        "meta": {
            "concept": "water boiling point",
            "dimension": "temperature"
        }
    }

    # Generate queries for both arms
    queries_a = generate_queries_r2(claim, "A", base_plan)
    queries_b = generate_queries_r2(claim, "B", base_plan)

    # Assert both arms generated queries
    assert len(queries_a) > 0, "Arm A should generate queries"
    assert len(queries_b) > 0, "Arm B should generate queries"

    # Assert queries are different
    assert set(queries_a) != set(queries_b), "Arm A and B queries should be different"

    # Assert less than 30% overlap (spec requirement)
    identical = set(queries_a) & set(queries_b)
    overlap_ratio = len(identical) / len(queries_a)
    assert overlap_ratio < 0.3, f"Query overlap {overlap_ratio:.1%} exceeds 30% threshold"


def test_arm_a_has_support_intent():
    """Test that Arm A queries have support-seeking intent."""

    claim = {
        "text": "Water boils at 100 degrees Celsius",
        "concept": "water boiling point",
        "dimension": "temperature",
        "entities": ["Water"],
        "numbers": {"number_units": [[100, "degrees Celsius"]]}
    }

    base_plan = {
        "meta": {
            "concept": "water boiling point",
            "dimension": "temperature"
        }
    }

    queries_a = generate_queries_r1(claim, "A", base_plan)

    # Join all queries to check for support-seeking keywords
    all_queries = " ".join(queries_a).lower()

    # Arm A should have support-seeking terms
    support_terms = ["evidence", "scientific", "confirmed", "established", "official", "standard", "data", "research", "studies"]
    has_support_term = any(term in all_queries for term in support_terms)

    assert has_support_term, f"Arm A queries should contain support-seeking terms. Queries: {queries_a}"


def test_arm_b_has_challenge_intent():
    """Test that Arm B queries have challenge-seeking intent."""

    claim = {
        "text": "Water boils at 100 degrees Celsius",
        "concept": "water boiling point",
        "dimension": "temperature",
        "entities": ["Water"],
        "numbers": {"number_units": [[100, "degrees Celsius"]]}
    }

    base_plan = {
        "meta": {
            "concept": "water boiling point",
            "dimension": "temperature"
        }
    }

    queries_b = generate_queries_r1(claim, "B", base_plan)

    # Join all queries to check for challenge-seeking keywords
    all_queries = " ".join(queries_b).lower()

    # Arm B should have challenge-seeking terms
    challenge_terms = ["not", "exceptions", "variations", "different", "depends", "varies", "altitude", "pressure", "atmospheric", "conditions"]
    has_challenge_term = any(term in all_queries for term in challenge_terms)

    assert has_challenge_term, f"Arm B queries should contain challenge-seeking terms. Queries: {queries_b}"


def test_zero_query_overlap():
    """Test that Arm A and Arm B have zero overlapping queries (ideal case)."""

    claim = {
        "text": "Water boils at 100 degrees Celsius",
        "concept": "water boiling point",
        "dimension": "temperature",
        "entities": ["Water"],
        "numbers": {"number_units": [[100, "degrees Celsius"]]}
    }

    base_plan = {
        "meta": {
            "concept": "water boiling point",
            "dimension": "temperature"
        }
    }

    # Test R1
    queries_r1_a = generate_queries_r1(claim, "A", base_plan)
    queries_r1_b = generate_queries_r1(claim, "B", base_plan)

    identical_r1 = set(queries_r1_a) & set(queries_r1_b)
    assert len(identical_r1) == 0, f"R1: Expected zero overlap, got {len(identical_r1)} identical queries: {identical_r1}"

    # Test R2
    queries_r2_a = generate_queries_r2(claim, "A", base_plan)
    queries_r2_b = generate_queries_r2(claim, "B", base_plan)

    identical_r2 = set(queries_r2_a) & set(queries_r2_b)
    assert len(identical_r2) == 0, f"R2: Expected zero overlap, got {len(identical_r2)} identical queries: {identical_r2}"


def test_r1_returns_5_queries():
    """Test that R1 returns approximately 5 queries (precision mode)."""

    claim = {
        "text": "Water boils at 100 degrees Celsius",
        "concept": "water boiling point",
        "dimension": "temperature",
        "entities": ["Water"],
        "numbers": {"number_units": [[100, "degrees Celsius"]]}
    }

    base_plan = {
        "meta": {
            "concept": "water boiling point",
            "dimension": "temperature"
        }
    }

    queries_a = generate_queries_r1(claim, "A", base_plan)
    queries_b = generate_queries_r1(claim, "B", base_plan)

    # R1 should return ~5 queries (precision mode)
    assert 3 <= len(queries_a) <= 7, f"R1 Arm A should return ~5 queries, got {len(queries_a)}"
    assert 3 <= len(queries_b) <= 7, f"R1 Arm B should return ~5 queries, got {len(queries_b)}"


def test_r2_returns_8_queries():
    """Test that R2 returns approximately 8 queries (recall mode)."""

    claim = {
        "text": "Water boils at 100 degrees Celsius",
        "concept": "water boiling point",
        "dimension": "temperature",
        "entities": ["Water"],
        "numbers": {"number_units": [[100, "degrees Celsius"]]}
    }

    base_plan = {
        "meta": {
            "concept": "water boiling point",
            "dimension": "temperature"
        }
    }

    queries_a = generate_queries_r2(claim, "A", base_plan)
    queries_b = generate_queries_r2(claim, "B", base_plan)

    # R2 should return ~8 queries (recall mode)
    assert 5 <= len(queries_a) <= 10, f"R2 Arm A should return ~8 queries, got {len(queries_a)}"
    assert 5 <= len(queries_b) <= 10, f"R2 Arm B should return ~8 queries, got {len(queries_b)}"


def test_different_claim_types():
    """Test arm differentiation works for various claim types."""

    claims = [
        {
            "text": "The Earth is 93 million miles from the Sun",
            "concept": "Earth-Sun distance",
            "dimension": "distance",
            "entities": ["Earth", "Sun"],
            "numbers": {"number_units": [[93, "million miles"]]}
        },
        {
            "text": "Vitamin C prevents colds",
            "concept": "Vitamin C cold prevention",
            "dimension": "efficacy",
            "entities": ["Vitamin C"],
            "numbers": {"number_units": []}
        },
        {
            "text": "Coffee contains caffeine",
            "concept": "coffee caffeine content",
            "dimension": "composition",
            "entities": ["coffee", "caffeine"],
            "numbers": {"number_units": []}
        }
    ]

    for claim in claims:
        base_plan = {
            "meta": {
                "concept": claim.get("concept", ""),
                "dimension": claim.get("dimension", "")
            }
        }

        queries_a = generate_queries_r1(claim, "A", base_plan)
        queries_b = generate_queries_r1(claim, "B", base_plan)

        # Assert queries are different for each claim
        identical = set(queries_a) & set(queries_b)
        overlap_ratio = len(identical) / len(queries_a) if queries_a else 0

        assert overlap_ratio < 0.3, f"Claim '{claim['text']}' has {overlap_ratio:.1%} overlap (>30%)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
