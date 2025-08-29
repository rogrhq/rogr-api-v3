import os
import json
import re
from typing import List, Dict, Optional
import requests
from evidence_shepherd import EvidenceShepherd, SearchStrategy, EvidenceCandidate, ProcessedEvidence, ClaimType

class OpenAIEvidenceShepherd(EvidenceShepherd):
    """OpenAI-powered evidence shepherd for smart fact-checking"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"
        
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
                'max_tokens': 1000
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None
    
    def analyze_claim(self, claim_text: str) -> SearchStrategy:
        """Use AI to analyze claim and create optimal search strategy"""
        
        system_prompt = """You are an expert fact-checker analyzing claims to determine the best verification strategy.

Your task: Analyze the claim and return a JSON response with search strategy.

Claim types:
- STATISTICAL: Contains numbers, percentages, survey data ("85% of Americans...")
- POLICY: About government actions, laws, announcements ("Biden signed...")  
- SCIENTIFIC: Research findings, studies ("Studies show...", "Research indicates...")
- HISTORICAL: Past events, dates ("In 2023...", "Last year...")
- OPINION: Expert opinions, beliefs ("Experts say...", "Many believe...")
- FACTUAL: Verifiable facts about companies, people, places ("Apple has...")

For each claim type, suggest:
1. Specific search queries (3-5) that would find the MOST RELEVANT evidence
2. Target domains that would have authoritative sources
3. How recent the evidence needs to be (months)

Return ONLY valid JSON in this format:
{
  "claim_type": "STATISTICAL",
  "search_queries": ["specific query 1", "specific query 2", "specific query 3"],
  "target_domains": ["domain1.com", "domain2.org"],
  "time_relevance_months": 12,
  "reasoning": "Brief explanation of strategy"
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
        
        system_prompt = """You are an expert fact-checker evaluating evidence relevance.

Your task: Determine how well evidence supports, contradicts, or relates to a specific claim.

RELEVANCE SCORING (0-100):
90-100: DIRECT - Evidence directly proves/disproves the claim with specific data
80-89:  STRONG - Evidence strongly supports/contradicts with related data  
70-79:  GOOD - Evidence provides relevant context or related information
60-69:  WEAK - Evidence mentions topic but doesn't directly address claim
50-59:  TANGENTIAL - Evidence related to topic but not claim specifics
0-49:   IRRELEVANT - Evidence unrelated or extremely weak connection

STANCE:
- "supporting": Evidence backs up the claim
- "contradicting": Evidence disputes the claim  
- "neutral": Evidence provides context but doesn't take a side

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
        """Process evidence batch efficiently with AI scoring"""
        
        if len(evidence_batch) == 0:
            return []
        
        # Process each evidence item
        processed_evidence = []
        for evidence in evidence_batch[:10]:  # Limit to avoid API costs
            processed = self.score_evidence_relevance(claim_text, evidence)
            processed_evidence.append(processed)
        
        # Sort by AI relevance score and confidence
        processed_evidence.sort(
            key=lambda x: (x.ai_relevance_score * x.ai_confidence), 
            reverse=True
        )
        
        # Return top evidence items that meet threshold
        high_relevance = [
            ev for ev in processed_evidence 
            if ev.ai_relevance_score >= 70 and ev.ai_confidence >= 0.6
        ]
        
        return high_relevance[:6]  # Top 6 most relevant
    
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