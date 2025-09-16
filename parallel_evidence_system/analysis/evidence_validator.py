"""
EvidenceRelevanceValidator - ES_ACI_PLAN.md lines 154-169

Evidence relevance validation component for Advanced Claim Interpretation pipeline.
Provides sophisticated multi-dimensional evidence relevance scoring with
semantic matching, logical relevance, scope alignment, and quality assessment.
"""

from dataclasses import dataclass
from typing import Optional
import anthropic


@dataclass
class RelevanceValidationResult:
    """
    Evidence relevance validation result per ES_ACI_PLAN.md specification.
    Multi-dimensional relevance assessment with detailed scoring breakdown.
    """
    semantic_match_score: float      # 0-100: Does evidence address claim subject?
    logical_relevance_score: float   # 0-100: Does evidence support/contradict assertion?
    scope_alignment_score: float     # 0-100: Does evidence scope match claim scope?
    evidence_quality_score: float    # 0-100: Is evidence methodologically sound?
    final_relevance_score: float     # Weighted combination
    relevance_reasoning: str         # Explanation of scoring


class EvidenceRelevanceValidator:
    """
    Evidence relevance validation component per ES_ACI_PLAN.md specification.

    Provides sophisticated multi-dimensional evidence relevance scoring with
    semantic matching, logical relevance, scope alignment, and quality assessment.
    """

    def __init__(self, ai_client: Optional[anthropic.Anthropic] = None):
        """
        Initialize evidence relevance validator with AI client.

        Args:
            ai_client: Anthropic client for relevance analysis (optional)
        """
        self.ai_client = ai_client or anthropic.Anthropic()

        # Scoring weights for final relevance calculation
        self.scoring_weights = {
            'semantic_match': 0.3,
            'logical_relevance': 0.4,
            'scope_alignment': 0.2,
            'evidence_quality': 0.1
        }

    def validate_relevance(self, claim_text: str, evidence_text: str,
                         claim_analysis: 'ClaimAnalysisResult') -> RelevanceValidationResult:
        """
        Validate evidence relevance with multi-dimensional scoring.

        Per ES_ACI_PLAN.md specification - provides comprehensive relevance
        assessment using claim analysis context for enhanced accuracy.

        Args:
            claim_text: The claim being fact-checked
            evidence_text: The evidence content to validate
            claim_analysis: Complete claim analysis from ACI pipeline

        Returns:
            RelevanceValidationResult: Multi-dimensional relevance assessment
        """
        # Create comprehensive relevance analysis prompt
        analysis_prompt = self._create_relevance_prompt(
            claim_text, evidence_text, claim_analysis
        )

        try:
            response = self.ai_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=700,
                messages=[{"role": "user", "content": analysis_prompt}]
            )

            # Parse response into structured scores
            return self._parse_relevance_response(
                response.content[0].text, claim_text, evidence_text, claim_analysis
            )

        except Exception as e:
            # Fallback to rule-based scoring if AI fails
            return self._fallback_relevance_scoring(
                claim_text, evidence_text, claim_analysis
            )

    def _create_relevance_prompt(self, claim_text: str, evidence_text: str,
                               claim_analysis: 'ClaimAnalysisResult') -> str:
        """Create structured prompt for AI relevance analysis."""
        return f"""Evaluate evidence relevance for fact-checking with multi-dimensional scoring:

CLAIM: "{claim_text}"

CLAIM ANALYSIS CONTEXT:
- Subject: {claim_analysis.semantic_result.claim_subject}
- Object: {claim_analysis.semantic_result.claim_object}
- Relationship: {claim_analysis.semantic_result.relationship_type}
- Assertion Type: {claim_analysis.logical_result.assertion_type}
- Scope: {claim_analysis.logical_result.claim_scope}
- Domain: {claim_analysis.domain_result.domain}

EVIDENCE: "{evidence_text[:800]}..."

Score each dimension (0-100):

1. SEMANTIC MATCH: Does evidence address the claim's subject and object?
2. LOGICAL RELEVANCE: Does evidence support/contradict the specific assertion?
3. SCOPE ALIGNMENT: Does evidence scope match claim scope (universal vs particular)?
4. EVIDENCE QUALITY: Is the evidence methodologically sound and credible?
5. OVERALL REASONING: Explain the relevance assessment

Respond in this exact format:
SEMANTIC: [0-100 score]
LOGICAL: [0-100 score]
SCOPE: [0-100 score]
QUALITY: [0-100 score]
REASONING: [detailed explanation]

Focus on relevance to the specific claim, not general topic similarity."""

    def _parse_relevance_response(self, response_text: str, claim_text: str,
                                evidence_text: str, claim_analysis: 'ClaimAnalysisResult') -> RelevanceValidationResult:
        """Parse AI response into RelevanceValidationResult structure."""
        import re

        # Extract scores using regex
        semantic_match = re.search(r'SEMANTIC:\s*(\d+)', response_text, re.IGNORECASE)
        logical_match = re.search(r'LOGICAL:\s*(\d+)', response_text, re.IGNORECASE)
        scope_match = re.search(r'SCOPE:\s*(\d+)', response_text, re.IGNORECASE)
        quality_match = re.search(r'QUALITY:\s*(\d+)', response_text, re.IGNORECASE)
        reasoning_match = re.search(r'REASONING:\s*(.+)', response_text, re.IGNORECASE | re.DOTALL)

        # Convert to float scores
        semantic_score = float(semantic_match.group(1)) if semantic_match else 50.0
        logical_score = float(logical_match.group(1)) if logical_match else 50.0
        scope_score = float(scope_match.group(1)) if scope_match else 50.0
        quality_score = float(quality_match.group(1)) if quality_match else 50.0

        # Calculate weighted final score
        final_score = (
            semantic_score * self.scoring_weights['semantic_match'] +
            logical_score * self.scoring_weights['logical_relevance'] +
            scope_score * self.scoring_weights['scope_alignment'] +
            quality_score * self.scoring_weights['evidence_quality']
        )

        reasoning = reasoning_match.group(1).strip() if reasoning_match else "AI analysis unavailable"

        return RelevanceValidationResult(
            semantic_match_score=semantic_score,
            logical_relevance_score=logical_score,
            scope_alignment_score=scope_score,
            evidence_quality_score=quality_score,
            final_relevance_score=final_score,
            relevance_reasoning=reasoning
        )

    def _fallback_relevance_scoring(self, claim_text: str, evidence_text: str,
                                  claim_analysis: 'ClaimAnalysisResult') -> RelevanceValidationResult:
        """Rule-based fallback scoring if AI processing fails."""
        claim_lower = claim_text.lower()
        evidence_lower = evidence_text.lower()

        # Basic semantic matching - check for subject/object keywords
        semantic_score = 0.0
        if claim_analysis.semantic_result.claim_subject.lower() in evidence_lower:
            semantic_score += 40.0
        if claim_analysis.semantic_result.claim_object.lower() in evidence_lower:
            semantic_score += 40.0

        # Basic keyword overlap
        claim_words = set(claim_lower.split())
        evidence_words = set(evidence_lower.split())
        overlap = len(claim_words & evidence_words) / len(claim_words) if claim_words else 0
        semantic_score += min(overlap * 20, 20.0)

        # Logical relevance - basic relationship matching
        logical_score = 50.0  # Default neutral
        if claim_analysis.semantic_result.relationship_type == "causal":
            causal_words = ['cause', 'effect', 'result', 'lead', 'due to']
            if any(word in evidence_lower for word in causal_words):
                logical_score = 75.0

        # Scope alignment - basic heuristic
        scope_score = 60.0  # Default moderate alignment
        if claim_analysis.logical_result.claim_scope == "universal":
            universal_words = ['all', 'every', 'always', 'never']
            if any(word in evidence_lower for word in universal_words):
                scope_score = 80.0

        # Quality - basic source indicators
        quality_score = 50.0
        quality_indicators = ['study', 'research', 'data', 'analysis', 'peer-reviewed']
        quality_score += min(sum(10 for word in quality_indicators if word in evidence_lower), 40)

        # Calculate final score
        final_score = (
            semantic_score * self.scoring_weights['semantic_match'] +
            logical_score * self.scoring_weights['logical_relevance'] +
            scope_score * self.scoring_weights['scope_alignment'] +
            quality_score * self.scoring_weights['evidence_quality']
        )

        reasoning = f"Rule-based scoring: Semantic match {semantic_score:.0f}%, logical relevance {logical_score:.0f}%, scope alignment {scope_score:.0f}%, quality {quality_score:.0f}%"

        return RelevanceValidationResult(
            semantic_match_score=semantic_score,
            logical_relevance_score=logical_score,
            scope_alignment_score=scope_score,
            evidence_quality_score=quality_score,
            final_relevance_score=final_score,
            relevance_reasoning=reasoning
        )