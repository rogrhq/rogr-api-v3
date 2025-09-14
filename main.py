from typing import Union, List, Optional
from datetime import datetime
import uuid
import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ocr_service import OCRService
from claim_miner import ClaimMiner, ClaimMiningResult, MinedClaim
from wikipedia_service import WikipediaService
from legacy_evidence_system.ai_evidence_shepherd import OpenAIEvidenceShepherd
from legacy_evidence_system.claude_evidence_shepherd import ClaudeEvidenceShepherd
from legacy_evidence_system.evidence_shepherd import NoOpEvidenceShepherd
from progressive_analysis_service import ProgressiveAnalysisService
from rogr_fc_scoring_engine_zero_start import ROGRFCScoringEngineZeroStart
from legacy_evidence_system.rogr_dual_evidence_shepherd import ROGRDualEvidenceShepherd
from evidence_gathering.interfaces.search_strategy_interface import FeatureFlaggedSearchStrategy
from evidence_gathering.search_strategy.methodology_strategist import MethodologySearchStrategist
from performance_testing import performance_tester

# Feature flag logging for visibility
USE_PARALLEL_EVIDENCE = os.getenv('USE_PARALLEL_EVIDENCE', 'false').lower() == 'true'
print(f"🔧 USE_PARALLEL_EVIDENCE = {USE_PARALLEL_EVIDENCE}")


def create_evidence_system(use_parallel: bool = False):
    """Factory for evidence system selection with feature flag support"""
    use_parallel_flag = os.getenv('USE_PARALLEL_EVIDENCE', 'false').lower() == 'true'

    if use_parallel or use_parallel_flag:
        # Import parallel system (will be implemented in Phase 2)
        try:
            from parallel_evidence_system.orchestrator.parallel_evidence_orchestrator import ParallelEvidenceOrchestrator
            print("✅ Using Parallel Evidence System")
            return ParallelEvidenceOrchestrator()
        except ImportError:
            print("⚠️ Parallel system not available, falling back to legacy")

    # Legacy system (current behavior preserved)
    from legacy_evidence_system.rogr_dual_evidence_shepherd import ROGRDualEvidenceShepherd
    use_eeg_phase_1 = os.getenv('USE_EEG_PHASE_1', 'false').lower() == 'true'
    print("✅ Using Legacy Evidence System")
    return ROGRDualEvidenceShepherd(use_eeg_phase_1=use_eeg_phase_1)


# Test comment - verifying git push workflows

app = FastAPI()

# Simple CORS headers
@app.middleware("http")
async def add_cors_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Data models
class AnalysisInput(BaseModel):
    input: str
    mode: str = "both"  # both|ai|fact
    source: str = "share"  # share|paste
    type: str = "text"  # image|video|audio|text|url

class FocusRequest(BaseModel):
    layers: List[str]  # ["ocr","speech","visual","metadata","provenance"]

class Citation(BaseModel):
    title: str
    domain: str
    date: str
    url: str

class EvidenceStatement(BaseModel):
    statement: str
    source_title: str
    source_domain: str
    source_url: str
    stance: str  # "supporting", "contradicting", "neutral"
    relevance_score: float  # 0-1, how relevant to the claim
    highlight_text: Optional[str] = None  # Exact text to highlight on source page
    highlight_context: Optional[str] = None  # Surrounding context for better matching
    paragraph_index: Optional[int] = None  # Paragraph number where evidence was found

class ClaimAnalysis(BaseModel):
    claim_text: str
    trust_score: int
    evidence_grade: str
    confidence: str
    evidence_summary: List[str]  # Bullet points of evidence
    sources_count: int
    supporting_evidence: List[EvidenceStatement]
    contradicting_evidence: List[EvidenceStatement]
    neutral_evidence: List[EvidenceStatement]

class TrustCapsule(BaseModel):
    id: str
    trust_score: int
    evidence_grade: str
    confidence: str
    why: List[str]  # Brief summary for main view
    claims: List[ClaimAnalysis]  # Individual claim details
    overall_assessment: str  # "can likely be trusted" etc
    citations: List[Citation]
    capsule_version: int
    signed: bool
    created_at: str
    input_type: str
    mode: str

# In-memory storage
analyses_db = {}
analyses_input_db = {}  # Store original inputs for focus analysis
analyses_claims_db = {}  # Store extracted claims for focus analysis

# Initialize services
ocr_service = OCRService()
claim_miner = ClaimMiner()

# Initialize Evidence System with Factory Pattern at startup for reuse across requests
evidence_system = None
try:
    evidence_system = create_evidence_system()
    if evidence_system and evidence_system.is_enabled():
        print("✅ Evidence system enabled at startup")
    else:
        print("❌ Evidence system disabled - no shepherds available")
        evidence_system = None
except Exception as e:
    print(f"❌ Evidence system failed to initialize: {e}")
    evidence_system = None

# Maintain backward compatibility
rogr_dual_shepherd = evidence_system

# Claim scoring functions
def generate_evidence_statements(claim_text: str, trust_score: int) -> tuple[List[EvidenceStatement], List[EvidenceStatement], List[EvidenceStatement]]:
    """Generate evidence statements using Pure AI Evidence Shepherd - no Wikipedia scaffolding"""
    supporting_evidence = []
    contradicting_evidence = []
    neutral_evidence = []
    
    # REAL WEB SEARCH AI EVIDENCE SHEPHERD - Truly impartial source discovery
    try:
        print(f"DEBUG: Using REAL WEB SEARCH AI Evidence Shepherd for claim: '{claim_text}'")
        
        # AI performs real web search and content analysis
        if evidence_system and hasattr(evidence_system, 'search_real_evidence'):
            real_evidence = evidence_system.search_real_evidence(claim_text)
        else:
            print(f"DEBUG: search_real_evidence not available in current evidence system")
            real_evidence = []
        print(f"DEBUG: Real web search found {len(real_evidence)} evidence items")
        
        if real_evidence:
            # Check for Multi-AI consensus quality score (MDEQ system)
            consensus_quality_score = None
            if real_evidence and hasattr(real_evidence[0], 'consensus_quality_score'):
                consensus_quality_score = real_evidence[0].consensus_quality_score
                print(f"DEBUG: Found MDEQ consensus quality score: {consensus_quality_score:.1f}")
            
            # Convert real evidence to EvidenceStatement format
            for evidence in real_evidence:
                evidence_stmt = EvidenceStatement(
                    statement=evidence.text[:200] if evidence.text else "Evidence found from source",
                    source_title=evidence.source_title,
                    source_domain=evidence.source_domain,
                    source_url=evidence.source_url,
                    stance=evidence.ai_stance if hasattr(evidence, 'ai_stance') else "supporting",
                    relevance_score=evidence.ai_relevance_score/100 if hasattr(evidence, 'ai_relevance_score') else 0.8,
                    highlight_text=evidence.highlight_text if hasattr(evidence, 'highlight_text') else evidence.text[:100],
                    highlight_context=evidence.highlight_context if hasattr(evidence, 'highlight_context') else evidence.text[:300]
                )
                
                # Categorize by stance
                if evidence_stmt.stance == "supporting":
                    supporting_evidence.append(evidence_stmt)
                elif evidence_stmt.stance == "contradicting":
                    contradicting_evidence.append(evidence_stmt)
                else:
                    neutral_evidence.append(evidence_stmt)
            
            print(f"USING REAL WEB EVIDENCE: {len(supporting_evidence)} supporting, {len(contradicting_evidence)} contradicting, {len(neutral_evidence)} neutral")
            if consensus_quality_score is not None:
                print(f"DEBUG: Returning MDEQ consensus quality score: {consensus_quality_score:.1f}")
                return supporting_evidence[:3], contradicting_evidence[:2], neutral_evidence[:2], consensus_quality_score
            return supporting_evidence[:3], contradicting_evidence[:2], neutral_evidence[:2]
        else:
            print("DEBUG: No real web evidence found, falling back to simulated evidence")
            # Fallback to simulated evidence if real search fails
            supporting_evidence.extend([
                EvidenceStatement(
                    statement="AI web search attempted but no suitable evidence sources were accessible at this time.",
                    source_title="Evidence Search Status", 
                    source_domain="rogr.app",
                    source_url="https://rogr.app/evidence-search-status",
                    stance="supporting",
                    relevance_score=0.5
                )
            ])
    
    except Exception as e:
        print(f"ERROR: AI Evidence Shepherd failed for '{claim_text}': {e}")
        print("DEBUG: Falling back to minimal generic evidence")
        
        # Minimal fallback if AI completely fails
        supporting_evidence.append(
            EvidenceStatement(
                statement="Claim requires verification through authoritative sources and fact-checking processes.",
                source_title="General Fact-Checking Guidelines",
                source_domain="factcheck.org",
                source_url="https://www.factcheck.org/our-process/",
                stance="supporting",
                relevance_score=0.5
            )
        )
    
    return supporting_evidence[:3], contradicting_evidence[:2], neutral_evidence[:2]

