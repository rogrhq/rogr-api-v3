import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from evidence_shepherd import EvidenceShepherd, SearchStrategy, EvidenceCandidate, ProcessedEvidence, ClaimType
from ai_provider import AIProvider, AIResponse
from web_search_service import WebSearchService
from web_content_extractor import WebContentExtractor

@dataclass
class StanceResult:
    """Result of stance classification"""
    stance: str  # "supporting", "contradicting", "neutral"
    confidence: float  # 0.0-1.0
    relevance_score: float  # 0-100
    key_excerpt: str
    reasoning: str

@dataclass
class ConsensusResult:
    """Result from multiple AI consensus"""
    final_stance: str
    consensus_confidence: float
    individual_results: List[StanceResult]
    agreement_level: float  # 0.0-1.0

class EvidenceShepherdV2(EvidenceShepherd):
    """Centralized Evidence Shepherd with pluggable AI providers"""
    
    def __init__(self, ai_providers: List[AIProvider]):
        self.ai_providers = [p for p in ai_providers if p.is_available()]
        self.web_search = WebSearchService()
        self.content_extractor = WebContentExtractor()
        
        print(f"Evidence Shepherd v2 initialized with {len(self.ai_providers)} AI providers: {[p.get_name() for p in self.ai_providers]}")
    
    def build_stance_classification_prompt(self, claim: str, evidence: str) -> str:
        """Centralized stance classification prompt - single source of truth"""
        return f"""Analyze this evidence against the claim and classify its stance.

CLAIM: {claim}

EVIDENCE: {evidence}

RELEVANCE SCORING (0-100):
90-100: STRONG support/contradiction with direct statements
80-89: STRONG support/contradiction with related data  
70-79: GOOD relevant context
60-69: WEAK relevance
<60: IRRELEVANT

STANCE CLASSIFICATION - Analyze what the evidence is DOING with the SPECIFIC CLAIM:

CRITICAL: For complex claims, focus on the CORE ASSERTION, not peripheral facts:
- Claim "X is rigged/fraudulent/fake" → Focus on PROCESS INTEGRITY, not outcomes
- Claim "X causes Y" → Focus on CAUSAL RELATIONSHIP, not just presence of X or Y
- Claim "X contains Y" → Focus on COMPOSITION, not just existence of X

"contradicting" - The evidence:
  • States the claim is FALSE, incorrect, debunked, or disproven
  • Contains direct negation: "There are no X", "X does not exist", "No X found"
  • Provides data/facts that directly oppose the CORE CLAIM
  • Uses language like "no evidence," "studies show otherwise," "myth," "false," "no link," "no association"
  • PROCESS CLAIMS: Evidence of investigations finding "no fraud," "secure," "verified," "audited"
  • Example: "Studies show no link between X and Y" when claim is "X causes Y"
  • Example: "No evidence of rigging found" when claim is "Election was rigged"

"supporting" - The evidence:
  • States the claim is TRUE, correct, or validated
  • Provides data/facts that directly confirm the SPECIFIC CLAIM
  • Uses language like "evidence shows," "proven," "confirmed," "causes," "leads to"
  • MUST address the actual claim assertion, not just related facts
  • Example: "Research confirms X causes Y" when claim is "X causes Y"
  • Example: "Evidence of rigging found" when claim is "Election was rigged"

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

Return ONLY valid JSON:
{{"relevance_score": 85, "stance": "supporting", "confidence": 0.9, "key_excerpt": "short key quote", "reasoning": "brief explanation"}}

CRITICAL JSON FORMATTING:
- key_excerpt must be under 100 characters
- Escape all quotes in excerpts with \"
- No line breaks in key_excerpt
- Return only the JSON, no explanatory text"""

    def classify_stance_with_ai(self, claim: str, evidence: str, provider: AIProvider) -> Optional[StanceResult]:
        """Use a specific AI provider to classify stance"""
        prompt = self.build_stance_classification_prompt(claim, evidence)
        
        response = provider.call_api(prompt, max_tokens=1000)
        if not response.success:
            print(f"AI call failed for {provider.get_name()}: {response.error}")
            return None
        
        try:
            # Extract JSON from response
            json_start = response.content.find('{')
            json_end = response.content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response.content[json_start:json_end]
                data = json.loads(json_text)
                
                return StanceResult(
                    stance=data.get('stance', 'neutral'),
                    confidence=float(data.get('confidence', 0.5)),
                    relevance_score=float(data.get('relevance_score', 50)),
                    key_excerpt=data.get('key_excerpt', evidence[:100]),
                    reasoning=data.get('reasoning', f'{provider.get_name()} analysis')
                )
            else:
                print(f"No valid JSON found in {provider.get_name()} response")
                return None
                
        except Exception as e:
            print(f"Error parsing {provider.get_name()} response: {e}")
            return None

    def get_consensus_analysis(self, claim: str, evidence: str) -> ConsensusResult:
        """Get consensus from all available AI providers"""
        individual_results = []
        
        for provider in self.ai_providers:
            result = self.classify_stance_with_ai(claim, evidence, provider)
            if result:
                individual_results.append(result)
        
        if not individual_results:
            # Fallback if all AIs fail
            return ConsensusResult(
                final_stance="neutral",
                consensus_confidence=0.0,
                individual_results=[],
                agreement_level=0.0
            )
        
        # Calculate consensus
        stances = [r.stance for r in individual_results]
        stance_counts = {s: stances.count(s) for s in set(stances)}
        final_stance = max(stance_counts.keys(), key=stance_counts.get)
        
        # Agreement level (what fraction agree with majority)
        agreement_level = stance_counts[final_stance] / len(individual_results)
        
        # Average confidence of majority stance supporters
        majority_results = [r for r in individual_results if r.stance == final_stance]
        consensus_confidence = sum(r.confidence for r in majority_results) / len(majority_results)
        
        return ConsensusResult(
            final_stance=final_stance,
            consensus_confidence=consensus_confidence,
            individual_results=individual_results,
            agreement_level=agreement_level
        )

    def score_evidence_relevance(self, claim_text: str, evidence: EvidenceCandidate) -> ProcessedEvidence:
        """Process single evidence using AI consensus"""
        consensus = self.get_consensus_analysis(claim_text, evidence.text)
        
        # Use the best result from consensus
        best_result = max(consensus.individual_results, key=lambda r: r.confidence) if consensus.individual_results else None
        
        if best_result:
            return ProcessedEvidence(
                text=evidence.text,
                source_url=evidence.source_url,
                source_domain=evidence.source_domain,
                source_title=evidence.source_title,
                ai_relevance_score=best_result.relevance_score,
                ai_stance=consensus.final_stance,
                ai_confidence=consensus.consensus_confidence,
                ai_reasoning=f"Consensus: {consensus.agreement_level:.1%} agreement ({len(consensus.individual_results)} AIs)",
                highlight_text=best_result.key_excerpt,
                highlight_context=evidence.text[:300]
            )
        else:
            # Fallback if all AIs fail
            return ProcessedEvidence(
                text=evidence.text,
                source_url=evidence.source_url,
                source_domain=evidence.source_domain,
                source_title=evidence.source_title,
                ai_relevance_score=50.0,
                ai_stance="neutral",
                ai_confidence=0.1,
                ai_reasoning="AI analysis failed",
                highlight_text=evidence.text[:100],
                highlight_context=evidence.text[:300]
            )

    def filter_evidence_batch(self, claim_text: str, evidence_batch: List[EvidenceCandidate]) -> List[ProcessedEvidence]:
        """Process batch of evidence with AI consensus"""
        processed_evidence = []
        
        print(f"Processing {len(evidence_batch)} evidence pieces with {len(self.ai_providers)} AIs")
        
        for evidence in evidence_batch:
            processed = self.score_evidence_relevance(claim_text, evidence)
            if processed.ai_relevance_score >= 50 and processed.ai_confidence >= 0.3:
                processed_evidence.append(processed)
        
        # Sort by weighted score (relevance * confidence)
        processed_evidence.sort(
            key=lambda x: (x.ai_relevance_score * x.ai_confidence), 
            reverse=True
        )
        
        return processed_evidence[:8]  # Return top 8

    def analyze_claim(self, claim_text: str) -> SearchStrategy:
        """Analyze claim and return search strategy (simple implementation)"""
        return SearchStrategy(
            claim_type=ClaimType.FACTUAL,
            search_queries=[claim_text],
            target_domains=[],
            time_relevance_months=24,
            authority_weight=0.7,
            confidence_threshold=0.5
        )
    
    def is_enabled(self) -> bool:
        """Check if at least one AI provider is available"""
        return len(self.ai_providers) > 0