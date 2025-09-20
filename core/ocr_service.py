import os
import json
import requests
import asyncio
from google.cloud import vision
from google.oauth2 import service_account
from typing import Optional

class OCRService:
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Cloud Vision client if credentials are available"""
        try:
            credentials_json = os.getenv('GOOGLE_CLOUD_CREDENTIALS')
            if not credentials_json:
                print("No GOOGLE_CLOUD_CREDENTIALS found in environment")
                return
            
            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
            print("Google Cloud Vision client initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize Google Cloud Vision client: {e}")
            self.client = None
    
    def is_enabled(self) -> bool:
        """Check if OCR service is properly initialized"""
        return self.client is not None
    
    async def extract_text_from_image(self, image_url: str) -> Optional[str]:
        """Extract text from image URL using Google Cloud Vision API"""
        if not self.is_enabled():
            return None
        
        try:
            # Download image from URL
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image_content = response.content
            
            # Create Vision API image object
            image = vision.Image(content=image_content)
            
            # Perform text detection
            response = self.client.text_detection(image=image)
            texts = response.text_annotations
            
            if response.error.message:
                raise Exception(f'Google Cloud Vision API error: {response.error.message}')
            
            if texts:
                # Return the first (most comprehensive) text annotation
                return texts[0].description.strip()
            
            return None
            
        except Exception as e:
            print(f"OCR extraction error: {e}")
            return None
    
    def format_ocr_insight(self, ocr_text: str) -> str:
        """Format OCR text into a Trust Capsule insight"""
        if not ocr_text:
            return "OCR: No text detected in image"
        
        # Truncate to 100 characters for regular analysis
        snippet = ocr_text[:100]
        if len(ocr_text) > 100:
            snippet += "..."
        
        return f"OCR: {snippet}"
    
    def format_focus_ocr_insight(self, ocr_text: str) -> str:
        """Format OCR text into a Focus analysis insight (longer snippet)"""
        if not ocr_text:
            return "Focus OCR Analysis: No text detected in image"
        
        # Truncate to 150 characters for focus analysis
        snippet = ocr_text[:150]
        if len(ocr_text) > 150:
            snippet += "..."
        
        return f"Focus OCR Analysis: {snippet}"