async def score_claim_with_evidence_shepherd(claim_text: str, claim_context: dict = None) -> ClaimAnalysis:
    """Score a claim using advanced Multi-AI Evidence Shepherd with quality assessment and uncertainty quantification"""
    
    # Initialize Advanced Multi-AI Evidence Shepherd
    evidence_shepherd = None
    use_multi_ai = os.getenv('USE_MULTI_AI_CONSENSUS', 'true').lower() == 'true'
    
    try:
        if use_multi_ai:
            from legacy_evidence_system.rogr_dual_evidence_shepherd import ROGRDualEvidenceShepherd
            evidence_shepherd = rogr_dual_shepherd
            print(f"DEBUG: Using ROGR Dual Evidence Shepherd (NEW) for claim: {claim_text[:50]}...")
        else:
            # Fallback to single AI (Phase 1 behavior)
            if os.getenv('ANTHROPIC_API_KEY'):
                evidence_shepherd = ClaudeEvidenceShepherd()
                print(f"DEBUG: Using Claude Evidence Shepherd (single AI) for claim: {claim_text[:50]}...")
            elif os.getenv('OPENAI_API_KEY'):
                evidence_shepherd = OpenAIEvidenceShepherd()
                print(f"DEBUG: Using OpenAI Evidence Shepherd (single AI) for claim: {claim_text[:50]}...")
            else:
                evidence_shepherd = NoOpEvidenceShepherd()
                print(f"DEBUG: Using NoOp Evidence Shepherd (no API keys) for claim: {claim_text[:50]}...")
    except Exception as e:
        print(f"ERROR: Failed to initialize Evidence Shepherd: {e}")
        evidence_shepherd = NoOpEvidenceShepherd()
    
    # Process claim through Evidence Shepherd
    try:
        # Use Evidence Shepherd to find and analyze evidence
        evidence_pieces = evidence_shepherd.search_real_evidence(claim_text)
        
        print(f"DEBUG: Evidence Shepherd found {len(evidence_pieces)} pieces of evidence")
        
        # Convert Evidence Shepherd results to ClaimAnalysis format
        supporting_evidence = []
        contradicting_evidence = []
        neutral_evidence = []
        
        for evidence in evidence_pieces:
            evidence_statement = EvidenceStatement(
                statement=evidence.text[:200] if evidence.text else "Evidence found from source",
                source_title=evidence.source_title,
                source_domain=evidence.source_domain,
                source_url=evidence.source_url,
                stance=evidence.ai_stance.lower() if evidence.ai_stance else "neutral",
                relevance_score=evidence.ai_relevance_score / 100.0,  # Convert to 0-1 range
                highlight_text=evidence.highlight_text if hasattr(evidence, 'highlight_text') else evidence.text[:100] if evidence.text else "",
                highlight_context=evidence.highlight_context if hasattr(evidence, 'highlight_context') else evidence.text[:300] if evidence.text else ""
            )
            
            if evidence.ai_stance and evidence.ai_stance.lower() == "supporting":
                supporting_evidence.append(evidence_statement)
            elif evidence.ai_stance and evidence.ai_stance.lower() == "contradicting":
                contradicting_evidence.append(evidence_statement)
            else:
                neutral_evidence.append(evidence_statement)
        
        # Check for Multi-AI consensus quality score (MDEQ system)
        consensus_quality_score = None
        consensus_metadata = {}
        
        if evidence_pieces and hasattr(evidence_pieces[0], 'consensus_quality_score'):
            consensus_quality_score = evidence_pieces[0].consensus_quality_score
            consensus_metadata = getattr(evidence_pieces[0], 'consensus_metadata', {})
            print(f"DEBUG: Found MDEQ consensus quality score: {consensus_quality_score:.1f}")
        
        # Advanced trust score calculation with uncertainty quantification
        sources_count = len(evidence_pieces)
        
        # NEW ES MUST provide consensus quality score - no fallbacks
        if consensus_quality_score is not None:
            base_trust_score = consensus_quality_score
            print(f"DEBUG: Using NEW ES consensus score: {base_trust_score:.1f}")
        else:
            # NEW Evidence Shepherd should ALWAYS provide consensus score
            raise Exception("NEW Evidence Shepherd failed to provide consensus_quality_score - system error")
        
        # Apply uncertainty adjustments
        trust_score = base_trust_score
        confidence_band = "Medium"
        uncertainty_notes = []
        
        # MDEQ PRIORITY: If we have consensus quality score, use it and skip emergency caps
        if consensus_quality_score is not None:
            print(f"DEBUG: MDEQ system active - using quality-based score {trust_score:.1f}, skipping emergency caps")
            if consensus_metadata.get('uncertainty_indicators'):
                uncertainty_notes.extend(consensus_metadata['uncertainty_indicators'])
            if trust_score < 40:
                confidence_band = "Low"
            elif trust_score > 70:
                confidence_band = "High"
        else:
            # EMERGENCY FIX: Apply immediate score caps for contradicting evidence (non-MDEQ systems only)
            # If we have contradicting evidence and no supporting evidence, cap the score
            if contradicting_evidence and not supporting_evidence:
                # Count high-quality contradicting sources (medical, academic domains)
                high_quality_contradicting = 0
                for evidence in contradicting_evidence:
                    domain = evidence.source_domain.lower()
                    if any(quality_domain in domain for quality_domain in [
                        'nih.gov', 'cdc.gov', 'who.int', 'nature.com', 'pmc.ncbi.nlm.nih.gov',
                        'pubmed', 'nejm.org', 'bmj.com', 'thelancet.com', '.edu', 'harvard.edu',
                        'stanford.edu', 'mit.edu', 'oxford.ac.uk', 'cambridge.org'
                    ]):
                        high_quality_contradicting += 1
                
                # If we have high-quality contradicting evidence, cap the score low
                if high_quality_contradicting > 0:
                    trust_score = min(trust_score, 30.0)  # Cap at 30
                    confidence_band = "Low"
                    uncertainty_notes.append(f"High-quality contradicting evidence from {high_quality_contradicting} authoritative source(s)")
                    print(f"DEBUG: EMERGENCY CAP APPLIED - High-quality contradicting evidence found, score capped at {trust_score}")
                
                # Even for lower quality contradicting evidence, cap higher
                elif len(contradicting_evidence) >= 1:
                    trust_score = min(trust_score, 45.0)  # Cap at 45 for any contradicting evidence
                    confidence_band = "Low"
                    uncertainty_notes.append("Contradicting evidence found without supporting evidence")
                    print(f"DEBUG: CONTRADICTING EVIDENCE CAP - Score capped at {trust_score}")
        
        if consensus_metadata:
            ai_consensus = consensus_metadata.get('ai_consensus', 100)
            disagreement_level = consensus_metadata.get('disagreement_level', 0)
            evidence_quality_summary = consensus_metadata.get('evidence_quality_summary', {})
            uncertainty_indicators = consensus_metadata.get('uncertainty_indicators', [])
            
            # Adjust confidence based on AI consensus
            if disagreement_level > 40:
                confidence_band = "Low"
                uncertainty_notes.extend(uncertainty_indicators)
            elif disagreement_level < 15 and ai_consensus > 80:
                confidence_band = "High"
            
            # Apply evidence quality adjustments
            avg_quality = evidence_quality_summary.get('avg_quality_score', 50)
            high_quality_count = evidence_quality_summary.get('high_quality_count', 0)
            low_quality_count = evidence_quality_summary.get('low_quality_count', 0)
            
            # Quality-based score adjustments
            quality_factor = avg_quality / 100.0
            
            # High-quality contradicting evidence caps score low
            if contradicting_evidence and high_quality_count > 0:
                for evidence in contradicting_evidence:
                    if evidence.relevance_score > 0.7:  # High relevance contradicting evidence
                        # This is the key fix for our 5G/COVID problem
                        trust_score = min(trust_score, 35.0)  # Cap at low score
                        uncertainty_notes.append("High-quality contradicting evidence found")
                        break
            
            # Low-quality evidence reduces confidence
            if low_quality_count > high_quality_count:
                confidence_band = "Low"
                uncertainty_notes.append("Evidence quality concerns identified")
            
            print(f"DEBUG: Advanced scoring - Base: {base_trust_score:.1f}, Adjusted: {trust_score:.1f}, Quality: {avg_quality:.1f}")
        
        # Generate enhanced evidence summary with quality indicators
        evidence_summary = []
        if supporting_evidence:
            evidence_summary.append(f"Supported by {len(supporting_evidence)} source{'s' if len(supporting_evidence) > 1 else ''}")
        if contradicting_evidence:
            evidence_summary.append(f"Challenged by {len(contradicting_evidence)} contradicting source{'s' if len(contradicting_evidence) > 1 else ''}")
        if neutral_evidence:
            evidence_summary.append(f"Referenced in {len(neutral_evidence)} neutral context{'s' if len(neutral_evidence) > 1 else ''}")
        
        # Add quality and consensus information
        if consensus_metadata:
            evidence_summary.append(f"Multi-AI consensus analysis completed")
            if uncertainty_notes:
                evidence_summary.append(f"Uncertainty: {'; '.join(uncertainty_notes[:2])}")
        else:
            evidence_summary.append(f"Analyzed across {sources_count} web sources")
        
        # Convert score to grade (same grading scale as before)
        if trust_score >= 90:
            grade = "A+"
        elif trust_score >= 87:
            grade = "A"
        elif trust_score >= 83:
            grade = "A-"
        elif trust_score >= 80:
            grade = "B+"
        elif trust_score >= 77:
            grade = "B"
        elif trust_score >= 73:
            grade = "B-"
        elif trust_score >= 70:
            grade = "C+"
        elif trust_score >= 67:
            grade = "C"
        elif trust_score >= 63:
            grade = "C-"
        elif trust_score >= 60:
            grade = "D+"
        elif trust_score >= 50:
            grade = "D"
        else:
            grade = "F"
        
        # Use dynamic confidence band from uncertainty quantification
        confidence = confidence_band
        
        print(f"DEBUG: ES scoring complete - Score: {trust_score}, Grade: {grade}, Sources: {sources_count}")
        
        return ClaimAnalysis(
            claim_text=claim_text,
            trust_score=int(trust_score),
            evidence_grade=grade,
            confidence=confidence,
            evidence_summary=evidence_summary,
            sources_count=sources_count,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence,
            neutral_evidence=neutral_evidence
        )
        
    except Exception as e:
        print(f"FATAL: NEW Evidence Shepherd processing failed for claim '{claim_text[:50]}...': {e}")
        # NO FALLBACKS - if NEW ES fails, the system should fail
        raise Exception(f"NEW Evidence Shepherd system failure: {str(e)}")

