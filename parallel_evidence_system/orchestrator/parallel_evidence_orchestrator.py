"""
ParallelEvidenceOrchestrator - COMPLETE_ARCHITECTURE_PLAN.md lines 155-193

Core parallel evidence system orchestrator integrating ACI pipeline with
ThreadSafeEvidenceWorkers for <30s evidence processing performance.
"""

from typing import List, Dict, Any, Optional
import logging
import time
import concurrent.futures
from dataclasses import dataclass
from ..analysis.claim_analysis_engine import ClaimAnalysisEngine, ClaimAnalysisResult
from ..workers.thread_safe_evidence_worker import (
    ThreadSafeEvidenceWorker,
    ParallelSearchStrategy,
    ProcessedEvidence
)
from ..resources.thread_safe_resource_pool import ThreadSafeResourcePool


@dataclass
class ConsensusResult:
    """
    Consensus analysis result from parallel evidence processing.
    Per COMPLETE_ARCHITECTURE_PLAN.md - aggregated evidence assessment.
    """
    claim_text: str
    trust_score: float                  # 0-100 consensus trust score
    evidence_summary: List[ProcessedEvidence]
    consensus_reasoning: str            # Explanation of consensus
    processing_metadata: Dict[str, Any] # Performance metrics, worker info
    claim_analysis: ClaimAnalysisResult # Complete ACI pipeline analysis


