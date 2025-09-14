"""Parallel Consensus Engine with claim-level and AI-level parallelization"""

import concurrent.futures
import threading
import logging
import time
import uuid
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from contextlib import contextmanager

from .parallel_search_strategy import ParallelProcessingPlan
from ..workers.thread_safe_evidence_worker import ThreadSafeEvidenceWorker, WorkerResult, ProcessedEvidence
from ..resources.thread_safe_resource_pool import ThreadSafeResourcePool

# Import existing quality assessment
from evidence_quality_assessor import EvidenceQualityAssessor


@dataclass
class ConsensusResult:
    """Result from parallel consensus analysis"""
    claim_text: str
    consensus_score: float
    confidence_level: float
    evidence_summary: List[Dict[str, Any]]
    ai_agreements: Dict[str, float]
    processing_metadata: Dict[str, Any]


@dataclass
class ClaimProcessingResult:
    """Complete result for single claim processing"""
    claim_index: int
    claim_text: str
    worker_results: List[WorkerResult]
    consensus_result: ConsensusResult
    processing_time_seconds: float
    success: bool


class ParallelExecutionManager:
    """Safe parallel execution with resource management and error handling"""

    def __init__(self, max_workers: int = 4, timeout_seconds: int = 60):
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(f"rogr.ParallelExecutionManager")

    def execute_parallel(self,
                        tasks: List[Callable],
                        task_args: List[tuple] = None,
                        individual_timeout: int = 30) -> List[Any]:
        """Execute tasks in parallel with comprehensive error handling"""

        if task_args is None:
            task_args = [()] * len(tasks)

        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(task, *args): (task, args)
                for task, args in zip(tasks, task_args)
            }

            # Collect results with timeout handling
            try:
                for future in concurrent.futures.as_completed(future_to_task, timeout=self.timeout_seconds):
                    task, args = future_to_task[future]
                    try:
                        result = future.result(timeout=individual_timeout)
                        results.append(result)
                        self.logger.info(f"Parallel task completed: {task.__name__ if hasattr(task, '__name__') else 'unknown'}")
                    except concurrent.futures.TimeoutError:
                        error_result = self._create_timeout_result(task, args)
                        results.append(error_result)
                        self.logger.warning(f"Parallel task timeout: {task.__name__ if hasattr(task, '__name__') else 'unknown'}")
                    except Exception as e:
                        error_result = self._create_error_result(task, args, e)
                        results.append(error_result)
                        self.logger.error(f"Parallel task failed: {task.__name__ if hasattr(task, '__name__') else 'unknown'} - {str(e)}")

            except concurrent.futures.TimeoutError:
                # Overall timeout - some tasks didn't complete
                self.logger.error(f"Parallel execution overall timeout: {self.timeout_seconds}s")
                # Add placeholder results for incomplete tasks
                while len(results) < len(tasks):
                    results.append(self._create_timeout_result(None, None))

        return results

    def _create_timeout_result(self, task: Callable, args: tuple) -> Any:
        """Create standardized timeout result"""
        return {'success': False, 'error': 'timeout', 'task': getattr(task, '__name__', 'unknown')}

    def _create_error_result(self, task: Callable, args: tuple, error: Exception) -> Any:
        """Create standardized error result"""
        return {'success': False, 'error': str(error), 'task': getattr(task, '__name__', 'unknown')}