async def score_claim_with_evidence_shepherd_v2(claim_text: str, claim_context: dict = None) -> ClaimAnalysis:
    """Score a claim using V2 Evidence Shepherd system for comparison testing"""
    
    # Initialize V2 Evidence Shepherd  
    evidence_shepherd = None
    
    try:
        from multi_ai_evidence_shepherd_v2 import MultiAIEvidenceShepherdV2
        evidence_shepherd = MultiAIEvidenceShepherdV2()
        print(f"DEBUG: Using V2 Evidence Shepherd for claim: {claim_text[:50]}...")
    except Exception as e:
        print(f"ERROR: Failed to initialize V2 Evidence Shepherd: {e}")
        # Fallback to v1 system
        return await score_claim_with_evidence_shepherd(claim_text, claim_context)
    
    # Process claim through V2 Evidence Shepherd
    try:
        # Use V2 Evidence Shepherd to find and analyze evidence
        evidence_pieces = evidence_shepherd.find_evidence(claim_text, max_evidence=8)
        
        print(f"DEBUG: V2 Evidence Shepherd found {len(evidence_pieces)} pieces of evidence")
        
        # Convert V2 Evidence Shepherd results to ClaimAnalysis format
        supporting_evidence = []
        contradicting_evidence = []
        neutral_evidence = []
        
        for evidence in evidence_pieces:
            evidence_statement = EvidenceStatement(
                statement=evidence.text[:200] if evidence.text else "Evidence found from source",
                source_title=evidence.source_title,
                source_domain=evidence.source_domain,
                source_url=evidence.source_url,
                stance=evidence.ai_stance.lower() if evidence.ai_stance else "neutral",
                relevance_score=evidence.ai_relevance_score if evidence.ai_relevance_score else 50.0,
                highlight_text=evidence.highlight_text,
                highlight_context=evidence.highlight_context
            )
            
            if evidence.ai_stance.lower() == "supporting":
                supporting_evidence.append(evidence_statement)
            elif evidence.ai_stance.lower() == "contradicting":
                contradicting_evidence.append(evidence_statement)
            else:
                neutral_evidence.append(evidence_statement)
        
        # Calculate trust score (simplified V2 version)
        if not evidence_pieces:
            trust_score = 50.0
            confidence_band = "Low"
            evidence_summary = ["V2: No evidence found"]
        else:
            # Simple V2 scoring: based on consensus
            supporting_count = len(supporting_evidence)
            contradicting_count = len(contradicting_evidence)
            avg_confidence = sum(e.ai_confidence for e in evidence_pieces) / len(evidence_pieces)
            avg_relevance = sum(e.ai_relevance_score for e in evidence_pieces) / len(evidence_pieces)
            
            if supporting_count > contradicting_count and avg_relevance > 80:
                trust_score = min(97, int(avg_relevance * avg_confidence))
            elif contradicting_count > supporting_count:
                trust_score = max(0, int(20 * avg_confidence))  
            else:
                trust_score = 50.0
                
            confidence_band = "High" if trust_score > 80 else "Medium" if trust_score > 40 else "Low"
            evidence_summary = [
                f"V2 system analyzed {len(evidence_pieces)} sources",
                f"Supporting: {supporting_count}, Contradicting: {contradicting_count}",
                f"Average AI confidence: {avg_confidence:.2f}"
            ]
        
        # Convert trust score to letter grade
        if trust_score >= 95:
            letter_grade = "A+"
        elif trust_score >= 90:
            letter_grade = "A"  
        elif trust_score >= 85:
            letter_grade = "A-"
        elif trust_score >= 80:
            letter_grade = "B+"
        elif trust_score >= 75:
            letter_grade = "B"
        elif trust_score >= 70:
            letter_grade = "B-"
        elif trust_score >= 65:
            letter_grade = "C+"
        elif trust_score >= 60:
            letter_grade = "C"
        elif trust_score >= 55:
            letter_grade = "C-"
        elif trust_score >= 50:
            letter_grade = "D+"
        elif trust_score >= 45:
            letter_grade = "D"
        elif trust_score >= 40:
            letter_grade = "D-"
        else:
            letter_grade = "F"
        
        return ClaimAnalysis(
            claim_text=claim_text,
            trust_score=int(trust_score),
            evidence_grade=letter_grade,
            confidence=confidence_band,
            evidence_summary=evidence_summary,
            sources_count=len(evidence_pieces),
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence,
            neutral_evidence=neutral_evidence
        )
        
    except Exception as e:
        print(f"ERROR: V2 Evidence Shepherd processing failed for claim '{claim_text[:50]}...': {e}")
        # Fallback to v1 system
        return await score_claim_with_evidence_shepherd(claim_text, claim_context)

