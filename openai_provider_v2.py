import os
import requests
from ai_provider import AIProvider, AIResponse

class OpenAIProviderV2(AIProvider):
    """Minimal OpenAI API wrapper for Evidence Shepherd v2"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4o"
        
    def call_api(self, prompt: str, max_tokens: int = 1000) -> AIResponse:
        """Make API call to OpenAI"""
        if not self.api_key:
            return AIResponse(
                content="",
                success=False,
                error="OPENAI_API_KEY not configured",
                provider="openai"
            )
            
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # OpenAI API format
            payload = {
                'model': self.model,
                'messages': [{"role": "user", "content": prompt}],
                'temperature': 0.3,
                'max_tokens': max_tokens
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=8)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            return AIResponse(
                content=content,
                success=True,
                provider="openai"
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                success=False,
                error=str(e),
                provider="openai"
            )
    
    def get_name(self) -> str:
        return "openai"
    
    def is_available(self) -> bool:
        return self.api_key is not None