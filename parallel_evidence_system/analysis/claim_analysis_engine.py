"""
ClaimAnalysisEngine - Complete ACI Pipeline Integration

Integrates all ACI pipeline components for complete claim interpretation.
Per ES_ACI_PLAN.md specification - provides unified claim analysis interface.
"""

from dataclasses import dataclass
from typing import Optional
import anthropic
from .semantic_analyzer import SemanticClaimAnalyzer, SemanticAnalysisResult
from .logical_analyzer import LogicalStructureAnalyzer, LogicalAnalysisResult
from .domain_classifier import DomainClassificationAnalyzer, ClassificationResult
from .evidence_validator import EvidenceRelevanceValidator, RelevanceValidationResult


@dataclass
class ClaimAnalysisResult:
    """
    Composite result from complete ACI pipeline analysis.
    Combines semantic, logical, and domain analysis results per specification.
    """
    semantic_result: SemanticAnalysisResult
    logical_result: LogicalAnalysisResult
    domain_result: ClassificationResult


class ClaimAnalysisEngine:
    """
    Complete ACI pipeline for sophisticated claim understanding per ES_ACI_PLAN.md.

    Integrates semantic analysis, logical structure analysis, and domain classification
    to provide comprehensive claim interpretation for enhanced evidence search strategies.
    """

    def __init__(self, ai_client: Optional[anthropic.Anthropic] = None):
        """
        Initialize complete ACI pipeline with all component analyzers.

        Args:
            ai_client: Anthropic client shared across all analyzers (optional)
        """
        self.ai_client = ai_client or anthropic.Anthropic()

        # Initialize all ACI pipeline components
        self.semantic_analyzer = SemanticClaimAnalyzer(self.ai_client)
        self.logical_analyzer = LogicalStructureAnalyzer(self.ai_client)
        self.domain_classifier = DomainClassificationAnalyzer(self.ai_client)
        self.evidence_validator = EvidenceRelevanceValidator(self.ai_client)

    def analyze_claim(self, claim_text: str) -> ClaimAnalysisResult:
        """
        Complete claim analysis using full ACI pipeline.

        Per ES_ACI_PLAN.md specification - pipeline approach where each stage
        builds on the previous stage for enhanced analysis accuracy.

        Args:
            claim_text: The claim text to analyze

        Returns:
            ClaimAnalysisResult: Complete analysis with all pipeline components
        """
        # Stage 1: Semantic Analysis - identify subject, object, relationships
        semantic_result = self.semantic_analyzer.analyze(claim_text)

        # Stage 2: Logical Analysis - build on semantic context
        logical_result = self.logical_analyzer.analyze(claim_text, semantic_result)

        # Stage 3: Domain Classification - enhanced by semantic and logical context
        domain_result = self.domain_classifier.classify(
            claim_text, semantic_result, logical_result
        )

        # Return composite result for strategy generation
        return ClaimAnalysisResult(
            semantic_result=semantic_result,
            logical_result=logical_result,
            domain_result=domain_result
        )

    def validate_evidence(self, claim_text: str, evidence_text: str,
                         claim_analysis: ClaimAnalysisResult) -> RelevanceValidationResult:
        """
        Validate evidence relevance using complete claim analysis context.

        Provides multi-dimensional relevance scoring enhanced by full claim analysis.

        Args:
            claim_text: The original claim being fact-checked
            evidence_text: The evidence content to validate
            claim_analysis: Complete claim analysis from analyze_claim()

        Returns:
            RelevanceValidationResult: Multi-dimensional relevance assessment
        """
        return self.evidence_validator.validate_relevance(
            claim_text, evidence_text, claim_analysis
        )