import json
from typing import List, Dict, Optional
from evidence_shepherd_v2 import EvidenceShepherdV2
from claude_provider_v2 import ClaudeProviderV2
from openai_provider_v2 import OpenAIProviderV2
from .evidence_shepherd import ProcessedEvidence, EvidenceCandidate
from web_search_service import WebSearchService
from web_content_extractor import WebContentExtractor

class MultiAIEvidenceShepherdV2:
    """V2 Multi-AI Evidence Shepherd with centralized logic"""
    
    def __init__(self):
        # Initialize AI providers
        ai_providers = []
        
        claude_provider = ClaudeProviderV2()
        if claude_provider.is_available():
            ai_providers.append(claude_provider)
            
        openai_provider = OpenAIProviderV2()
        if openai_provider.is_available():
            ai_providers.append(openai_provider)
        
        # Create centralized evidence shepherd
        self.core_shepherd = EvidenceShepherdV2(ai_providers)
        
        # Web services
        self.web_search = WebSearchService()
        self.content_extractor = WebContentExtractor()
        
        print(f"Multi-AI Evidence Shepherd v2 initialized with {len(ai_providers)} providers")
    
    def is_non_claim(self, claim_text: str) -> bool:
        """Fast detection of non-claims (delegate to core shepherd if needed)"""
        claim_lower = claim_text.lower().strip()
        
        # Skip extremely short inputs
        if len(claim_text.strip()) < 8:
            return True
        
        # Skip URLs - they should be processed
        if claim_lower.startswith(('http://', 'https://', 'www.')):
            return False
        
        # Basic non-claim patterns
        if any(pattern in claim_lower for pattern in ['what', 'how', 'why', 'when', 'where', 'who']):
            return True
            
        return False
    
    def find_evidence(self, claim_text: str, max_evidence: int = 8) -> List[ProcessedEvidence]:
        """Find and process evidence using centralized v2 logic"""
        
        if self.is_non_claim(claim_text):
            print(f"Skipping non-claim: {claim_text[:50]}...")
            return []
        
        print(f"V2 Evidence Shepherd processing: {claim_text[:50]}...")
        
        # Web search for evidence candidates
        if not self.web_search.is_enabled():
            print("Web search not enabled")
            return []
        
        search_results = self.web_search.search(claim_text, max_results=15)
        if not search_results:
            print("No search results found")
            return []
        
        print(f"Found {len(search_results)} search results")
        
        # Extract content and create evidence candidates
        evidence_candidates = []
        for result in search_results:
            content = self.content_extractor.extract_content(result['url'])
            if content and len(content.strip()) > 100:  # Minimum content threshold
                candidate = EvidenceCandidate(
                    text=content,
                    source_url=result['url'],
                    source_domain=result['domain'],
                    source_title=result['title'],
                    found_via_query=claim_text,
                    raw_relevance=75.0  # Default relevance
                )
                evidence_candidates.append(candidate)
        
        if not evidence_candidates:
            print("No valid evidence candidates extracted")
            return []
        
        print(f"Processing {len(evidence_candidates)} evidence candidates with v2 system")
        
        # Use centralized v2 processing
        processed_evidence = self.core_shepherd.filter_evidence_batch(claim_text, evidence_candidates)
        
        print(f"V2 processing complete: {len(processed_evidence)} evidence pieces")
        
        return processed_evidence[:max_evidence]
    
    def get_debug_info(self) -> Dict:
        """Get debug information about v2 system"""
        return {
            "version": "v2",
            "ai_providers": [p.get_name() for p in self.core_shepherd.ai_providers],
            "web_search_enabled": self.web_search.is_enabled(),
            "centralized_logic": True
        }