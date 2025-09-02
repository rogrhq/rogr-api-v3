import os
import json
import re
from typing import List, Dict, Optional
import requests
from evidence_shepherd import EvidenceShepherd, SearchStrategy, EvidenceCandidate, ProcessedEvidence, ClaimType
from web_search_service import WebSearchService
from web_content_extractor import WebContentExtractor

class OpenAIEvidenceShepherd(EvidenceShepherd):
    """OpenAI-powered evidence shepherd for smart fact-checking"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"
        
        # Initialize web search and content extraction services
        self.web_search = WebSearchService()
        self.content_extractor = WebContentExtractor()
        
        print(f"AI Evidence Shepherd initialized with real web search: {self.web_search.is_enabled()}")
        
    def _call_openai(self, messages: List[Dict], temperature: float = 0.3) -> Optional[str]:
        """Make API call to OpenAI"""
        if not self.api_key:
            return None
            
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': 800  # Increased to ensure all evidence scores returned
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=6)  # Reduced from 8 to 6
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None
    
    def is_non_claim(self, claim_text: str) -> bool:
        """SPEED OPTIMIZATION: Fast detection of non-claims to skip processing"""
        
        claim_lower = claim_text.lower().strip()
        
        # NEVER skip URLs - they should always be processed
        if claim_lower.startswith(('http://', 'https://', 'www.')):
            return False
        
        # Skip extremely short inputs
        if len(claim_text.strip()) < 8:
            return True
        
        # Skip obvious non-factual content
        non_claim_patterns = [
            # General topics without specific claims
            r'^(renewable energy|climate change|artificial intelligence|healthcare|education)$',
            r'^(technology|science|politics|economics|business)$',
            
            # Questions
            r'^\s*(what|how|why|when|where|who|which|can|could|would|should|is|are|do|does)',
            
            # Commands/instructions
            r'^\s*(tell me|show me|explain|describe|find|search|look|check)',
            
            # Single words or very generic phrases
            r'^\w+$',  # Single word
            r'^(the|a|an)\s+\w+$',  # Article + single word
            
            # Vague statements
            r'^(this is|that is|it is|there are|there is)\s+(good|bad|important|interesting|useful)',
        ]
        
        for pattern in non_claim_patterns:
            if re.match(pattern, claim_lower):
                return True
        
        # Check for specific claim indicators that SHOULD be processed
        factual_indicators = [
            r'\d+%',  # Percentages
            r'\d+\s*(million|billion|thousand)',  # Large numbers
            r'(study|research|survey|poll)\s+(shows?|found|indicates?)',
            r'(according to|reported by|announced|confirmed)',
            r'\d{4}',  # Years
            r'(increased?|decreased?|rose|fell|grew)\s+by',
            r'(says?|claims?|stated?|announced?)\s+(that)?',
        ]
        
        for indicator in factual_indicators:
            if re.search(indicator, claim_lower):
                return False  # Definitely a factual claim
        
        # If no clear indicators, check word count and complexity
        words = claim_text.split()
        if len(words) < 4:  # Very short statements likely non-claims
            return True
        
        return False  # Default to processing if unsure
    
    def analyze_claim(self, claim_text: str) -> SearchStrategy:
        """Use AI to analyze claim and create optimal search strategy"""
        
        # SPEED OPTIMIZATION: Skip non-claims immediately
        if self.is_non_claim(claim_text):
            print(f"SKIPPED non-claim: '{claim_text[:50]}...'")
            return self._create_minimal_strategy(claim_text)
        
        # SPEED OPTIMIZATION: Use specialized prompts based on complexity
        if len(claim_text) < 50:  # Short claims get fast prompt
            system_prompt = """Expert fact-checker: Quickly analyze this claim and return search strategy.

Claim types: STATISTICAL (numbers/%), POLICY (government), SCIENTIFIC (studies), HISTORICAL (dates), FACTUAL (general facts)

Return JSON:
{"claim_type": "FACTUAL", "search_queries": ["query1", "query2"], "target_domains": [], "time_relevance_months": 12}"""
        else:  # Longer claims get detailed prompt
            system_prompt = """You are an expert fact-checker analyzing claims for optimal verification strategy.

