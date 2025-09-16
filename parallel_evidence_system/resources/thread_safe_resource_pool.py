"""
ThreadSafeResourcePool implementation following FLAWLESS_IMPLEMENTATION_METHODOLOGY.md L2 validation

TRACEABILITY:
- COMPLETE_ARCHITECTURE_PLAN.md lines 48-64: ThreadSafeResourcePool specification
- CODE_PATTERNS.md lines 13-39: ThreadSafeComponent pattern
- ADR-002: Thread-Safe Resource Management Pattern
- COMPLETE_COMPONENT_SPECIFICATIONS.md lines 413-421: WorkerResourceBundle creation
"""

import threading  # ADR-002: Thread-local resource isolation
import uuid       # CODE_PATTERNS.md: Component ID generation
from abc import ABC, abstractmethod  # CODE_PATTERNS.md lines 13-14
from typing import Any
from dataclasses import dataclass

# Import from local module - traced to COMPLETE_COMPONENT_SPECIFICATIONS.md line 418
from .worker_resource_bundle import WorkerResourceBundle


class ThreadSafeComponent(ABC):
    """
    Base class ensuring thread-safe initialization and resource management

    TRACEABILITY: CODE_PATTERNS.md lines 13-39
    """

    def __init__(self):
        self._local = threading.local()  # CODE_PATTERNS.md line 17
        self._lock = threading.Lock()    # CODE_PATTERNS.md line 18
        self.component_id = self._generate_component_id()  # CODE_PATTERNS.md line 19

    def _generate_component_id(self) -> str:
        """Generate unique component identifier for logging/debugging"""
        # TRACEABILITY: CODE_PATTERNS.md lines 23-24
        return f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"

    @abstractmethod
    def _initialize_thread_resources(self):
        """Each subclass must implement thread-local resource initialization"""
        # TRACEABILITY: CODE_PATTERNS.md lines 27-29
        pass

    def get_thread_resources(self):
        """Get or create thread-local resources"""
        # TRACEABILITY: CODE_PATTERNS.md lines 32-38
        if not hasattr(self._local, 'initialized'):
            with self._lock:
                if not hasattr(self._local, 'initialized'):
                    self._initialize_thread_resources()
                    self._local.initialized = True
        return self._local


class ThreadLocalSessionPool:
    """
    Thread-local HTTP session pool

    TRACEABILITY: ADR-002 line 36 web_search service requirement
    """

    def __init__(self):
        self._local = threading.local()  # ADR-002: thread isolation

    def get_local(self):
        """Get thread-local HTTP session"""
        if not hasattr(self._local, 'session'):
            import requests  # Legacy system dependency verified via grep
            self._local.session = requests.Session()
        return self._local.session


class ThreadLocalAIClientPool:
    """
    Thread-local AI client pool

    TRACEABILITY: COMPLETE_COMPONENT_SPECIFICATIONS.md line 418 evidence_validator requirement
    """

    def __init__(self):
        self._local = threading.local()  # ADR-002: thread isolation

    def get_local(self):
        """Get thread-local AI client"""
        if not hasattr(self._local, 'client'):
            import anthropic  # Legacy system dependency verified via grep
            self._local.client = anthropic.Anthropic()
        return self._local.client


class APIRateLimitPool:
    """
    API rate limiting pool with worker coordination

    TRACEABILITY: COMPLETE_COMPONENT_SPECIFICATIONS.md line 405 rate_limiter requirement
    """

    def __init__(self):
        self._rate_limiter = None  # Phase 1 foundation - implementation in Phase 2

    def get_limiter(self):
        """Get rate limiter for API calls"""
        return self._rate_limiter


class ThreadSafeResourcePool(ThreadSafeComponent):
    """
    Thread-safe resource pool with complete isolation

    TRACEABILITY:
    - COMPLETE_ARCHITECTURE_PLAN.md lines 48-64: Core specification
    - ADR-002: Thread-Safe Resource Management Pattern
    - CODE_PATTERNS.md ThreadSafeComponent pattern
    """

    def __init__(self):
        super().__init__()  # CODE_PATTERNS.md ThreadSafeComponent pattern
        # TRACEABILITY: ADR-002 lines 34-39 resource pools
        self._session_pool = ThreadLocalSessionPool()
        self._ai_client_pool = ThreadLocalAIClientPool()
        self._api_limiter = APIRateLimitPool()

    def _initialize_thread_resources(self):
        """Initialize thread-local resource bundle"""
        # TRACEABILITY: CODE_PATTERNS.md abstractmethod implementation requirement
        # Thread-local resources initialized on first access via WorkerResourceBundle creation
        pass

    def get_worker_resources(self) -> WorkerResourceBundle:
        """
        Get thread-isolated worker resource bundle

        TRACEABILITY:
        - COMPLETE_ARCHITECTURE_PLAN.md line 58: Method signature
        - COMPLETE_COMPONENT_SPECIFICATIONS.md lines 413-421: Implementation pattern
        """
        if not hasattr(self._local, 'resources'):
            # TRACEABILITY: Circular import prevention pattern
            from .web_search_service import WebSearchService
            from .web_content_extractor import WebContentExtractor
            from ..analysis.evidence_validator import EvidenceRelevanceValidator

            # TRACEABILITY: COMPLETE_COMPONENT_SPECIFICATIONS.md lines 415-420
            self._local.resources = WorkerResourceBundle(
                web_search=WebSearchService(session=self._session_pool.get_local()),
                content_extractor=WebContentExtractor(session=self._session_pool.get_local()),
                evidence_validator=EvidenceRelevanceValidator(client=self._ai_client_pool.get_local()),
                rate_limiter=self._api_limiter.get_limiter()
            )
        return self._local.resources

    def cleanup_thread_resources(self):
        """
        Clean up thread-local resources

        TRACEABILITY: CODE_PATTERNS.md resource cleanup pattern requirement
        """
        if hasattr(self._local, 'resources'):
            # HTTP session cleanup per CODE_PATTERNS.md context manager pattern
            if hasattr(self._local.resources, 'web_search'):
                if hasattr(self._local.resources.web_search, 'session'):
                    self._local.resources.web_search.session.close()

            if hasattr(self._local.resources, 'content_extractor'):
                if hasattr(self._local.resources.content_extractor, 'session'):
                    self._local.resources.content_extractor.session.close()

            # Clear local resources
            delattr(self._local, 'resources')
            delattr(self._local, 'initialized')