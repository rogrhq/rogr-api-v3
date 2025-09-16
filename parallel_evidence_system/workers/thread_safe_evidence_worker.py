"""
ThreadSafeEvidenceWorker - COMPLETE_ARCHITECTURE_PLAN.md lines 110-152

Completely stateless evidence execution worker per Phase 2 specifications.
Pure execution pattern - no strategy generation, no shared state.
"""

from typing import List, Optional
import logging
import time
from dataclasses import dataclass
from ..resources.thread_safe_resource_pool import ThreadSafeResourcePool
from ..resources.worker_resource_bundle import WorkerResourceBundle
from ..analysis.evidence_validator import RelevanceValidationResult


@dataclass
class ParallelSearchStrategy:
    """
    Search strategy data structure for parallel execution.
    Per COMPLETE_ARCHITECTURE_PLAN.md - complete strategy from orchestrator.
    """
    claim_text: str
    search_queries: List[str]
    claim_analysis: 'ClaimAnalysisResult'  # Forward reference to avoid circular import
    methodology_requirements: List[str] = None
    parallel_execution_plan: dict = None


@dataclass
class ProcessedEvidence:
    """
    Processed evidence result per COMPLETE_ARCHITECTURE_PLAN.md specification.
    Complete evidence assessment with relevance scoring and metadata.
    """
    text: str                           # Evidence content
    source_url: str                     # Original source URL
    source_domain: str                  # Source domain
    source_title: str                   # Source title
    relevance_score: float              # 0-100 relevance score
    quality_score: float                # 0-100 quality score
    processing_metadata: dict           # Worker ID, processing time, etc.
    relevance_reasoning: str            # Explanation of relevance assessment