CLAIM TYPES & SEARCH OPTIMIZATION:
- STATISTICAL: Numbers, percentages → Search official sources, surveys, government data
- POLICY: Government actions → Search official announcements, news reports, gov sites  
- SCIENTIFIC: Research findings → Search journals, studies, institutional sources
- HISTORICAL: Past events → Search news archives, official records, multiple sources
- FACTUAL: General verifiable facts → Search authoritative sources, primary documentation

SPEED REQUIREMENTS: Focus on 2-3 highest-impact search queries that will find the most authoritative evidence quickly.

Return ONLY JSON:
{
  "claim_type": "STATISTICAL",
  "search_queries": ["specific high-impact query 1", "specific high-impact query 2"],
  "target_domains": ["authoritative-domain.gov", "major-source.org"],
  "time_relevance_months": 12,
  "reasoning": "Brief strategy explanation"
}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this claim: {claim_text}"}
        ]
        
        response = self._call_openai(messages)
        if not response:
            # Fallback to basic strategy
            return self._fallback_strategy(claim_text)
        
        try:
            strategy_data = json.loads(response)
            
            claim_type = ClaimType(strategy_data.get('claim_type', 'factual').lower())
            
            # Set authority weights based on claim type
            authority_weights = {
                ClaimType.STATISTICAL: 0.9,  # Need authoritative polling/survey data
                ClaimType.POLICY: 0.95,      # Government sources critical
                ClaimType.SCIENTIFIC: 1.0,   # Peer review essential
                ClaimType.HISTORICAL: 0.8,   # Multiple sources needed
                ClaimType.OPINION: 0.6,      # Expert opinions vary
                ClaimType.FACTUAL: 0.7       # Good sourcing important
            }
            
            confidence_thresholds = {
                ClaimType.STATISTICAL: 0.8,
                ClaimType.POLICY: 0.9,
                ClaimType.SCIENTIFIC: 0.85,
                ClaimType.HISTORICAL: 0.7,
                ClaimType.OPINION: 0.6,
                ClaimType.FACTUAL: 0.75
            }
            
            return SearchStrategy(
                claim_type=claim_type,
                search_queries=strategy_data.get('search_queries', [claim_text]),
                target_domains=strategy_data.get('target_domains', []),
                time_relevance_months=strategy_data.get('time_relevance_months', 24),
                authority_weight=authority_weights.get(claim_type, 0.7),
                confidence_threshold=confidence_thresholds.get(claim_type, 0.7)
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing AI strategy response: {e}")
            return self._fallback_strategy(claim_text)
    
    def score_evidence_relevance(self, claim_text: str, evidence: EvidenceCandidate) -> ProcessedEvidence:
        """Use AI to score evidence relevance with detailed analysis"""
        
        system_prompt = f"""You are an expert fact-checker evaluating evidence for the claim: "{claim_text}"

Your task: Determine how well evidence supports, contradicts, or relates to this specific claim.

RELEVANCE SCORING (0-100):
90-100: DIRECT - Evidence directly proves/disproves the claim with specific data
80-89:  STRONG - Evidence strongly supports/contradicts with related data  
70-79:  GOOD - Evidence provides relevant context or related information
60-69:  WEAK - Evidence mentions topic but doesn't directly address claim
50-59:  TANGENTIAL - Evidence related to topic but not claim specifics
0-49:   IRRELEVANT - Evidence unrelated or extremely weak connection

STANCE CLASSIFICATION - Analyze what the evidence is DOING with the claim:

"contradicting" - The evidence:
  • States the claim is FALSE, incorrect, debunked, or disproven
  • Provides data/facts that directly oppose the claim
  • Uses language like "no evidence," "studies show otherwise," "myth," "false," "no link," "no association"
  • Example: "Studies show no link between X and Y" when claim is "X causes Y"

"supporting" - The evidence:
  • States the claim is TRUE, correct, or validated
  • Provides data/facts that directly confirm the claim  
  • Uses language like "evidence shows," "proven," "confirmed," "causes," "leads to"
  • Example: "Research confirms X causes Y" when claim is "X causes Y"

"neutral" - The evidence:
  • Merely mentions or describes the claim without judgment
  • Discusses the claim as a phenomenon/belief without endorsing or refuting
  • Reports what others believe without taking a position
  • Example: "Some people believe X causes Y" or "The theory that X causes Y"

CRITICAL: Focus on what the evidence ASSERTS about truth, not just keyword presence.
- Describing a theory WITHOUT endorsing it = neutral
- Explaining why something is false = contradicting  
- Providing evidence something is true = supporting

CONFIDENCE (0-1):
How certain are you about your assessment?

Return ONLY valid JSON:
{
  "relevance_score": 85,
  "stance": "supporting",
  "confidence": 0.9,
  "reasoning": "Explain why this score/stance in 1-2 sentences",
  "key_excerpt": "The most important 10-20 words from evidence"
}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"CLAIM: {claim_text}\n\nEVIDENCE: {evidence.text[:800]}\n\nSOURCE: {evidence.source_title} ({evidence.source_domain})"}
        ]
        
        response = self._call_openai(messages, temperature=0.1)
        if not response:
            # Fallback to keyword matching
            return self._fallback_evidence_score(claim_text, evidence)
        
        try:
            score_data = json.loads(response)
            
            return ProcessedEvidence(
                text=evidence.text,
                source_url=evidence.source_url,
                source_domain=evidence.source_domain,
                source_title=evidence.source_title,
                ai_relevance_score=float(score_data.get('relevance_score', 50)),
                ai_stance=score_data.get('stance', 'neutral'),
                ai_confidence=float(score_data.get('confidence', 0.5)),
                ai_reasoning=score_data.get('reasoning', 'AI analysis completed'),
                highlight_text=score_data.get('key_excerpt', evidence.text[:100]),
                highlight_context=evidence.text[:300]
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing AI relevance response: {e}")
            return self._fallback_evidence_score(claim_text, evidence)
    
    def filter_evidence_batch(self, claim_text: str, evidence_batch: List[EvidenceCandidate]) -> List[ProcessedEvidence]:
        """Process evidence batch efficiently with AI scoring - OPTIMIZED for speed"""
        
        if len(evidence_batch) == 0:
            return []
        
        # Limit evidence to process (quality over quantity)
        evidence_to_process = evidence_batch[:4]  # Reduced from 6 to 4 for speed
        
        # Try batch processing first (SPEED OPTIMIZATION)
        try:
            batch_results = self._batch_score_evidence(claim_text, evidence_to_process)
            if batch_results:
                return batch_results
        except Exception as e:
            print(f"Batch processing failed: {e}, falling back to individual scoring")
        
        # Fallback to individual processing if batch fails
        print("FALLBACK: Using individual processing instead of batch")
        processed_evidence = []
        for i, evidence in enumerate(evidence_to_process):
            processed = self.score_evidence_relevance(claim_text, evidence)
            processed_evidence.append(processed)
            print(f"Individual {i+1}: score={processed.ai_relevance_score}, confidence={processed.ai_confidence}")
        
        # Sort by AI relevance score and confidence
        processed_evidence.sort(
            key=lambda x: (x.ai_relevance_score * x.ai_confidence), 
            reverse=True
        )
        
        # Return top evidence items with RELAXED threshold for speed
        high_relevance = [
            ev for ev in processed_evidence 
            if ev.ai_relevance_score >= 60 and ev.ai_confidence >= 0.5  # Lowered thresholds
        ]
        
        print(f"AI FILTER DEBUG: {len(processed_evidence)} processed → {len(high_relevance)} passed threshold")
        for i, ev in enumerate(processed_evidence[:3]):  # Show first 3 for debugging
            print(f"  Evidence {i+1}: score={ev.ai_relevance_score}, confidence={ev.ai_confidence}")
        
        return high_relevance[:4]  # Top 4 most relevant (reduced for speed)
    
    def _create_minimal_strategy(self, claim_text: str) -> SearchStrategy:
        """Create minimal strategy for non-claims to return quickly"""
        return SearchStrategy(
            claim_type=ClaimType.FACTUAL,
            search_queries=[claim_text],  # Single basic query
            target_domains=[],
            time_relevance_months=12,
            authority_weight=0.3,  # Lower weight for non-claims
            confidence_threshold=0.3  # Lower threshold for non-claims
        )
    
    def _batch_score_evidence(self, claim_text: str, evidence_batch: List[EvidenceCandidate]) -> List[ProcessedEvidence]:
        """SPEED OPTIMIZATION: Score all evidence in single API call"""
        
        if not evidence_batch:
            return []
        
        # ULTRA-FAST batch prompt for maximum speed
        system_prompt = f"""Score evidence for claim: "{claim_text}". FAST processing.

90+: DIRECT proof/disproof
80-89: STRONG support/contradiction
70-79: GOOD relevance
60-69: WEAK relevance
<60: IRRELEVANT

STANCE - What is evidence DOING:
"contradicting": States claim FALSE, "no evidence," "no link," "myth"
"supporting": States claim TRUE, "evidence shows," "confirmed"  
"neutral": Just describes claim without judgment

Return JSON only:
[{{"evidence_index": 0, "relevance_score": 85, "stance": "supporting", "confidence": 0.9, "key_excerpt": "key quote"}}]"""

        # Build evidence list for batch processing (ULTRA-COMPRESSED for speed)
        evidence_texts = []
        for i, evidence in enumerate(evidence_batch):
            evidence_texts.append(f"EVIDENCE {i}: {evidence.text[:150]}")  # Reduced from 300 to 150 chars
        
        batch_content = f"CLAIM: {claim_text[:100]}\n\n" + "\n".join(evidence_texts)  # Removed extra newlines
        
        print(f"BATCH: Sending {len(evidence_batch)} evidence items to OpenAI")
        print(f"BATCH: Total content length: {len(batch_content)} chars")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": batch_content}
        ]
        
        # Single API call for all evidence
        response = self._call_openai(messages, temperature=0.1)
        if not response:
            print("BATCH: OpenAI API call failed")
            return []  # Will trigger fallback to individual processing
        
        print(f"BATCH: OpenAI response received, length: {len(response)}")
        
        try:
            print(f"BATCH: Attempting to parse JSON response: {response[:200]}...")
            batch_scores = json.loads(response)
            print(f"BATCH: Successfully parsed {len(batch_scores)} evidence scores")
            
            processed_evidence = []
            for score_data in batch_scores:
                evidence_index = score_data.get('evidence_index', 0)
                
                if evidence_index >= len(evidence_batch):
                    continue
                    
                evidence = evidence_batch[evidence_index]
                
                processed = ProcessedEvidence(
                    text=evidence.text,
                    source_url=evidence.source_url,
                    source_domain=evidence.source_domain,
                    source_title=evidence.source_title,
                    ai_relevance_score=float(score_data.get('relevance_score', 50)),
                    ai_stance=score_data.get('stance', 'neutral'),
                    ai_confidence=float(score_data.get('confidence', 0.5)),
                    ai_reasoning=score_data.get('reasoning', 'Batch processing'),
                    highlight_text=score_data.get('key_excerpt', evidence.text[:100]),
                    highlight_context=evidence.text[:300]
                )
                processed_evidence.append(processed)
            
            # Sort and filter as before
            processed_evidence.sort(
                key=lambda x: (x.ai_relevance_score * x.ai_confidence), 
                reverse=True
            )
            
            high_relevance = [
                ev for ev in processed_evidence 
                if ev.ai_relevance_score >= 60 and ev.ai_confidence >= 0.5  # Lowered thresholds
            ]
            
            return high_relevance[:6]
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing batch AI response: {e}")
            return []  # Will trigger fallback
    
    def search_real_evidence(self, claim_text: str) -> List[EvidenceCandidate]:
        """REAL WEB SEARCH: Find actual evidence from all available sources"""
        
        if not self.is_enabled():
            print("AI Evidence Shepherd disabled - no OpenAI API key")
            return []
        
        try:
            # Step 1: AI analyzes claim and creates search strategy
            search_strategy = self.analyze_claim(claim_text)
            print(f"AI Search Strategy: {search_strategy.claim_type.value} with {len(search_strategy.search_queries)} queries")
            
            # Step 2: Execute real web searches using AI-generated queries
            all_search_results = []
            
            for query in search_strategy.search_queries[:2]:  # Reduced to 2 queries for speed
                print(f"Searching web for: '{query}'")
                search_results = self.web_search.search_web(query, max_results=6)  # Reduced to 6 per query
                all_search_results.extend(search_results)
                print(f"Found {len(search_results)} results for '{query}'")
            
            # Step 3: PARALLEL content extraction from discovered URLs (SPEED OPTIMIZATION)
            top_results = all_search_results[:8]  # Reduced from 15 to 8 for speed
            urls_to_extract = [result.url for result in top_results]
            
            print(f"PARALLEL EXTRACTION: Processing {len(urls_to_extract)} URLs simultaneously")
            
            # Extract content from all URLs in parallel
            extraction_results = self.content_extractor.extract_content_batch(urls_to_extract)
            
            # Build evidence candidates from parallel extraction results
            evidence_candidates = []
            
            for i, search_result in enumerate(top_results):
                if i < len(extraction_results):
                    content_data = extraction_results[i]
                    
                    # Get the query that found this result (use first query as fallback)
                    found_query = search_strategy.search_queries[0] if search_strategy.search_queries else "unknown"
                    
                    if content_data['success'] and content_data['word_count'] > 50:
                        # Create evidence candidate with real content
                        evidence_candidate = EvidenceCandidate(
                            text=content_data['content'][:800],  # Reduced from 1000 to 800 for speed
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
                            raw_relevance=0.6  # Lower relevance for snippet-only
                        )
                        evidence_candidates.append(evidence_candidate)
            
            print(f"Real web search found {len(evidence_candidates)} evidence candidates from {len(all_search_results)} total results")
            
            # Step 4: AI evaluates all discovered evidence for relevance and stance
            processed_evidence = self.filter_evidence_batch(claim_text, evidence_candidates)
            
            return processed_evidence
        
        except Exception as e:
            print(f"Real web search failed: {e}")
            return []
    
    def is_enabled(self) -> bool:
        """Check if OpenAI API is properly configured"""
        return bool(self.api_key)
    
    def _fallback_strategy(self, claim_text: str) -> SearchStrategy:
        """Fallback strategy when AI is unavailable"""
        # Try to detect claim type with keywords
        claim_lower = claim_text.lower()
        
        if any(indicator in claim_lower for indicator in ['%', 'percent', 'survey', 'poll', 'study shows']):
            claim_type = ClaimType.STATISTICAL
        elif any(indicator in claim_lower for indicator in ['government', 'law', 'policy', 'announced']):
            claim_type = ClaimType.POLICY
        elif any(indicator in claim_lower for indicator in ['research', 'scientist', 'journal']):
            claim_type = ClaimType.SCIENTIFIC
        else:
            claim_type = ClaimType.FACTUAL
        
        # Extract key terms
        words = re.findall(r'\b[A-Za-z]{4,}\b', claim_text)
        search_queries = [' '.join(words[:5])]
        
        return SearchStrategy(
            claim_type=claim_type,
            search_queries=search_queries,
            target_domains=[],
            time_relevance_months=24,
            authority_weight=0.7,
            confidence_threshold=0.6
        )
    
    def _fallback_evidence_score(self, claim_text: str, evidence: EvidenceCandidate) -> ProcessedEvidence:
        """Fallback evidence scoring when AI unavailable"""
        # Simple keyword overlap
        claim_words = set(claim_text.lower().split())
        evidence_words = set(evidence.text.lower().split())
        overlap = len(claim_words.intersection(evidence_words))
        relevance = min(85, max(20, overlap * 12))
        
        return ProcessedEvidence(
            text=evidence.text,
            source_url=evidence.source_url,
            source_domain=evidence.source_domain,
            source_title=evidence.source_title,
            ai_relevance_score=relevance,
            ai_stance="neutral",
            ai_confidence=0.4,
            ai_reasoning="Keyword matching fallback",
            highlight_text=evidence.text[:100],
            highlight_context=evidence.text[:300]
        )