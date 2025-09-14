"""Worker resource bundle for isolated evidence processing"""

from dataclasses import dataclass
from typing import Optional
import requests


@dataclass
class WorkerResourceBundle:
    """Resource bundle for isolated worker execution"""
    worker_id: str
    http_session: requests.Session
    anthropic_api_key: Optional[str]
    openai_api_key: Optional[str]
    thread_id: int

    def is_ai_available(self, provider: str) -> bool:
        """Check if AI provider is available"""
        if provider.lower() == 'anthropic':
            return bool(self.anthropic_api_key)
        elif provider.lower() == 'openai':
            return bool(self.openai_api_key)
        return False

    def has_any_ai_provider(self) -> bool:
        """Check if any AI provider is available"""
        return bool(self.anthropic_api_key) or bool(self.openai_api_key)