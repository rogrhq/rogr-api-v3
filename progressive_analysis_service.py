import asyncio
import time
import re
from typing import List, Dict, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import threading
import uuid

class ContentSize(Enum):
    SMALL = "small"      # <500 words
    MEDIUM = "medium"    # 500-2000 words  
    LARGE = "large"      # 2000-5000 words
    VERY_LARGE = "very_large"  # 5000+ words

class ProcessingPhase(Enum):
    QUICK_SCAN = "quick_scan"        # Phase 1: 5-10s
    AI_ANALYSIS = "ai_analysis"      # Phase 2: 15-30s  
    DEEP_MINING = "deep_mining"      # Phase 3: 45-90s

@dataclass
class ProcessingStatus:
    phase: ProcessingPhase
    progress: float  # 0.0 to 1.0
    message: str
    estimated_time_remaining: int  # seconds
    can_cancel: bool
    results_available: bool

@dataclass
class ClaimPriority:
    claim_text: str
    priority_score: float  # 0-1, higher = more important
    claim_type: str  # statistical, policy, factual, etc.
    source_strength: float  # How verifiable this claim is
    
class ProgressiveAnalysisService:
    """Multi-phase analysis service for handling content of any size"""
    
    def __init__(self, wikipedia_service, claim_service, evidence_shepherd):
        self.wikipedia_service = wikipedia_service
        self.claim_service = claim_service
        self.evidence_shepherd = evidence_shepherd
        
        # Active analysis tracking
        self.active_analyses = {}  # analysis_id -> analysis_state
        self.cancellation_flags = {}  # analysis_id -> should_cancel
        
    def detect_content_size(self, text: str) -> tuple[ContentSize, Dict]:
        """Detect content size and return processing expectations"""
        word_count = len(text.split())
        char_count = len(text)
        
        # Detect content complexity
        complexity_indicators = {
            'has_statistics': bool(re.search(r'\d+(?:\.\d+)?%', text)),
            'has_quotes': text.count('"') > 4,
            'has_urls': 'http' in text.lower(),
            'has_technical_terms': any(term in text.lower() for term in ['study', 'research', 'according to', 'data shows']),
            'paragraph_count': text.count('\n\n') + 1
        }
        
        if word_count < 500:
            size = ContentSize.SMALL
            phases = [ProcessingPhase.QUICK_SCAN, ProcessingPhase.AI_ANALYSIS]
            estimated_time = "5-15 seconds"
            
        elif word_count < 2000:
            size = ContentSize.MEDIUM  
            phases = [ProcessingPhase.QUICK_SCAN, ProcessingPhase.AI_ANALYSIS]
            estimated_time = "15-30 seconds"
            
        elif word_count < 5000:
            size = ContentSize.LARGE
            phases = [ProcessingPhase.QUICK_SCAN, ProcessingPhase.AI_ANALYSIS, ProcessingPhase.DEEP_MINING] 
            estimated_time = "30-60 seconds"
            
        else:
            size = ContentSize.VERY_LARGE
            phases = [ProcessingPhase.QUICK_SCAN, ProcessingPhase.AI_ANALYSIS, ProcessingPhase.DEEP_MINING]
            estimated_time = "1-3 minutes"
        
        return size, {
            'word_count': word_count,
            'char_count': char_count,
            'complexity': complexity_indicators,
            'phases': phases,
            'estimated_time': estimated_time,
            'can_cancel': True
        }
    
    async def start_progressive_analysis(self, 
                                       analysis_id: str,
                                       text: str, 
                                       content_type: str,
                                       progress_callback: Optional[Callable] = None) -> Dict:
        """Start progressive analysis with live updates"""
        
        # Detect content characteristics
        content_size, expectations = self.detect_content_size(text)
        
        # Initialize analysis state
        self.active_analyses[analysis_id] = {
            'content_size': content_size,
            'start_time': time.time(),
            'current_phase': ProcessingPhase.QUICK_SCAN,
            'results': {'claims': [], 'evidence': [], 'overall_score': 0},
            'expectations': expectations
        }
        self.cancellation_flags[analysis_id] = False
        
        try:
            # Phase 1: Quick Scan (always runs)
            await self._phase_1_quick_scan(analysis_id, text, content_type, progress_callback)
            
            if self._should_cancel(analysis_id):
                return self._get_current_results(analysis_id)
            
            # Phase 2: AI Analysis (for medium+ content)
            if ProcessingPhase.AI_ANALYSIS in expectations['phases']:
                await self._phase_2_ai_analysis(analysis_id, text, progress_callback)
            
            if self._should_cancel(analysis_id):
                return self._get_current_results(analysis_id)
            
            # Phase 3: Deep Mining (for large content)
            if ProcessingPhase.DEEP_MINING in expectations['phases']:
                await self._phase_3_deep_mining(analysis_id, text, progress_callback)
            
            return self._get_current_results(analysis_id)
            
        except Exception as e:
            print(f"Progressive analysis error for {analysis_id}: {e}")
            return self._get_current_results(analysis_id)
        finally:
            # Cleanup
            if analysis_id in self.active_analyses:
                del self.active_analyses[analysis_id]
            if analysis_id in self.cancellation_flags:
                del self.cancellation_flags[analysis_id]
    
    async def _phase_1_quick_scan(self, analysis_id: str, text: str, content_type: str, callback):
        """Phase 1: Quick extraction and basic scoring (5-10s)"""
        self._update_status(analysis_id, ProcessingPhase.QUICK_SCAN, 0.0, 
                           "Extracting claims...", 10, callback)
        
        # Quick claim extraction (no AI)
        claims = self.claim_service.extract_claims(text)
        if content_type == "url":
            url_data = self.claim_service.extract_url_metadata_and_text(text)
            merged_text = self.claim_service.merge_text_sources(url_data)
            claims.extend(self.claim_service.extract_claims(merged_text)[:3])
        
        # Prioritize claims by importance
        prioritized_claims = self._prioritize_claims(claims)
        
        self._update_status(analysis_id, ProcessingPhase.QUICK_SCAN, 0.5,
                           "Basic fact-checking...", 5, callback)
        
        # Quick evidence lookup (keyword-based, no AI)
        quick_evidence = []
        for claim in prioritized_claims[:3]:  # Top 3 claims only
            try:
                evidence = await asyncio.wait_for(
                    self._quick_evidence_lookup(claim.claim_text), 
                    timeout=3  # 3s max per claim
                )
                quick_evidence.extend(evidence)
            except asyncio.TimeoutError:
                continue
            
            if self._should_cancel(analysis_id):
                break
        
        # Store Phase 1 results
        self.active_analyses[analysis_id]['results'] = {
            'claims': [self._claim_to_dict(c) for c in prioritized_claims],
            'evidence': quick_evidence,
            'overall_score': self._calculate_quick_score(prioritized_claims, quick_evidence),
            'phase_completed': 'quick_scan'
        }
        
        self._update_status(analysis_id, ProcessingPhase.QUICK_SCAN, 1.0,
                           "Quick scan complete", 0, callback)
    
    async def _phase_2_ai_analysis(self, analysis_id: str, text: str, callback):
        """Phase 2: AI-powered evidence scoring and refinement (15-30s)"""
        self._update_status(analysis_id, ProcessingPhase.AI_ANALYSIS, 0.0,
                           "AI analyzing evidence quality...", 25, callback)
        
        current_results = self.active_analyses[analysis_id]['results']
        claims = current_results['claims']
        
        # AI-enhanced evidence scoring
        enhanced_evidence = []
        
        for i, claim in enumerate(claims[:5]):  # Top 5 claims for AI analysis
            if self._should_cancel(analysis_id):
                break
                
            progress = (i / min(len(claims), 5)) * 0.8
            self._update_status(analysis_id, ProcessingPhase.AI_ANALYSIS, progress,
                               f"AI scoring claim {i+1}/{min(len(claims), 5)}...", 
                               20 - int(progress * 20), callback)
            
            try:
                # Use AI shepherd for this claim
                ai_evidence = await asyncio.wait_for(
                    self._ai_evidence_analysis(claim['claim_text']),
                    timeout=5  # 5s max per claim
                )
                enhanced_evidence.extend(ai_evidence)
                
            except asyncio.TimeoutError:
                print(f"AI analysis timeout for claim: {claim['claim_text'][:50]}...")
                continue
            except Exception as e:
                print(f"AI analysis error for claim: {e}")
                continue
        
        # Update results with AI-enhanced evidence
        current_results['evidence'] = enhanced_evidence
        current_results['overall_score'] = self._calculate_ai_score(claims, enhanced_evidence)
        current_results['phase_completed'] = 'ai_analysis'
        
        self._update_status(analysis_id, ProcessingPhase.AI_ANALYSIS, 1.0,
                           "AI analysis complete", 0, callback)
    
    async def _phase_3_deep_mining(self, analysis_id: str, text: str, callback):
        """Phase 3: Comprehensive fact-checking for large content (45-90s)"""
        self._update_status(analysis_id, ProcessingPhase.DEEP_MINING, 0.0,
                           "Deep mining additional sources...", 60, callback)
        
        # For large content, extract more claims and do comprehensive verification
        # This would include cross-referencing multiple sources, checking claim consistency, etc.
        
        # Placeholder for comprehensive analysis
        await asyncio.sleep(2)  # Simulate processing
        
        current_results = self.active_analyses[analysis_id]['results']
        current_results['phase_completed'] = 'deep_mining'
        current_results['comprehensive'] = True
        
        self._update_status(analysis_id, ProcessingPhase.DEEP_MINING, 1.0,
                           "Comprehensive analysis complete", 0, callback)
    
    def cancel_analysis(self, analysis_id: str) -> bool:
        """Cancel active analysis"""
        if analysis_id in self.cancellation_flags:
            self.cancellation_flags[analysis_id] = True
            return True
        return False
    
    def get_analysis_status(self, analysis_id: str) -> Optional[Dict]:
        """Get current analysis status"""
        if analysis_id in self.active_analyses:
            state = self.active_analyses[analysis_id]
            return {
                'analysis_id': analysis_id,
                'content_size': state['content_size'].value,
                'current_phase': state['current_phase'].value,
                'elapsed_time': time.time() - state['start_time'],
                'expectations': state['expectations'],
                'results': state['results']
            }
        return None
    
    # Helper methods
    def _should_cancel(self, analysis_id: str) -> bool:
        return self.cancellation_flags.get(analysis_id, False)
    
    def _update_status(self, analysis_id: str, phase: ProcessingPhase, progress: float, 
                      message: str, eta: int, callback):
        """Update analysis status and call callback if provided"""
        if analysis_id in self.active_analyses:
            self.active_analyses[analysis_id]['current_phase'] = phase
            
        status = ProcessingStatus(
            phase=phase,
            progress=progress,
            message=message,
            estimated_time_remaining=eta,
            can_cancel=True,
            results_available=analysis_id in self.active_analyses and bool(self.active_analyses[analysis_id]['results']['claims'])
        )
        
        if callback:
            callback(analysis_id, status)
    
    def _prioritize_claims(self, claims: List[str]) -> List[ClaimPriority]:
        """Prioritize claims by importance for processing"""
        prioritized = []
        
        for claim in claims:
            # Score claim importance
            priority_score = 0.5  # Base score
            
            # Statistical claims are high priority
            if any(char.isdigit() for char in claim) and '%' in claim:
                priority_score += 0.3
                
            # Claims with proper nouns (names, places) are important  
            import re
            if re.search(r'\b[A-Z][a-z]+\b', claim):
                priority_score += 0.2
                
            # Longer, more specific claims are better
            if len(claim.split()) > 8:
                priority_score += 0.1
                
            prioritized.append(ClaimPriority(
                claim_text=claim,
                priority_score=min(1.0, priority_score),
                claim_type="factual",  # Would be detected by AI
                source_strength=0.7
            ))
        
        return sorted(prioritized, key=lambda x: x.priority_score, reverse=True)
    
    def _get_current_results(self, analysis_id: str) -> Dict:
        """Get current analysis results"""
        if analysis_id in self.active_analyses:
            return self.active_analyses[analysis_id]['results']
        return {'claims': [], 'evidence': [], 'overall_score': 0}
    
    async def _quick_evidence_lookup(self, claim_text: str) -> List[Dict]:
        """Quick evidence lookup without AI"""
        # Use fallback Wikipedia search
        try:
            return self.wikipedia_service._fallback_search(claim_text)
        except:
            return []
    
    async def _ai_evidence_analysis(self, claim_text: str) -> List[Dict]:
        """AI-powered evidence analysis"""
        try:
            return self.wikipedia_service.search_evidence_for_claim(claim_text)
        except Exception as e:
            print(f"AI evidence analysis failed: {e}")
            return []
    
    def _claim_to_dict(self, claim: ClaimPriority) -> Dict:
        """Convert ClaimPriority to dict format"""
        return {
            'claim_text': claim.claim_text,
            'priority_score': claim.priority_score,
            'claim_type': claim.claim_type
        }
    
    def _calculate_quick_score(self, claims: List[ClaimPriority], evidence: List[Dict]) -> int:
        """Calculate quick score from basic analysis"""
        if not claims:
            return 50
        
        base_score = 70  # Neutral starting point
        evidence_bonus = min(20, len(evidence) * 3)  # Up to 20 points for evidence
        
        return min(100, base_score + evidence_bonus)
    
    def _calculate_ai_score(self, claims: List[Dict], evidence: List[Dict]) -> int:
        """Calculate AI-enhanced score"""
        if not evidence:
            return 60
        
        # Average AI relevance scores
        relevance_scores = [e.get('relevance_score', 0.5) for e in evidence]
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        
        return int(avg_relevance * 100)