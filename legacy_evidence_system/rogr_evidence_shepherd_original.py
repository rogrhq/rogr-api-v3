import os
import json
import re
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from evidence_gathering.interfaces.search_strategy_interface import SearchStrategyResult
import requests
from .evidence_shepherd import EvidenceShepherd, SearchStrategy, EvidenceCandidate, ProcessedEvidence, ClaimType, MultiDomainClaimAnalysis
from web_search_service import WebSearchService
from web_content_extractor import WebContentExtractor

class ROGREvidenceShepherd(EvidenceShepherd):
    """ROGR evidence shepherd for professional fact-checking with AI-powered analysis"""
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-haiku-20240307"  # Use faster Haiku model for speed
        
        # Initialize web search and content extraction services
        self.web_search = WebSearchService()
        self.content_extractor = WebContentExtractor()
        
        print(f"Claude Evidence Shepherd initialized with real web search: {self.web_search.is_enabled()}")
        
    def _call_claude(self, messages: List[Dict], max_tokens: int = 1000) -> Optional[str]:
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
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result['content'][0]['text'].strip()
            
        except Exception as e:
            print(f"Claude API error: {e}")
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
    
    def _classify_claim_domains(self, claim_text: str) -> Optional[MultiDomainClaimAnalysis]:
        """Classify claim into multiple domains for professional fact-checking"""
        
        system_prompt = f"""You are an expert fact-checker analyzing this claim for multi-domain evidence requirements: "{claim_text}"

MULTI-DOMAIN ANALYSIS: Identify if this claim requires evidence from multiple domains:

DOMAIN TYPES:
- scientific: Medical, biological, physical sciences, peer-reviewed research
- medical: Healthcare, pharmaceuticals, clinical studies, medical institutions  
- intelligence: Government assessments, classified analysis, geopolitical intelligence
- policy: Government regulations, official announcements, legislative actions
- economic: Financial data, market analysis, economic indicators
- historical: Past events, chronological facts, documented occurrences
- statistical: Data analysis, surveys, numerical claims, demographics

MULTI-DOMAIN EXAMPLES:
- "Lab leak theory is most likely COVID origin" → PRIMARY: [scientific, medical], SECONDARY: [intelligence]
- "Climate policies will hurt economy" → PRIMARY: [economic, policy], SECONDARY: [scientific]
- "Vaccines cause autism" → PRIMARY: [medical, scientific], SECONDARY: []

Return ONLY JSON:
{{
  "primary_domains": ["domain1", "domain2"],
  "secondary_domains": ["domain3"],
  "domain_priorities": {{"scientific": 0.8, "medical": 0.7, "intelligence": 0.4}},
  "specialized_queries": {{
    "scientific": ["scientific query 1", "scientific query 2"],
    "medical": ["medical query 1"],  
    "intelligence": ["intelligence query 1"]
  }},
  "authority_domains": {{
    "scientific": ["nature.com", "science.org", "pmc.ncbi.nlm.nih.gov"],
    "medical": ["cdc.gov", "who.int", "mayoclinic.org"],
    "intelligence": ["oversight.house.gov", "dni.gov"]
  }},
  "reasoning": "Multi-domain strategy explanation"
}}

If single domain, use: "primary_domains": ["single_domain"], "secondary_domains": []"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze domains for: {claim_text}"}
        ]
        
        try:
            response = self._call_claude(messages, max_tokens=800)
            if not response:
                return None
            
            domain_data = json.loads(response)
            
            return MultiDomainClaimAnalysis(
                primary_domains=domain_data.get('primary_domains', []),
                secondary_domains=domain_data.get('secondary_domains', []),
                domain_priorities=domain_data.get('domain_priorities', {}),
                cross_domain_dependencies={},  # Can be enhanced later
                specialized_queries=domain_data.get('specialized_queries', {}),
                authority_domains=domain_data.get('authority_domains', {})
            )
            
        except (json.JSONDecodeError, KeyError, Exception) as e:
            print(f"⚠️ Multi-domain analysis failed: {e}")
            return None

    def analyze_claim(self, claim_text: str) -> SearchStrategy:
        """Use Claude to analyze claim and create optimal search strategy with multi-domain support"""
        
        # SPEED OPTIMIZATION: Skip non-claims immediately
        if self.is_non_claim(claim_text):
            print(f"SKIPPED non-claim: '{claim_text[:50]}...'")
            return self._create_minimal_strategy(claim_text)

        # NEW: Multi-domain claim classification
        print(f"🔍 Analyzing claim domains: {claim_text}")
        multi_domain_analysis = self._classify_claim_domains(claim_text)
        
        if multi_domain_analysis:
            print(f"📊 Multi-domain detected: PRIMARY {multi_domain_analysis.primary_domains}, SECONDARY {multi_domain_analysis.secondary_domains}")
            return self._create_multi_domain_search_strategy(claim_text, multi_domain_analysis)
        else:
            print("📄 Single-domain analysis fallback")
            # Fallback to original single-domain approach
        
        # Specialized prompt for Claude - CLAIM-SPECIFIC search strategy
        system_prompt = f"""You are an expert fact-checker creating search queries to verify this specific claim: "{claim_text}"

