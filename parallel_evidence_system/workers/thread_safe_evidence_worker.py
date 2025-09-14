"""Thread-safe evidence worker for stateless parallel execution"""

import threading
import logging
import uuid
import time
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from dataclasses import dataclass

from ..resources.thread_safe_resource_pool import ThreadSafeResourcePool
from .worker_resource_bundle import WorkerResourceBundle
from ..orchestrator.parallel_search_strategy import WorkerTask, EEGSearchQuery, ClaimAnalysis

# Import existing evidence processing components
from web_search_service import WebSearchService
from web_content_extractor import WebContentExtractor
from evidence_quality_assessor import EvidenceQualityAssessor


@dataclass
class ProcessedEvidence:
    """Single piece of processed evidence from worker"""
    evidence_id: str
    source_url: str
    content_extract: str
    relevance_score: float
    quality_score: float
    methodology_compliance: float
    processing_metadata: Dict[str, Any]


@dataclass
class WorkerResult:
    """Complete result from ThreadSafeEvidenceWorker execution"""
    task_id: str
    worker_id: str
    evidence_list: List[ProcessedEvidence]
    processing_time_seconds: float
    success: bool
    error_message: Optional[str] = None


class ThreadSafeComponent:
    """Base class ensuring thread-safe initialization and resource management"""

    def __init__(self):
        self._local = threading.local()
        self._lock = threading.Lock()
        self.component_id = self._generate_component_id()

    def _generate_component_id(self) -> str:
        """Generate unique component identifier for logging/debugging"""
        return f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"

    def _initialize_thread_resources(self):
        """Each subclass must implement thread-local resource initialization"""
        raise NotImplementedError("Subclasses must implement _initialize_thread_resources")

    def get_thread_resources(self):
        """Get or create thread-local resources"""
        if not hasattr(self._local, 'initialized'):
            with self._lock:
                if not hasattr(self._local, 'initialized'):
                    self._initialize_thread_resources()
                    self._local.initialized = True
        return self._local


class ROGRException(Exception):
    """Base exception with context tracking"""
    def __init__(self, message: str, context: Dict[str, Any], original_error: Exception = None):
        self.message = message
        self.context = context
        self.original_error = original_error
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        return f"{self.context.get('component_name', 'Unknown')}.{self.context.get('operation_name', 'Unknown')}: {self.message}"


