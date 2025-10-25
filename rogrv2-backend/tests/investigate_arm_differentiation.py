"""
Investigation script for arm differentiation bug in query generation.

Tests whether arm parameter actually differentiates queries in generate_queries_r1/r2.
"""

from intelligence.strategy.plan_v2 import generate_queries_r1, generate_queries_r2


def investigate_query_generation():
    """Investigate whether arm parameter actually differentiates queries."""

    claim = {
        "text": "Water boils at 100 degrees Celsius",
        "concept": "water boiling point",
        "dimension": "temperature",
        "entities": ["Water", "Celsius"],
        "numbers": {"number_units": []}
    }

    base_plan = {"meta": {"concept": "water boiling point", "dimension": "temperature"}}

    # Generate R1 queries for both arms
    queries_a_r1 = generate_queries_r1(claim, "A", base_plan)
    queries_b_r1 = generate_queries_r1(claim, "B", base_plan)

    print("=== ARM DIFFERENTIATION TEST ===")
    print("\n--- R1 (Precision) Queries ---")
    print(f"\nArm A queries ({len(queries_a_r1)}):")
    for i, q in enumerate(queries_a_r1, 1):
        print(f"  {i}. {q}")

    print(f"\nArm B queries ({len(queries_b_r1)}):")
    for i, q in enumerate(queries_b_r1, 1):
        print(f"  {i}. {q}")

    # Check for identical queries in R1
    identical_r1 = set(queries_a_r1) & set(queries_b_r1)
    unique_to_a_r1 = set(queries_a_r1) - set(queries_b_r1)
    unique_to_b_r1 = set(queries_b_r1) - set(queries_a_r1)

    print(f"\n=== R1 ANALYSIS ===")
    print(f"Identical queries: {len(identical_r1)}")
    print(f"Unique to Arm A: {len(unique_to_a_r1)}")
    print(f"Unique to Arm B: {len(unique_to_b_r1)}")

    if len(identical_r1) == len(queries_a_r1):
        print("\n❌ R1 BUG CONFIRMED: All queries are identical!")
        print("   The arm parameter is NOT being used to differentiate.")
        r1_bug = True
    elif len(identical_r1) / len(queries_a_r1) > 0.7:
        print("\n⚠️  R1 WARNING: >70% queries identical, arm differentiation weak")
        r1_bug = True
    else:
        print("\n✅ R1 arm differentiation working (queries are different)")
        r1_bug = False

    # Generate R2 queries for both arms
    print("\n\n--- R2 (Recall) Queries ---")
    queries_a_r2 = generate_queries_r2(claim, "A", base_plan)
    queries_b_r2 = generate_queries_r2(claim, "B", base_plan)

    print(f"\nArm A queries ({len(queries_a_r2)}):")
    for i, q in enumerate(queries_a_r2, 1):
        print(f"  {i}. {q}")

    print(f"\nArm B queries ({len(queries_b_r2)}):")
    for i, q in enumerate(queries_b_r2, 1):
        print(f"  {i}. {q}")

    # Check for identical queries in R2
    identical_r2 = set(queries_a_r2) & set(queries_b_r2)
    unique_to_a_r2 = set(queries_a_r2) - set(queries_b_r2)
    unique_to_b_r2 = set(queries_b_r2) - set(queries_a_r2)

    print(f"\n=== R2 ANALYSIS ===")
    print(f"Identical queries: {len(identical_r2)}")
    print(f"Unique to Arm A: {len(unique_to_a_r2)}")
    print(f"Unique to Arm B: {len(unique_to_b_r2)}")

    if len(identical_r2) == len(queries_a_r2):
        print("\n❌ R2 BUG CONFIRMED: All queries are identical!")
        print("   The arm parameter is NOT being used to differentiate.")
        r2_bug = True
    elif len(identical_r2) / len(queries_a_r2) > 0.7:
        print("\n⚠️  R2 WARNING: >70% queries identical, arm differentiation weak")
        r2_bug = True
    else:
        print("\n✅ R2 arm differentiation working (queries are different)")
        r2_bug = False

    # Overall conclusion
    print("\n\n=== OVERALL CONCLUSION ===")
    if r1_bug and r2_bug:
        print("❌ BUG CONFIRMED: Both R1 and R2 have arm differentiation issues")
    elif r1_bug or r2_bug:
        print("⚠️  PARTIAL BUG: One of R1 or R2 has arm differentiation issues")
    else:
        print("✅ No bug found: Both R1 and R2 differentiate arms properly")

    return {
        "r1": {
            "queries_a": queries_a_r1,
            "queries_b": queries_b_r1,
            "identical_count": len(identical_r1),
            "bug_confirmed": r1_bug
        },
        "r2": {
            "queries_a": queries_a_r2,
            "queries_b": queries_b_r2,
            "identical_count": len(identical_r2),
            "bug_confirmed": r2_bug
        },
        "overall_bug_confirmed": r1_bug or r2_bug
    }


if __name__ == "__main__":
    result = investigate_query_generation()
