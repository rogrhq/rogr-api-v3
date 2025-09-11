import os
import json
import re
from typing import List, Dict, Optional, TYPE_CHECKING
from evidence_shepherd import EvidenceShepherd, SearchStrategy, EvidenceCandidate, ProcessedEvidence, ClaimType
from web_search_service import WebSearchService
from web_content_extractor import WebContentExtractor

class ROGREvidenceShepherd(EvidenceShepherd):
    """PURE STRATEGY EXECUTOR - Receives complete strategy, executes queries only"""
    
    def __init__(self):
        """Initialize with just execution capabilities"""
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.web_search = WebSearchService()
        self.content_extractor = WebContentExtractor()
    
    def is_enabled(self) -> bool:
        """Check if Claude API is properly configured"""
        return bool(self.api_key)
    
    def search_real_evidence(self, claim_text: str, strategy: SearchStrategy) -> List[EvidenceCandidate]:
        """Pure executor - receives complete strategy, executes queries"""
        
        if not self.is_enabled():
            print("Claude Evidence Shepherd disabled - no Anthropic API key")
            return []
        
        try:
            # Pure execution - no strategy generation
            queries = strategy.search_queries
            print(f"Executing {strategy.strategy_source}: {len(queries)} queries")
            
            # Execute web searches using provided queries
            all_search_results = []
            
            for query in queries:
                print(f"Searching web for: '{query}'")
                search_results = self.web_search.search_web(query, max_results=8)
                all_search_results.extend(search_results)
                print(f"Found {len(search_results)} results for '{query}'")
            
            # PARALLEL content extraction from discovered URLs
            top_results = all_search_results[:10]
            urls_to_extract = [result.url for result in top_results]
            
            print(f"CLAUDE PARALLEL EXTRACTION: Processing {len(urls_to_extract)} URLs simultaneously")
            
            # Extract content from all URLs in parallel
            extraction_results = self.content_extractor.extract_content_batch(urls_to_extract)
            
            # Build evidence candidates from parallel extraction results
            evidence_candidates = []
            
            for i, search_result in enumerate(top_results):
                if i < len(extraction_results):
                    content_data = extraction_results[i]
                    
                    # Get the query that found this result
                    found_query = queries[0] if queries else "unknown"
                    
                    if content_data['success'] and content_data['word_count'] > 50:
                        # Create evidence candidate with real content
                        evidence_candidate = EvidenceCandidate(
                            text=content_data['content'][:800],
                            source_url=content_data['url'],
                            source_domain=content_data['domain'],
                            source_title=content_data['title'],
                            found_via_query=found_query,
                            raw_relevance=0.8
                        )
                        evidence_candidates.append(evidence_candidate)
                    else:
                        # Fallback to search snippet if content extraction failed
                        evidence_candidate = EvidenceCandidate(
                            text=search_result.snippet,
                            source_url=search_result.url,
                            source_domain=search_result.source_domain,
                            source_title=search_result.title,
                            found_via_query=found_query,
                            raw_relevance=0.6
                        )
                        evidence_candidates.append(evidence_candidate)
            
            print(f"Claude web search found {len(evidence_candidates)} evidence candidates from {len(all_search_results)} total results")
            
            # Process evidence using existing filter_evidence_batch method
            processed_evidence = self.filter_evidence_batch(claim_text, evidence_candidates)
            
            return processed_evidence
        
        except Exception as e:
            print(f"Claude web search failed: {e}")
            return []
    
    def filter_evidence_batch(self, claim_text: str, evidence_batch: List[EvidenceCandidate]) -> List[ProcessedEvidence]:
        """Process evidence batch efficiently with Claude scoring - OPTIMIZED for speed"""
        
        if len(evidence_batch) == 0:
            return []
        
        # Score each piece of evidence for relevance
        processed_evidence = []
        for evidence in evidence_batch:
            try:
                scored_evidence = self.score_evidence_relevance_claude(claim_text, evidence)
                if scored_evidence.ai_relevance_score >= 70:  # Quality threshold
                    processed_evidence.append(scored_evidence)
            except Exception as e:
                print(f"Evidence scoring failed: {e}")
                continue
        
        # Sort by relevance score and return top pieces
        processed_evidence.sort(key=lambda x: x.ai_relevance_score, reverse=True)
        return processed_evidence[:5]  # Return top 5 most relevant
    
    def score_evidence_relevance_claude(self, claim_text: str, evidence: EvidenceCandidate) -> ProcessedEvidence:
        """Score evidence using Claude for relevance and stance"""
        
        scoring_prompt = f"""PROFESSIONAL FACT-CHECKING: Rate this evidence for the claim: "{claim_text}"

EVIDENCE: {evidence.text[:400]}
SOURCE: {evidence.source_domain} - {evidence.source_title}

Rate 0-100 for RELEVANCE to the specific claim (not general topic):
- 90-100: Directly addresses and verifies/refutes the exact claim
- 70-89: Strong relevance with supporting/contradicting information  
- 50-69: Moderate relevance, tangentially related
- 30-49: Weak relevance, background information only
- 0-29: Irrelevant or off-topic

STANCE (supporting/contradicting/neutral):
- supporting: Evidence supports the claim's truth
- contradicting: Evidence challenges/refutes the claim  
- neutral: Evidence is factual but doesn't clearly support or contradict

Return ONLY JSON:
{{
  "relevance_score": 85,
  "stance": "supporting",
  "reasoning": "Brief explanation"
}}"""

        messages = [
            {"role": "user", "content": f"Score this evidence"}
        ]
        
        try:
            response = self._call_claude(messages, max_tokens=200, system_message=scoring_prompt)
            if not response:
                return self._create_fallback_evidence(claim_text, evidence)
            
            score_data = json.loads(response)
            
            return ProcessedEvidence(
                text=evidence.text,
                source_url=evidence.source_url,
                source_domain=evidence.source_domain,
                source_title=evidence.source_title,
                ai_relevance_score=score_data.get('relevance_score', 50),
                ai_stance=score_data.get('stance', 'neutral'),
                ai_confidence=0.8,
                ai_reasoning=score_data.get('reasoning', 'No reasoning provided')
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"❌ ROGR evidence scoring failed: {e}")
            return self._create_fallback_evidence(claim_text, evidence)
    
    def _create_fallback_evidence(self, claim_text: str, evidence: EvidenceCandidate) -> ProcessedEvidence:
        """Create fallback processed evidence when AI scoring fails"""
        return ProcessedEvidence(
            text=evidence.text,
            source_url=evidence.source_url,
            source_domain=evidence.source_domain,
            source_title=evidence.source_title,
            ai_relevance_score=60,  # Neutral fallback score
            ai_stance='neutral',
            ai_confidence=0.3,
            ai_reasoning='Fallback scoring due to AI unavailability'
        )
    
    def _call_claude(self, messages: list, max_tokens: int = 1000, system_message: str = "") -> Optional[str]:
        """Call Claude API with proper error handling"""
        if not self.is_enabled():
            return None
        
        import anthropic
        
        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                messages=messages,
                system=system_message
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Claude API call failed: {e}")
            return None

    def analyze_claim(self, claim_text: str) -> SearchStrategy:
        """ARCHITECTURE EVOLUTION: Strategy generation moved to orchestrator level.
        Individual Evidence Shepherds are now pure strategy executors.
        This method should not be called - use orchestrator._get_complete_strategy()"""
        raise NotImplementedError(
            "Individual Evidence Shepherd is now a pure strategy executor. "
            "Strategy generation has been moved to ROGRDualEvidenceShepherd._get_complete_strategy(). "
            "Use search_real_evidence(claim_text, strategy) with external strategy instead."
        )

    def score_evidence_relevance(self, claim_text: str, evidence: EvidenceCandidate) -> ProcessedEvidence:
        """ARCHITECTURE EVOLUTION: Method signature updated for pure executor pattern"""
        return self.score_evidence_relevance_claude(claim_text, evidence)

    # REMOVED METHODS - No longer part of pure executor:
    # - analyze_claim() - Strategy generation moved to orchestrator
    # - _classify_claim_domains() - Multi-domain analysis moved to orchestrator
    # - _create_multi_domain_search_strategy() - Strategy creation moved to orchestrator
    # - _create_minimal_strategy() - Fallback strategies moved to orchestrator
    # - _fallback_strategy() - All fallbacks moved to orchestrator
    # - is_non_claim() - Claim analysis moved to orchestrator