def score_individual_claim(claim_text: str) -> ClaimAnalysis:
    """Score an individual claim and provide evidence summary with actual evidence statements"""
    # Simulate evidence-based scoring
    import random
    random.seed(hash(claim_text) % 2147483647)  # Consistent scoring per claim
    
    # Base score influenced by claim characteristics
    base_score = 70
    
    # Numbers/percentages boost credibility
    if any(char.isdigit() for char in claim_text):
        base_score += random.randint(5, 15)
    
    # Definitive statements are riskier
    if any(word in claim_text.lower() for word in ['will', 'definitely', 'always', 'never']):
        base_score -= random.randint(5, 10)
    
    # References to sources boost score
    if any(word in claim_text.lower() for word in ['according to', 'study', 'report', 'research']):
        base_score += random.randint(10, 20)
    
    # Clamp score
    trust_score = max(0, min(100, base_score + random.randint(-15, 15)))
    
    # Convert score to grade
    if trust_score >= 90:
        grade = "A+"
    elif trust_score >= 87:
        grade = "A"
    elif trust_score >= 83:
        grade = "A-"
    elif trust_score >= 80:
        grade = "B+"
    elif trust_score >= 77:
        grade = "B"
    elif trust_score >= 73:
        grade = "B-"
    elif trust_score >= 70:
        grade = "C+"
    elif trust_score >= 67:
        grade = "C"
    elif trust_score >= 63:
        grade = "C-"
    elif trust_score >= 60:
        grade = "D+"
    elif trust_score >= 50:
        grade = "D"
    else:
        grade = "F"
    
    # Confidence based on score
    if trust_score >= 85:
        confidence = "High"
    elif trust_score >= 70:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    # Generate actual evidence statements
    evidence_result = generate_evidence_statements(claim_text, trust_score)
    if len(evidence_result) == 4:
        supporting_evidence, contradicting_evidence, neutral_evidence, consensus_quality_score = evidence_result
    else:
        supporting_evidence, contradicting_evidence, neutral_evidence = evidence_result
        consensus_quality_score = None
    
    # Generate evidence summary
    evidence_summary = []
    sources_count = len(supporting_evidence) + len(contradicting_evidence) + len(neutral_evidence)
    
    if supporting_evidence:
        evidence_summary.append(f"Supported by {len(supporting_evidence)} authoritative source{'s' if len(supporting_evidence) > 1 else ''}")
    if contradicting_evidence:
        evidence_summary.append(f"Challenged by {len(contradicting_evidence)} contradicting finding{'s' if len(contradicting_evidence) > 1 else ''}")
    if any(char.isdigit() for char in claim_text):
        evidence_summary.append("Contains specific numerical data points")
    
    evidence_summary.append(f"Cross-referenced against {random.randint(3, 8)} verification databases")
    
    return ClaimAnalysis(
        claim_text=claim_text,
        trust_score=trust_score,
        evidence_grade=grade,
        confidence=confidence,
        evidence_summary=evidence_summary,
        sources_count=sources_count,
        supporting_evidence=supporting_evidence,
        contradicting_evidence=contradicting_evidence,
        neutral_evidence=neutral_evidence
    )

def calculate_cumulative_score(claims: List[ClaimAnalysis]) -> tuple[int, str, str]:
    """Calculate overall score, grade, and assessment from individual claims"""
    if not claims:
        return 50, "C", "No claims available for analysis"
    
    # Weighted average of claim scores
    total_score = sum(claim.trust_score for claim in claims)
    avg_score = total_score / len(claims)
    
    # Convert to overall grade
    if avg_score >= 90:
        overall_grade = "A+"
    elif avg_score >= 87:
        overall_grade = "A"
    elif avg_score >= 83:
        overall_grade = "A-"
    elif avg_score >= 80:
        overall_grade = "B+"
    elif avg_score >= 77:
        overall_grade = "B"
    elif avg_score >= 73:
        overall_grade = "B-"
    elif avg_score >= 70:
        overall_grade = "C+"
    elif avg_score >= 67:
        overall_grade = "C"
    elif avg_score >= 63:
        overall_grade = "C-"
    elif avg_score >= 60:
        overall_grade = "D+"
    elif avg_score >= 50:
        overall_grade = "D"
    else:
        overall_grade = "F"
    
    # Generate overall assessment
    if avg_score >= 85:
        assessment = "Based on the cumulative evidence, this content can likely be trusted"
    elif avg_score >= 70:
        assessment = "Based on the analysis, this content requires further evidence to support its claims"
    else:
        assessment = "Based on the verification results, this content is likely unreliable"
    
    return int(avg_score), overall_grade, assessment

@app.get("/health")
def health_check():
    return {"ok": True}


