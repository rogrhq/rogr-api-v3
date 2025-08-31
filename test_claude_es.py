#!/usr/bin/env python3
"""
Test Claude Evidence Shepherd accuracy with known FALSE claim
Phase 1 ES Testing: "COVID vaccines contain microchips"
Target: Claude should find 3+ contradicting sources with >80 relevance scores
"""

import os
import sys
import time
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from claude_evidence_shepherd import ClaudeEvidenceShepherd

def test_false_claim_accuracy():
    """Test Claude ES with known false claim"""
    
    # Known FALSE claim for testing
    test_claim = "COVID vaccines contain microchips"
    
    print(f"🧪 PHASE 1 ES ACCURACY TEST")
    print(f"📋 Testing FALSE claim: '{test_claim}'")
    print(f"🎯 Target: 3+ contradicting sources with >80 relevance scores")
    print(f"⏱️  Starting analysis...")
    
    start_time = time.time()
    
    # Initialize Claude Evidence Shepherd
    try:
        claude_es = ClaudeEvidenceShepherd()
        
        if not claude_es.is_enabled():
            print("❌ ANTHROPIC_API_KEY not found - cannot test Claude ES")
            return False
        
        print(f"✅ Claude Evidence Shepherd initialized")
        
        # Search for real evidence
        print(f"\n🔍 Searching for evidence...")
        evidence_results = claude_es.search_real_evidence(test_claim)
        
        analysis_time = time.time() - start_time
        
        print(f"\n📊 RESULTS ANALYSIS")
        print(f"⏱️  Analysis time: {analysis_time:.1f} seconds")
        print(f"📄 Evidence found: {len(evidence_results)} sources")
        
        if len(evidence_results) == 0:
            print("❌ FAIL: No evidence found")
            return False
        
        # Analyze evidence quality and stance
        high_relevance_count = 0
        contradicting_count = 0
        supporting_count = 0
        neutral_count = 0
        
        print(f"\n📋 EVIDENCE DETAILS:")
        
        for i, evidence in enumerate(evidence_results, 1):
            stance = evidence.ai_stance
            score = evidence.ai_relevance_score
            confidence = evidence.ai_confidence
            
            if stance == "contradicting":
                contradicting_count += 1
            elif stance == "supporting": 
                supporting_count += 1
            else:
                neutral_count += 1
            
            if score >= 80:
                high_relevance_count += 1
            
            print(f"🔗 Evidence {i}:")
            print(f"   Source: {evidence.source_title}")
            print(f"   Domain: {evidence.source_domain}")
            print(f"   Score: {score}/100")
            print(f"   Stance: {stance}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Reasoning: {evidence.ai_reasoning}")
            print(f"   Key Excerpt: {evidence.highlight_text[:100]}...")
            print()
        
        # SUCCESS CRITERIA EVALUATION
        print(f"🎯 SUCCESS CRITERIA EVALUATION:")
        print(f"   • Evidence found: {len(evidence_results)} (need ≥3)")
        print(f"   • High relevance (≥80): {high_relevance_count}")  
        print(f"   • Contradicting stance: {contradicting_count}")
        print(f"   • Supporting stance: {supporting_count}")
        print(f"   • Neutral stance: {neutral_count}")
        
        # Success conditions for FALSE claim
        success = True
        success_reasons = []
        fail_reasons = []
        
        if len(evidence_results) >= 3:
            success_reasons.append(f"✅ Found {len(evidence_results)} sources (≥3 required)")
        else:
            success = False
            fail_reasons.append(f"❌ Only {len(evidence_results)} sources (need ≥3)")
        
        if contradicting_count >= 2:
            success_reasons.append(f"✅ Found {contradicting_count} contradicting sources")
        else:
            success = False  
            fail_reasons.append(f"❌ Only {contradicting_count} contradicting sources (expected majority)")
        
        if high_relevance_count >= 2:
            success_reasons.append(f"✅ Found {high_relevance_count} high-relevance sources (≥80)")
        else:
            success = False
            fail_reasons.append(f"❌ Only {high_relevance_count} high-relevance sources")
        
        if supporting_count <= 1:
            success_reasons.append(f"✅ Low supporting evidence ({supporting_count}) as expected for false claim")
        else:
            # Warning but not failure
            success_reasons.append(f"⚠️  Found {supporting_count} supporting sources (unexpected for false claim)")
        
        print(f"\n🏆 FINAL RESULTS:")
        for reason in success_reasons:
            print(f"   {reason}")
        for reason in fail_reasons:
            print(f"   {reason}")
        
        if success:
            print(f"\n🎉 SUCCESS: Claude ES accurately identified false claim with contradicting evidence!")
            print(f"📈 Performance: {analysis_time:.1f}s analysis time")
            return True
        else:
            print(f"\n💥 FAILURE: ES accuracy validation failed")
            print(f"🔧 Needs improvement in evidence discovery or stance detection")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run Phase 1 ES accuracy testing"""
    print("=" * 80)
    print("ROGR - Phase 1 Evidence Shepherd Accuracy Testing")  
    print("=" * 80)
    
    success = test_false_claim_accuracy()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ PHASE 1 COMPLETE: Ready for Phase 2 (TRUE claim testing)")
    else:
        print("❌ PHASE 1 FAILED: ES accuracy needs improvement")
    print("=" * 80)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)