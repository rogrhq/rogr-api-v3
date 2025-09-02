#!/usr/bin/env python3
"""
Test script to diagnose stance classification issues in MDEQ system
Specifically testing why Johns Hopkins evidence is misclassified as "supporting"
for the claim "Vaccines cause autism"
"""

import asyncio
import json
import httpx
from datetime import datetime

# Backend URL
BACKEND_URL = "https://811efd66-721a-418d-978d-2fb9a8b674e6-00-18dh30ad08soc.janeway.replit.dev"

# Test claims with known expected outcomes
TEST_CLAIMS = [
    {
        "text": "Vaccines cause autism",
        "expected_grade": "F",
        "expected_score_max": 30,
        "description": "Medical misinformation - should find contradicting evidence"
    },
    {
        "text": "The Earth is flat",
        "expected_grade": "F", 
        "expected_score_max": 30,
        "description": "Scientific misinformation - should find contradicting evidence"
    },
    {
        "text": "COVID vaccines contain microchips",
        "expected_grade": "F",
        "expected_score_max": 30,
        "description": "Conspiracy theory - should find contradicting evidence"
    }
]

async def test_claim(claim_data):
    """Test a single claim and return detailed results"""
    print(f"\n{'='*80}")
    print(f"Testing: {claim_data['text']}")
    print(f"Description: {claim_data['description']}")
    print(f"Expected: <{claim_data['expected_score_max']}/{claim_data['expected_grade']}")
    print(f"{'='*80}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Submit analysis
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Submitting claim for analysis...")
        
        response = await client.post(
            f"{BACKEND_URL}/analyses",
            json={
                "input": claim_data["text"],
                "mode": "both",
                "source": "paste", 
                "type": "text"
            }
        )
        
        if response.status_code != 200:
            print(f"ERROR: Failed to submit analysis: {response.status_code}")
            return None
            
        result = response.json()
        analysis_id = result.get("id")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Analysis ID: {analysis_id}")
        
        # Poll for completion
        max_polls = 30
        for i in range(max_polls):
            await asyncio.sleep(2)
            
            poll_response = await client.get(f"{BACKEND_URL}/analyses/{analysis_id}")
            if poll_response.status_code != 200:
                continue
                
            poll_data = poll_response.json()
            status = poll_data.get("status")
            
            if status == "completed":
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Analysis completed in {(i+1)*2} seconds")
                
                # Extract key metrics
                trust_capsule = poll_data.get("trust_capsule", {})
                trust_score = trust_capsule.get("trust_score", 0)
                evidence_grade = trust_capsule.get("evidence_grade", "?")
                why = trust_capsule.get("why", [])
                system_used = trust_capsule.get("system_used", "unknown")
                
                # Get detailed evidence if available
                detail_response = await client.get(f"{BACKEND_URL}/analyses/{analysis_id}/details")
                evidence_details = {}
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    evidence_details = detail_data.get("evidence", {})
                
                # Analyze results
                print(f"\n📊 RESULTS:")
                print(f"  Score: {trust_score}/{evidence_grade}")
                print(f"  System: {system_used}")
                print(f"  Pass/Fail: {'✅ PASS' if trust_score <= claim_data['expected_score_max'] else '❌ FAIL'}")
                
                print(f"\n📝 Evidence Summary:")
                for reason in why[:3]:
                    print(f"  - {reason}")
                
                # Check for evidence classification
                if evidence_details:
                    print(f"\n🔍 Evidence Classification Analysis:")
                    
                    # Look for Johns Hopkins or similar authoritative medical sources
                    supporting_count = 0
                    contradicting_count = 0
                    
                    for claim_key, claim_evidence in evidence_details.items():
                        if isinstance(claim_evidence, dict):
                            supporting = claim_evidence.get("supporting_evidence", [])
                            contradicting = claim_evidence.get("contradicting_evidence", [])
                            
                            supporting_count += len(supporting)
                            contradicting_count += len(contradicting)
                            
                            # Check for misclassified medical evidence
                            for evidence in supporting:
                                if any(domain in evidence.get("source_domain", "").lower() 
                                      for domain in ["hopkins", "cdc", "who", "nih", "mayo"]):
                                    print(f"  ⚠️ WARNING: Medical source classified as SUPPORTING!")
                                    print(f"     Source: {evidence.get('source_title', 'Unknown')}")
                                    print(f"     Domain: {evidence.get('source_domain', 'Unknown')}")
                                    print(f"     Text: {evidence.get('text', '')[:200]}...")
                                    print(f"     Stance: {evidence.get('stance', 'unknown')}")
                    
                    print(f"\n  Total Evidence Count:")
                    print(f"    Supporting: {supporting_count}")
                    print(f"    Contradicting: {contradicting_count}")
                    
                    if supporting_count > contradicting_count and claim_data['expected_score_max'] == 30:
                        print(f"  ⚠️ STANCE ISSUE: More supporting than contradicting for false claim!")
                
                return {
                    "claim": claim_data["text"],
                    "score": trust_score,
                    "grade": evidence_grade,
                    "passed": trust_score <= claim_data["expected_score_max"],
                    "system": system_used,
                    "evidence_balance": f"{supporting_count}S/{contradicting_count}C" if evidence_details else "N/A"
                }
            
            elif status == "failed":
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Analysis failed")
                return None
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Analysis timed out")
        return None

async def main():
    """Run all tests and generate summary report"""
    print(f"\n{'='*80}")
    print(f"MDEQ STANCE CLASSIFICATION DIAGNOSTIC TEST")
    print(f"Backend: {BACKEND_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    results = []
    for claim_data in TEST_CLAIMS:
        result = await test_claim(claim_data)
        if result:
            results.append(result)
        await asyncio.sleep(5)  # Delay between tests to avoid rate limiting
    
    # Generate summary report
    print(f"\n{'='*80}")
    print(f"SUMMARY REPORT")
    print(f"{'='*80}")
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
    print(f"\nDetailed Results:")
    print(f"{'Claim':<40} {'Score':<10} {'Grade':<8} {'Evidence':<12} {'Status':<10}")
    print(f"{'-'*80}")
    
    for result in results:
        claim_short = result["claim"][:37] + "..." if len(result["claim"]) > 40 else result["claim"]
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{claim_short:<40} {result['score']:<10} {result['grade']:<8} {result['evidence_balance']:<12} {status:<10}")
    
    # Identify patterns
    print(f"\n🔍 Pattern Analysis:")
    if any(not r["passed"] for r in results):
        print(f"  - Stance classification issues detected")
        print(f"  - Evidence balance may be inverted for false claims")
        print(f"  - Medical/scientific sources possibly misclassified")
    else:
        print(f"  - All tests passed! Stance classification working correctly")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())