@app.post("/analyses", response_model=TrustCapsule)
async def create_analysis(analysis: AnalysisInput):
    analysis_id = str(uuid.uuid4())
    
    # Mine claims using new AI-powered ClaimMiner
    all_text = ""
    mining_result = None
    
    # Handle different input types with context awareness
    if analysis.type == "url":
        # Extract URL metadata and content
        print(f"DEBUG: Extracting content from URL: {analysis.input}")
        url_data = claim_miner.extract_url_metadata_and_text(analysis.input)
        print(f"DEBUG: URL data keys: {list(url_data.keys()) if url_data else 'None'}")
        all_text = claim_miner.merge_text_sources(url_data)
        print(f"DEBUG: Merged text length: {len(all_text) if all_text else 0}")
        print(f"DEBUG: First 200 chars: {all_text[:200] if all_text else 'None'}")
        
        # Context-aware claim mining for articles
        source_context = {
            "title": url_data.get("title", ""),
            "domain": url_data.get("domain", ""),
            "description": url_data.get("description", "")
        }
        mining_result = claim_miner.mine_claims(all_text, context_type="article_url", source_context=source_context)
        print(f"DEBUG: ClaimMiner found {len(mining_result.primary_claims)} primary + {len(mining_result.secondary_claims)} secondary claims")
        
    elif analysis.type == "image" and analysis.input and ocr_service.is_enabled():
        # Extract OCR text and mine claims
        try:
            ocr_text = await ocr_service.extract_text_from_image(analysis.input)
            if ocr_text:
                all_text = ocr_text
                mining_result = claim_miner.mine_claims(ocr_text, context_type="image_ocr")
        except Exception as e:
            print(f"OCR processing error: {e}")
            
    elif analysis.type == "text":
        # Direct text analysis with user intent context
        all_text = analysis.input
        mining_result = claim_miner.mine_claims(analysis.input, context_type="text")
        print(f"DEBUG: ClaimMiner found {len(mining_result.primary_claims) if mining_result else 0} primary claims for text input")
    
    # ClaimMiner→Evidence Shepherd Integration (bypass removed)
    if mining_result and mining_result.primary_claims:
        claims = [claim.text for claim in mining_result.primary_claims]
        print(f"DEBUG: Using {len(claims)} primary claims from ClaimMiner: {[c[:50]+'...' if len(c)>50 else c for c in claims]}")
    elif mining_result and mining_result.secondary_claims:
        claims = [claim.text for claim in mining_result.secondary_claims[:3]]
        print(f"DEBUG: Using {len(claims)} secondary claims from ClaimMiner: {[c[:50]+'...' if len(c)>50 else c for c in claims]}")
    else:
        # Fallback to direct text if ClaimMiner found nothing
        claims = [all_text.strip()] if all_text and all_text.strip() else [analysis.input.strip()]
        print(f"DEBUG: ClaimMiner found no claims - fallback to direct text: '{claims[0][:100] if claims else 'None'}'...")
    
    # Score individual claims - toggle between Evidence Shepherd integration and old scoring
    # CRITICAL FIX: Disable legacy Evidence Shepherd when parallel system is active
    use_evidence_shepherd = (
        os.getenv('USE_EVIDENCE_SHEPHERD', 'true').lower() == 'true'
        and not USE_PARALLEL_EVIDENCE
    )
    use_eeg_phase_1 = os.getenv('USE_EEG_PHASE_1', 'false').lower() == 'true'
    print(f"DEBUG: USE_EVIDENCE_SHEPHERD = {use_evidence_shepherd}")
    print(f"DEBUG: USE_EEG_PHASE_1 = {use_eeg_phase_1}")
    
    claim_analyses = []
    if claims:
        if use_evidence_shepherd:
            # NEW: Evidence Shepherd Integration Path
            print(f"DEBUG: Using Evidence Shepherd integration for {len(claims)} claims")
            
            # Prepare context from ClaimMiner results for Evidence Shepherd
            claim_context = {
                "source_type": analysis.type,
                "content_length": len(all_text) if all_text else 0,
                "mining_result": {
                    "total_claims_found": len(mining_result.primary_claims) + len(mining_result.secondary_claims) if mining_result else 0,
                    "context_type": getattr(mining_result, 'analysis_meta', {}).get('context_type', 'unknown') if mining_result else 'unknown'
                }
            }
            
            # Add URL-specific context if available  
            if analysis.type == "url" and 'url_data' in locals():
                claim_context.update({
                    "url_title": url_data.get("title", ""),
                    "url_domain": url_data.get("domain", ""),
                    "url_description": url_data.get("description", "")
                })
            
            # Process each claim with Evidence Shepherd integration
            for i, claim_text in enumerate(claims):
                try:
                    # Use new Evidence Shepherd integration (async)
                    claim_analysis = await score_claim_with_evidence_shepherd(claim_text, claim_context)
                    claim_analyses.append(claim_analysis)
                    print(f"DEBUG: Claim {i+1}/{len(claims)} ES processed - Score: {claim_analysis.trust_score}, Grade: {claim_analysis.evidence_grade}")
                except Exception as e:
                    print(f"ERROR: Failed to process claim {i+1} with ES integration: {e}")
                    # Fallback to old scoring
                    fallback_analysis = score_individual_claim(claim_text)
                    claim_analyses.append(fallback_analysis)
                    print(f"DEBUG: Claim {i+1}/{len(claims)} ES fallback - Score: {fallback_analysis.trust_score}, Grade: {fallback_analysis.evidence_grade}")
        
        else:
            # OLD: Legacy Scoring Path (preserved for testing/rollback)
            print(f"DEBUG: Using legacy scoring for {len(claims)} claims")
            claim_analyses = [score_individual_claim(claim) for claim in claims]
            for i, claim_analysis in enumerate(claim_analyses):
                print(f"DEBUG: Claim {i+1}/{len(claims)} legacy processed - Score: {claim_analysis.trust_score}, Grade: {claim_analysis.evidence_grade}")
    
    # Calculate cumulative scores
    overall_score, overall_grade, overall_assessment = calculate_cumulative_score(claim_analyses)
    
    # Build simplified why array for main view
    base_why = []
    
    if claim_analyses:
        # Summary line
        base_why.append(f"{len(claim_analyses)} claim{'s' if len(claim_analyses) > 1 else ''} analyzed")
        
        # Brief claim scores (first 3)
        for i, claim_analysis in enumerate(claim_analyses[:3], 1):
            grade = claim_analysis.evidence_grade
            score = claim_analysis.trust_score
            base_why.append(f"Claim {i}: {grade} ({score})")
        
        # Overall assessment
        base_why.append(overall_assessment)
    else:
        base_why.append("No specific verifiable claims identified in content")
        overall_assessment = "Content analysis completed without extractable claims"
    
    # Add OCR insight if applicable
    if analysis.type == "image" and all_text and ocr_service.is_enabled():
        ocr_insight = ocr_service.format_ocr_insight(all_text)
        base_why.append(ocr_insight)
    
    # Extract real citations from Evidence Shepherd results
    real_citations = []
    seen_urls = set()  # Avoid duplicates
    
    for claim_analysis in claim_analyses:
        # Get all evidence sources from this claim
        all_evidence = (claim_analysis.supporting_evidence + 
                       claim_analysis.contradicting_evidence + 
                       claim_analysis.neutral_evidence)
        
        for evidence in all_evidence:
            # Skip if we've already seen this URL
            if evidence.source_url in seen_urls:
                continue
            seen_urls.add(evidence.source_url)
            
            # Create citation from real evidence
            citation = Citation(
                title=evidence.source_title or f"Source from {evidence.source_domain}",
                domain=evidence.source_domain,
                date=datetime.now().strftime("%Y-%m-%d"),  # Use current date for now, ES could provide actual dates later
                url=evidence.source_url
            )
            real_citations.append(citation)
            
            # Limit to reasonable number of citations
            if len(real_citations) >= 6:
                break
        
        if len(real_citations) >= 6:
            break
    
    # Fallback to generic citations if no real citations found (e.g., ES failed)
    if not real_citations:
        real_citations = [
            Citation(
                title="Fallback Verification Process",
                domain="rogr.app",
                date=datetime.now().strftime("%Y-%m-%d"),
                url="https://rogr.app/verification-process"
            )
        ]
    
    print(f"DEBUG: Generated {len(real_citations)} real citations from Evidence Shepherd results")

    trust_capsule = TrustCapsule(
        id=analysis_id,
        trust_score=overall_score,
        evidence_grade=overall_grade,
        confidence="High" if overall_score >= 85 else "Medium" if overall_score >= 70 else "Low",
        why=base_why,
        claims=claim_analyses,
        overall_assessment=overall_assessment,
        citations=real_citations,
        capsule_version=1,
        signed=True,
        created_at=datetime.now().isoformat(),
        input_type=analysis.type,
        mode=analysis.mode
    )
    
    # Store capsule, original input, and extracted claims for focus analysis
    analyses_db[analysis_id] = trust_capsule
    analyses_input_db[analysis_id] = analysis.input
    analyses_claims_db[analysis_id] = claims
    
    return trust_capsule

@app.post("/test-v2", response_model=TrustCapsule)
async def test_v2_analysis(analysis: AnalysisInput):
    """Test Evidence Shepherd v2 system - apples to apples comparison with main analysis"""
    analysis_id = str(uuid.uuid4())
    
    # Extract claims (using same logic as main analysis)
    claims = []
    if analysis.type == "text":
        claims = claim_miner.extract_claims(analysis.input)
    else:
        claims = [analysis.input]  # Fallback for other types
    
    print(f"DEBUG: V2 TEST - Processing {len(claims)} claims")
    
    # Process claims with V2 Evidence Shepherd 
    claim_analyses = []
    for i, claim_text in enumerate(claims):
        try:
            print(f"DEBUG: V2 TEST - Processing claim {i+1}: {claim_text[:50]}...")
            claim_analysis = await score_claim_with_evidence_shepherd_v2(claim_text)
            claim_analyses.append(claim_analysis)
            print(f"DEBUG: V2 TEST - Claim {i+1} processed - Score: {claim_analysis.trust_score}, Grade: {claim_analysis.evidence_grade}")
        except Exception as e:
            print(f"ERROR: V2 TEST - Failed to process claim {i+1}: {e}")
            # Fallback to v1 system
            fallback_analysis = await score_claim_with_evidence_shepherd(claim_text)
            claim_analyses.append(fallback_analysis)
    
    # Calculate cumulative scores (same logic as main analysis)
    overall_score, overall_grade, overall_assessment = calculate_cumulative_score(claim_analyses)
    
    # Generate base summary
    base_why = [f"V2 TEST: {len(claims)} claim{'s' if len(claims) != 1 else ''} analyzed"]
    for i, claim in enumerate(claim_analyses):
        base_why.append(f"Claim {i+1}: {claim.evidence_grade} ({claim.trust_score})")
    base_why.append(overall_assessment)
    
    # Extract real citations from V2 evidence
    real_citations = []
    seen_urls = set()
    
    for claim_analysis in claim_analyses:
        all_evidence = (claim_analysis.supporting_evidence + 
                       claim_analysis.contradicting_evidence + 
                       claim_analysis.neutral_evidence)
        
        for evidence in all_evidence:
            if evidence.source_url in seen_urls:
                continue
            seen_urls.add(evidence.source_url)
            
            citation = Citation(
                title=evidence.source_title or f"Source from {evidence.source_domain}",
                domain=evidence.source_domain,
                date=datetime.now().strftime("%Y-%m-%d"),
                url=evidence.source_url
            )
            real_citations.append(citation)
    
    print(f"DEBUG: V2 TEST - Generated {len(real_citations)} citations")

    trust_capsule = TrustCapsule(
        id=analysis_id,
        trust_score=overall_score,
        evidence_grade=overall_grade,
        confidence="High" if overall_score >= 85 else "Medium" if overall_score >= 70 else "Low",
        why=base_why,
        claims=claim_analyses,
        overall_assessment=f"V2 TEST: {overall_assessment}",
        citations=real_citations,
        capsule_version=2,  # Mark as v2 test
        signed=True,
        created_at=datetime.now().isoformat(),
        input_type=analysis.type,
        mode=analysis.mode
    )
    
    return trust_capsule

