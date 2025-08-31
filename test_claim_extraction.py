#!/usr/bin/env python3
"""Test claim extraction service with known claims"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from claim_extraction_service import ClaimExtractionService

def test_claim_extraction():
    """Test claim extraction with various inputs"""
    
    service = ClaimExtractionService()
    
    test_cases = [
        "COVID vaccines contain microchips",
        "The Earth is flat", 
        "Vaccines cause autism",
        "Climate change is a hoax",
        "The moon landing was faked",
        "5G towers cause COVID-19"
    ]
    
    print("🧪 TESTING CLAIM EXTRACTION SERVICE")
    print("=" * 50)
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n{i}. Input: '{test_text}'")
        
        extracted_claims = service.extract_claims(test_text)
        
        print(f"   Extracted: {len(extracted_claims)} claims")
        for j, claim in enumerate(extracted_claims):
            print(f"   Claim {j+1}: '{claim}'")
        
        if len(extracted_claims) == 0:
            print("   ❌ FAILED: No claims extracted")
        else:
            print("   ✅ SUCCESS: Claims extracted")
    
    print("\n" + "=" * 50)
    print("TESTING COMPLETE")

if __name__ == "__main__":
    test_claim_extraction()