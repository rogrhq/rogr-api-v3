import re
import requests
from typing import List, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup

class ClaimExtractionService:
    def __init__(self):
        pass
    
    def extract_claims(self, text: str) -> List[str]:
        """Extract 1-3 short, checkable claims from text"""
        if not text or len(text.strip()) < 10:
            return []
        
        # Clean the text
        text = self._clean_text(text)
        
        # Extract potential claims using various strategies
        claims = []
        
        # Strategy 1: Look for factual statements with numbers/dates
        number_claims = self._extract_number_claims(text)
        claims.extend(number_claims[:2])  # Max 2 from numbers
        
        # Strategy 2: Look for definitive statements
        definitive_claims = self._extract_definitive_claims(text)
        claims.extend(definitive_claims[:2])  # Max 2 from definitive
        
        # Strategy 3: Extract key sentences
        if len(claims) < 3:
            key_claims = self._extract_key_sentences(text)
            claims.extend(key_claims[:3-len(claims)])
        
        # Clean up and deduplicate
        final_claims = self._clean_and_deduplicate(claims)
        
        # Return max 3 claims
        return final_claims[:3]
    
    def extract_url_metadata_and_text(self, url: str) -> dict:
        """Extract metadata and content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; ROGR-Bot/1.0; Fact-checking service)'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract metadata
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            return {
                'title': title,
                'description': description,
                'content': content,
                'domain': urlparse(url).netloc,
                'url': url
            }
            
        except Exception as e:
            print(f"URL extraction error: {e}")
            return {
                'title': '',
                'description': '',
                'content': '',
                'domain': urlparse(url).netloc if url else '',
                'url': url
            }
    
    def merge_text_sources(self, url_data: dict, ocr_text: str = "") -> str:
        """Merge URL metadata, content, and OCR text for claim extraction"""
        text_parts = []
        
        # Add title and description
        if url_data.get('title'):
            text_parts.append(f"Title: {url_data['title']}")
        if url_data.get('description'):
            text_parts.append(f"Description: {url_data['description']}")
        
        # Add main content
        if url_data.get('content'):
            text_parts.append(url_data['content'])
        
        # Add OCR text
        if ocr_text:
            text_parts.append(f"Image text: {ocr_text}")
        
        return " ".join(text_parts)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()
    
    def _extract_number_claims(self, text: str) -> List[str]:
        """Extract claims containing numbers, percentages, or dates"""
        claims = []
        
        # Find sentences with numbers/percentages/dates
        patterns = [
            r'[^.!?]*\d+(?:\.\d+)?%[^.!?]*[.!?]',  # Percentages
            r'[^.!?]*\$\d+(?:,\d{3})*(?:\.\d{2})?[^.!?]*[.!?]',  # Money
            r'[^.!?]*\b\d{4}\b[^.!?]*[.!?]',  # Years
            r'[^.!?]*\b\d+(?:,\d{3})*(?:\.\d+)?\s+(?:million|billion|thousand)[^.!?]*[.!?]',  # Large numbers
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_claim = self._clean_sentence(match)
                if clean_claim and len(clean_claim) < 200:
                    claims.append(clean_claim)
        
        return claims[:3]
    
    def _extract_definitive_claims(self, text: str) -> List[str]:
        """Extract definitive factual statements"""
        claims = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        # Look for definitive patterns
        definitive_patterns = [
            r'\bis\b',
            r'\bwas\b',
            r'\bwill\b',
            r'\bhave\b',
            r'\bhas\b',
            r'\bwere\b',
            r'\baccording to\b',
            r'\bstudies? (?:show|found|indicate)',
            r'\breports? that\b',
            r'\bannounced\b'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 200:
                continue
                
            for pattern in definitive_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    clean_claim = self._clean_sentence(sentence)
                    if clean_claim:
                        claims.append(clean_claim)
                    break
        
        return claims[:3]
    
    def _extract_key_sentences(self, text: str) -> List[str]:
        """Extract key sentences as fallback claims"""
        sentences = re.split(r'[.!?]+', text)
        
        claims = []
        for sentence in sentences:
            sentence = sentence.strip()
            if 30 <= len(sentence) <= 150:  # Good length for claims
                clean_claim = self._clean_sentence(sentence)
                if clean_claim:
                    claims.append(clean_claim)
        
        return claims[:3]
    
    def _clean_sentence(self, sentence: str) -> str:
        """Clean and validate a sentence for use as a claim"""
        # Remove leading/trailing punctuation
        sentence = re.sub(r'^[^\w]+|[^\w]+$', '', sentence.strip())
        
        # Skip if too short or contains problematic patterns
        if len(sentence) < 15:
            return ""
        if re.search(r'^(?:click|subscribe|follow|watch|read more)', sentence, re.IGNORECASE):
            return ""
        
        # Ensure proper capitalization
        if sentence:
            sentence = sentence[0].upper() + sentence[1:]
        
        return sentence
    
    def _clean_and_deduplicate(self, claims: List[str]) -> List[str]:
        """Remove duplicates and very similar claims"""
        if not claims:
            return []
        
        unique_claims = []
        
        for claim in claims:
            if not claim:
                continue
                
            # Check for similarity with existing claims
            is_duplicate = False
            for existing in unique_claims:
                if self._claims_similar(claim, existing):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_claims.append(claim)
        
        return unique_claims
    
    def _claims_similar(self, claim1: str, claim2: str) -> bool:
        """Check if two claims are too similar"""
        # Simple similarity check based on shared words
        words1 = set(claim1.lower().split())
        words2 = set(claim2.lower().split())
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        intersection = words1.intersection(words2)
        similarity = len(intersection) / max(len(words1), len(words2))
        
        return similarity > 0.6  # 60% word overlap threshold
    
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
                # Extract text from paragraphs
                paragraphs = content_elem.find_all('p')
                if paragraphs:
                    text_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                    return " ".join(text_parts[:5])  # First 5 paragraphs
        
        # Fallback: extract from all paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs:
            text_parts = [p.get_text().strip() for p in paragraphs[:5] if p.get_text().strip()]
            return " ".join(text_parts)
        
        return ""