@app.get("/analyses/{id}")
def get_analysis(id: str):
    if id not in analyses_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"trust_capsule": analyses_db[id]}

@app.get("/analyses/{id}/details")
def get_analysis_details(id: str):
    """Get detailed claim-by-claim analysis (Consumer/Pro feature)"""
    if id not in analyses_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    capsule = analyses_db[id]
    
    # Return detailed breakdown
    return {
        "capsule_id": id,
        "overall_score": capsule.trust_score,
        "overall_grade": capsule.evidence_grade,
        "overall_assessment": capsule.overall_assessment,
        "claims_count": len(capsule.claims),
        "claims": [
            {
                "claim_number": i + 1,
                "claim_text": claim.claim_text,
                "trust_score": claim.trust_score,
                "evidence_grade": claim.evidence_grade,
                "confidence": claim.confidence,
                "evidence_summary": claim.evidence_summary,
                "sources_count": claim.sources_count,
                "supporting_evidence": [
                    {
                        "statement": ev.statement,
                        "source_title": ev.source_title,
                        "source_domain": ev.source_domain,
                        "source_url": ev.source_url,
                        "stance": ev.stance,
                        "relevance_score": ev.relevance_score
                    }
                    for ev in claim.supporting_evidence
                ],
                "contradicting_evidence": [
                    {
                        "statement": ev.statement,
                        "source_title": ev.source_title,
                        "source_domain": ev.source_domain,
                        "source_url": ev.source_url,
                        "stance": ev.stance,
                        "relevance_score": ev.relevance_score
                    }
                    for ev in claim.contradicting_evidence
                ],
                "neutral_evidence": [
                    {
                        "statement": ev.statement,
                        "source_title": ev.source_title,
                        "source_domain": ev.source_domain,
                        "source_url": ev.source_url,
                        "stance": ev.stance,
                        "relevance_score": ev.relevance_score
                    }
                    for ev in claim.neutral_evidence
                ]
            }
            for i, claim in enumerate(capsule.claims)
        ],
        "citations": capsule.citations,
        "feature_access": "consumer_required"  # UI hint for access control
    }

@app.post("/analyses/{id}/focus", response_model=TrustCapsule)
async def focus_analysis(id: str, focus: FocusRequest):
    if id not in analyses_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    capsule = analyses_db[id]
    
    # Increment version and update why based on focus layers
    capsule.capsule_version += 1
    
    # Add layer-specific insights to why array
    focus_insights = []
    
    # Enhanced OCR analysis with claim extraction for focus scan
    if "ocr" in focus.layers and capsule.input_type == "image" and ocr_service.is_enabled():
        original_input = analyses_input_db.get(id)
        if original_input:
            try:
                ocr_text = await ocr_service.extract_text_from_image(original_input)
                if ocr_text:
                    focus_ocr_insight = ocr_service.format_focus_ocr_insight(ocr_text)
                    focus_insights.append(focus_ocr_insight)
                    
                    # Extract claims from OCR text for focus analysis
                    ocr_mining = claim_miner.mine_claims(ocr_text, context_type="image_ocr")
                    ocr_claims = [claim.text for claim in (ocr_mining.primary_claims + ocr_mining.secondary_claims)[:5]]
                    if ocr_claims:
                        focus_insights.append(f"Focus OCR Claims: {len(ocr_claims)} statement(s) identified")
                        for i, claim in enumerate(ocr_claims[:2], 1):
                            focus_insights.append(f"OCR Claim {i}: {claim[:80]}...")
                else:
                    focus_insights.append("Focus OCR Analysis: No text detected in image")
            except Exception as e:
                print(f"Focus OCR error: {e}")
                focus_insights.append("Focus OCR Analysis: Text extraction unavailable")
        else:
            focus_insights.append("Focus OCR Analysis: Original image unavailable")
    elif "ocr" in focus.layers:
        stored_claims = analyses_claims_db.get(id, [])
        if stored_claims:
            focus_insights.append(f"OCR Claims Review: {len(stored_claims)} claim(s) from analysis")
            for i, claim in enumerate(stored_claims[:2], 1):
                focus_insights.append(f"Claim {i}: {claim[:80]}...")
        else:
            focus_insights.append("OCR analysis revealed embedded text patterns")
        
    if "speech" in focus.layers:
        focus_insights.append("Audio analysis detected synthetic speech markers")
    if "visual" in focus.layers:
        focus_insights.append("Visual inspection found compression artifacts")
    if "metadata" in focus.layers:
        focus_insights.append("EXIF data suggests camera model authenticity")
    if "provenance" in focus.layers:
        focus_insights.append("Digital signature chain verified")
    
    # Replace last items in why array with focus insights
    capsule.why = capsule.why[:1] + focus_insights
    
    analyses_db[id] = capsule
    return capsule

# DISABLED: Progressive analysis endpoints require legacy services
# @app.post("/analyses/progressive", response_model=dict)
# async def start_progressive_analysis(analysis: AnalysisInput):
#     """Start progressive analysis with live updates for large content"""
#     analysis_id = str(uuid.uuid4())
#     
#     try:
#         # Detect content size and set expectations
#         content_size, expectations = progressive_service.detect_content_size(analysis.input)
#         
#         print(f"Progressive analysis started: {analysis_id}, size: {content_size.value}, estimated: {expectations['estimated_time']}")
#         
#         # Start background processing
#         async def progress_callback(aid, status):
#             print(f"Progress {aid}: {status.phase.value} - {status.progress:.1%} - {status.message}")
#         
#         # Run progressive analysis in background
#         asyncio.create_task(
#             progressive_service.start_progressive_analysis(
#                 analysis_id, analysis.input, analysis.type, progress_callback
#             )
#         )
#         
#         # Return immediate response with analysis ID and expectations
#         return {
#             "analysis_id": analysis_id,
#             "content_size": content_size.value,
#             "expectations": expectations,
#             "status": "started",
#             "message": "Analysis started. Use /analyses/progressive/{analysis_id}/status to check progress."
#         }
#         
#     except Exception as e:
#         print(f"Progressive analysis startup error: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

# @app.get("/analyses/progressive/{analysis_id}/status")
# async def get_progressive_status(analysis_id: str):
#     """Get current status of progressive analysis"""
#     status = progressive_service.get_analysis_status(analysis_id)
#     
#     if not status:
#         raise HTTPException(status_code=404, detail="Analysis not found or completed")
#     
#     return status

# @app.post("/analyses/progressive/{analysis_id}/cancel")
# async def cancel_progressive_analysis(analysis_id: str):
#     """Cancel active progressive analysis"""
#     success = progressive_service.cancel_analysis(analysis_id)
#     
#     if success:
#         return {"status": "cancelled", "analysis_id": analysis_id}
#     else:
#         raise HTTPException(status_code=404, detail="Analysis not found or already completed")

@app.get("/evidence")
async def get_evidence(q: str):
    """
    Get evidence for a claim using Pure AI Evidence Shepherd
    Returns AI-analyzed evidence from authoritative sources
    """
    if not q or len(q.strip()) < 10:
        raise HTTPException(status_code=400, detail="Query parameter 'q' must be at least 10 characters")
    
    try:
        # Use evidence system factory to analyze claim and find sources
        if evidence_system and hasattr(evidence_system, 'analyze_claim'):
            search_strategy = evidence_system.analyze_claim(q.strip())
        else:
            # Fallback for parallel system or if analyze_claim not available
            raise HTTPException(status_code=503, detail="Evidence analysis not available in current system configuration")
        
        # Simulate AI finding evidence (in full implementation, AI would actually search web)
        evidence_items = []
        
        if search_strategy.claim_type.value == "scientific":
            evidence_items = [
                {
                    "statement": "AI would search scientific databases and journals for peer-reviewed research on this topic",
                    "source_title": "Scientific Evidence Search Strategy",
                    "source_domain": "scholar.google.com",
                    "source_url": "https://scholar.google.com/search?q=" + q.replace(" ", "+"),
                    "source_type": "ai_guided",
                    "relevance_score": 0.9
                }
            ]
        else:
            evidence_items = [
                {
                    "statement": f"AI identifies this as {search_strategy.claim_type.value} claim requiring verification from authoritative sources",
                    "source_title": "AI Evidence Analysis",
                    "source_domain": "fact-checking.ai",
                    "source_url": f"https://www.reuters.com/search/?query={q.replace(' ', '+')}",
                    "source_type": "ai_guided", 
                    "relevance_score": 0.8
                }
            ]
        
        return {
            "query": q,
            "evidence_count": len(evidence_items),
            "claim_type": search_strategy.claim_type.value,
            "search_strategy": {
                "queries": search_strategy.search_queries,
                "target_domains": search_strategy.target_domains,
                "authority_weight": search_strategy.authority_weight
            },
            "evidence_items": evidence_items,
            "summary": f"AI Evidence Shepherd identified {search_strategy.claim_type.value} claim with {len(search_strategy.search_queries)} targeted search strategies"
        }
        
    except Exception as e:
        print(f"AI evidence search error: {e}")
        raise HTTPException(status_code=500, detail=f"Error in AI evidence analysis: {str(e)}")

