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

class TrustCapsule(BaseModel):
    id: str
    trust_score: int
    evidence_grade: str
    confidence: str
    why: List[str]
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
    
    # Build why array starting with claims
    base_why = []
    
    if claims:
        base_why.append(f"Claims identified: {len(claims)} checkable statement{'s' if len(claims) > 1 else ''}")
        for i, claim in enumerate(claims[:3], 1):
            base_why.append(f"Claim {i}: {claim}")
    else:
        base_why.append("No specific verifiable claims identified in content")
    
    # Add OCR insight if applicable
    if analysis.type == "image" and all_text and ocr_service.is_enabled():
        ocr_insight = ocr_service.format_ocr_insight(all_text)
        base_why.append(ocr_insight)
    
    fake_capsule = TrustCapsule(
        id=analysis_id,
        trust_score=85,
        evidence_grade="B+",
        confidence="High",
        why=base_why,
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