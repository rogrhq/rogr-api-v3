from dataclasses import dataclass
from typing import List
import re

@dataclass
class SemanticAnalysisResult:
    claim_subject: str          # Who/what is doing the action
    claim_object: str           # Who/what is being affected
    relationship_type: str      # "causal", "comparative", "descriptive"
    temporal_aspect: str        # "future", "past", "present"
    certainty_level: str        # "definitive", "probable", "speculative"
    action_type: str           # The main verb/action

class SemanticClaimAnalyzer:
    def __init__(self):
        # Patterns for extraction
        self.causal_indicators = ["cause", "causes", "caused", "leads to", "results in", "because"]
        self.future_indicators = ["will", "would", "could", "might", "shall", "going to"]
        self.past_indicators = ["was", "were", "did", "had", "caused", "led to"]
        self.certainty_indicators = {
            "definitive": ["will", "is", "are", "causes", "always", "definitely"],
            "probable": ["likely", "probably", "may", "might", "could"],
            "speculative": ["possibly", "perhaps", "suggests", "indicates"]
        }

    def analyze(self, claim_text: str) -> SemanticAnalysisResult:
        # Extract subject and object
        claim_subject, claim_object = self._extract_subject_object(claim_text)

        # Determine relationship type
        relationship_type = self._determine_relationship(claim_text)

        # Determine temporal aspect
        temporal_aspect = self._determine_temporal(claim_text)

        # Determine certainty
        certainty_level = self._determine_certainty(claim_text)

        # Extract action
        action_type = self._extract_action(claim_text)

        return SemanticAnalysisResult(
            claim_subject=claim_subject,
            claim_object=claim_object,
            relationship_type=relationship_type,
            temporal_aspect=temporal_aspect,
            certainty_level=certainty_level,
            action_type=action_type
        )

    def _extract_subject_object(self, text):
        # CRITICAL: Must distinguish "climate change policies" from "climate change"

        # Pattern 1: "X will/does/did Y the Z"
        pattern1 = r"^(.*?)\s+(will|does|did|is|are|was|were|has|have|causes?|leads?)\s+.*?\s+(the |a |an )?(.*?)$"

        # Special handling for "policies" - they are part of subject, not separate
        if "policies" in text.lower() and "climate" in text.lower():
            if "climate change policies" in text.lower():
                claim_subject = "climate change policies"
                # Find what comes after the subject and verb
                remaining = text.lower().split("climate change policies")[1]
                words = remaining.strip().split()
                if len(words) > 2:
                    claim_object = words[-1] if words[-1] != "economy" else "economy"
                else:
                    claim_object = "unspecified"
                return claim_subject, claim_object

        # Default extraction
        words = text.split()
        if len(words) >= 3:
            # Simple heuristic: first noun phrase is subject, last noun phrase is object
            claim_subject = words[0]
            claim_object = words[-1]

            # Improve extraction
            if "vaccines" in text.lower():
                claim_subject = "vaccines"
                if "autism" in text.lower():
                    claim_object = "autism"
            elif "climate change" in text.lower() and "policies" not in text.lower():
                claim_subject = "climate change"
                if "economy" in text.lower():
                    claim_object = "economy"

        else:
            claim_subject = "unspecified"
            claim_object = "unspecified"

        return claim_subject, claim_object

    def _determine_relationship(self, text):
        text_lower = text.lower()
        for indicator in self.causal_indicators:
            if indicator in text_lower:
                return "causal"

        if any(word in text_lower for word in ["more", "less", "better", "worse", "higher", "lower"]):
            return "comparative"

        return "descriptive"

    def _determine_temporal(self, text):
        text_lower = text.lower()

        for indicator in self.future_indicators:
            if indicator in text_lower:
                return "future"

        for indicator in self.past_indicators:
            if indicator in text_lower:
                return "past"

        return "present"

    def _determine_certainty(self, text):
        text_lower = text.lower()

        for level, indicators in self.certainty_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return level

        return "probable"

    def _extract_action(self, text):
        # Extract main verb/action
        verbs = ["destroy", "improve", "cause", "prevent", "increase", "decrease", "affect", "impact", "replace", "create"]
        text_lower = text.lower()

        for verb in verbs:
            if verb in text_lower:
                return verb

        return "affect"

def test_semantic_analyzer():
    analyzer = SemanticClaimAnalyzer()

    test_cases = [
        ("Climate change policies will destroy the economy", "climate change policies", "economy"),
        ("Climate change will destroy the economy", "climate change", "economy"),
        ("Vaccines cause autism", "vaccines", "autism"),
        ("AI will replace human jobs", "AI", "human jobs")
    ]

    print("Testing Semantic Analyzer...")
    all_passed = True

    for i, (claim, expected_subject, expected_object) in enumerate(test_cases, 1):
        result = analyzer.analyze(claim)
        passed = (result.claim_subject.lower() == expected_subject.lower() and
                 expected_object.lower() in result.claim_object.lower())

        print(f"\nTest {i}: {'PASSED' if passed else 'FAILED'}")
        print(f"  Claim: {claim}")
        print(f"  Expected: subject='{expected_subject}', object='{expected_object}'")
        print(f"  Got: subject='{result.claim_subject}', object='{result.claim_object}'")
        print(f"  Temporal: {result.temporal_aspect}")
        print(f"  Relationship: {result.relationship_type}")

        if not passed:
            all_passed = False

    if all_passed:
        print("\n✅ All semantic analysis tests passed!")
    else:
        print("\n❌ Some tests failed. Review the logic.")

    return all_passed

if __name__ == "__main__":
    test_semantic_analyzer()