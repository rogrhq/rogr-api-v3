import os
import json
import re
import requests
from typing import List, Dict, Optional, Union
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dataclasses import dataclass

@dataclass
class MinedClaim:
    """A claim identified by the ClaimMiner with metadata"""
    text: str
    relevance_score: int  # 0-100, how relevant to context
    specificity_score: int  # 0-100, how specific/concrete
    consequence_score: int  # 0-100, how important if true/false
    factual_assertion: bool  # Is this a factual claim vs opinion
    claim_type: str  # "statistical", "policy", "scientific", "historical", "factual"
    context_reasoning: str  # Why this relevance score

@dataclass 
class ClaimMiningResult:
    """Complete result from claim mining process"""
    primary_claims: List[MinedClaim]  # Auto-processed by ES (high relevance)
    secondary_claims: List[MinedClaim]  # User-selectable (medium relevance)
    tertiary_claims: List[MinedClaim]  # Available but lower priority (low relevance)
    analysis_meta: Dict  # Context analysis, total claims found, etc.

class ClaimMiner:
    """AI-powered claim mining with context awareness and relevance ranking"""
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-haiku-20240307"
        
        # For URL content extraction
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        
        print(f"ClaimMiner initialized - Claude API: {bool(self.api_key)}")
    
    def _call_claude(self, messages: List[Dict], max_tokens: int = 2000) -> Optional[str]:
        """Make API call to Claude"""
        if not self.api_key:
            return None
            
        try:
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            # Convert messages to Claude format
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    user_messages.append(msg)
            
            payload = {
                'model': self.model,
                'max_tokens': max_tokens,
                'messages': user_messages,
                'system': system_message
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            return result['content'][0]['text'].strip()
            
        except Exception as e:
            print(f"Claude API error: {e}")
            return None
    
    def mine_claims(self, content: str, context_type: str = "text", source_context: Dict = None) -> ClaimMiningResult:
        """
        Mine all factual claims from content with context awareness
        
        Args:
            content: The text content to analyze
            context_type: "text", "article_url", "social_post", "image_ocr"
            source_context: Additional context like article title, domain, user intent
        """
        
        if not content or len(content.strip()) < 10:
            return ClaimMiningResult([], [], [], {"error": "Content too short"})
        
        # Extract context information
        context_info = self._build_context_info(content, context_type, source_context)
        
        # Generate context-aware prompt for Claude
        system_prompt = self._create_mining_prompt(context_type, context_info)
        
        # Call Claude to mine claims
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"CONTENT TO ANALYZE:\n\n{content[:3000]}"}  # Limit for speed
        ]
        
        response = self._call_claude(messages, max_tokens=2000)
        if not response:
            # Fallback to simple extraction if Claude fails
            return self._fallback_claim_mining(content)
        
        try:
            # Parse Claude's JSON response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                result_data = json.loads(json_text)
                
                return self._process_claude_results(result_data, context_info)
            else:
                print(f"ClaimMiner: No valid JSON in Claude response")
                return self._fallback_claim_mining(content)
                
        except (json.JSONDecodeError, KeyError) as e:
            print(f"ClaimMiner: Error parsing Claude response: {e}")
            return self._fallback_claim_mining(content)
    
    def _build_context_info(self, content: str, context_type: str, source_context: Dict) -> Dict:
        """Build context information for intelligent claim mining"""
        
        context_info = {
            "type": context_type,
            "content_length": len(content),
            "word_count": len(content.split())
        }
        
        if source_context:
            context_info.update(source_context)
        
        # Extract additional context based on type
        if context_type == "article_url" and source_context:
            context_info["focus"] = f"Article: '{source_context.get('title', 'Unknown')}' from {source_context.get('domain', 'unknown domain')}"
        elif context_type == "text":
            context_info["focus"] = "User-submitted text for fact-checking"
        elif context_type == "social_post":
            context_info["focus"] = "Social media content"
        
        return context_info
    
    def _create_mining_prompt(self, context_type: str, context_info: Dict) -> str:
        """Create context-aware prompt for Claude claim mining"""
        
        base_prompt = """You are ROGR's ClaimMiner. Your job is to find ALL verifiable factual claims in content and rank them by contextual relevance.

CONTEXT: {focus}

MISSION: Extract every factual assertion that could be fact-checked, ranked by relevance to the content's main purpose.

CLAIM CRITERIA (for ALL claims):
1. FACTUAL ASSERTION: Makes a specific factual statement (not opinion/preference)
2. SPECIFIC: Concrete enough that evidence could prove/disprove it  
3. CONSEQUENTIAL: Would matter to readers if true or false
4. CLEAR: Unambiguous meaning

RELEVANCE SCORING (0-100):
- 90-100: Central to main content purpose/narrative
- 70-89:  Important supporting details or key context
- 50-69:  Mentioned facts that are less central
- 30-49:  Background context or tangential facts
- 0-29:   Off-topic or minor details

CLAIM TYPES:
- statistical: Numbers, percentages, quantities, rates
- policy: Government actions, laws, regulations, official positions  
- scientific: Research findings, medical claims, technical facts
- historical: Past events, dates, sequences of events
- factual: General verifiable statements

RETURN ALL CLAIMS - don't filter based on difficulty to verify. Let the Evidence Shepherd handle that.

FORMAT (JSON only):
{{
  "primary_claims": [
    {{
      "text": "Exact claim text",
      "relevance_score": 95,
      "specificity_score": 90, 
      "consequence_score": 85,
      "factual_assertion": true,
      "claim_type": "statistical",
      "context_reasoning": "Central statistic in main argument"
    }}
  ],
  "secondary_claims": [similar format for 50-79 relevance],
  "tertiary_claims": [similar format for 30-49 relevance],
  "analysis_meta": {{
    "total_claims_found": 8,
    "context_analysis": "Brief explanation of content focus and claim relevance reasoning",
    "confidence": 0.85
  }}
}}""".format(focus=context_info.get("focus", "General content"))

        return base_prompt
    
    def _process_claude_results(self, result_data: Dict, context_info: Dict) -> ClaimMiningResult:
        """Process Claude's JSON results into ClaimMiningResult structure"""
        
        try:
            primary_claims = [
                MinedClaim(**claim_data) 
                for claim_data in result_data.get("primary_claims", [])
            ]
            
            secondary_claims = [
                MinedClaim(**claim_data) 
                for claim_data in result_data.get("secondary_claims", [])
            ]
            
            tertiary_claims = [
                MinedClaim(**claim_data) 
                for claim_data in result_data.get("tertiary_claims", [])
            ]
            
            analysis_meta = result_data.get("analysis_meta", {})
            analysis_meta["context_info"] = context_info
            
            return ClaimMiningResult(
                primary_claims=primary_claims,
                secondary_claims=secondary_claims, 
                tertiary_claims=tertiary_claims,
                analysis_meta=analysis_meta
            )
            
        except Exception as e:
            print(f"Error processing Claude results: {e}")
            return self._fallback_claim_mining(result_data.get("raw_content", ""))
    
    def _fallback_claim_mining(self, content: str) -> ClaimMiningResult:
        """Simple fallback claim extraction when Claude fails"""
        
        # Basic sentence extraction
        sentences = re.split(r'[.!?]+', content)
        fallback_claims = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if 20 <= len(sentence) <= 200:
                # Simple checks for factual statements
                if any(pattern in sentence.lower() for pattern in ['is', 'was', 'are', 'were', 'has', 'have', 'contain', 'cause', '%']):
                    claim = MinedClaim(
                        text=sentence,
                        relevance_score=60,  # Default medium relevance
                        specificity_score=50,
                        consequence_score=50,
                        factual_assertion=True,
                        claim_type="factual",
                        context_reasoning="Fallback extraction"
                    )
                    fallback_claims.append(claim)
        
        # Split into tiers
        primary = fallback_claims[:3]
        secondary = fallback_claims[3:6] 
        tertiary = fallback_claims[6:]
        
        return ClaimMiningResult(
            primary_claims=primary,
            secondary_claims=secondary,
            tertiary_claims=tertiary,
            analysis_meta={"fallback_mode": True, "total_claims_found": len(fallback_claims)}
        )
    
    def extract_url_metadata_and_text(self, url: str) -> Dict:
        """Extract metadata and content from URL (maintaining compatibility with existing code)"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            # Extract metadata
            description = self._extract_description(soup)
            
            return {
                'title': title,
                'content': content,
                'description': description,
                'domain': urlparse(url).netloc,
                'url': url
            }
            
        except Exception as e:
            print(f"URL extraction error: {e}")
            return {
                'title': '',
                'content': '',
                'description': '',
                'domain': urlparse(url).netloc if url else '',
                'url': url
            }
    
    def merge_text_sources(self, url_data: Dict, ocr_text: str = "") -> str:
        """Merge URL metadata, content, and OCR text (compatibility method)"""
        text_parts = []
        
        if url_data.get('title'):
            text_parts.append(f"Title: {url_data['title']}")
        if url_data.get('description'):
            text_parts.append(f"Description: {url_data['description']}")
        if url_data.get('content'):
            text_parts.append(url_data['content'])
        if ocr_text:
            text_parts.append(f"Image text: {ocr_text}")
        
        return " ".join(text_parts)
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        desc_tag = soup.find('meta', attrs={'name': 'description'}) or \
                   soup.find('meta', attrs={'property': 'og:description'})
        if desc_tag:
            return desc_tag.get('content', '').strip()
        return ""
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        # Try common article selectors
        content_selectors = [
            'article',
            '.article-content',
            '.post-content', 
            '.entry-content',
            'main',
            '.content'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                paragraphs = content_elem.find_all('p')
                if paragraphs:
                    text_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                    return " ".join(text_parts[:10])  # First 10 paragraphs
        
        # Fallback: extract from all paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs:
            text_parts = [p.get_text().strip() for p in paragraphs[:10] if p.get_text().strip()]
            return " ".join(text_parts)
        
        return ""
    
    def is_enabled(self) -> bool:
        """Check if Claude API is available"""
        return bool(self.api_key)

    # Legacy compatibility methods
    def extract_claims(self, text: str) -> List[str]:
        """Legacy compatibility method - returns just claim texts"""
        result = self.mine_claims(text, context_type="text")
        
        # Return all claims as simple text list for backward compatibility
        all_claims = result.primary_claims + result.secondary_claims + result.tertiary_claims
        return [claim.text for claim in all_claims[:5]]  # Limit to 5 for compatibility