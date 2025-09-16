"""
LogicalStructureAnalyzer - ES_ACI_PLAN.md lines 107-114

Logical structure analysis component for Advanced Claim Interpretation pipeline.
Analyzes claim logical structure including assertion types, logical operators,
scope classification, and evidence requirements building on semantic analysis.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import re
import anthropic
from .semantic_analyzer import SemanticAnalysisResult


@dataclass
class LogicalAnalysisResult:
    """
    Logical analysis result structure per ES_ACI_PLAN.md specification.
    Complete logical structure breakdown of claim for evidence requirements.
    """
    assertion_type: str         # "causal", "correlational", "descriptive"
    logical_operators: List[str] # ["if", "then", "because", "therefore"]
    claim_scope: str            # "universal", "particular", "conditional"
    qualifying_language: List[str] # ["might", "always", "never", "likely"]
    evidence_requirements: Dict[str, str] # What evidence would prove/disprove


class LogicalStructureAnalyzer:
    """
    Logical structure analysis component per ES_ACI_PLAN.md specification.

    Analyzes claim logical structure including assertion types, logical operators,
    scope classification, and evidence requirements building on semantic analysis.
    """

    def __init__(self, ai_client: Optional[anthropic.Anthropic] = None):
        """
        Initialize logical analyzer with AI client for advanced analysis.

        Args:
            ai_client: Anthropic client for logical processing (optional)
        """
        self.ai_client = ai_client or anthropic.Anthropic()

        # Logical operators patterns
        self.logical_operators = {
            'conditional': ['if', 'when', 'unless', 'provided that'],
            'causal': ['because', 'since', 'as a result', 'therefore', 'thus'],
            'comparative': ['than', 'compared to', 'versus', 'relative to'],
            'temporal': ['before', 'after', 'during', 'while', 'then']
        }

        # Scope indicators
        self.scope_patterns = {
            'universal': ['all', 'every', 'always', 'never', 'none'],
            'particular': ['some', 'many', 'most', 'few', 'several'],
            'conditional': ['if', 'when', 'unless', 'in case']
        }

        # Qualifying language patterns
        self.qualifying_patterns = {
            'certainty': ['definitely', 'certainly', 'absolutely'],
            'probability': ['likely', 'probably', 'possibly'],
            'speculation': ['might', 'could', 'may', 'perhaps']
        }

    def analyze(self, claim_text: str, semantic_result: SemanticAnalysisResult) -> LogicalAnalysisResult:
        """
        Analyze logical structure of claim building on semantic analysis.

        Per ES_ACI_PLAN.md specification - analyzes logical operators, scope,
        and evidence requirements using semantic context.

        Args:
            claim_text: The claim text to analyze
            semantic_result: Output from SemanticClaimAnalyzer

        Returns:
            LogicalAnalysisResult: Complete logical structure analysis
        """
        # Use AI for sophisticated logical analysis
        analysis_prompt = self._create_analysis_prompt(claim_text, semantic_result)

        try:
            response = self.ai_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=600,
                messages=[{"role": "user", "content": analysis_prompt}]
            )

            # Parse AI response into structured result
            return self._parse_analysis_response(response.content[0].text, claim_text, semantic_result)

        except Exception as e:
            # Fallback to rule-based analysis if AI fails
            return self._fallback_analysis(claim_text, semantic_result)

    def _create_analysis_prompt(self, claim_text: str, semantic_result: SemanticAnalysisResult) -> str:
        """Create structured prompt for AI logical analysis."""
        return f"""Analyze this claim's logical structure for fact-checking evidence requirements:

CLAIM: "{claim_text}"

SEMANTIC CONTEXT:
- Subject: {semantic_result.claim_subject}
- Object: {semantic_result.claim_object}
- Relationship: {semantic_result.relationship_type}
- Temporal: {semantic_result.temporal_aspect}

Extract these logical components:

1. ASSERTION TYPE: causal, correlational, or descriptive
2. LOGICAL OPERATORS: List any logical connectors (if, then, because, therefore, etc.)
3. CLAIM SCOPE: universal (all/never), particular (some/many), or conditional (if/when)
4. QUALIFYING LANGUAGE: List certainty modifiers (might, always, likely, etc.)
5. EVIDENCE REQUIREMENTS: What specific evidence would prove or disprove this claim

