from typing import Union, List, Optional
from datetime import datetime
import uuid
import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ocr_service import OCRService
from claim_extraction_service import ClaimExtractionService

# Test comment - verifying git push workflow

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

class ClaimAnalysis(BaseModel):
    claim_text: str
    trust_score: int
    evidence_grade: str
    confidence: str
    evidence_summary: List[str]  # Bullet points of evidence
    sources_count: int

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
claim_service = ClaimExtractionService()

# Claim scoring functions
def score_individual_claim(claim_text: str) -> ClaimAnalysis:
    """Score an individual claim and provide evidence summary"""
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
    
    # Generate evidence summary
    evidence_summary = []
    sources_count = random.randint(2, 5)
    
    if 'according to' in claim_text.lower():
        evidence_summary.append("Referenced authoritative source material")
    if any(char.isdigit() for char in claim_text):
        evidence_summary.append("Contains specific numerical data points")
    if trust_score >= 80:
        evidence_summary.append(f"Corroborated by {sources_count} independent sources")
    else:
        evidence_summary.append(f"Limited verification from {sources_count} sources")
    
    if trust_score < 70:
        evidence_summary.append("Conflicting information found in fact-check databases")
    
    evidence_summary.append(f"Cross-referenced against {random.randint(3, 8)} verification databases")
    
    return ClaimAnalysis(
        claim_text=claim_text,
        trust_score=trust_score,
        evidence_grade=grade,
        confidence=confidence,
        evidence_summary=evidence_summary,
        sources_count=sources_count
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
    
    # Extract claims and build analysis
    claims = []
    all_text = ""
    
    # Handle different input types
    if analysis.type == "url":
        # Extract URL metadata and content
        url_data = claim_service.extract_url_metadata_and_text(analysis.input)
        all_text = claim_service.merge_text_sources(url_data)
        claims = claim_service.extract_claims(all_text)
    elif analysis.type == "image" and analysis.input and ocr_service.is_enabled():
        # Extract OCR text and claims
        try:
            ocr_text = await ocr_service.extract_text_from_image(analysis.input)
            if ocr_text:
                all_text = ocr_text
                claims = claim_service.extract_claims(ocr_text)
        except Exception as e:
            print(f"OCR processing error: {e}")
    elif analysis.type == "text":
        # Direct text analysis
        all_text = analysis.input
        claims = claim_service.extract_claims(analysis.input)
    
    # Score individual claims
    claim_analyses = []
    if claims:
        claim_analyses = [score_individual_claim(claim) for claim in claims]
    
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
    
    fake_capsule = TrustCapsule(
        id=analysis_id,
        trust_score=overall_score,
        evidence_grade=overall_grade,
        confidence="High" if overall_score >= 85 else "Medium" if overall_score >= 70 else "Low",
        why=base_why,
        claims=claim_analyses,
        overall_assessment=overall_assessment,
        citations=[
            Citation(
                title="Reuters Fact Check Database",
                domain="reuters.com",
                date="2024-08-15",
                url="https://reuters.com/fact-check/example"
            ),
            Citation(
                title="Associated Press Verification",
                domain="apnews.com", 
                date="2024-08-20",
                url="https://apnews.com/article/verification"
            )
        ],
        capsule_version=1,
        signed=True,
        created_at=datetime.now().isoformat(),
        input_type=analysis.type,
        mode=analysis.mode
    )
    
    # Store capsule, original input, and extracted claims for focus analysis
    analyses_db[analysis_id] = fake_capsule
    analyses_input_db[analysis_id] = analysis.input
    analyses_claims_db[analysis_id] = claims
    
    return fake_capsule

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
                "sources_count": claim.sources_count
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
                    ocr_claims = claim_service.extract_claims(ocr_text)
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