class ThreadSafeEvidenceWorker:
    """
    Completely stateless evidence execution worker per COMPLETE_ARCHITECTURE_PLAN.md.

    Pure execution pattern implementation:
    - No strategy generation (orchestrator provides complete strategy)
    - No shared state between workers
    - Thread-safe resource isolation
    - Performance target: <30s evidence processing per worker
    """

    def __init__(self, worker_id: str, resource_pool: ThreadSafeResourcePool):
        """
        Initialize thread-safe evidence worker per specification lines 115-117.

        Args:
            worker_id: Unique worker identifier for logging/debugging
            resource_pool: Thread-safe resource pool for isolated resource access
        """
        self.worker_id = worker_id
        self.resource_pool = resource_pool
        self.resources: Optional[WorkerResourceBundle] = None

        # Initialize logging for this worker
        self.logger = logging.getLogger(f"ThreadSafeEvidenceWorker.{worker_id}")
        self.logger.info(f"Worker {worker_id} initialized")

    def execute_strategy(self, strategy: ParallelSearchStrategy) -> List[ProcessedEvidence]:
        """
        Pure execution - no strategy generation, no shared state per lines 119-151.

        Per COMPLETE_ARCHITECTURE_PLAN.md specification:
        - Thread-safe web search using isolated HTTP sessions
        - Thread-safe parallel content extraction
        - Thread-safe AI evidence scoring with isolated clients
        - Returns top 5 most relevant evidence pieces

        Args:
            strategy: Complete search strategy from ParallelEvidenceOrchestrator

        Returns:
            List[ProcessedEvidence]: Top 5 most relevant evidence pieces
        """
        start_time = time.time()

        # Get thread-local resources
        self.resources = self.resource_pool.get_worker_resources()

        self.logger.info(
            f"Worker {self.worker_id} executing strategy for claim: {strategy.claim_text[:50]}..."
        )

        try:
            # Step 1: Thread-safe web search (lines 124-127)
            evidence_candidates = self._execute_web_search(strategy)

            # Step 2: Thread-safe parallel content extraction (lines 129-131)
            extracted_content = self._extract_content_batch(evidence_candidates)

            # Step 3: Thread-safe AI evidence scoring (lines 133-150)
            processed_evidence = self._score_evidence_relevance(
                strategy, extracted_content
            )

            # Return top 5 most relevant (line 151)
            top_evidence = processed_evidence[:5]

            processing_time = time.time() - start_time
            self.logger.info(
                f"Worker {self.worker_id} completed processing in {processing_time:.2f}s, "
                f"found {len(top_evidence)} evidence pieces"
            )

            return top_evidence

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(
                f"Worker {self.worker_id} failed after {processing_time:.2f}s: {str(e)}"
            )
            return []  # Return empty list on failure

    def _execute_web_search(self, strategy: ParallelSearchStrategy) -> List[dict]:
        """
        Thread-safe web search per lines 124-127.
        Uses isolated HTTP session from WorkerResourceBundle.
        """
        evidence_candidates = []

        for query in strategy.search_queries:
            try:
                # Use thread-local web search service
                results = self.resources.web_search.search_web(query, max_results=8)
                evidence_candidates.extend(results)

                self.logger.debug(
                    f"Worker {self.worker_id} found {len(results)} results for query: {query[:30]}..."
                )

            except Exception as e:
                self.logger.warning(
                    f"Worker {self.worker_id} web search failed for query '{query[:30]}...': {str(e)}"
                )
                continue

        self.logger.info(
            f"Worker {self.worker_id} collected {len(evidence_candidates)} evidence candidates"
        )

        return evidence_candidates

    def _extract_content_batch(self, evidence_candidates: List[dict]) -> List[dict]:
        """
        Thread-safe parallel content extraction per lines 129-131.
        Uses isolated HTTP session from WorkerResourceBundle.
        """
        # Limit to top 10 candidates for performance
        top_candidates = evidence_candidates[:10]
        urls = [result.get('url', '') for result in top_candidates if result.get('url')]

        if not urls:
            self.logger.warning(f"Worker {self.worker_id} has no valid URLs for content extraction")
            return []

        try:
            # Use thread-local content extractor
            extraction_results = self.resources.content_extractor.extract_content_batch(urls)

            # Combine original candidates with extracted content
            combined_results = []
            for i, candidate in enumerate(top_candidates):
                if i < len(extraction_results) and extraction_results[i]['success']:
                    combined_result = {
                        **candidate,
                        'extracted_content': extraction_results[i]['content'][:800],  # Limit content
                        'extraction_success': True
                    }
                    combined_results.append(combined_result)

            self.logger.info(
                f"Worker {self.worker_id} successfully extracted content from {len(combined_results)} sources"
            )

            return combined_results

        except Exception as e:
            self.logger.error(
                f"Worker {self.worker_id} content extraction failed: {str(e)}"
            )
            return []

    def _score_evidence_relevance(self, strategy: ParallelSearchStrategy,
                                extracted_content: List[dict]) -> List[ProcessedEvidence]:
        """
        Thread-safe AI evidence scoring per lines 133-150.
        Uses isolated AI client from WorkerResourceBundle.
        """
        processed_evidence = []

        for content_item in extracted_content:
            if not content_item.get('extraction_success') or not content_item.get('extracted_content'):
                continue

            try:
                # Use thread-local evidence validator
                relevance_result = self.resources.evidence_validator.validate_relevance(
                    claim_text=strategy.claim_text,
                    evidence_text=content_item['extracted_content'],
                    claim_analysis=strategy.claim_analysis
                )

                # Create ProcessedEvidence object
                processed_evidence_item = ProcessedEvidence(
                    text=content_item['extracted_content'],
                    source_url=content_item.get('url', ''),
                    source_domain=content_item.get('domain', ''),
                    source_title=content_item.get('title', ''),
                    relevance_score=relevance_result.final_relevance_score,
                    quality_score=relevance_result.evidence_quality_score,
                    processing_metadata={
                        'worker_id': self.worker_id,
                        'processing_time': time.time(),
                        'semantic_score': relevance_result.semantic_match_score,
                        'logical_score': relevance_result.logical_relevance_score,
                        'scope_score': relevance_result.scope_alignment_score
                    },
                    relevance_reasoning=relevance_result.relevance_reasoning
                )

                processed_evidence.append(processed_evidence_item)

                self.logger.debug(
                    f"Worker {self.worker_id} scored evidence: {relevance_result.final_relevance_score:.1f}/100"
                )

            except Exception as e:
                self.logger.warning(
                    f"Worker {self.worker_id} evidence scoring failed for item: {str(e)}"
                )
                continue

        # Sort by relevance score (highest first)
        processed_evidence.sort(key=lambda x: x.relevance_score, reverse=True)

        self.logger.info(
            f"Worker {self.worker_id} processed {len(processed_evidence)} evidence items"
        )

        return processed_evidence