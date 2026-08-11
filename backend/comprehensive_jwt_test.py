#!/usr/bin/env python3
"""
Comprehensive JWT Edge Case Testing

This script tests a wide variety of JWT edge cases that could potentially
cause inconsistent behavior between /analyze and /feedback routes.
"""

import requests
import json
import sys
import uuid

BASE_URL = "http://localhost:5000/api/v1"

# Various malformed JWT tokens to test
JWT_TEST_CASES = [
    ("No Authorization Header", {}),
    ("Empty Authorization", {"Authorization": ""}),
    ("No Bearer Prefix", {"Authorization": "some-token"}),
    ("Bearer Only", {"Authorization": "Bearer"}),
    ("Bearer Empty", {"Authorization": "Bearer "}),
    ("Malformed JWT - No Dots", {"Authorization": "Bearer notajwttoken"}),
    ("Malformed JWT - One Dot", {"Authorization": "Bearer header.payload"}),
    ("Malformed JWT - Three Dots", {"Authorization": "Bearer header.payload.signature.extra"}),
    ("Malformed JWT - Invalid Base64", {"Authorization": "Bearer invalid!@#.invalid!@#.invalid!@#"}),
    ("Expired Token", {"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYwMDAwMDAwMCwianRpIjoiZXhwaXJlZC10b2tlbiIsInR5cGUiOiJhY2Nlc3MiLCJzdWIiOiJ0ZXN0LXVzZXIiLCJuYmYiOjE2MDAwMDAwMDAsImV4cCI6MTYwMDAwMDEwMH0.invalid"}),
    ("Invalid Signature", {"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTcwMDAwMDAwMCwianRpIjoiaW52YWxpZC1zaWduYXR1cmUiLCJ0eXBlIjoiYWNjZXNzIiwic3ViIjoidGVzdC11c2VyIiwibmJmIjoxNzAwMDAwMDAwLCJleHAiOjk5OTk5OTk5OTl9.wrong_signature"}),
    ("Wrong Token Type", {"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTcwMDAwMDAwMCwianRpIjoid3JvbmctdHlwZSIsInR5cGUiOiJyZWZyZXNoIiwic3ViIjoidGVzdC11c2VyIiwibmJmIjoxNzAwMDAwMDAwLCJleHAiOjk5OTk5OTk5OTl9.signature"}),
    ("Extra Spaces", {"Authorization": "   Bearer   some.jwt.token   "}),
    ("Multiple Bearer", {"Authorization": "Bearer token1 Bearer token2"}),
    ("Case Sensitive", {"Authorization": "bearer some.jwt.token"}),
    ("Unicode Characters", {"Authorization": "Bearer tôkēn.wìth.ūnïcödé"}),
]

def make_request(endpoint, method="POST", data=None, headers=None):
    """Make HTTP request and return structured response."""
    url = f"{BASE_URL}{endpoint}"
    req_headers = {"Content-Type": "application/json"}
    
    if headers:
        req_headers.update(headers)
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=data, headers=req_headers, timeout=20)
        elif method.upper() == "GET":
            response = requests.get(url, headers=req_headers, timeout=20)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        try:
            json_data = response.json()
        except:
            json_data = {"raw_text": response.text[:200]}
        
        return {
            "status": response.status_code,
            "data": json_data,
            "is_jwt_error": response.status_code in [401, 422],
            "is_server_error": response.status_code >= 500
        }
        
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "data": {"error": "Request timeout"}, "is_jwt_error": False, "is_server_error": False}
    except Exception as e:
        return {"status": "ERROR", "data": {"error": str(e)}, "is_jwt_error": False, "is_server_error": False}

def create_test_analysis():
    """Create a test analysis and return its ID."""
    print("Creating test analysis...")
    result = make_request("/analyze", "POST", {"content": "Test analysis for JWT testing"})
    
    if result["status"] == 200:
        analysis_id = result["data"].get("id")
        if analysis_id:
            print(f"✅ Test analysis created: {analysis_id}")
            return analysis_id
    
    print(f"❌ Failed to create test analysis: {result}")
    return None

