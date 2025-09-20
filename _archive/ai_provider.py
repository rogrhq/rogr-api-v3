from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class AIResponse:
    """Standardized response from any AI provider"""
    content: str
    success: bool
    error: Optional[str] = None
    provider: str = ""
    
class AIProvider(ABC):
    """Abstract interface for AI providers (Claude, OpenAI, Gemini, etc.)"""
    
    @abstractmethod
    def call_api(self, prompt: str, max_tokens: int = 1000) -> AIResponse:
        """Make API call to the AI provider"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return provider name (claude, openai, gemini, etc.)"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available"""
        pass