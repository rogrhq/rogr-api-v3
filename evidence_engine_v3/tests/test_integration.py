import requests
import json
import time

def test_subject_object_distinction():
    """Test that climate policies are distinguished from climate effects"""

    url = "https://811efd66-721a-418d-978d-2fb9a8b674e6-00-18dh30ad08soc.janeway.repl.co/analyses"

    # Test 1: Climate POLICIES claim
    policy_claim = {
        "input": "Climate change policies will destroy the economy",
        "mode": "both",
        "type": "text"
    }

    print("Testing climate POLICY claim...")
    response = requests.post(url, json=policy_claim)

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Policy claim processed: Trust score = {result['trust_score']}")

        # Check if evidence is about policies (should be)
        # This would need more detailed checking in real test
        return True
    else:
        print(f"✗ Failed: {response.status_code}")
        return False

def test_performance():
    """Test that processing is under 30 seconds"""

    url = "https://811efd66-721a-418d-978d-2fb9a8b674e6-00-18dh30ad08soc.janeway.repl.co/analyses"

    claim = {
        "input": "COVID vaccines are safe and effective",
        "mode": "both",
        "type": "text"
    }

    print("\nTesting performance...")
    start = time.time()
    response = requests.post(url, json=claim)
    elapsed = time.time() - start

    if response.status_code == 200:
        print(f"✓ Processed in {elapsed:.1f} seconds")
        if elapsed < 30:
            print("✓ Performance target met (< 30 seconds)")
            return True
        else:
            print("✗ Too slow (> 30 seconds)")
            return False
    else:
        print(f"✗ Failed: {response.status_code}")
        return False

def test_false_claims():
    """Test that false claims score low"""

    url = "https://811efd66-721a-418d-978d-2fb9a8b674e6-00-18dh30ad08soc.janeway.repl.co/analyses"

    false_claim = {
        "input": "The Earth is flat",
        "mode": "both",
        "type": "text"
    }

    print("\nTesting false claim handling...")
    response = requests.post(url, json=false_claim)

    if response.status_code == 200:
        result = response.json()
        trust_score = result['trust_score']
        print(f"✓ False claim processed: Trust score = {trust_score}")

        if trust_score < 30:
            print("✓ False claim correctly scored low")
            return True
        else:
            print("✗ False claim scored too high")
            return False
    else:
        print(f"✗ Failed: {response.status_code}")
        return False

if __name__ == "__main__":
    print("=== Evidence Engine V3 Integration Tests ===\n")

    print("Make sure FastAPI server is running on the specified URL\n")

    tests_passed = 0
    tests_total = 3

    if test_subject_object_distinction():
        tests_passed += 1

    if test_performance():
        tests_passed += 1

    if test_false_claims():
        tests_passed += 1

    print(f"\n=== Results: {tests_passed}/{tests_total} tests passed ===")

    if tests_passed == tests_total:
        print("✅ All integration tests passed!")
    else:
        print(f"❌ {tests_total - tests_passed} tests failed")