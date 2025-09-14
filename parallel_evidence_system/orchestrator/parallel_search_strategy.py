"""Parallel search strategy data structures for orchestrated evidence processing"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class ClaimComplexity(Enum):
    """Claim complexity levels for processing strategy optimization"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    HIGHLY_COMPLEX = "highly_complex"


@dataclass
class ClaimAnalysis:
    """ACI semantic analysis results for claim understanding"""
    claim_text: str
    semantic_classification: str
    logical_structure: Dict[str, Any]
    domain_categories: List[str]
    complexity_level: ClaimComplexity
    key_entities: List[str]
    temporal_context: Optional[str] = None
    geographic_context: Optional[str] = None


@dataclass
class EEGSearchQuery:
    """Enhanced EEG Phase 1 query with methodology-first approach"""
    query_text: str
    methodology_type: str  # "statistical", "observational", "experimental", etc.
    ifcn_compliance_score: float
    expected_evidence_type: str
    priority_weight: float = 1.0


@dataclass
class ParallelSearchStrategy:
    """Complete search strategy for parallel evidence processing"""
    session_id: str
    claim_analysis: ClaimAnalysis
    eeg_queries: List[EEGSearchQuery]
    processing_metadata: Dict[str, Any]

    @property
    def total_queries(self) -> int:
        """Total number of search queries"""
        return len(self.eeg_queries)

    @property
    def complexity_level(self) -> ClaimComplexity:
        """Claim complexity level"""
        return self.claim_analysis.complexity_level

    def get_high_priority_queries(self, limit: int = 5) -> List[EEGSearchQuery]:
        """Get highest priority queries for processing"""
        sorted_queries = sorted(self.eeg_queries, key=lambda q: q.priority_weight, reverse=True)
        return sorted_queries[:limit]


@dataclass
class WorkerTask:
    """Individual task for ThreadSafeEvidenceWorker"""
    task_id: str
    worker_id: str
    search_query: EEGSearchQuery
    claim_context: ClaimAnalysis
    ai_provider: str  # "anthropic" or "openai"
    timeout_seconds: int = 30


@dataclass
class ParallelProcessingPlan:
    """Complete processing plan with worker task distribution"""
    strategy: ParallelSearchStrategy
    worker_tasks: List[WorkerTask]
    estimated_duration_seconds: float
    concurrency_level: int

    @classmethod
    def from_strategy(cls, strategy: ParallelSearchStrategy, max_workers: int = 4) -> 'ParallelProcessingPlan':
        """Create processing plan from search strategy"""
        worker_tasks = []

        # Distribute queries across workers and AI providers
        for i, query in enumerate(strategy.eeg_queries):
            ai_provider = "anthropic" if i % 2 == 0 else "openai"
            worker_id = f"worker_{i % max_workers}"

            task = WorkerTask(
                task_id=f"task_{i}_{strategy.session_id}",
                worker_id=worker_id,
                search_query=query,
                claim_context=strategy.claim_analysis,
                ai_provider=ai_provider,
                timeout_seconds=30
            )
            worker_tasks.append(task)

        # Estimate duration based on complexity
        base_duration = 15  # seconds
        complexity_multiplier = {
            ClaimComplexity.SIMPLE: 1.0,
            ClaimComplexity.MODERATE: 1.2,
            ClaimComplexity.COMPLEX: 1.5,
            ClaimComplexity.HIGHLY_COMPLEX: 2.0
        }

        estimated_duration = base_duration * complexity_multiplier[strategy.complexity_level]

        return cls(
            strategy=strategy,
            worker_tasks=worker_tasks,
            estimated_duration_seconds=estimated_duration,
            concurrency_level=min(len(worker_tasks), max_workers)
        )