class ParallelEvidenceOrchestrator:
    """
    Core parallel evidence system orchestrator per COMPLETE_ARCHITECTURE_PLAN.md.

    Integrates ACI pipeline with ThreadSafeEvidenceWorkers for parallel evidence
    processing with <30s performance target (from current 396s baseline).

    Architecture per lines 155-193:
    - Centralized strategy generation using complete ACI pipeline
    - Parallel execution across multiple ThreadSafeEvidenceWorkers
    - Consensus analysis with quality-weighted evidence aggregation
    """

    def __init__(self, max_workers: int = 3, worker_timeout: int = 25):
        """
        Initialize parallel evidence orchestrator per lines 158-162.

        Args:
            max_workers: Maximum concurrent ThreadSafeEvidenceWorkers (default 3)
            worker_timeout: Timeout per worker in seconds (default 25s for <30s total)
        """
        self.max_workers = max_workers
        self.worker_timeout = worker_timeout

        # Initialize core components per specification
        self.claim_analysis_engine = ClaimAnalysisEngine()
        self.resource_pool = ThreadSafeResourcePool()

        # Initialize logging
        self.logger = logging.getLogger("ParallelEvidenceOrchestrator")
        self.logger.info(f"Orchestrator initialized with {max_workers} workers, {worker_timeout}s timeout")

    def process_claim(self, claim_text: str) -> ConsensusResult:
        """
        Complete parallel evidence processing per lines 164-193.

        Per COMPLETE_ARCHITECTURE_PLAN.md specification:
        - Stage 1: Complete ACI pipeline analysis (lines 167-170)
        - Stage 2: Strategy generation with ACI integration (lines 172-175)
        - Stage 3: Parallel evidence execution (lines 177-185)
        - Stage 4: Consensus analysis and aggregation (lines 187-193)

        Args:
            claim_text: Claim to fact-check and analyze

        Returns:
            ConsensusResult: Complete parallel evidence assessment with consensus
        """
        start_time = time.time()
        self.logger.info(f"Processing claim: {claim_text[:50]}...")

        try:
            # Stage 1: Complete ACI pipeline analysis (lines 167-170)
            claim_analysis = self._execute_aci_analysis(claim_text)

            # Stage 2: Strategy generation with ACI integration (lines 172-175)
            parallel_strategy = self._generate_parallel_strategy(claim_text, claim_analysis)

            # Stage 3: Parallel evidence execution (lines 177-185)
            all_evidence = self._execute_parallel_workers(parallel_strategy)

            # Stage 4: Consensus analysis and aggregation (lines 187-193)
            consensus_result = self._analyze_consensus(
                claim_text, claim_analysis, all_evidence, start_time
            )

            processing_time = time.time() - start_time
            self.logger.info(
                f"Claim processing completed in {processing_time:.2f}s, "
                f"trust score: {consensus_result.trust_score:.1f}/100"
            )

            return consensus_result

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Claim processing failed after {processing_time:.2f}s: {str(e)}")

            # Return fallback result on failure
            return self._create_fallback_result(claim_text, str(e))

    def _execute_aci_analysis(self, claim_text: str) -> ClaimAnalysisResult:
        """
        Execute complete ACI pipeline analysis per lines 167-170.
        Provides semantic, logical, and domain analysis for enhanced strategy generation.
        """
        try:
            analysis_result = self.claim_analysis_engine.analyze_claim(claim_text)

            self.logger.info(
                f"ACI analysis complete - Domain: {analysis_result.domain_result.domain}, "
                f"Relationship: {analysis_result.semantic_result.relationship_type}, "
                f"Scope: {analysis_result.logical_result.claim_scope}"
            )

            return analysis_result

        except Exception as e:
            self.logger.error(f"ACI pipeline analysis failed: {str(e)}")
            raise

    def _generate_parallel_strategy(self, claim_text: str,
                                  claim_analysis: ClaimAnalysisResult) -> ParallelSearchStrategy:
        """
        Generate parallel search strategy per lines 172-175.
        Integrates ACI analysis with methodology requirements for enhanced search targeting.
        """
        try:
            # Use domain classification methodology requirements
            methodology_requirements = claim_analysis.domain_result.methodology_requirements

            # Generate enhanced search queries based on semantic analysis
            search_queries = self._generate_search_queries(
                claim_text, claim_analysis, methodology_requirements
            )

            strategy = ParallelSearchStrategy(
                claim_text=claim_text,
                search_queries=search_queries,
                claim_analysis=claim_analysis,
                methodology_requirements=methodology_requirements,
                parallel_execution_plan={
                    'max_workers': self.max_workers,
                    'worker_timeout': self.worker_timeout,
                    'target_evidence_per_worker': 5
                }
            )

            self.logger.info(
                f"Strategy generated - Queries: {len(search_queries)}, "
                f"Methodologies: {len(methodology_requirements)}"
            )

            return strategy

        except Exception as e:
            self.logger.error(f"Strategy generation failed: {str(e)}")
            raise

    def _generate_search_queries(self, claim_text: str, claim_analysis: ClaimAnalysisResult,
                               methodology_requirements: List[str]) -> List[str]:
        """
        Generate enhanced search queries using ACI analysis context.
        Combines semantic analysis with methodology requirements for targeted search.
        """
        queries = []

        # Base query from claim
        queries.append(claim_text)

        # Subject-focused queries from semantic analysis
        subject = claim_analysis.semantic_result.claim_subject
        object_target = claim_analysis.semantic_result.claim_object

        if subject != "unknown":
            queries.append(f"{subject} evidence research")

        if object_target != "unknown":
            queries.append(f"{subject} {claim_analysis.semantic_result.action_type} {object_target}")

        # Methodology-enhanced queries
        for methodology in methodology_requirements[:2]:  # Limit to top 2
            if methodology == "peer_reviewed":
                queries.append(f"{subject} peer reviewed study")
            elif methodology == "government_official":
                queries.append(f"{subject} official government analysis")
            elif methodology == "systematic_review":
                queries.append(f"{subject} systematic review meta-analysis")

        # Domain-specific queries
        domain = claim_analysis.domain_result.domain
        if domain == "medical_claim":
            queries.append(f"{subject} clinical trial research")
        elif domain == "economic_claim":
            queries.append(f"{subject} economic analysis data")
        elif domain == "scientific_claim":
            queries.append(f"{subject} scientific research findings")

        # Limit to 8 queries for performance
        return queries[:8]

    def _execute_parallel_workers(self, strategy: ParallelSearchStrategy) -> List[ProcessedEvidence]:
        """
        Execute parallel evidence workers per lines 177-185.
        Distributes strategy across multiple ThreadSafeEvidenceWorkers for concurrent processing.
        """
        all_evidence = []

        # Create worker instances
        workers = [
            ThreadSafeEvidenceWorker(f"worker_{i}", self.resource_pool)
            for i in range(self.max_workers)
        ]

        self.logger.info(f"Executing {len(workers)} parallel workers")

        # Execute workers in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all workers with identical strategy
            future_to_worker = {
                executor.submit(worker.execute_strategy, strategy): f"worker_{i}"
                for i, worker in enumerate(workers)
            }

            # Collect results with timeout handling
            for future in concurrent.futures.as_completed(future_to_worker, timeout=self.worker_timeout + 5):
                worker_id = future_to_worker[future]
                try:
                    evidence_batch = future.result(timeout=self.worker_timeout)
                    all_evidence.extend(evidence_batch)

                    self.logger.info(
                        f"{worker_id} completed - {len(evidence_batch)} evidence pieces"
                    )

                except concurrent.futures.TimeoutError:
                    self.logger.warning(f"{worker_id} timeout after {self.worker_timeout}s")
                except Exception as e:
                    self.logger.error(f"{worker_id} failed: {str(e)}")

        self.logger.info(f"Parallel execution complete - {len(all_evidence)} total evidence pieces")
        return all_evidence

    def _analyze_consensus(self, claim_text: str, claim_analysis: ClaimAnalysisResult,
                         all_evidence: List[ProcessedEvidence], start_time: float) -> ConsensusResult:
        """
        Analyze consensus from parallel evidence per lines 187-193.
        Aggregates evidence with quality weighting for final trust score calculation.
        """
        if not all_evidence:
            return self._create_fallback_result(claim_text, "No evidence found")

        # Sort evidence by relevance score (highest first)
        sorted_evidence = sorted(all_evidence, key=lambda x: x.relevance_score, reverse=True)

        # Take top 10 most relevant evidence pieces
        top_evidence = sorted_evidence[:10]

        # Calculate consensus trust score (weighted average)
        total_weight = 0
        weighted_sum = 0

        for evidence in top_evidence:
            # Weight by both relevance and quality scores
            weight = (evidence.relevance_score * evidence.quality_score) / 10000  # Normalize
            weighted_sum += evidence.relevance_score * weight
            total_weight += weight

        trust_score = weighted_sum / total_weight if total_weight > 0 else 50.0

        # Generate consensus reasoning
        consensus_reasoning = self._generate_consensus_reasoning(
            claim_analysis, top_evidence, trust_score
        )

        # Create processing metadata
        processing_time = time.time() - start_time
        processing_metadata = {
            'processing_time_seconds': processing_time,
            'total_evidence_found': len(all_evidence),
            'top_evidence_count': len(top_evidence),
            'workers_used': self.max_workers,
            'performance_target_met': processing_time < 30.0
        }

        return ConsensusResult(
            claim_text=claim_text,
            trust_score=trust_score,
            evidence_summary=top_evidence,
            consensus_reasoning=consensus_reasoning,
            processing_metadata=processing_metadata,
            claim_analysis=claim_analysis
        )

    def _generate_consensus_reasoning(self, claim_analysis: ClaimAnalysisResult,
                                    top_evidence: List[ProcessedEvidence],
                                    trust_score: float) -> str:
        """
        Generate explanation of consensus analysis and trust score calculation.
        """
        reasoning_parts = [
            f"Analyzed as {claim_analysis.domain_result.domain} with {claim_analysis.semantic_result.relationship_type} relationship.",
            f"Found {len(top_evidence)} relevant evidence pieces.",
            f"Average relevance score: {sum(e.relevance_score for e in top_evidence) / len(top_evidence):.1f}/100."
        ]

        # Add confidence assessment
        if trust_score >= 80:
            reasoning_parts.append("High confidence in evidence consensus.")
        elif trust_score >= 60:
            reasoning_parts.append("Moderate confidence with mixed evidence.")
        else:
            reasoning_parts.append("Low confidence, limited or conflicting evidence.")

        return " ".join(reasoning_parts)

    def _create_fallback_result(self, claim_text: str, error_reason: str) -> ConsensusResult:
        """
        Create fallback result when processing fails.
        """
        return ConsensusResult(
            claim_text=claim_text,
            trust_score=50.0,  # Neutral score on failure
            evidence_summary=[],
            consensus_reasoning=f"Processing failed: {error_reason}",
            processing_metadata={'error': error_reason},
            claim_analysis=None  # No analysis available on failure
        )