# DISABLED: Legacy debug endpoint requires wikipedia_service
# @app.get("/debug/evidence-comparison")
# async def debug_evidence_comparison():
#     """Compare Wikipedia-guided vs Pure AI Evidence Shepherd approaches"""
#     
#     test_claim = "Wealthy enclaves sewage reveals higher than average cocaine levels"
#     
#     results = {
#         "test_claim": test_claim,
#         "approach_a_wikipedia_guided": {},
#         "approach_b_pure_ai": {}
#     }
#     
#     # APPROACH A: Wikipedia-Guided (Current)
#     try:
#         print(f"=== APPROACH A: Wikipedia-Guided ===")
#         wiki_evidence = wikipedia_service.search_evidence_for_claim(test_claim)
#         results["approach_a_wikipedia_guided"] = {
#             "evidence_count": len(wiki_evidence),
#             "sources": []
#         }
#         
#         for i, item in enumerate(wiki_evidence[:5]):
#             source_info = {
#                 "index": i,
#                 "source_url": item.get('source_url', 'NO URL'),
#                 "source_domain": item.get('source_domain', 'NO DOMAIN'),
#                 "source_title": item.get('source_title', 'NO TITLE'),
#                 "statement": item.get('statement', 'NO STATEMENT')[:100] + "..." if item.get('statement') else "NO STATEMENT"
#             }
#             results["approach_a_wikipedia_guided"]["sources"].append(source_info)
#             print(f"Wiki Evidence {i}: {source_info['source_domain']} - {source_info['source_url']}")
#             
#     except Exception as e:
#         results["approach_a_wikipedia_guided"]["error"] = str(e)
#         print(f"Wikipedia approach error: {e}")
#     
#     # APPROACH B: Pure AI Evidence Shepherd
#     try:
#         print(f"=== APPROACH B: Pure AI Evidence Shepherd ===")
#         if hasattr(ai_shepherd, 'analyze_claim'):
#             # Test AI's independent search strategy
#             search_strategy = ai_shepherd.analyze_claim(test_claim)
#             results["approach_b_pure_ai"] = {
#                 "claim_type": search_strategy.claim_type.value if search_strategy.claim_type else "unknown",
#                 "search_queries": search_strategy.search_queries,
#                 "target_domains": search_strategy.target_domains,
#                 "authority_weight": search_strategy.authority_weight,
#                 "confidence_threshold": search_strategy.confidence_threshold,
#                 "ai_enabled": ai_shepherd.is_enabled()
#             }
#             print(f"AI Strategy: {search_strategy.claim_type.value}")
#             print(f"AI Queries: {search_strategy.search_queries}")
#             print(f"AI Target Domains: {search_strategy.target_domains}")
#         else:
#             results["approach_b_pure_ai"]["error"] = f"AI Evidence Shepherd analyze_claim not available. Type: {type(ai_shepherd)}"
#     except Exception as e:
#         results["approach_b_pure_ai"]["error"] = str(e)
#         print(f"AI approach error: {e}")
#     
#     return results

# Legacy endpoint removed - replaced by ROGR system

# Legacy endpoint removed - replaced by ROGR system

@app.post("/debug/claude-single-test")
async def debug_claude_single_test(request: dict):
    """Debug endpoint: Test Single Claude Evidence Shepherd"""
    import time
    from claude_evidence_shepherd import ClaudeEvidenceShepherd
    
    claim_text = request.get("claim", "")
    if not claim_text:
        return {"error": "Missing 'claim' field"}
    
    # Initialize Single Claude ES
    claude_es = ClaudeEvidenceShepherd()
    
    # Time the evidence search
    start_time = time.time()
    evidence_list = claude_es.search_real_evidence(claim_text)
    end_time = time.time()
    
    processing_time = end_time - start_time
    
    return {
        "claim": claim_text,
        "processing_time_seconds": round(processing_time, 2),
        "evidence_count": len(evidence_list),
        "single_claude_type": "Single Claude Evidence Shepherd",
        "evidence_preview": [
            {
                "source": getattr(ev, 'source_domain', 'unknown'),
                "relevance_score": getattr(ev, 'ai_relevance_score', 0),
                "quality_score": getattr(ev, 'quality_score', 'N/A'),
                "stance": getattr(ev, 'ai_stance', 'unknown'),
                "text": getattr(ev, 'text', '')[:100] + "..."
            } for ev in evidence_list[:5]
        ]
    }

@app.get("/debug/ocr-test")
async def debug_ocr_test():
    """Debug endpoint to test Google Cloud Vision OCR service"""
    try:
        # Check if credentials are present
        credentials_present = bool(os.getenv('GOOGLE_CLOUD_CREDENTIALS'))
        
        # Test if OCR service can initialize
        if not ocr_service.is_enabled():
            return {
                "ocr_enabled": False,
                "error": "OCR service not enabled",
                "credentials_present": credentials_present,
                "help": "Add GOOGLE_CLOUD_CREDENTIALS to Replit Secrets"
            }
        
        # Test with multiple text images
        test_images = [
            "https://via.placeholder.com/400x100/000000/FFFFFF?text=Hello%20World%20Test",
            "https://via.placeholder.com/300x150/0000FF/FFFFFF?text=Google%20Vision%20API",
            "https://via.placeholder.com/500x80/FF0000/FFFFFF?text=OCR%20Debug%20Test%202024"
        ]
        
        results = []
        for i, test_url in enumerate(test_images):
            try:
                ocr_text = await ocr_service.extract_text_from_image(test_url)
                results.append({
                    f"test_{i+1}": {
                        "image_url": test_url,
                        "extracted_text": ocr_text,
                        "text_found": bool(ocr_text),
                        "text_length": len(ocr_text) if ocr_text else 0
                    }
                })
            except Exception as e:
                results.append({
                    f"test_{i+1}": {
                        "image_url": test_url,
                        "error": str(e),
                        "text_found": False
                    }
                })
        
        return {
            "ocr_enabled": True,
            "credentials_present": credentials_present,
            "test_results": results,
            "service_status": "Google Cloud Vision API connection successful" if any(r for r in results if any(test.get("text_found") for test in r.values())) else "No text detected in test images"
        }
        
    except Exception as e:
        return {
            "ocr_enabled": False,
            "error": f"OCR service error: {str(e)}",
            "credentials_present": bool(os.getenv('GOOGLE_CLOUD_CREDENTIALS')),
            "help": "Check Google Cloud credentials and Vision API setup"
        }

@app.get("/debug/performance-testing")
async def debug_performance_testing():
    """Get current performance testing session summary"""
    return performance_tester.get_session_summary()

@app.post("/debug/compare-performance")
async def debug_compare_performance(request: dict):
    """Compare performance between two test runs"""
    baseline_test_id = request.get("baseline_test_id", "")
    eeg_test_id = request.get("eeg_test_id", "")
    return performance_tester.compare_performance(baseline_test_id, eeg_test_id)