CRITICAL: Your queries must be DIRECTLY RELATED to verifying this exact claim, not general topics.

CLAIM-SPECIFIC SEARCH STRATEGY:
- INCLUDE the claim's key terms in search queries
- SEARCH for direct verification, not general background
- PRIORITIZE authoritative sources that would address this specific assertion

EXAMPLES:
Bad: "what is X" (too general)
Good: "X is Y scientific classification" (claim-specific)

Bad: "definition of stars" 
Good: "sun stellar classification astronomy" (for "sun is a star")

REQUIREMENTS: Generate 3 targeted search queries that directly verify or refute this claim.

Return ONLY JSON:
{{
  "claim_type": "FACTUAL",
  "search_queries": ["claim-specific query 1", "claim-specific query 2", "claim-specific query 3"],
  "target_domains": ["relevant-authority.gov", "relevant-source.org"],
  "time_relevance_months": 12,
  "reasoning": "Brief strategy explanation"
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this claim: {claim_text}"}
        ]
        
        response = self._call_claude(messages, max_tokens=500)
        if not response:
            raise ValueError("ROGR Evidence Shepherd: Failed to get AI response for claim analysis")
        
        try:
            strategy_data = json.loads(response)
            
            claim_type = ClaimType(strategy_data.get('claim_type', 'factual').lower())
            
            # Set authority weights based on claim type
            authority_weights = {
                ClaimType.STATISTICAL: 0.9,
                ClaimType.POLICY: 0.95,
                ClaimType.SCIENTIFIC: 1.0,
                ClaimType.HISTORICAL: 0.8,
                ClaimType.OPINION: 0.6,
                ClaimType.FACTUAL: 0.7
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
            print(f"❌ ROGR strategy parsing failed: {e}")
            raise ValueError(f"ROGR Evidence Shepherd: Failed to parse claim analysis: {e}")

    def _create_multi_domain_search_strategy(self, claim_text: str, analysis: MultiDomainClaimAnalysis) -> SearchStrategy:
        """Create search strategy for multi-domain claims"""
        
        # Combine all specialized queries from all domains
        all_queries = []
        all_target_domains = []
        
        # Add queries for primary domains (most important)
        for domain in analysis.primary_domains:
            domain_queries = analysis.specialized_queries.get(domain, [])
            all_queries.extend(domain_queries)
            
            # Add authority domains for this domain type
            domain_authorities = analysis.authority_domains.get(domain, [])
            all_target_domains.extend(domain_authorities)
        
        # Add queries for secondary domains (supporting evidence)
        for domain in analysis.secondary_domains:
            domain_queries = analysis.specialized_queries.get(domain, [])
            all_queries.extend(domain_queries[:2])  # Limit secondary queries
            
            # Add some authority domains for secondary domains
            domain_authorities = analysis.authority_domains.get(domain, [])
            all_target_domains.extend(domain_authorities[:3])  # Limit secondary domains
        
        # Fallback if no queries generated
        if not all_queries:
            all_queries = [claim_text]
        
        # Determine primary claim type for authority weighting
        primary_domain = analysis.primary_domains[0] if analysis.primary_domains else 'factual'
        claim_type = ClaimType.SCIENTIFIC if primary_domain in ['scientific', 'medical'] else ClaimType.FACTUAL
        
        # Set authority weights based on primary domain
        authority_weight = 1.0 if 'scientific' in analysis.primary_domains or 'medical' in analysis.primary_domains else 0.7
        confidence_threshold = 0.85 if 'scientific' in analysis.primary_domains else 0.75
        
        return SearchStrategy(
            claim_type=claim_type,
            search_queries=all_queries[:6],  # Limit total queries for performance
            target_domains=list(set(all_target_domains)),  # Remove duplicates
            time_relevance_months=12,  # Multi-domain claims often need recent evidence
            authority_weight=authority_weight,
            confidence_threshold=confidence_threshold,
            multi_domain_analysis=analysis
        )
    
    def filter_evidence_batch(self, claim_text: str, evidence_batch: List[EvidenceCandidate]) -> List[ProcessedEvidence]:
        """Process evidence batch efficiently with Claude scoring - OPTIMIZED for speed"""
        
        if len(evidence_batch) == 0:
            return []
        
        # Process all available evidence for professional fact-checking
        evidence_to_process = evidence_batch  # No artificial limits - process all candidates
        
        # Process evidence batch with ROGR system (no fallbacks - fail fast)
        batch_results = self._batch_score_evidence_claude(claim_text, evidence_to_process)
        
        # Sort by AI relevance score and confidence
        batch_results.sort(
            key=lambda x: (x.ai_relevance_score * x.ai_confidence), 
            reverse=True
        )
        
        # Return top evidence items
        high_relevance = [
            ev for ev in batch_results 
            if ev.ai_relevance_score >= 50 and ev.ai_confidence >= 0.3
        ]
        
        print(f"ROGR FILTER: {len(batch_results)} processed → {len(high_relevance)} passed threshold")
        for i, ev in enumerate(batch_results[:3]):  # Show first 3 for debugging
            print(f"  ROGR Evidence {i+1}: score={ev.ai_relevance_score}, confidence={ev.ai_confidence}")
        
        return high_relevance[:4]  # Top 4 most relevant
    
    def _batch_score_evidence_claude(self, claim_text: str, evidence_batch: List[EvidenceCandidate]) -> List[ProcessedEvidence]:
        """Claude batch processing with superior context handling"""
        
        if not evidence_batch:
            return []
        
        # EVIDENCE EVALUATION PROTOCOL - IDENTICAL to OpenAI for MDEQ consistency
        system_prompt = f"""Expert fact-checker: Score evidence relevance for the claim: "{claim_text}"

EVIDENCE EVALUATION PROTOCOL - Follow this sequence:
STEP 1: CLAIM ISOLATION - Focus only on core factual assertion: "{claim_text}"
STEP 2: TRUTH POSITION ANALYSIS - What does evidence say about claim truth?
STEP 3: RELEVANCE-STANCE ALIGNMENT - If unclear → default to "neutral"  
STEP 4: NEGATION OVERRIDE - Explicit negation words → "contradicting" (regardless of context)
STEP 5: CONFIDENCE GATE - If confidence < 0.7 → default to "neutral"

SCORING (0-100):
90+: DIRECT proof/disproof with specific data
80-89: STRONG support/contradiction with related data  
70-79: GOOD relevant context
60-69: WEAK relevance
<60: IRRELEVANT

STANCE CLASSIFICATION - Analyze what the evidence is DOING with the SPECIFIC CLAIM:

CRITICAL: For complex claims, focus on the CORE ASSERTION, not peripheral facts:
- Claim "X is rigged/fraudulent/fake" → Focus on PROCESS INTEGRITY, not outcomes
- Claim "X causes Y" → Focus on CAUSAL RELATIONSHIP, not just presence of X or Y
- Claim "X contains Y" → Focus on COMPOSITION, not just existence of X

STANCE CLASSIFICATION - Analyze what the evidence is DOING with the claim:

"contradicting" - The evidence:
  • States the claim is FALSE, incorrect, debunked, or disproven
  • Contains direct negation: "There are no X", "X does not exist", "No X found"
  • Provides data/facts that directly oppose the claim
  • Uses language like "no evidence," "studies show otherwise," "myth," "false," "no link," "no association"
  • Example: "Studies show no link between X and Y" when claim is "X causes Y"
  • Example: "There are no microchips in vaccines" when claim is "Vaccines contain microchips"

"supporting" - The evidence:
  • States the claim is TRUE, correct, or validated
  • Provides data/facts that directly confirm the claim  
  • Uses language like "evidence shows," "proven," "confirmed," "causes," "leads to"
  • Example: "Research confirms X causes Y" when claim is "X causes Y"

"neutral" - The evidence:
  • Merely mentions or describes the claim without judgment
  • Discusses the claim as a phenomenon/belief without endorsing or refuting
  • Reports outcomes/results WITHOUT addressing the process/mechanism in the claim
  • Reports what others believe without taking a position
  • ELECTIONS: Simple results ("X won") are NEUTRAL to process claims ("election rigged")
  • Example: "Biden won the election" is NEUTRAL to "Election was rigged"
  • Example: "Some people believe X causes Y" or "The theory that X causes Y"

CONFIDENCE: How certain are you (0.0-1.0)?
70-79: GOOD relevant context
60-69: WEAK relevance
<60: IRRELEVANT

STANCE CLASSIFICATION - Analyze what the evidence is DOING with the SPECIFIC CLAIM:

CRITICAL: For complex claims, focus on the CORE ASSERTION, not peripheral facts:
- Claim "X is rigged/fraudulent/fake" → Focus on PROCESS INTEGRITY, not outcomes
- Claim "X causes Y" → Focus on CAUSAL RELATIONSHIP, not just presence of X or Y
- Claim "X contains Y" → Focus on COMPOSITION, not just existence of X

STANCE CLASSIFICATION - Analyze what the evidence is DOING with the claim:

"contradicting" - The evidence:
  • States the claim is FALSE, incorrect, debunked, or disproven
  • Contains direct negation: "There are no X", "X does not exist", "No X found"
  • Provides data/facts that directly oppose the claim
  • Uses language like "no evidence," "studies show otherwise," "myth," "false," "no link," "no association"
  • Example: "Studies show no link between X and Y" when claim is "X causes Y"
  • Example: "There are no microchips in vaccines" when claim is "Vaccines contain microchips"

"supporting" - The evidence:
  • States the claim is TRUE, correct, or validated
  • Provides data/facts that directly confirm the claim  
  • Uses language like "evidence shows," "proven," "confirmed," "causes," "leads to"
  • Example: "Research confirms X causes Y" when claim is "X causes Y"

"neutral" - The evidence:
  • Merely mentions or describes the claim without judgment
  • Discusses the claim as a phenomenon/belief without endorsing or refuting
  • Reports outcomes/results WITHOUT addressing the process/mechanism in the claim
  • Reports what others believe without taking a position
  • ELECTIONS: Simple results ("X won") are NEUTRAL to process claims ("election rigged")
  • Example: "Biden won the election" is NEUTRAL to "Election was rigged"
  • Example: "Some people believe X causes Y" or "The theory that X causes Y"

MANDATORY STEP 4 - NEGATION OVERRIDE:
If evidence contains ["no", "not", "false", "debunked", "myth", "disproven"] directly about the claim → FORCE stance = "contradicting"
Example: "There are no microchips" for claim "vaccines contain microchips" = CONTRADICTING (not supporting)

MANDATORY STEP 5 - CONFIDENCE GATE:
If your confidence < 0.7 → FORCE stance = "neutral" for safety

Return ONLY valid JSON array with ALL evidence scored:
[{{"evidence_index": 0, "relevance_score": 85, "stance": "supporting", "confidence": 0.9, "key_excerpt": "short key quote"}}]

CRITICAL JSON FORMATTING:
- key_excerpt must be under 100 characters
- Escape all quotes in excerpts with \"
- No line breaks in key_excerpt
- Return only the JSON array, no explanatory text"""

        # Build evidence list - Claude can handle more content
        evidence_texts = []
        for i, evidence in enumerate(evidence_batch):
            evidence_texts.append(f"EVIDENCE {i}: {evidence.text[:400]}\nSOURCE: {evidence.source_title} ({evidence.source_domain})")  # More text than OpenAI
        
        batch_content = f"CLAIM: {claim_text}\n\n" + "\n\n".join(evidence_texts)
        
        print(f"CLAUDE BATCH: Sending {len(evidence_batch)} evidence items to Claude")
        print(f"CLAUDE BATCH: Total content length: {len(batch_content)} chars")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": batch_content}
        ]
        
        # Single API call for all evidence
        response = self._call_claude(messages, max_tokens=2000)  # Much higher than OpenAI
        if not response:
            print("CLAUDE BATCH: API call failed")
            return []
        
        print(f"CLAUDE BATCH: Response received, length: {len(response)}")
        print(f"CLAUDE BATCH: Attempting to parse JSON response: {response[:200]}...")
        
        try:
            # Extract JSON from response (may have explanatory text)
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                print(f"ROGR BATCH: Extracted JSON: {json_text[:100]}...")
                
                # Fix common JSON escaping issues before parsing
                json_text = json_text.replace('\\n', ' ').replace('\\t', ' ')
                # Fix unescaped quotes in key_excerpt fields
                import re
                json_text = re.sub(r'("key_excerpt":\s*")([^"]*)"([^"]*)"([^"]*")(")', r'\1\2\"\3\"\4\5', json_text)
                
                batch_scores = json.loads(json_text)
            else:
                print("ROGR BATCH: No valid JSON array found in response")
                raise ValueError("No valid JSON array found in AI response")
                
            print(f"CLAUDE BATCH: Successfully parsed {len(batch_scores)} evidence scores")
            
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
                    ai_reasoning=score_data.get('reasoning', 'Claude batch processing'),
                    highlight_text=score_data.get('key_excerpt', evidence.text[:100]),
                    highlight_context=evidence.text[:300]
                )
                processed_evidence.append(processed)
            
            # Sort and filter
            processed_evidence.sort(
                key=lambda x: (x.ai_relevance_score * x.ai_confidence), 
                reverse=True
            )
            
            high_relevance = [
                ev for ev in processed_evidence 
                if ev.ai_relevance_score >= 50 and ev.ai_confidence >= 0.3  # Match individual processing
            ]
            
            return high_relevance[:4]
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"❌ ROGR JSON parsing failed: {e}")
            print(f"❌ Raw response: {response}")
            raise ValueError(f"ROGR Evidence Shepherd JSON parsing failed: {e}")
    
    def score_evidence_relevance(self, claim_text: str, evidence: EvidenceCandidate) -> ProcessedEvidence:
        """Required abstract method implementation"""
        return self.score_evidence_relevance_claude(claim_text, evidence)
    
    def score_evidence_relevance_claude(self, claim_text: str, evidence: EvidenceCandidate) -> ProcessedEvidence:
        """Use Claude to score individual evidence relevance"""
        
        system_prompt = f"""You are an expert fact-checker evaluating evidence for the claim: "{claim_text}"

RELEVANCE SCORING (0-100):
90-100: DIRECT - Evidence directly proves/disproves the claim with specific data
80-89:  STRONG - Evidence strongly supports/contradicts with related data  
70-79:  GOOD - Evidence provides relevant context or related information
60-69:  WEAK - Evidence mentions topic but doesn't directly address claim
50-59:  TANGENTIAL - Evidence related to topic but not claim specifics
0-49:   IRRELEVANT - Evidence unrelated or extremely weak connection

STANCE relative to the claim "{claim_text}":
- "supporting": Evidence that supports/proves the claim is TRUE
- "contradicting": Evidence that disproves/refutes the claim is FALSE
- "neutral": Evidence that neither supports nor contradicts the claim

Return ONLY valid JSON:
{
  "relevance_score": 85,
  "stance": "supporting", 
  "confidence": 0.9,
  "reasoning": "Brief explanation",
  "key_excerpt": "Short quote under 100 chars"
}

CRITICAL: key_excerpt must be under 100 characters with escaped quotes (\")"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"CLAIM: {claim_text}\n\nEVIDENCE: {evidence.text[:800]}\n\nSOURCE: {evidence.source_title} ({evidence.source_domain})"}
        ]
        
        response = self._call_claude(messages, max_tokens=300)
        if not response:
            raise ValueError("ROGR Evidence Shepherd: Failed to get AI response for evidence scoring")
        
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
                ai_reasoning=score_data.get('reasoning', 'Claude analysis completed'),
                highlight_text=score_data.get('key_excerpt', evidence.text[:100]),
                highlight_context=evidence.text[:300]
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"❌ ROGR evidence scoring failed: {e}")
            raise ValueError(f"ROGR Evidence Shepherd: Failed to parse evidence scoring: {e}")
    
    def search_real_evidence(self, claim_text: str, strategy: SearchStrategy) -> List[EvidenceCandidate]:
        """Pure executor - receives complete strategy, executes queries"""
        
        if not self.is_enabled():
            print("Claude Evidence Shepherd disabled - no Anthropic API key")
            return []
        
        try:
            # Pure execution - no strategy generation
            queries = strategy.search_queries
            print(f"Executing {strategy.strategy_source}: {len(queries)} queries")
            
            # Step 2: Execute real web searches using strategy queries
            all_search_results = []
            
            for query in queries:
                print(f"Searching web for: '{query}'")
                search_results = self.web_search.search_web(query, max_results=8)  # More results per query
                all_search_results.extend(search_results)
                print(f"Found {len(search_results)} results for '{query}'")
            
            # Step 3: PARALLEL content extraction from discovered URLs (COMPREHENSIVE)
            top_results = all_search_results[:10]  # More results for professional thoroughness
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
                            text=content_data['content'][:800],  # Same as OpenAI for comparison
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
            
            # Step 4: Claude evaluates all discovered evidence for relevance and stance
            processed_evidence = self.filter_evidence_batch(claim_text, evidence_candidates)
            
            return processed_evidence
        
        except Exception as e:
            print(f"Claude web search failed: {e}")
            return []
    
    def is_enabled(self) -> bool:
        """Check if Claude API is properly configured"""
        return bool(self.api_key)
    
    def _create_minimal_strategy(self, claim_text: str) -> SearchStrategy:
        """Create minimal strategy for non-claims to return quickly"""
        return SearchStrategy(
            claim_type=ClaimType.FACTUAL,
            search_queries=[claim_text],
            target_domains=[],
            time_relevance_months=12,
            authority_weight=0.3,
            confidence_threshold=0.3
        )
    
    def _fallback_strategy(self, claim_text: str) -> SearchStrategy:
        """Fallback strategy when Claude is unavailable"""
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
        """Fallback evidence scoring when Claude unavailable"""
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