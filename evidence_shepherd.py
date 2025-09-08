from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class ClaimType(Enum):
    STATISTICAL = "statistical"  # "85% of Americans..."
    POLICY = "policy"           # "Government announced..."
    SCIENTIFIC = "scientific"   # "Studies show..."
    HISTORICAL = "historical"   # "In 2023..."
    OPINION = "opinion"         # "Experts believe..."
    FACTUAL = "factual"         # "Company has 500 employees"

@dataclass
class MultiDomainClaimAnalysis:
    """Multi-dimensional claim analysis for professional fact-checking"""
    primary_domains: List[str]      # Must have evidence (e.g., ['virology', 'epidemiology'])
    secondary_domains: List[str]    # Should have evidence (e.g., ['intelligence', 'geopolitics']) 
    domain_priorities: Dict[str, float]  # Weight by importance (0.0-1.0)
    cross_domain_dependencies: Dict[str, List[str]]  # Which domains should reference others
    specialized_queries: Dict[str, List[str]]  # Domain-specific search queries
    authority_domains: Dict[str, List[str]]  # Preferred domains per domain type

@dataclass
class SearchStrategy:
    """Defines how to search for evidence for a specific claim"""
    claim_type: ClaimType
    search_queries: List[str]
    target_domains: List[str]  # Preferred domains for this claim type
    time_relevance_months: int  # How recent should evidence be
    authority_weight: float    # How much to weight source authority
    confidence_threshold: float  # Minimum confidence to include evidence
    # NEW: Multi-domain support
    multi_domain_analysis: Optional[MultiDomainClaimAnalysis] = None

@dataclass 
class EvidenceCandidate:
    """Raw evidence before AI processing"""
    text: str
    source_url: str
    source_domain: str
    source_title: str
    found_via_query: str
    raw_relevance: float  # Initial keyword-based relevance

@dataclass
class ProcessedEvidence:
    """Evidence after AI shepherd processing"""
    text: str
    source_url: str
    source_domain: str
    source_title: str
    ai_relevance_score: float  # 0-100, AI-determined relevance
    ai_stance: str  # "supporting", "contradicting", "neutral"
    ai_confidence: float  # 0-1, how confident AI is in its assessment
    ai_reasoning: str  # Why AI scored it this way
    highlight_text: Optional[str] = None
    highlight_context: Optional[str] = None
    
class EvidenceShepherd(ABC):
    """Abstract interface for AI-powered evidence processing"""
    
    @abstractmethod
    def analyze_claim(self, claim_text: str) -> SearchStrategy:
        """
        Analyze a claim and determine the best search strategy
        
        Args:
            claim_text: The claim to fact-check
            
        Returns:
            SearchStrategy with optimized search parameters
        """
        pass
    
    @abstractmethod
    def score_evidence_relevance(self, claim_text: str, evidence: EvidenceCandidate) -> ProcessedEvidence:
        """
        Use AI to score how relevant evidence is to a specific claim
        
        Args:
            claim_text: The original claim
            evidence: Raw evidence candidate
            
        Returns:
            ProcessedEvidence with AI scoring and analysis
        """
        pass
    
    @abstractmethod
    def filter_evidence_batch(self, claim_text: str, evidence_batch: List[EvidenceCandidate]) -> List[ProcessedEvidence]:
        """
        Process multiple evidence candidates efficiently
        
        Args:
            claim_text: The original claim
            evidence_batch: List of evidence candidates
            
        Returns:
            Filtered and scored evidence, sorted by relevance
        """
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if AI shepherd is properly configured and available"""
        pass

class NoOpEvidenceShepherd(EvidenceShepherd):
    """Fallback implementation that does no AI processing"""
    
    def analyze_claim(self, claim_text: str) -> SearchStrategy:
        # Default strategy: treat everything as factual, use basic keywords
        words = claim_text.lower().split()
        search_queries = [' '.join(words[:5])]  # First 5 words
        
        return SearchStrategy(
            claim_type=ClaimType.FACTUAL,
            search_queries=search_queries,
            target_domains=[],
            time_relevance_months=24,
            authority_weight=0.7,
            confidence_threshold=0.5
        )
    
    def score_evidence_relevance(self, claim_text: str, evidence: EvidenceCandidate) -> ProcessedEvidence:
        # Simple keyword matching fallback
        claim_words = set(claim_text.lower().split())
        evidence_words = set(evidence.text.lower().split())
        overlap = len(claim_words.intersection(evidence_words))
        relevance = min(100, overlap * 10)
        
        return ProcessedEvidence(
            text=evidence.text,
            source_url=evidence.source_url,
            source_domain=evidence.source_domain,
            source_title=evidence.source_title,
            ai_relevance_score=relevance,
            ai_stance="neutral",
            ai_confidence=0.3,
            ai_reasoning="Fallback keyword matching",
            highlight_text=evidence.text[:100]
        )
    
    def filter_evidence_batch(self, claim_text: str, evidence_batch: List[EvidenceCandidate]) -> List[ProcessedEvidence]:
        processed = [self.score_evidence_relevance(claim_text, ev) for ev in evidence_batch]
        return sorted(processed, key=lambda x: x.ai_relevance_score, reverse=True)[:5]
    
    def is_enabled(self) -> bool:
        return True