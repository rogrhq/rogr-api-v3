#!/usr/bin/env python3
"""
Test ClaimMiner implementation with known claims
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_claim_miner_simple():
    """Simple test without Claude API to verify structure"""
    
    from claim_miner import ClaimMiner
    
    miner = ClaimMiner()
    
    test_cases = [
        ("COVID vaccines contain microchips", "text"),
        ("The Earth is flat", "text"),
        ("Biden received 81 million votes in the 2020 election", "text")
    ]
    
    print("🧪 TESTING CLAIM MINER IMPLEMENTATION")
    print("=" * 60)
    
    for i, (test_text, context_type) in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_text}'")
        print(f"   Context: {context_type}")
        
        try:
            # Test claim mining
            result = miner.mine_claims(test_text, context_type=context_type)
            
            print(f"   📊 RESULTS:")
            print(f"     Primary claims: {len(result.primary_claims)}")
            print(f"     Secondary claims: {len(result.secondary_claims)}")
            print(f"     Tertiary claims: {len(result.tertiary_claims)}")
            
            # Show primary claims
            for j, claim in enumerate(result.primary_claims, 1):
                print(f"     Primary {j}: '{claim.text}' (relevance: {claim.relevance_score})")
            
            # Show analysis meta
            if result.analysis_meta:
                print(f"     Meta: {result.analysis_meta}")
            
            # Test legacy compatibility
            legacy_claims = miner.extract_claims(test_text)
            print(f"     Legacy compatibility: {len(legacy_claims)} claims")
            
            success = len(result.primary_claims) > 0 or len(result.secondary_claims) > 0
            print(f"     ✅ SUCCESS" if success else "     ❌ FAILED")
            
        except Exception as e:
            print(f"     ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("CLAIM MINER IMPLEMENTATION TEST COMPLETE")

if __name__ == "__main__":
    test_claim_miner_simple()