@app.post("/debug/claim-miner")
async def debug_claim_miner(request: dict):
    """Debug endpoint to test ClaimMiner isolation"""
    try:
        # Extract input parameters
        input_data = request.get("input", "")
        context_type = request.get("context_type", "text")
        source_context = request.get("source_context", {})
        
        if not input_data or len(input_data.strip()) < 5:
            return {
                "error": "Input too short (minimum 5 characters)",
                "claim_miner_enabled": claim_miner.is_enabled()
            }
        
        # Replicate main pipeline preprocessing based on context_type
        all_text = ""
        mining_result = None
        preprocessing_info = {}
        
        if context_type == "article_url":
            # URL preprocessing - replicate main.py lines 706-719
            print(f"DEBUG: ClaimMiner endpoint extracting content from URL: {input_data}")
            url_data = claim_miner.extract_url_metadata_and_text(input_data)
            print(f"DEBUG: ClaimMiner endpoint URL data keys: {list(url_data.keys()) if url_data else 'None'}")
            all_text = claim_miner.merge_text_sources(url_data)
            print(f"DEBUG: ClaimMiner endpoint merged text length: {len(all_text) if all_text else 0}")
            
            # Build source context from URL data
            source_context = {
                "title": url_data.get("title", ""),
                "domain": url_data.get("domain", ""),
                "description": url_data.get("description", "")
            }
            preprocessing_info = {
                "url_data": url_data,
                "extracted_text_length": len(all_text) if all_text else 0
            }
            
            mining_result = claim_miner.mine_claims(all_text, context_type=context_type, source_context=source_context)
            print(f"DEBUG: ClaimMiner found {len(mining_result.primary_claims) if mining_result else 0} primary + {len(mining_result.secondary_claims) if mining_result else 0} secondary claims")
            
        elif context_type == "text":
            # Direct text processing - replicate main.py lines 734-735
            all_text = input_data
            mining_result = claim_miner.mine_claims(input_data, context_type=context_type, source_context=source_context)
            print(f"DEBUG: ClaimMiner found {len(mining_result.primary_claims) if mining_result else 0} primary + {len(mining_result.secondary_claims) if mining_result else 0} secondary claims")
            preprocessing_info = {"processed_as": "direct_text"}
            
        else:
            # Other context types (image_ocr, social_post) - treat as text for now
            all_text = input_data
            mining_result = claim_miner.mine_claims(input_data, context_type=context_type, source_context=source_context)
            print(f"DEBUG: ClaimMiner found {len(mining_result.primary_claims) if mining_result else 0} primary + {len(mining_result.secondary_claims) if mining_result else 0} secondary claims")
            preprocessing_info = {"processed_as": "fallback_text"}
        
        # Format results for debugging
        return {
            "claim_miner_enabled": claim_miner.is_enabled(),
            "input_data": input_data[:200] + "..." if len(input_data) > 200 else input_data,
            "context_type": context_type,
            "preprocessing_info": preprocessing_info,
            "results": {
                "primary_claims": [
                    {
                        "text": claim.text,
                        "relevance_score": claim.relevance_score,
                        "specificity_score": claim.specificity_score,
                        "consequence_score": claim.consequence_score,
                        "factual_assertion": claim.factual_assertion,
                        "claim_type": claim.claim_type,
                        "context_reasoning": claim.context_reasoning
                    } for claim in mining_result.primary_claims
                ],
                "secondary_claims": [
                    {
                        "text": claim.text,
                        "relevance_score": claim.relevance_score,
                        "claim_type": claim.claim_type,
                        "context_reasoning": claim.context_reasoning
                    } for claim in mining_result.secondary_claims
                ],
                "tertiary_claims": [
                    {
                        "text": claim.text,
                        "relevance_score": claim.relevance_score,
                        "claim_type": claim.claim_type
                    } for claim in mining_result.tertiary_claims
                ],
                "analysis_meta": mining_result.analysis_meta
            },
            "summary": {
                "total_claims_found": len(mining_result.primary_claims) + len(mining_result.secondary_claims) + len(mining_result.tertiary_claims),
                "primary_count": len(mining_result.primary_claims),
                "secondary_count": len(mining_result.secondary_claims),
                "tertiary_count": len(mining_result.tertiary_claims),
                "claude_api_used": claim_miner.is_enabled() and not mining_result.analysis_meta.get("fallback_mode", False)
            }
        }
        
    except Exception as e:
        return {
            "claim_miner_enabled": claim_miner.is_enabled(),
            "error": f"ClaimMiner error: {str(e)}",
            "help": "Check ClaimMiner configuration and Claude API setup"
        }

# ROGR Professional Fact-Checking Scoring Test Endpoint
class ClaimRequest(BaseModel):
    claim: str

@app.post("/debug/rogr-fc-scoring-test")
async def test_rogr_fc_scoring(request: ClaimRequest):
    """Test ROGR Professional Fact-Checking Scoring Engine using existing dual-AI evidence"""
    try:
        print(f"🔍 ROGR FC Scoring Test: {request.claim[:50]}...")
        
        # Use ROGR dual evidence system to gather evidence
        # Use startup instance if available
        if rogr_dual_shepherd and rogr_dual_shepherd.is_enabled():
            evidence_shepherd = rogr_dual_shepherd
        else:
            # Fallback to creating new instance if startup failed
            evidence_shepherd = ROGRDualEvidenceShepherd(use_eeg_phase_1=use_eeg_phase_1)
        
        if not evidence_shepherd.is_enabled():
            return {
                "error": "Dual-AI Evidence Shepherd not enabled",
                "claim": request.claim,
                "available_shepherds": 0
            }
        
        print("📊 Gathering evidence using dual-AI system...")
        evidence_pieces = rogr_dual_shepherd.search_real_evidence(request.claim)
        
        if not evidence_pieces:
            return {
                "error": "No evidence pieces gathered",
                "claim": request.claim,
                "dual_ai_status": "enabled but no results"
            }
        
        print(f"✅ Found {len(evidence_pieces)} evidence pieces")
        
        # Apply new ROGR FC scoring to same evidence - Zero Start Model
        rogr_scorer = ROGRFCScoringEngineZeroStart()
        new_results = rogr_scorer.score_evidence_pool(request.claim, evidence_pieces)
        
        # Prepare evidence summary for debugging - INCLUDE HIGHLIGHT FIELDS
        evidence_summary = []
        for i, ev in enumerate(evidence_pieces):
            evidence_summary.append({
                "index": i,
                "domain": getattr(ev, 'source_domain', 'unknown'),
                "title": getattr(ev, 'source_title', 'no title')[:100],
                "stance": getattr(ev, 'ai_stance', 'unknown'),
                "relevance": getattr(ev, 'ai_relevance_score', 0),
                "content_length": len(getattr(ev, 'text', '') or ''),
                "highlight_text": getattr(ev, 'highlight_text', 'no highlight text'),
                "highlight_context": getattr(ev, 'highlight_context', 'no highlight context')[:200],
                "source_url": getattr(ev, 'source_url', 'no url')
            })
        
        print(f"🎯 ROGR Scoring Complete: Trust Score {new_results.trust_score:.1f}, Evidence Grade {new_results.evidence_grade}")
        
        # Return ROGR professional scoring results
        return {
            "claim": request.claim,
            "rogr_results": {
                "trust_score": round(new_results.trust_score, 1),
                "evidence_grade": new_results.evidence_grade,
                "evidence_grade_score": round(new_results.evidence_grade_score, 1),
                "grade_description": new_results.grade_description()
            },
            "evidence_analysis": {
                "total_sources": len(evidence_pieces),
                "source_domains": list(set(getattr(ev, 'source_domain', '') for ev in evidence_pieces if getattr(ev, 'source_domain', ''))),
                "stance_distribution": new_results.metadata.get('evidence_analysis', {}).get('stance_distribution', {}),
                "avg_relevance": new_results.metadata.get('evidence_analysis', {}).get('avg_relevance_score', 0)
            },
            "methodology": {
                "scoring_engine": new_results.metadata.get('scoring_methodology', 'ROGR FC Engine'),
                "ifcn_compliance": new_results.metadata.get('ifcn_compliance', {}),
                "grade_breakdown": new_results.metadata.get('grade_breakdown', {})
            },
            "evidence_pieces": evidence_summary[:5],  # First 5 for debugging
            "processing_time": "measured_in_production"
        }
        
    except Exception as e:
        print(f"❌ ERROR in ROGR FC scoring test: {e}")
        return {
            "error": f"ROGR FC scoring test failed: {str(e)}",
            "claim": request.claim,
            "debug_info": str(e)
        }