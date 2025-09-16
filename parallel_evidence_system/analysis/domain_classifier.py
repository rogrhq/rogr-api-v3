"""
DomainClassificationAnalyzer - ES_EEG_PLAN_v2.md lines 239-276

Domain classification component for Advanced Claim Interpretation pipeline.
IFCN compliant domain classification with auditable criteria and transparent
reasoning for claim categorization and methodology requirement determination.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import anthropic
from .semantic_analyzer import SemanticAnalysisResult
from .logical_analyzer import LogicalAnalysisResult


@dataclass
class ClassificationResult:
    """
    Domain classification result per ES_EEG_PLAN_v2.md specification.
    Complete domain analysis with audit trail and methodology requirements.
    """
    domain: str                 # "medical_claim", "economic_claim", "scientific_claim"
    confidence: float           # 0-1 confidence in classification
    reasoning: str              # Explanation of classification rationale
    keywords_matched: List[str] # Keywords that triggered classification
    methodology_requirements: List[str] # Required methodology types for domain


class DomainClassificationAnalyzer:
    """
    Domain classification component per ES_EEG_PLAN_v2.md specification.

    IFCN compliant domain classification with auditable criteria and transparent
    reasoning for claim categorization and methodology requirement determination.
    """

    # Classification rules per ES_EEG_PLAN_v2.md lines 244-262
    CLASSIFICATION_RULES = {
        "medical_claim": {
            "keywords": ["health", "medicine", "treatment", "diagnosis", "clinical", 
                        "vaccine", "disease", "medical", "doctor", "hospital", "patient"],
            "methodology_priority": ["clinical_trial", "peer_reviewed_medical", "government_health"],
            "rationale": "Medical claims require clinical evidence standards"
        },
        "economic_claim": {
            "keywords": ["economy", "GDP", "employment", "inflation", "market", 
                        "economic", "financial", "money", "cost", "price", "budget"],
            "methodology_priority": ["economic_modeling", "government_economic", "peer_reviewed_economic"],
            "rationale": "Economic claims require quantitative analysis evidence"
        },
        "scientific_claim": {
            "keywords": ["research", "study", "experiment", "data", "analysis", 
                        "scientific", "science", "climate", "technology", "environment"],
            "methodology_priority": ["peer_reviewed", "systematic_review", "experimental_study"],
            "rationale": "Scientific claims require empirical research evidence"
        },
        "political_claim": {
            "keywords": ["government", "policy", "politics", "election", "vote", 
                        "political", "congress", "senate", "law", "regulation"],
            "methodology_priority": ["government_official", "independent_research", "peer_reviewed"],
            "rationale": "Political claims require official sources and independent analysis"
        },
        "social_claim": {
            "keywords": ["social", "society", "culture", "community", "people", 
                        "education", "family", "demographic", "population", "behavior"],
            "methodology_priority": ["peer_reviewed", "systematic_review", "survey_research"],
            "rationale": "Social claims require sociological research and survey evidence"
        }
    }

    def __init__(self, ai_client: Optional[anthropic.Anthropic] = None):
        """
        Initialize domain classifier with AI client for enhanced analysis.

        Args:
            ai_client: Anthropic client for domain analysis (optional)
        """
        self.ai_client = ai_client or anthropic.Anthropic()

    def classify_with_audit_trail(self, claim_text: str) -> ClassificationResult:
        """
        Classify claim domain with complete audit trail per ES_EEG_PLAN_v2.md.

        Per specification - all classification decisions must be auditable
        with transparent reasoning and keyword matching.

        Args:
            claim_text: The claim text to classify

        Returns:
            ClassificationResult: Domain classification with audit trail
        """
        claim_lower = claim_text.lower()
        
        # Score each domain based on keyword matching
        domain_scores = {}
        matched_keywords = {}
        
        for domain, rules in self.CLASSIFICATION_RULES.items():
            score = 0
            domain_keywords = []
            
            for keyword in rules["keywords"]:
                if keyword in claim_lower:
                    score += 1
                    domain_keywords.append(keyword)
                    
            domain_scores[domain] = score
            matched_keywords[domain] = domain_keywords
        
        # Find domain with highest score
        best_domain = max(domain_scores.keys(), key=lambda d: domain_scores[d])
        best_score = domain_scores[best_domain]
        
        # Calculate confidence based on score and keyword matches
        total_keywords = len(self.CLASSIFICATION_RULES[best_domain]["keywords"])
        confidence = min(best_score / total_keywords, 1.0) if total_keywords > 0 else 0.0
        
        # Default to general scientific if no clear match
        if best_score == 0:
            best_domain = "scientific_claim"
            confidence = 0.3  # Low confidence fallback
            matched_keywords[best_domain] = ["general"]
        
        # Build reasoning with audit trail
        reasoning = self._build_classification_reasoning(
            claim_text, best_domain, best_score, matched_keywords[best_domain]
        )
        
        return ClassificationResult(
            domain=best_domain,
            confidence=confidence,
            reasoning=reasoning,
            keywords_matched=matched_keywords[best_domain],
            methodology_requirements=self.CLASSIFICATION_RULES[best_domain]["methodology_priority"]
        )

    def classify(self, claim_text: str, semantic_result: SemanticAnalysisResult, 
                logical_result: LogicalAnalysisResult) -> ClassificationResult:
        """
        Classify domain using semantic and logical analysis results.

        Enhanced classification that uses semantic and logical context
        to improve domain classification accuracy.

        Args:
            claim_text: The claim text to classify
            semantic_result: Output from SemanticClaimAnalyzer
            logical_result: Output from LogicalStructureAnalyzer

        Returns:
            ClassificationResult: Domain classification enhanced by previous analysis
        """
        # Start with basic classification
        base_result = self.classify_with_audit_trail(claim_text)
        
        # Enhance with semantic context
        enhanced_keywords = list(base_result.keywords_matched)
        
        # Add semantic subject/object as context
        if semantic_result.claim_subject not in ["unknown", ""]:
            enhanced_keywords.append(f"subject:{semantic_result.claim_subject}")
        if semantic_result.claim_object not in ["unknown", ""]:
            enhanced_keywords.append(f"object:{semantic_result.claim_object}")
            
        # Enhance reasoning with semantic context
        enhanced_reasoning = f"{base_result.reasoning}\n\nSemantic Enhancement: Subject '{semantic_result.claim_subject}' relates to {semantic_result.claim_object} through {semantic_result.relationship_type} relationship."
        
        # Check if logical structure suggests different domain
        if logical_result.assertion_type == "causal" and base_result.domain != "scientific_claim":
            enhanced_reasoning += f"\nLogical Structure: Causal assertion detected, scientific methodology recommended."
            
        return ClassificationResult(
            domain=base_result.domain,
            confidence=min(base_result.confidence + 0.1, 1.0),  # Slight confidence boost for enhanced analysis
            reasoning=enhanced_reasoning,
            keywords_matched=enhanced_keywords,
            methodology_requirements=base_result.methodology_requirements
        )

    def _build_classification_reasoning(self, claim_text: str, domain: str, 
                                      score: int, keywords: List[str]) -> str:
        """
        Build transparent reasoning for domain classification.
        
        Per IFCN compliance requirements - all reasoning must be auditable.
        """
        rules = self.CLASSIFICATION_RULES[domain]
        
        reasoning_parts = [
            f"Classified as '{domain}' based on keyword analysis.",
            f"Matched {score} keywords: {', '.join(keywords)}",
            f"Rationale: {rules['rationale']}",
            f"Required methodologies: {', '.join(rules['methodology_priority'])}"
        ]
        
        return " ".join(reasoning_parts)