class ThreadSafeEvidenceWorker(ThreadSafeComponent):
    """
    Stateless evidence worker using ThreadSafeResourcePool for isolated parallel execution

    Implements:
    - Thread-safe resource isolation via ThreadSafeComponent pattern
    - Stateless execution with WorkerResourceBundle
    - Error handling with OperationContext pattern
    - Evidence processing with quality scoring
    """

    def __init__(self, worker_id: str, resource_pool: ThreadSafeResourcePool):
        super().__init__()
        self.worker_id = worker_id
        self.resource_pool = resource_pool
        self.logger = logging.getLogger(f"rogr.ThreadSafeEvidenceWorker.{worker_id}")

    def _initialize_thread_resources(self):
        """Initialize thread-local resources using resource pool"""
        resources = self.resource_pool.get_thread_resources()

        self._local.session = resources['http_session']
        self._local.anthropic_api_key = resources['anthropic_api_key']
        self._local.openai_api_key = resources['openai_api_key']
        self._local.worker_id = f"worker_{threading.current_thread().ident}"

        # Initialize evidence processing components with isolated resources
        # Pass the HTTP session to services that need it
        self._local.web_search = WebSearchService()
        self._local.content_extractor = WebContentExtractor()
        self._local.quality_assessor = EvidenceQualityAssessor()

    def execute_task(self, task: WorkerTask) -> WorkerResult:
        """
        Execute single worker task with comprehensive error handling

        Args:
            task: WorkerTask containing search query and context

        Returns:
            WorkerResult with processed evidence or error information
        """
        start_time = time.time()

        context = {
            'session_id': task.task_id,
            'component_name': 'ThreadSafeEvidenceWorker',
            'operation_name': 'execute_task',
            'claim_text': task.claim_context.claim_text[:50]
        }

        self.logger.info("Starting task execution", extra={
            'task_id': task.task_id,
            'worker_id': self.worker_id,
            'ai_provider': task.ai_provider,
            'query_preview': task.search_query.query_text[:50]
        })

        try:
            with self._managed_execution_context():
                evidence_list = self._process_evidence(task, context)

                processing_time = time.time() - start_time

                self.logger.info("Task execution successful", extra={
                    'task_id': task.task_id,
                    'worker_id': self.worker_id,
                    'evidence_count': len(evidence_list),
                    'duration_seconds': processing_time
                })

                return WorkerResult(
                    task_id=task.task_id,
                    worker_id=self.worker_id,
                    evidence_list=evidence_list,
                    processing_time_seconds=processing_time,
                    success=True
                )

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)

            self.logger.error("Task execution failed", extra={
                'task_id': task.task_id,
                'worker_id': self.worker_id,
                'error_type': type(e).__name__,
                'error_message': error_message,
                'duration_seconds': processing_time
            })

            # PHASE 3 DEBUG: Print error details directly to ensure visibility
            print(f"WORKER ERROR DETAILS - Task: {task.task_id}, Worker: {self.worker_id}")
            print(f"ERROR TYPE: {type(e).__name__}")
            print(f"ERROR MESSAGE: {error_message}")
            print(f"DURATION: {processing_time}s")

            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                evidence_list=[],
                processing_time_seconds=processing_time,
                success=False,
                error_message=error_message
            )

    @contextmanager
    def _managed_execution_context(self):
        """Context manager for resource management during task execution"""
        resources = self.get_thread_resources()
        try:
            yield resources
        finally:
            # Resource cleanup handled by resource pool
            pass

    def _process_evidence(self, task: WorkerTask, context: Dict[str, Any]) -> List[ProcessedEvidence]:
        """
        Process evidence for given task using thread-local resources

        Args:
            task: WorkerTask to process
            context: Execution context for error handling

        Returns:
            List of ProcessedEvidence objects
        """
        resources = self.get_thread_resources()
        evidence_list = []

        # Step 1: Execute web search using thread-local web search service
        try:
            search_results = self._execute_web_search(
                task.search_query.query_text,
                resources,
                context
            )
        except Exception as e:
            raise ROGRException(f"Web search failed for query: {task.search_query.query_text}", context, e)

        # Step 2: Extract and process content from search results
        for i, search_result in enumerate(search_results[:5]):  # Limit to top 5 results
            try:
                evidence = self._process_single_result(
                    search_result,
                    task,
                    resources,
                    f"{task.task_id}_evidence_{i}"
                )
                if evidence:
                    evidence_list.append(evidence)

            except Exception as e:
                self.logger.warning(f"Failed to process search result {i}", extra={
                    'task_id': task.task_id,
                    'result_url': search_result.get('url', 'unknown'),
                    'error': str(e)
                })
                continue

        return evidence_list

    def _execute_web_search(self, query: str, resources: Any, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute web search using thread-local web search service"""
        try:
            # Use thread-local web search service
            search_results = resources.web_search.search(query, max_results=10)
            return search_results if search_results else []

        except Exception as e:
            raise ROGRException(f"Web search service failed", context, e)

    def _process_single_result(self,
                              search_result: Dict[str, Any],
                              task: WorkerTask,
                              resources: Any,
                              evidence_id: str) -> Optional[ProcessedEvidence]:
        """
        Process single search result into evidence

        Args:
            search_result: Raw search result from web search
            task: Original worker task
            resources: Thread-local resources
            evidence_id: Unique identifier for this evidence

        Returns:
            ProcessedEvidence object or None if processing fails
        """
        try:
            # Extract content using thread-local content extractor
            content_data = resources.content_extractor.extract_content(search_result['url'])

            if not content_data or not content_data.get('cleaned_content'):
                return None

            # Calculate quality scores using thread-local quality assessor
            quality_scores = resources.quality_assessor.assess_evidence_quality(
                content_data['cleaned_content'],
                task.claim_context.claim_text
            )

            # Create processed evidence
            evidence = ProcessedEvidence(
                evidence_id=evidence_id,
                source_url=search_result['url'],
                content_extract=content_data['cleaned_content'][:1000],  # First 1000 chars
                relevance_score=quality_scores.get('relevance_score', 0.0),
                quality_score=quality_scores.get('overall_quality', 0.0),
                methodology_compliance=quality_scores.get('methodology_score', 0.0),
                processing_metadata={
                    'worker_id': self.worker_id,
                    'task_id': task.task_id,
                    'search_query': task.search_query.query_text,
                    'ai_provider': task.ai_provider,
                    'processed_at': time.time(),
                    'content_length': len(content_data['cleaned_content'])
                }
            )

            return evidence

        except Exception as e:
            self.logger.warning(f"Failed to process evidence from {search_result.get('url', 'unknown')}: {str(e)}")
            return None

    def get_worker_status(self) -> Dict[str, Any]:
        """Get current worker status and metrics"""
        return {
            'worker_id': self.worker_id,
            'component_id': self.component_id,
            'thread_id': threading.current_thread().ident,
            'thread_name': threading.current_thread().name,
            'thread_local_initialized': hasattr(self._local, 'initialized'),
            'resource_pool_id': self.resource_pool.pool_id
        }