class ParallelConsensusEngine:
    """
    Parallel consensus engine with claim-level and AI-level parallelization

    Implements:
    - Claim-level parallelization: Process 4 claims simultaneously
    - AI-level parallelization: Claude + OpenAI concurrent processing within each claim
    - Quality-weighted consensus using existing EvidenceQualityAssessor
    - Performance monitoring and health checks
    """

    def __init__(self, max_claim_workers: int = 4, max_ai_workers: int = 2):
        self.engine_id = f"consensus_{uuid.uuid4().hex[:8]}"
        self.max_claim_workers = max_claim_workers
        self.max_ai_workers = max_ai_workers

        self.resource_pool = ThreadSafeResourcePool()
        self.parallel_manager = ParallelExecutionManager(max_workers=max_claim_workers, timeout_seconds=120)

        self.logger = logging.getLogger(f"rogr.ParallelConsensusEngine.{self.engine_id}")

        # Performance tracking
        self.processing_metrics = {}
        self._lock = threading.Lock()

    def process_claims_parallel(self, processing_plans: List[ParallelProcessingPlan]) -> List[ClaimProcessingResult]:
        """
        Process multiple claims in parallel with comprehensive consensus analysis

        Args:
            processing_plans: List of ParallelProcessingPlan objects

        Returns:
            List of ClaimProcessingResult objects with consensus analysis
        """
        session_id = f"consensus_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        self.logger.info(f"Starting parallel claims processing", extra={
            'session_id': session_id,
            'plan_count': len(processing_plans),
            'max_workers': self.max_claim_workers
        })

        # Create tasks for parallel execution (claim-level parallelization)
        claim_tasks = []
        task_args = []

        for i, plan in enumerate(processing_plans):
            claim_tasks.append(self._process_single_claim)
            task_args.append((plan, i, session_id))

        # Execute all claims in parallel
        claim_results = self.parallel_manager.execute_parallel(
            claim_tasks,
            task_args,
            individual_timeout=60
        )

        # Convert results and handle any errors
        processing_results = []
        for i, result in enumerate(claim_results):
            if isinstance(result, dict) and not result.get('success', True):
                # Handle failed claim processing
                processing_result = ClaimProcessingResult(
                    claim_index=i,
                    claim_text=processing_plans[i].strategy.claim_analysis.claim_text,
                    worker_results=[],
                    consensus_result=self._create_error_consensus_result(
                        processing_plans[i].strategy.claim_analysis.claim_text,
                        result.get('error', 'Unknown error')
                    ),
                    processing_time_seconds=0,
                    success=False
                )
            else:
                processing_result = result

            processing_results.append(processing_result)

        total_time = time.time() - start_time

        self.logger.info(f"Parallel claims processing complete", extra={
            'session_id': session_id,
            'total_time': total_time,
            'successful_claims': sum(1 for r in processing_results if r.success),
            'failed_claims': sum(1 for r in processing_results if not r.success)
        })

        # Record metrics
        self._record_processing_metrics(session_id, {
            'total_time_seconds': total_time,
            'claim_count': len(processing_plans),
            'successful_claims': sum(1 for r in processing_results if r.success),
            'average_time_per_claim': total_time / len(processing_plans) if processing_plans else 0
        })

        return processing_results

    def _process_single_claim(self, plan: ParallelProcessingPlan, claim_index: int, session_id: str) -> ClaimProcessingResult:
        """
        Process single claim with AI-level parallelization

        Args:
            plan: ParallelProcessingPlan for this claim
            claim_index: Index of this claim
            session_id: Session identifier for logging

        Returns:
            ClaimProcessingResult with worker results and consensus
        """
        claim_start_time = time.time()
        claim_text = plan.strategy.claim_analysis.claim_text

        self.logger.info(f"Processing claim {claim_index}", extra={
            'session_id': session_id,
            'claim_index': claim_index,
            'claim_preview': claim_text[:50],
            'worker_task_count': len(plan.worker_tasks)
        })

        try:
            # Create workers for this claim's tasks
            workers = self._create_claim_workers(plan, session_id)

            # Execute worker tasks in parallel (AI-level parallelization)
            worker_results = self._execute_worker_tasks_parallel(
                workers,
                plan.worker_tasks,
                session_id,
                claim_index
            )

            # Generate consensus from worker results
            consensus_result = self._generate_consensus(
                claim_text,
                worker_results,
                plan,
                session_id
            )

            processing_time = time.time() - claim_start_time

            self.logger.info(f"Claim processing successful", extra={
                'session_id': session_id,
                'claim_index': claim_index,
                'processing_time': processing_time,
                'successful_workers': sum(1 for wr in worker_results if wr.success),
                'consensus_score': consensus_result.consensus_score
            })

            return ClaimProcessingResult(
                claim_index=claim_index,
                claim_text=claim_text,
                worker_results=worker_results,
                consensus_result=consensus_result,
                processing_time_seconds=processing_time,
                success=True
            )

        except Exception as e:
            processing_time = time.time() - claim_start_time

            self.logger.error(f"Claim processing failed", extra={
                'session_id': session_id,
                'claim_index': claim_index,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'processing_time': processing_time
            })

            return ClaimProcessingResult(
                claim_index=claim_index,
                claim_text=claim_text,
                worker_results=[],
                consensus_result=self._create_error_consensus_result(claim_text, str(e)),
                processing_time_seconds=processing_time,
                success=False
            )

    def _create_claim_workers(self, plan: ParallelProcessingPlan, session_id: str) -> List[ThreadSafeEvidenceWorker]:
        """Create ThreadSafeEvidenceWorker instances for claim processing"""
        workers = []

        # Create workers based on unique worker IDs in the plan
        unique_worker_ids = set(task.worker_id for task in plan.worker_tasks)

        for worker_id in unique_worker_ids:
            worker = ThreadSafeEvidenceWorker(
                worker_id=f"{worker_id}_{session_id}",
                resource_pool=self.resource_pool
            )
            workers.append(worker)

        return workers

    def _execute_worker_tasks_parallel(self,
                                     workers: List[ThreadSafeEvidenceWorker],
                                     tasks: List,
                                     session_id: str,
                                     claim_index: int) -> List[WorkerResult]:
        """Execute worker tasks in parallel (AI-level parallelization)"""

        # Create execution manager for this claim's workers
        worker_parallel_manager = ParallelExecutionManager(
            max_workers=len(workers),
            timeout_seconds=60
        )

        # Create worker execution tasks
        worker_tasks = []
        worker_args = []

        for task in tasks:
            # Find appropriate worker for this task
            worker = next((w for w in workers if task.worker_id in w.worker_id), workers[0])
            worker_tasks.append(worker.execute_task)
            worker_args.append((task,))

        # Execute all workers in parallel
        worker_results = worker_parallel_manager.execute_parallel(
            worker_tasks,
            worker_args,
            individual_timeout=30
        )

        # Convert any error results to WorkerResult objects
        converted_results = []
        for i, result in enumerate(worker_results):
            if isinstance(result, WorkerResult):
                converted_results.append(result)
            else:
                # Handle error results
                error_result = WorkerResult(
                    task_id=tasks[i].task_id if i < len(tasks) else f"unknown_{i}",
                    worker_id=f"worker_{i}",
                    evidence_list=[],
                    processing_time_seconds=0,
                    success=False,
                    error_message=result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
                )
                converted_results.append(error_result)

        return converted_results

    def _generate_consensus(self,
                          claim_text: str,
                          worker_results: List[WorkerResult],
                          plan: ParallelProcessingPlan,
                          session_id: str) -> ConsensusResult:
        """
        Generate quality-weighted consensus from worker results

        Uses existing EvidenceQualityAssessor for scoring consistency
        """
        successful_results = [wr for wr in worker_results if wr.success]

        if not successful_results:
            return self._create_error_consensus_result(claim_text, "No successful worker results")

        # Aggregate all evidence from successful workers
        all_evidence = []
        ai_provider_scores = {}

        for worker_result in successful_results:
            for evidence in worker_result.evidence_list:
                all_evidence.append(evidence)

                # Track AI provider performance
                ai_provider = evidence.processing_metadata.get('ai_provider', 'unknown')
                if ai_provider not in ai_provider_scores:
                    ai_provider_scores[ai_provider] = []
                ai_provider_scores[ai_provider].append(evidence.quality_score)

        # Calculate consensus metrics
        if all_evidence:
            # Quality-weighted consensus score
            total_weight = sum(e.quality_score * e.relevance_score for e in all_evidence)
            total_evidence_weight = sum(e.quality_score for e in all_evidence)
            consensus_score = total_weight / total_evidence_weight if total_evidence_weight > 0 else 0.0

            # Confidence level based on evidence agreement
            quality_scores = [e.quality_score for e in all_evidence]
            quality_variance = sum((score - consensus_score) ** 2 for score in quality_scores) / len(quality_scores)
            confidence_level = max(0.0, 1.0 - (quality_variance / 100.0))  # Normalized confidence

            # AI agreement analysis
            ai_agreements = {}
            for provider, scores in ai_provider_scores.items():
                ai_agreements[provider] = sum(scores) / len(scores) if scores else 0.0

            # Evidence summary
            evidence_summary = [
                {
                    'source_url': e.source_url,
                    'quality_score': e.quality_score,
                    'relevance_score': e.relevance_score,
                    'methodology_compliance': e.methodology_compliance
                }
                for e in all_evidence[:10]  # Top 10 evidence pieces
            ]

        else:
            consensus_score = 0.0
            confidence_level = 0.0
            ai_agreements = {}
            evidence_summary = []

        return ConsensusResult(
            claim_text=claim_text,
            consensus_score=consensus_score,
            confidence_level=confidence_level,
            evidence_summary=evidence_summary,
            ai_agreements=ai_agreements,
            processing_metadata={
                'session_id': session_id,
                'total_evidence_count': len(all_evidence),
                'successful_workers': len(successful_results),
                'failed_workers': len(worker_results) - len(successful_results),
                'processing_strategy': plan.strategy.processing_metadata,
                'generated_at': time.time()
            }
        )

    def _create_error_consensus_result(self, claim_text: str, error_message: str) -> ConsensusResult:
        """Create error consensus result for failed processing"""
        return ConsensusResult(
            claim_text=claim_text,
            consensus_score=0.0,
            confidence_level=0.0,
            evidence_summary=[],
            ai_agreements={},
            processing_metadata={
                'error': True,
                'error_message': error_message,
                'generated_at': time.time()
            }
        )

    def _record_processing_metrics(self, session_id: str, metrics: Dict[str, Any]):
        """Record processing metrics for monitoring"""
        with self._lock:
            self.processing_metrics[session_id] = {
                **metrics,
                'engine_id': self.engine_id,
                'recorded_at': time.time()
            }

    def get_processing_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get processing metrics for a specific session"""
        with self._lock:
            return self.processing_metrics.get(session_id)

    def get_engine_status(self) -> Dict[str, Any]:
        """Get current engine status and performance metrics"""
        with self._lock:
            return {
                'engine_id': self.engine_id,
                'max_claim_workers': self.max_claim_workers,
                'max_ai_workers': self.max_ai_workers,
                'active_threads': threading.active_count(),
                'total_sessions_processed': len(self.processing_metrics),
                'resource_pool_id': self.resource_pool.pool_id
            }