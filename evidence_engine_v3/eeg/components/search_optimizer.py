from dataclasses import dataclass
from typing import List

@dataclass
class SearchStrategy:
    primary_queries: List[str]        # Main search queries
    methodology_queries: List[str]    # "peer reviewed", "government study"
    counter_queries: List[str]        # "debunked", "myth", "false"
    total_queries: int

class SearchOptimizer:
    def __init__(self):
        self.max_queries = 12  # HARD LIMIT
        self.methodology_terms = [
            "peer reviewed study",
            "government report",
            "scientific research",
            "official data"
        ]
        self.counter_terms = [
            "debunked",
            "myth",
            "false",
            "disproven",
            "fact check"
        ]

    def optimize_searches(self, claim_text: str, semantic_result=None) -> SearchStrategy:
        """
        Generate optimized search queries - MAX 12 total
        """
        queries = SearchStrategy(
            primary_queries=[],
            methodology_queries=[],
            counter_queries=[],
            total_queries=0
        )

        # Clean the claim text
        claim_clean = claim_text.strip()

        # 1. Primary queries (4 max)
        queries.primary_queries = [
            claim_clean,  # Original claim
            f'"{claim_clean}"',  # Exact match
        ]

        # Add subject-specific query if available
        if semantic_result and hasattr(semantic_result, 'claim_subject'):
            queries.primary_queries.append(
                f"{semantic_result.claim_subject} {semantic_result.claim_object}"
            )

        # Limit primary queries
        queries.primary_queries = queries.primary_queries[:4]

        # 2. Methodology queries (4 max)
        for i, term in enumerate(self.methodology_terms[:4]):
            # Combine claim with methodology term
            queries.methodology_queries.append(
                f"{claim_clean} {term}"
            )

        # 3. Counter-evidence queries (4 max)
        for i, term in enumerate(self.counter_terms[:4]):
            queries.counter_queries.append(
                f"{claim_clean} {term}"
            )

        # ENFORCE HARD LIMIT
        total = (len(queries.primary_queries) +
                len(queries.methodology_queries) +
                len(queries.counter_queries))

        if total > self.max_queries:
            # Trim excess queries
            excess = total - self.max_queries

            # Trim from counter queries first
            if len(queries.counter_queries) > 2:
                trim = min(excess, len(queries.counter_queries) - 2)
                queries.counter_queries = queries.counter_queries[:-trim]
                excess -= trim

            # Then from methodology queries
            if excess > 0 and len(queries.methodology_queries) > 2:
                trim = min(excess, len(queries.methodology_queries) - 2)
                queries.methodology_queries = queries.methodology_queries[:-trim]
                excess -= trim

            # Finally from primary if needed
            if excess > 0:
                queries.primary_queries = queries.primary_queries[:-excess]

        queries.total_queries = (len(queries.primary_queries) +
                                len(queries.methodology_queries) +
                                len(queries.counter_queries))

        return queries

    def get_all_queries(self, strategy: SearchStrategy) -> List[str]:
        """Get all queries as a single list"""
        all_queries = (strategy.primary_queries +
                      strategy.methodology_queries +
                      strategy.counter_queries)
        return all_queries

def test_search_optimizer():
    optimizer = SearchOptimizer()

    test_claims = [
        "COVID vaccines are safe and effective",
        "Climate change policies will destroy the economy",
        "The Earth is flat"
    ]

    print("Testing Search Optimizer...")
    all_passed = True

    for claim in test_claims:
        strategy = optimizer.optimize_searches(claim)

        print(f"\nClaim: {claim}")
        print(f"Primary queries ({len(strategy.primary_queries)}): {strategy.primary_queries[:2]}...")
        print(f"Methodology queries ({len(strategy.methodology_queries)}): {strategy.methodology_queries[:2]}...")
        print(f"Counter queries ({len(strategy.counter_queries)}): {strategy.counter_queries[:2]}...")
        print(f"TOTAL QUERIES: {strategy.total_queries}")

        if strategy.total_queries > 12:
            print(f"❌ FAILED: Too many queries ({strategy.total_queries} > 12)")
            all_passed = False
        elif strategy.total_queries < 6:
            print(f"⚠️ WARNING: Very few queries ({strategy.total_queries} < 6)")
        else:
            print(f"✅ Query count OK: {strategy.total_queries} queries")

        # Check for counter-evidence
        if len(strategy.counter_queries) == 0:
            print("❌ FAILED: No counter-evidence queries")
            all_passed = False

    if all_passed:
        print("\n✅ All search optimization tests passed!")
    else:
        print("\n❌ Some tests failed. Review the optimizer.")

    return all_passed

if __name__ == "__main__":
    test_search_optimizer()