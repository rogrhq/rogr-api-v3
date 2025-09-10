"""
Search Strategy Interface - Clean Integration Point

Provides a stable interface between the Enhanced Evidence Gathering system
and existing Evidence Shepherd implementations. Designed for backward
compatibility and feature flag support.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class ImplementationVersion(Enum):
    """Version control for different search strategy implementations"""
    LEGACY = "legacy"           # Current basic search approach
    EEG_PHASE_1 = "eeg_phase_1" # Enhanced methodology-based search
    EEG_FULL = "eeg_full"       # Complete EEG implementation (future)


@dataclass
class MethodologySearchQuery:
    """Enhanced search query with methodology context"""
    query_text: str
    methodology_type: str           # "peer_reviewed", "government_official", etc.
    priority: float                 # 0.0-1.0, for query prioritization
    max_results: int = 8           # Results to retrieve for this query
    timeout_seconds: int = 8       # Per-query timeout
    context_tags: List[str] = None # Additional context for the query
    
    def __post_init__(self):
        if self.context_tags is None:
            self.context_tags = []


@dataclass
class SearchStrategyResult:
    """Result of search strategy generation"""
    queries: List[MethodologySearchQuery]
    total_estimated_time: float     # Estimated processing time in seconds
    methodology_coverage: List[str] # Methodology types covered
    performance_metrics: Dict[str, float] # Performance predictions
    ifcn_compliance_status: bool    # IFCN compliance verification
    version_used: ImplementationVersion # Which implementation was used
    audit_trail: List[str]         # Decision audit trail for transparency


class SearchStrategyInterface(ABC):
    """
    Interface for search strategy generation systems
    
    Allows clean integration between Evidence Shepherds and different
    search strategy implementations (legacy, EEG Phase 1, EEG Full)
    """
    
    @abstractmethod
    def generate_search_strategy(
        self, 
        claim_text: str,
        claim_context: Optional[Dict] = None,
        performance_requirements: Optional[Dict] = None
    ) -> SearchStrategyResult:
        """
        Generate search strategy for a given claim
        
        Args:
            claim_text: The claim to fact-check
            claim_context: Additional context (domain, urgency, etc.)
            performance_requirements: Time/resource constraints
            
        Returns:
            SearchStrategyResult with queries and metadata
        """
        pass
    
    @abstractmethod
    def validate_strategy(self, strategy: SearchStrategyResult) -> Dict[str, bool]:
        """
        Validate search strategy meets quality and compliance requirements
        
        Args:
            strategy: Generated search strategy to validate
            
        Returns:
            Dict of validation results (ifcn_compliant, within_performance_limits, etc.)
        """
        pass
    
    @abstractmethod
    def get_implementation_info(self) -> Dict[str, str]:
        """
        Get information about this search strategy implementation
        
        Returns:
            Dict with version, capabilities, and configuration info
        """
        pass


class LegacySearchStrategyAdapter(SearchStrategyInterface):
    """
    Adapter for current search approach - maintains backward compatibility
    """
    
    def generate_search_strategy(
        self, 
        claim_text: str,
        claim_context: Optional[Dict] = None,
        performance_requirements: Optional[Dict] = None
    ) -> SearchStrategyResult:
        """Generate search strategy using current approach"""
        
        # Convert current basic search to new interface format
        basic_queries = [
            MethodologySearchQuery(
                query_text=f"{claim_text} evidence",
                methodology_type="general",
                priority=1.0,
                max_results=8
            ),
            MethodologySearchQuery(
                query_text=f"{claim_text} study research",
                methodology_type="general", 
                priority=0.8,
                max_results=8
            ),
            MethodologySearchQuery(
                query_text=f"{claim_text} analysis report",
                methodology_type="general",
                priority=0.6,
                max_results=8
            )
        ]
        
        return SearchStrategyResult(
            queries=basic_queries,
            total_estimated_time=30.0,  # Current average
            methodology_coverage=["general"],
            performance_metrics={"precision_estimate": 0.4},
            ifcn_compliance_status=True,  # Basic compliance
            version_used=ImplementationVersion.LEGACY,
            audit_trail=["Legacy adapter - basic keyword search"]
        )
    
    def validate_strategy(self, strategy: SearchStrategyResult) -> Dict[str, bool]:
        """Basic validation for legacy approach"""
        return {
            "ifcn_compliant": True,
            "within_performance_limits": len(strategy.queries) <= 5,
            "methodology_adequate": True
        }
    
    def get_implementation_info(self) -> Dict[str, str]:
        """Legacy implementation info"""
        return {
            "version": "legacy",
            "description": "Current basic search approach",
            "capabilities": "keyword_search,basic_query_generation",
            "ifcn_compliance_level": "basic"
        }


class FeatureFlaggedSearchStrategy:
    """
    Feature flag wrapper for A/B testing different search strategies
    """
    
    def __init__(self, feature_flags: Dict[str, bool] = None):
        self.feature_flags = feature_flags or {}
        
        # Initialize available implementations
        self.legacy_strategy = LegacySearchStrategyAdapter()
        self.eeg_strategy = None  # Will be initialized when EEG is ready
        
    def get_active_strategy(self) -> SearchStrategyInterface:
        """Get the currently active search strategy based on feature flags"""
        
        if self.feature_flags.get("use_eeg_phase_1", False) and self.eeg_strategy:
            return self.eeg_strategy
        else:
            return self.legacy_strategy
    
    def generate_search_strategy(
        self, 
        claim_text: str,
        claim_context: Optional[Dict] = None,
        performance_requirements: Optional[Dict] = None
    ) -> SearchStrategyResult:
        """Generate search strategy using active implementation"""
        
        active_strategy = self.get_active_strategy()
        return active_strategy.generate_search_strategy(
            claim_text, claim_context, performance_requirements
        )