Respond in this exact format:
ASSERTION: [assertion_type]
OPERATORS: [operator1, operator2]
SCOPE: [scope_type]
QUALIFIERS: [qualifier1, qualifier2]
EVIDENCE_PROVE: [what would prove this]
EVIDENCE_DISPROVE: [what would disprove this]

Focus on logical structure and evidence requirements, not claim truth."""

    def _parse_analysis_response(self, response_text: str, claim_text: str, semantic_result: SemanticAnalysisResult) -> LogicalAnalysisResult:
        """Parse AI response into LogicalAnalysisResult structure."""

        # Extract fields using regex patterns
        assertion_match = re.search(r'ASSERTION:\s*(.+)', response_text, re.IGNORECASE)
        operators_match = re.search(r'OPERATORS:\s*(.+)', response_text, re.IGNORECASE)
        scope_match = re.search(r'SCOPE:\s*(.+)', response_text, re.IGNORECASE)
        qualifiers_match = re.search(r'QUALIFIERS:\s*(.+)', response_text, re.IGNORECASE)
        prove_match = re.search(r'EVIDENCE_PROVE:\s*(.+)', response_text, re.IGNORECASE)
        disprove_match = re.search(r'EVIDENCE_DISPROVE:\s*(.+)', response_text, re.IGNORECASE)

        # Parse operators and qualifiers as lists
        operators = []
        if operators_match:
            operators = [op.strip() for op in operators_match.group(1).split(',') if op.strip()]

        qualifiers = []
        if qualifiers_match:
            qualifiers = [qual.strip() for qual in qualifiers_match.group(1).split(',') if qual.strip()]

        # Build evidence requirements dictionary
        evidence_requirements = {}
        if prove_match:
            evidence_requirements['prove'] = prove_match.group(1).strip()
        if disprove_match:
            evidence_requirements['disprove'] = disprove_match.group(1).strip()

        return LogicalAnalysisResult(
            assertion_type=assertion_match.group(1).strip().lower() if assertion_match else "descriptive",
            logical_operators=operators,
            claim_scope=scope_match.group(1).strip().lower() if scope_match else "particular",
            qualifying_language=qualifiers,
            evidence_requirements=evidence_requirements
        )

    def _fallback_analysis(self, claim_text: str, semantic_result: SemanticAnalysisResult) -> LogicalAnalysisResult:
        """Rule-based fallback analysis if AI processing fails."""
        claim_lower = claim_text.lower()

        # Detect logical operators
        found_operators = []
        for category, operators in self.logical_operators.items():
            for op in operators:
                if op in claim_lower:
                    found_operators.append(op)

        # Determine scope
        scope = "particular"
        for scope_type, patterns in self.scope_patterns.items():
            if any(pattern in claim_lower for pattern in patterns):
                scope = scope_type
                break

        # Find qualifying language
        qualifiers = []
        for category, patterns in self.qualifying_patterns.items():
            for pattern in patterns:
                if pattern in claim_lower:
                    qualifiers.append(pattern)

        # Map semantic relationship to assertion type
        assertion_type = "descriptive"
        if semantic_result.relationship_type == "causal":
            assertion_type = "causal"
        elif any(op in claim_lower for op in ['correlate', 'associate', 'link']):
            assertion_type = "correlational"

        # Basic evidence requirements
        evidence_requirements = {
            'prove': f"Evidence showing {semantic_result.claim_subject} {semantic_result.action_type} {semantic_result.claim_object}",
            'disprove': f"Evidence showing {semantic_result.claim_subject} does not {semantic_result.action_type} {semantic_result.claim_object}"
        }

        return LogicalAnalysisResult(
            assertion_type=assertion_type,
            logical_operators=found_operators[:5],  # Limit to 5 operators
            claim_scope=scope,
            qualifying_language=qualifiers[:5],  # Limit to 5 qualifiers
            evidence_requirements=evidence_requirements
        )