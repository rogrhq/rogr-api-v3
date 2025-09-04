import os
import requests
from ai_provider import AIProvider, AIResponse

class ClaudeProviderV2(AIProvider):
    """Minimal Claude API wrapper for Evidence Shepherd v2"""
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-haiku-20240307"
        
    def call_api(self, prompt: str, max_tokens: int = 1000) -> AIResponse:
        """Make API call to Claude"""
        if not self.api_key:
            return AIResponse(
                content="",
                success=False,
                error="ANTHROPIC_API_KEY not configured",
                provider="claude"
            )
            
        try:
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            # Claude API format
            payload = {
                'model': self.model,
                'max_tokens': max_tokens,
                'messages': [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            content = result['content'][0]['text'].strip()
            
            return AIResponse(
                content=content,
                success=True,
                provider="claude"
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                success=False,
                error=str(e),
                provider="claude"
            )
    
    def get_name(self) -> str:
        return "claude"
    
    def is_available(self) -> bool:
        return self.api_key is not None