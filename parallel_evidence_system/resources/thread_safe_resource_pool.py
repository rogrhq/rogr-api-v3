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

        # CRITICAL FIX: Single shared session to prevent anti-bot detection
        # Multiple sessions from same IP = bot fingerprint, single session = human-like
        self._shared_session = requests.Session()
        self._shared_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })

    def _initialize_thread_resources(self):
        """Initialize thread-local resources"""
        # No longer create thread-local session - use shared session
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
            'http_session': self._shared_session,  # Use shared session instead of thread-local
            'anthropic_api_key': self._local.anthropic_api_key,
            'openai_api_key': self._local.openai_api_key,
            'thread_id': self._local.thread_id
        }

    @contextmanager
    def managed_session(self):
        """Context manager for HTTP session with guaranteed cleanup"""
        # Use shared session for all requests
        try:
            yield self._shared_session
        finally:
            # Session cleanup not needed - shared session persists
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