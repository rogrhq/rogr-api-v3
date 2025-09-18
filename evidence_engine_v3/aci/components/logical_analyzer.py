from dataclasses import dataclass
from typing import List, Dict

@dataclass
class LogicalAnalysisResult:
    assertion_type: str              # "causal", "correlational", "descriptive"
    logical_operators: List[str]     # ["if", "then", "because", "therefore"]
    claim_scope: str                 # "universal", "particular", "conditional"
    qualifying_language: List[str]   # ["might", "always", "never", "likely"]
    evidence_requirements: Dict[str, str]  # What evidence would prove/disprove

class LogicalStructureAnalyzer:
    def __init__(self):
        self.causal_words = ["causes", "leads to", "results in", "produces", "creates"]
        self.correlation_words = ["associated", "linked", "correlated", "related", "connected"]
        self.universal_words = ["all", "every", "always", "never", "none"]
        self.particular_words = ["some", "most", "many", "few", "several"]
        self.conditional_words = ["if", "when", "unless", "provided", "assuming"]
        self.qualifying_words = ["might", "could", "probably", "likely", "possibly", "perhaps"]

    def analyze(self, claim_text: str, semantic_result=None) -> LogicalAnalysisResult:
        text_lower = claim_text.lower()

        # Determine assertion type
        assertion_type = self._determine_assertion_type(text_lower)

        # Find logical operators
        logical_operators = self._find_logical_operators(text_lower)

        # Determine scope
        claim_scope = self._determine_scope(text_lower)

        # Find qualifying language
        qualifying_language = self._find_qualifying_language(text_lower)

        # Determine evidence requirements
        evidence_requirements = self._determine_evidence_requirements(
            claim_text, assertion_type, claim_scope
        )

        return LogicalAnalysisResult(
            assertion_type=assertion_type,
            logical_operators=logical_operators,
            claim_scope=claim_scope,
            qualifying_language=qualifying_language,
            evidence_requirements=evidence_requirements
        )

    def _determine_assertion_type(self, text_lower):
        # Check for causal language
        for word in self.causal_words:
            if word in text_lower:
                return "causal"

        # Check for correlation language
        for word in self.correlation_words:
            if word in text_lower:
                return "correlational"

        # Check for implicit causation
        if "higher among" in text_lower or "more likely" in text_lower:
            return "correlational"

        return "descriptive"

    def _find_logical_operators(self, text_lower):
        operators = []
        operator_words = ["if", "then", "because", "therefore", "thus", "hence", "so", "since"]

        for op in operator_words:
            if op in text_lower:
                operators.append(op)

        return operators

    def _determine_scope(self, text_lower):
        # Check for conditional
        for word in self.conditional_words:
            if word in text_lower:
                return "conditional"

        # Check for universal
        for word in self.universal_words:
            if word in text_lower:
                return "universal"

        # Check for particular
        for word in self.particular_words:
            if word in text_lower:
                return "particular"

        return "particular"  # Default to particular

    def _find_qualifying_language(self, text_lower):
        found_qualifiers = []
        for word in self.qualifying_words:
            if word in text_lower:
                found_qualifiers.append(word)
        return found_qualifiers

    def _determine_evidence_requirements(self, claim_text, assertion_type, claim_scope):
        requirements = {}

        if assertion_type == "causal":
            requirements["needed"] = "Studies showing direct causation"
            requirements["type"] = "Controlled experiments or longitudinal studies"
        elif assertion_type == "correlational":
            requirements["needed"] = "Statistical data showing correlation"
            requirements["type"] = "Observational studies or surveys"
        else:
            requirements["needed"] = "Descriptive data or documentation"
            requirements["type"] = "Reports or verified records"

        if claim_scope == "universal":
            requirements["scope"] = "Comprehensive evidence covering all cases"
        elif claim_scope == "conditional":
            requirements["scope"] = "Evidence under specified conditions"
        else:
            requirements["scope"] = "Representative sample evidence"

        return requirements

def test_logical_analyzer():
    analyzer = LogicalStructureAnalyzer()

    test_cases = [
        ("Smoking causes cancer", "causal", "particular"),
        ("Cancer rates are higher among smokers", "correlational", "particular"),
        ("All vaccines are safe", "descriptive", "universal"),
        ("Most vaccines are safe", "descriptive", "particular"),
        ("If minimum wage increases, unemployment will rise", "causal", "conditional")
    ]

    print("Testing Logical Analyzer...")
    all_passed = True

    for i, (claim, expected_assertion, expected_scope) in enumerate(test_cases, 1):
        result = analyzer.analyze(claim)
        passed = (result.assertion_type == expected_assertion and
                 result.claim_scope == expected_scope)

        print(f"\nTest {i}: {'PASSED' if passed else 'FAILED'}")
        print(f"  Claim: {claim}")
        print(f"  Expected: assertion={expected_assertion}, scope={expected_scope}")
        print(f"  Got: assertion={result.assertion_type}, scope={result.claim_scope}")
        print(f"  Qualifiers: {result.qualifying_language}")

        if not passed:
            all_passed = False

    if all_passed:
        print("\n✅ All logical analysis tests passed!")
    else:
        print("\n❌ Some tests failed. Review the logic.")

    return all_passed

if __name__ == "__main__":
    test_logical_analyzer()