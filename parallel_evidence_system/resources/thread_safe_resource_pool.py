"""Thread-safe resource pool for parallel evidence processing"""

import threading
import os
from typing import Dict, Any, Optional
from contextlib import contextmanager
import requests
import uuid


class ThreadSafeResourcePool:
    """Thread-safe resource pool with isolated HTTP sessions and AI clients"""

    def __init__(self):
        self._local = threading.local()
        self._lock = threading.Lock()
        self._pool_id = f"pool_{uuid.uuid4().hex[:8]}"

    def _initialize_thread_resources(self):
        """Initialize thread-local resources"""
        self._local.http_session = requests.Session()
        self._local.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self._local.openai_api_key = os.getenv('OPENAI_API_KEY')
        self._local.thread_id = threading.current_thread().ident
        self._local.initialized = True

    def get_thread_resources(self) -> Dict[str, Any]:
        """Get or create thread-local resource bundle"""
        if not hasattr(self._local, 'initialized'):
            with self._lock:
                if not hasattr(self._local, 'initialized'):
                    self._initialize_thread_resources()

        return {
            'http_session': self._local.http_session,
            'anthropic_api_key': self._local.anthropic_api_key,
            'openai_api_key': self._local.openai_api_key,
            'thread_id': self._local.thread_id
        }

    @contextmanager
    def managed_session(self):
        """Context manager for HTTP session with guaranteed cleanup"""
        resources = self.get_thread_resources()
        session = resources['http_session']
        try:
            yield session
        finally:
            # Session cleanup handled by thread cleanup
            pass

    def cleanup_thread_resources(self):
        """Clean up thread-local resources"""
        if hasattr(self._local, 'http_session'):
            self._local.http_session.close()
        if hasattr(self._local, 'initialized'):
            self._local.initialized = False

    @property
    def pool_id(self) -> str:
        """Get unique pool identifier"""
        return self._pool_id