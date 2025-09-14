#!/usr/bin/env python3
"""
Test script for Evidence Shepherd v2 system
Run this to verify v2 works before integrating with main system
"""

from multi_ai_evidence_shepherd_v2 import MultiAIEvidenceShepherdV2

def test_basic_claims():
    """Test v2 system with basic claims"""
    
    print("=== EVIDENCE SHEPHERD V2 TEST ===")
    
    # Initialize v2 system
    shepherd_v2 = MultiAIEvidenceShepherdV2()
    
    # Debug info
    debug_info = shepherd_v2.get_debug_info()
    print(f"Debug Info: {debug_info}")
    
    # Test claims
    test_claims = [
        "The sun is a star",
        "The Earth is flat", 
        "COVID vaccines contain microchips"
    ]
    
    for claim in test_claims:
        print(f"\n--- Testing: {claim} ---")
        
        try:
            evidence = shepherd_v2.find_evidence(claim, max_evidence=3)
            
            print(f"Found {len(evidence)} evidence pieces:")
            for i, ev in enumerate(evidence):
                print(f"  [{i+1}] {ev.source_domain}: {ev.ai_stance} "
                      f"(relevance: {ev.ai_relevance_score:.1f}, "
                      f"confidence: {ev.ai_confidence:.2f})")
                print(f"      \"{ev.highlight_text}\"")
        
        except Exception as e:
            print(f"ERROR processing '{claim}': {e}")
    
    print("\n=== V2 TEST COMPLETE ===")

if __name__ == "__main__":
    test_basic_claims()