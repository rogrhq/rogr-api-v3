"""
Methodology Search Strategist - Core EEG Phase 1 Implementation

IFCN-compliant search strategy generation focusing on evidence methodology
rather than institutional bias. Implements progressive complexity with 
performance safeguards.

Key Features:
- Methodology-first approach (no institutional targeting)
- Auditable domain classification
- Progressive implementation (Stage 1: Foundation)
- Performance controls (max 12 queries per claim)
- IFCN compliance validation
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from ..interfaces.search_strategy_interface import (
    SearchStrategyInterface, 
    SearchStrategyResult, 
    MethodologySearchQuery,
    ImplementationVersion
)


class MethodologyType(Enum):
    """Evidence methodology types - IFCN compliant, no institutional bias"""
    PEER_REVIEWED = "peer_reviewed"
    GOVERNMENT_OFFICIAL = "government_official" 
    SYSTEMATIC_REVIEW = "systematic_review"
    EXPERIMENTAL_STUDY = "experimental_study"
    OBSERVATIONAL_RESEARCH = "observational_research"
    INDEPENDENT_RESEARCH = "independent_research"


class DomainType(Enum):
    """Domain classifications based on transparent, auditable criteria"""
    MEDICAL = "medical"
    SCIENTIFIC = "scientific" 
    ECONOMIC = "economic"
    POLICY = "policy"
    STATISTICAL = "statistical"
    HISTORICAL = "historical"
    GENERAL = "general"


@dataclass
class DomainClassificationResult:
    """Auditable domain classification with transparent reasoning"""
    primary_domain: DomainType
    confidence: float                    # 0.0-1.0
    reasoning: str                      # Explanation of classification
    keywords_matched: List[str]         # Evidence for classification
    methodology_requirements: List[MethodologyType]  # Required evidence types
    alternative_domains: List[Tuple[DomainType, float]]  # Other possible domains


@dataclass
class MethodologyRequirements:
    """Requirements for different methodology types"""
    search_terms: List[str]
    quality_indicators: List[str]
    transparency_score: float
    priority_weight: float


class MethodologySearchStrategist(SearchStrategyInterface):
    """
    Core implementation of methodology-first search strategy generation
    
    Stage 1 Implementation: Foundation with core methodology types
    - Peer-reviewed research
    - Government official analysis
    - Systematic reviews
    
    Future stages will add complexity progressively
    """
    
    def __init__(self):
        """Initialize with Stage 1 configuration"""
        self.stage = 1
        self.max_queries_per_claim = 12
        self.max_processing_time = 45  # seconds
        self.version = ImplementationVersion.EEG_PHASE_1
        
        # Stage 1: Core methodology types only
        self.active_methodology_types = [
            MethodologyType.PEER_REVIEWED,
            MethodologyType.GOVERNMENT_OFFICIAL,
            MethodologyType.SYSTEMATIC_REVIEW
        ]
        
        self._initialize_methodology_definitions()
        self._initialize_domain_classification()
    
    def _initialize_methodology_definitions(self):
        """Define methodology requirements - IFCN compliant"""
        
        self.methodology_requirements = {
            MethodologyType.PEER_REVIEWED: MethodologyRequirements(
                search_terms=[
                    "peer reviewed study", "academic research", "journal article",
                    "published research", "scientific study"
                ],
                quality_indicators=[
                    "methodology", "sample size", "peer review", "journal"
                ],
                transparency_score=0.9,
                priority_weight=1.0
            ),
            
            MethodologyType.GOVERNMENT_OFFICIAL: MethodologyRequirements(
                search_terms=[
                    "government analysis", "official report", "regulatory assessment",
                    "government study", "official data", "policy analysis"
                ],
                quality_indicators=[
                    "official", "government", "regulatory", "policy", "data"
                ],
                transparency_score=0.85,
                priority_weight=0.9
            ),
            
            MethodologyType.SYSTEMATIC_REVIEW: MethodologyRequirements(
                search_terms=[
                    "systematic review", "meta-analysis", "literature review",
                    "review study", "meta analysis"
                ],
                quality_indicators=[
                    "systematic", "meta-analysis", "literature", "review", "studies"
                ],
                transparency_score=0.95,
                priority_weight=1.0
            )
        }
    
    def _initialize_domain_classification(self):
        """Initialize auditable domain classification criteria"""
        
        self.domain_classification_rules = {
            DomainType.MEDICAL: {
                "keywords": [
                    "health", "medicine", "medical", "treatment", "diagnosis", 
                    "clinical", "patient", "disease", "therapy", "drug",
                    "hospital", "doctor", "physician", "vaccine", "symptom"
                ],
                "methodology_priority": [
                    MethodologyType.SYSTEMATIC_REVIEW,
                    MethodologyType.PEER_REVIEWED,
                    MethodologyType.GOVERNMENT_OFFICIAL
                ],
                "rationale": "Medical claims require clinical evidence standards"
            },
            
            DomainType.SCIENTIFIC: {
                "keywords": [
                    "research", "study", "experiment", "data", "analysis",
                    "scientific", "laboratory", "test", "evidence", "findings",
                    "methodology", "results", "hypothesis", "theory"
                ],
                "methodology_priority": [
                    MethodologyType.PEER_REVIEWED,
                    MethodologyType.SYSTEMATIC_REVIEW,
                    MethodologyType.GOVERNMENT_OFFICIAL
                ],
                "rationale": "Scientific claims require empirical research evidence"
            },
            
            DomainType.ECONOMIC: {
                "keywords": [
                    "economy", "economic", "GDP", "employment", "unemployment",
                    "inflation", "market", "financial", "budget", "tax",
                    "trade", "business", "industry", "profit", "income"
                ],
                "methodology_priority": [
                    MethodologyType.GOVERNMENT_OFFICIAL,
                    MethodologyType.PEER_REVIEWED,
                    MethodologyType.SYSTEMATIC_REVIEW
                ],
                "rationale": "Economic claims require quantitative analysis evidence"
            },
            
            DomainType.POLICY: {
                "keywords": [
                    "policy", "government", "law", "regulation", "legislation",
                    "political", "administration", "congress", "senate", "bill",
                    "act", "rule", "directive", "mandate", "executive"
                ],
                "methodology_priority": [
                    MethodologyType.GOVERNMENT_OFFICIAL,
                    MethodologyType.PEER_REVIEWED,
                    MethodologyType.SYSTEMATIC_REVIEW
                ],
                "rationale": "Policy claims require official government evidence"
            },
            
            DomainType.STATISTICAL: {
                "keywords": [
                    "percent", "percentage", "%", "statistics", "data",
                    "survey", "poll", "census", "rate", "average",
                    "median", "study shows", "research found", "analysis revealed"
                ],
                "methodology_priority": [
                    MethodologyType.PEER_REVIEWED,
                    MethodologyType.GOVERNMENT_OFFICIAL,
                    MethodologyType.SYSTEMATIC_REVIEW
                ],
                "rationale": "Statistical claims require data-based evidence"
            }
        }
    
    def classify_claim_domain(self, claim_text: str) -> DomainClassificationResult:
        """
        Classify claim domain using transparent, auditable criteria
        
        IFCN Compliant: All classification decisions include reasoning
        """
        claim_lower = claim_text.lower()
        domain_scores = {}
        matched_keywords = {}
        
        # Score each domain based on keyword matches
        for domain, rules in self.domain_classification_rules.items():
            matches = []
            for keyword in rules["keywords"]:
                if keyword in claim_lower:
                    matches.append(keyword)
            
            # Calculate score based on matches and keyword importance
            score = len(matches) / len(rules["keywords"])
            if matches:
                domain_scores[domain] = score
                matched_keywords[domain] = matches
        
        # Determine primary domain
        if not domain_scores:
            primary_domain = DomainType.GENERAL
            confidence = 1.0
            reasoning = "No specific domain keywords detected, using general classification"
            keywords_matched = []
            methodology_requirements = [MethodologyType.PEER_REVIEWED]
        else:
            primary_domain = max(domain_scores, key=domain_scores.get)
            confidence = domain_scores[primary_domain]
            reasoning = f"Classified as {primary_domain.value} based on keywords: {matched_keywords[primary_domain]}"
            keywords_matched = matched_keywords[primary_domain]
            methodology_requirements = self.domain_classification_rules[primary_domain]["methodology_priority"]
        
        # Get alternative domains
        alternative_domains = [
            (domain, score) for domain, score in domain_scores.items() 
            if domain != primary_domain
        ]
        alternative_domains.sort(key=lambda x: x[1], reverse=True)
        
        return DomainClassificationResult(
            primary_domain=primary_domain,
            confidence=confidence,
            reasoning=reasoning,
            keywords_matched=keywords_matched,
            methodology_requirements=methodology_requirements[:3],  # Top 3 methodologies
            alternative_domains=alternative_domains[:2]  # Top 2 alternatives
        )
    
    def generate_methodology_queries(
        self, 
        claim_text: str, 
        methodology_type: MethodologyType,
        max_queries: int = 3
    ) -> List[MethodologySearchQuery]:
        """Generate queries for specific methodology type"""
        
        requirements = self.methodology_requirements[methodology_type]
        queries = []
        
        # Generate queries by combining claim with methodology terms
        for i, search_term in enumerate(requirements.search_terms[:max_queries]):
            query_text = f"{claim_text} {search_term}"
            
            # Calculate priority based on methodology weight and term order
            priority = requirements.priority_weight * (1.0 - (i * 0.1))
            
            query = MethodologySearchQuery(
                query_text=query_text,
                methodology_type=methodology_type.value,
                priority=priority,
                max_results=8,
                timeout_seconds=8,
                context_tags=[
                    f"transparency_score:{requirements.transparency_score}",
                    f"methodology_type:{methodology_type.value}"
                ]
            )
            queries.append(query)
        
        return queries
    
    def generate_search_strategy(
        self, 
        claim_text: str,
        claim_context: Optional[Dict] = None,
        performance_requirements: Optional[Dict] = None
    ) -> SearchStrategyResult:
        """
        Generate IFCN-compliant search strategy using methodology-first approach
        
        Stage 1 Implementation: Foundation with performance safeguards
        """
        
        audit_trail = ["Starting EEG Phase 1 search strategy generation"]
        
        # Step 1: Classify claim domain (auditable)
        domain_classification = self.classify_claim_domain(claim_text)
        audit_trail.append(f"Domain classification: {domain_classification.reasoning}")
        
        # Step 2: Determine methodology requirements
        required_methodologies = domain_classification.methodology_requirements
        audit_trail.append(f"Required methodologies: {[m.value for m in required_methodologies]}")
        
        # Step 3: Generate queries for each required methodology
        all_queries = []
        methodology_coverage = []
        
        for methodology in required_methodologies[:3]:  # Stage 1: Limit to top 3
            if methodology in self.active_methodology_types:
                queries = self.generate_methodology_queries(claim_text, methodology, max_queries=3)
                all_queries.extend(queries)
                methodology_coverage.append(methodology.value)
                audit_trail.append(f"Generated {len(queries)} queries for {methodology.value}")
        
        # Step 4: Apply performance safeguards
        if len(all_queries) > self.max_queries_per_claim:
            # Prioritize and trim
            all_queries.sort(key=lambda q: q.priority, reverse=True)
            all_queries = all_queries[:self.max_queries_per_claim]
            audit_trail.append(f"Trimmed to {len(all_queries)} queries for performance")
        
        # Step 5: Calculate performance metrics
        estimated_time = len(all_queries) * 4  # 4 seconds average per query
        performance_metrics = {
            "precision_estimate": 0.7,  # Target improvement over current 0.4
            "query_count": len(all_queries),
            "methodology_types": len(methodology_coverage)
        }
        
        # Step 6: IFCN compliance check
        ifcn_compliance = self._validate_ifcn_compliance(all_queries, domain_classification)
        
        return SearchStrategyResult(
            queries=all_queries,
            total_estimated_time=estimated_time,
            methodology_coverage=methodology_coverage,
            performance_metrics=performance_metrics,
            ifcn_compliance_status=ifcn_compliance,
            version_used=self.version,
            audit_trail=audit_trail
        )
    
    def _validate_ifcn_compliance(
        self, 
        queries: List[MethodologySearchQuery], 
        domain_classification: DomainClassificationResult
    ) -> bool:
        """Validate search strategy meets IFCN standards"""
        
        # Check 1: No institutional bias (queries focus on methodology, not institutions)
        institutional_terms = ["cdc.gov", "nih.gov", "fda.gov", "who.int"]
        has_institutional_bias = any(
            any(term in query.query_text.lower() for term in institutional_terms)
            for query in queries
        )
        
        # Check 2: Methodology transparency (all queries have methodology context)
        has_methodology_context = all(
            query.methodology_type != "unknown" for query in queries
        )
        
        # Check 3: Auditable classification (domain classification has reasoning)
        has_classification_reasoning = bool(domain_classification.reasoning)
        
        # All checks must pass for IFCN compliance
        return (not has_institutional_bias) and has_methodology_context and has_classification_reasoning
    
    def validate_strategy(self, strategy: SearchStrategyResult) -> Dict[str, bool]:
        """Validate search strategy meets quality and compliance requirements"""
        
        return {
            "ifcn_compliant": strategy.ifcn_compliance_status,
            "within_performance_limits": (
                len(strategy.queries) <= self.max_queries_per_claim and 
                strategy.total_estimated_time <= self.max_processing_time
            ),
            "methodology_adequate": len(strategy.methodology_coverage) >= 1,
            "has_audit_trail": len(strategy.audit_trail) > 0,
            "queries_have_context": all(
                query.methodology_type != "unknown" for query in strategy.queries
            )
        }
    
    def get_implementation_info(self) -> Dict[str, str]:
        """Get information about this search strategy implementation"""
        
        return {
            "version": self.version.value,
            "stage": str(self.stage),
            "description": "EEG Phase 1 - Methodology-first search with IFCN compliance",
            "capabilities": "methodology_targeting,domain_classification,performance_safeguards",
            "ifcn_compliance_level": "full",
            "max_queries": str(self.max_queries_per_claim),
            "methodology_types": ",".join([mt.value for mt in self.active_methodology_types])
        }