def test_jwt_consistency():
    """Test JWT handling consistency across routes."""
    
    print("🎯 Comprehensive JWT Edge Case Testing")
    print("=" * 60)
    
    # Create test analysis for feedback testing
    analysis_id = create_test_analysis()
    if not analysis_id:
        return False
    
    print(f"📝 Testing {len(JWT_TEST_CASES)} JWT edge cases...")
    print()
    
    results = {}
    inconsistencies = []
    jwt_errors = []
    server_errors = []
    
    for case_name, auth_header in JWT_TEST_CASES:
        print(f"🧪 {case_name}")
        
        # Test /analyze (GET existing to avoid ML overhead)
        analyze_result = make_request(f"/analyze/{analysis_id}", "GET", headers=auth_header)
        
        # Test /feedback
        feedback_data = {
            "analysisId": analysis_id,
            "feedback": {"type": "helpful", "comment": f"Test feedback for {case_name}"}
        }
        feedback_result = make_request("/feedback", "POST", feedback_data, headers=auth_header)
        
        results[case_name] = {
            "analyze": analyze_result,
            "feedback": feedback_result
        }
        
        # Check for various error types
        analyze_jwt = analyze_result["is_jwt_error"]
        feedback_jwt = feedback_result["is_jwt_error"]
        analyze_server = analyze_result["is_server_error"]
        feedback_server = feedback_result["is_server_error"]
        
        # Display results
        analyze_status = f"{analyze_result['status']} ({'JWT' if analyze_jwt else 'SERVER' if analyze_server else 'OK'})"
        feedback_status = f"{feedback_result['status']} ({'JWT' if feedback_jwt else 'SERVER' if feedback_server else 'OK'})"
        
        print(f"  /analyze:  {analyze_status}")
        print(f"  /feedback: {feedback_status}")
        
        # Track problems
        if analyze_jwt or feedback_jwt:
            jwt_errors.append({
                "case": case_name,
                "analyze_jwt": analyze_jwt,
                "feedback_jwt": feedback_jwt,
                "analyze_status": analyze_result["status"],
                "feedback_status": feedback_result["status"]
            })
        
        if analyze_server or feedback_server:
            server_errors.append({
                "case": case_name,
                "analyze_server": analyze_server,
                "feedback_server": feedback_server,
                "analyze_status": analyze_result["status"],
                "feedback_status": feedback_result["status"]
            })
        
        # Check for inconsistencies
        if (analyze_jwt != feedback_jwt) or (analyze_server != feedback_server):
            inconsistencies.append({
                "case": case_name,
                "analyze": analyze_result,
                "feedback": feedback_result
            })
        
        print()
    
    # Analysis and report
    print("🔍 ANALYSIS RESULTS")
    print("=" * 40)
    
    print(f"📊 Summary:")
    print(f"  Total test cases: {len(JWT_TEST_CASES)}")
    print(f"  JWT validation errors: {len(jwt_errors)}")
    print(f"  Server errors (500+): {len(server_errors)}")
    print(f"  Inconsistencies: {len(inconsistencies)}")
    print()
    
    # Report JWT errors
    if jwt_errors:
        print(f"🚨 JWT VALIDATION ERRORS FOUND:")
        print("   Optional-auth routes should NOT return 401/422!")
        for error in jwt_errors:
            print(f"   • {error['case']}:")
            if error["analyze_jwt"]:
                print(f"     - /analyze: {error['analyze_status']}")
            if error["feedback_jwt"]:
                print(f"     - /feedback: {error['feedback_status']}")
        print()
    
    # Report server errors
    if server_errors:
        print(f"🔥 SERVER ERRORS FOUND:")
        for error in server_errors:
            print(f"   • {error['case']}:")
            if error["analyze_server"]:
                print(f"     - /analyze: {error['analyze_status']}")
            if error["feedback_server"]:
                print(f"     - /feedback: {error['feedback_status']}")
        print()
    
    # Report inconsistencies
    if inconsistencies:
        print(f"❌ INCONSISTENCIES FOUND:")
        for inc in inconsistencies:
            print(f"   • {inc['case']}:")
            print(f"     - /analyze:  {inc['analyze']['status']} ({'JWT' if inc['analyze']['is_jwt_error'] else 'SERVER' if inc['analyze']['is_server_error'] else 'OK'})")
            print(f"     - /feedback: {inc['feedback']['status']} ({'JWT' if inc['feedback']['is_jwt_error'] else 'SERVER' if inc['feedback']['is_server_error'] else 'OK'})")
        print()
        return False
    
    # Final verdict
    if jwt_errors:
        print(f"❌ ISSUE CONFIRMED:")
        print(f"   Optional-auth routes are returning JWT validation errors")
        print(f"   when they should handle invalid tokens gracefully.")
        return False
    elif server_errors:
        print(f"⚠️  SERVER ERRORS DETECTED:")
        print(f"   Routes are crashing on certain JWT edge cases.")
        return False
    else:
        print(f"✅ ALL TESTS PASSED:")
        print(f"   Both routes handle all JWT edge cases consistently and gracefully.")
        print(f"   No JWT validation errors or server crashes detected.")
        return True

if __name__ == "__main__":
    try:
        # Health check
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code != 200:
            print(f"❌ Backend not available: {health.status_code}")
            sys.exit(1)
        
        success = test_jwt_consistency()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Test script failed: {e}")
        sys.exit(1)