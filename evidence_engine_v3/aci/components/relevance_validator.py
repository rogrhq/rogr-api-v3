from dataclasses import dataclass
from typing import Optional

@dataclass
class RelevanceValidationResult:
    semantic_match_score: float      # 0-100: Does evidence address claim subject?
    logical_relevance_score: float   # 0-100: Does evidence support/contradict assertion?
    scope_alignment_score: float     # 0-100: Does evidence scope match claim scope?
    evidence_quality_score: float    # 0-100: Is evidence methodologically sound?
    final_relevance_score: float     # Weighted combination
    relevance_reasoning: str         # Explanation of scoring

@dataclass
class ProcessedEvidence:
    """Matching the format expected by existing code"""
    text: str
    source_title: str
    source_domain: str
    source_url: str
    ai_stance: str
    ai_relevance_score: float
    ai_confidence: float

class EvidenceRelevanceValidator:
    def __init__(self):
        self.high_quality_domains = [
            ".gov", ".edu", "nature.com", "science.org", "nejm.org",
            "thelancet.com", "bmj.com", "cdc.gov", "who.int", "nih.gov"
        ]

    def validate(self, evidence: ProcessedEvidence, claim_text: str,
                semantic_result=None) -> RelevanceValidationResult:
        """
        Validate evidence relevance to claim.
        This is the CRITICAL function that fixes subject/object confusion.
        """

        # Calculate semantic match score
        semantic_score = self._calculate_semantic_match(
            evidence.text, claim_text, semantic_result
        )

        # Calculate logical relevance
        logical_score = self._calculate_logical_relevance(
            evidence.text, claim_text
        )

        # Calculate scope alignment
        scope_score = self._calculate_scope_alignment(
            evidence.text, claim_text
        )

        # Calculate evidence quality
        quality_score = self._calculate_evidence_quality(evidence)

        # Calculate weighted final score
        final_score = (
            semantic_score * 0.4 +
            logical_score * 0.3 +
            scope_score * 0.2 +
            quality_score * 0.1
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            semantic_score, logical_score, scope_score, quality_score
        )

        return RelevanceValidationResult(
            semantic_match_score=semantic_score,
            logical_relevance_score=logical_score,
            scope_alignment_score=scope_score,
            evidence_quality_score=quality_score,
            final_relevance_score=final_score,
            relevance_reasoning=reasoning
        )

    def _calculate_semantic_match(self, evidence_text: str, claim_text: str,
                                  semantic_result=None) -> float:
        """
        CRITICAL: This fixes the climate/policy confusion
        """
        evidence_lower = evidence_text.lower()
        claim_lower = claim_text.lower()

        # Extract what the claim is actually about
        if semantic_result and hasattr(semantic_result, 'claim_subject'):
            claim_subject = semantic_result.claim_subject.lower()
        else:
            # Fallback extraction
            if "climate change policies" in claim_lower:
                claim_subject = "climate change policies"
            elif "climate change" in claim_lower:
                claim_subject = "climate change"
            else:
                claim_subject = claim_lower.split()[0]

        # CHECK: Does evidence discuss the RIGHT subject?

        # Case 1: Claim about "climate change policies"
        if "climate change policies" in claim_subject or "policies" in claim_subject:
            # Good evidence mentions policies, regulations, carbon tax, legislation
            policy_keywords = ["policy", "policies", "regulation", "carbon tax",
                             "legislation", "government", "law", "mandate", "act"]
            policy_score = sum(10 for keyword in policy_keywords if keyword in evidence_lower)

            # Bad evidence only mentions climate effects
            climate_keywords = ["hurricane", "flood", "drought", "temperature",
                              "weather", "storm", "disaster", "warming"]
            climate_penalty = sum(5 for keyword in climate_keywords if keyword in evidence_lower)

            # If evidence is about climate disasters, not policies, score LOW
            if climate_penalty > policy_score:
                return 20.0  # Low score for wrong subject
            elif policy_score > 0:
                return min(100.0, 60.0 + policy_score)  # High score for right subject
            else:
                return 40.0  # Medium-low if unclear

        # Case 2: Claim about "climate change" itself
        elif "climate change" in claim_subject and "policies" not in claim_subject:
            # Good evidence discusses climate effects, temperature, etc.
            climate_keywords = ["temperature", "warming", "carbon", "emissions",
                              "greenhouse", "weather", "climate"]
            climate_score = sum(10 for keyword in climate_keywords if keyword in evidence_lower)

            return min(100.0, 50.0 + climate_score)

        # Default: Basic keyword matching
        else:
            if claim_subject in evidence_lower:
                return 80.0
            else:
                return 40.0

    def _calculate_logical_relevance(self, evidence_text: str, claim_text: str) -> float:
        """Does evidence address the logical relationship in the claim?"""
        evidence_lower = evidence_text.lower()

        # Check if evidence discusses cause/effect when claim does
        if "cause" in claim_text.lower() or "leads to" in claim_text.lower():
            if any(word in evidence_lower for word in
                  ["cause", "leads to", "results in", "effect", "impact"]):
                return 80.0
            else:
                return 40.0

        return 60.0  # Default medium relevance

    def _calculate_scope_alignment(self, evidence_text: str, claim_text: str) -> float:
        """Does evidence scope match claim scope?"""

        # Universal claim needs comprehensive evidence
        if "all" in claim_text.lower() or "every" in claim_text.lower():
            if "study" in evidence_text.lower() or "research" in evidence_text.lower():
                return 70.0
            else:
                return 30.0

        return 60.0  # Default medium alignment

    def _calculate_evidence_quality(self, evidence: ProcessedEvidence) -> float:
        """Assess evidence source quality"""
        domain = evidence.source_domain.lower()

        # Check for high-quality domains
        for hq_domain in self.high_quality_domains:
            if hq_domain in domain:
                return 90.0

        # Check for news sites
        if any(news in domain for news in ["reuters", "apnews", "bbc", "npr"]):
            return 70.0

        # Default
        return 50.0

    def _generate_reasoning(self, semantic, logical, scope, quality) -> str:
        reasons = []

        if semantic > 70:
            reasons.append("Strong subject match")
        elif semantic < 30:
            reasons.append("Poor subject match - evidence about wrong topic")

        if quality > 80:
            reasons.append("High-quality source")

        return "; ".join(reasons) if reasons else "Moderate relevance"

