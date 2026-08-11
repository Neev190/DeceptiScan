#!/usr/bin/env python3
"""
Focused JWT Test - Verify both routes handle JWT consistently

This test:
1. First creates a valid analysis via /analyze
2. Tests both routes with various JWT states using valid data
3. Focuses on JWT validation behavior specifically
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000/api/v1"
MALFORMED_TOKEN = "malformed.jwt.token"
EXPIRED_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYwMDAwMDAwMCwianRpIjoiZXhwaXJlZC10b2tlbiIsInR5cGUiOiJhY2Nlc3MiLCJzdWIiOiJ0ZXN0LXVzZXIiLCJuYmYiOjE2MDAwMDAwMDAsImV4cCI6MTYwMDAwMDEwMH0.invalid"

def test_request(url, method="POST", data=None, token=None):
    """Make a test request and return structured result."""
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=15)
        else:
            response = requests.get(url, headers=headers, timeout=15)
        
        try:
            json_data = response.json()
        except:
            json_data = {"raw_response": response.text}
        
        return {
            "status": response.status_code,
            "data": json_data,
            "success": 200 <= response.status_code < 300
        }
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "data": {"error": "Request timed out"}, "success": False}
    except Exception as e:
        return {"status": "ERROR", "data": {"error": str(e)}, "success": False}

def main():
    print("🎯 Focused JWT Consistency Test")
    print("=" * 50)
    
    # Step 1: Create a valid analysis to get an analysis ID
    print("📝 Step 1: Creating a valid analysis...")
    analyze_data = {"content": "This is test content for JWT consistency testing."}
    
    create_result = test_request(f"{BASE_URL}/analyze", "POST", analyze_data)
    
    if not create_result["success"]:
        print(f"❌ Failed to create analysis: {create_result}")
        return False
    
    analysis_id = create_result["data"].get("id")
    if not analysis_id:
        print(f"❌ No analysis ID returned: {create_result['data']}")
        return False
    
    print(f"✅ Created analysis: {analysis_id}")
    print()
    
    # Step 2: Test JWT handling consistency
    print("🔍 Step 2: Testing JWT handling consistency")
    print("-" * 40)
    
    feedback_data = {
        "analysisId": analysis_id,
        "feedback": {"type": "helpful", "comment": "Test feedback"}
    }
    
    jwt_test_cases = [
        ("No Token", None),
        ("Malformed Token", MALFORMED_TOKEN), 
        ("Expired Token", EXPIRED_TOKEN),
        ("Empty Bearer", ""),
    ]
    
    results = {}
    
    for case_name, token in jwt_test_cases:
        print(f"🧪 Testing: {case_name}")
        
        # Test /analyze (using GET to existing analysis to avoid ML overhead)
        analyze_result = test_request(f"{BASE_URL}/analyze/{analysis_id}", "GET", token=token)
        
        # Test /feedback
        feedback_result = test_request(f"{BASE_URL}/feedback", "POST", feedback_data, token=token)
        
        results[case_name] = {
            "analyze": analyze_result,
            "feedback": feedback_result
        }
        
        print(f"  /analyze:  {analyze_result['status']} ({'✅' if analyze_result['success'] else '❌'})")
        print(f"  /feedback: {feedback_result['status']} ({'✅' if feedback_result['success'] else '❌'})")
        
        # Check for JWT-specific errors
        analyze_jwt_error = analyze_result["status"] in [401, 422]
        feedback_jwt_error = feedback_result["status"] in [401, 422]
        
        if analyze_jwt_error or feedback_jwt_error:
            print(f"  ⚠️  JWT Error Detected:")
            if analyze_jwt_error:
                error_info = analyze_result["data"].get("error", {})
                print(f"      /analyze: {error_info.get('code', 'N/A')} - {error_info.get('message', 'N/A')}")
            if feedback_jwt_error:
                error_info = feedback_result["data"].get("error", {})
                print(f"      /feedback: {error_info.get('code', 'N/A')} - {error_info.get('message', 'N/A')}")
        
        print()
    
    # Step 3: Analyze results for consistency
    print("🔍 Step 3: Consistency Analysis")
    print("-" * 30)
    
    inconsistencies = []
    jwt_error_routes = []
    
    for case_name, case_results in results.items():
        analyze_status = case_results["analyze"]["status"]
        feedback_status = case_results["feedback"]["status"]
        
        # Check for JWT validation errors (401/422)
        analyze_jwt_error = analyze_status in [401, 422]
        feedback_jwt_error = feedback_status in [401, 422]
        
        if analyze_jwt_error:
            jwt_error_routes.append(f"/analyze ({case_name})")
        if feedback_jwt_error:
            jwt_error_routes.append(f"/feedback ({case_name})")
        
        # Check for different handling between routes
        if (analyze_jwt_error and not feedback_jwt_error) or (feedback_jwt_error and not analyze_jwt_error):
            inconsistencies.append({
                "case": case_name,
                "analyze_status": analyze_status,
                "feedback_status": feedback_status,
                "analyze_jwt_error": analyze_jwt_error,
                "feedback_jwt_error": feedback_jwt_error
            })
    
    # Results
    print(f"📊 Results Summary:")
    print(f"  Total test cases: {len(jwt_test_cases)}")
    print(f"  JWT errors found: {len(jwt_error_routes)}")
    print(f"  Inconsistencies: {len(inconsistencies)}")
    print()
    
    if jwt_error_routes:
        print(f"⚠️  JWT Validation Errors Detected:")
        for route in jwt_error_routes:
            print(f"    • {route}")
        print()
        print(f"🚨 ISSUE: Optional-auth routes should NOT return JWT validation errors!")
        print(f"   Both /analyze and /feedback are declared as optional-auth routes.")
        print(f"   They should handle malformed/expired tokens gracefully (as anonymous).")
        print()
    
    if inconsistencies:
        print(f"❌ INCONSISTENT JWT HANDLING:")
        for inc in inconsistencies:
            print(f"  • {inc['case']}:")
            print(f"      /analyze:  {inc['analyze_status']} ({'JWT error' if inc['analyze_jwt_error'] else 'Handled gracefully'})")
            print(f"      /feedback: {inc['feedback_status']} ({'JWT error' if inc['feedback_jwt_error'] else 'Handled gracefully'})")
        print()
        return False
    elif jwt_error_routes:
        print(f"❌ PROBLEM CONFIRMED:")
        print(f"   Optional-auth routes are returning JWT validation errors")
        print(f"   when they should handle invalid tokens gracefully.")
        return False
    else:
        print(f"✅ JWT HANDLING IS CONSISTENT:")
        print(f"   Both routes handle all JWT scenarios gracefully (no 401/422 errors)")
        print(f"   This is the expected behavior for optional-auth routes.")
        return True

if __name__ == "__main__":
    try:
        # Quick connectivity test
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code != 200:
            print(f"❌ Backend health check failed: {health.status_code}")
            sys.exit(1)
        
        success = main()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)