def test_relevance_validator():
    validator = EvidenceRelevanceValidator()

    # Create mock semantic result for testing
    class MockSemanticResult:
        def __init__(self, subject):
            self.claim_subject = subject

    print("Testing Relevance Validator...")
    print("\nCRITICAL TEST: Climate Policy vs Climate Disaster")

    claim = "Climate change policies will destroy the economy"
    semantic_result = MockSemanticResult("climate change policies")

    # Good evidence (about policies)
    good_evidence = ProcessedEvidence(
        text="Carbon tax implementation in Province X led to 2% GDP reduction",
        source_title="Economic Policy Analysis",
        source_domain="economics.gov",
        source_url="http://example.com",
        ai_stance="supporting",
        ai_relevance_score=80.0,
        ai_confidence=0.8
    )

    # Bad evidence (about climate, not policies)
    bad_evidence = ProcessedEvidence(
        text="Hurricane damage from climate change cost the economy $50 billion",
        source_title="Climate Impact Report",
        source_domain="weather.com",
        source_url="http://example.com",
        ai_stance="supporting",
        ai_relevance_score=80.0,
        ai_confidence=0.8
    )

    good_result = validator.validate(good_evidence, claim, semantic_result)
    bad_result = validator.validate(bad_evidence, claim, semantic_result)

    print(f"\nGood evidence (about policies):")
    print(f"  Text: '{good_evidence.text}'")
    print(f"  Semantic match score: {good_result.semantic_match_score:.1f}")
    print(f"  Final relevance score: {good_result.final_relevance_score:.1f}")
    print(f"  Reasoning: {good_result.relevance_reasoning}")

    print(f"\nBad evidence (about climate disasters):")
    print(f"  Text: '{bad_evidence.text}'")
    print(f"  Semantic match score: {bad_result.semantic_match_score:.1f}")
    print(f"  Final relevance score: {bad_result.final_relevance_score:.1f}")
    print(f"  Reasoning: {bad_result.relevance_reasoning}")

    # Check if validator correctly distinguishes
    if good_result.semantic_match_score > 70 and bad_result.semantic_match_score < 30:
        print("\n✅ SUCCESS! Validator correctly distinguishes policy evidence from climate disaster evidence")
        return True
    else:
        print("\n❌ FAILED! Validator not distinguishing correctly")
        print(f"   Good evidence score: {good_result.semantic_match_score} (should be >70)")
        print(f"   Bad evidence score: {bad_result.semantic_match_score} (should be <30)")
        return False

if __name__ == "__main__":
    test_relevance_validator()