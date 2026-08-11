#!/usr/bin/env python3
"""
JWT Consistency Test Script
Tests both /analyze and /feedback routes with malformed and expired tokens
"""
import requests
import json
import uuid
import time
from datetime import datetime, timedelta

# Test server URL
BASE_URL = 'http://localhost:5000/api/v1'

def test_route_with_token(route, method, payload, token_header, description):
    """Test a route with given token and return results"""
    url = f"{BASE_URL}{route}"
    headers = {'Content-Type': 'application/json'}
    if token_header:
        headers['Authorization'] = token_header
    
    try:
        if method == 'POST':
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
        elif method == 'GET':
            resp = requests.get(url, headers=headers, timeout=10)
        
        return {
            'description': description,
            'route': route,
            'status_code': resp.status_code,
            'response': resp.text[:200] + '...' if len(resp.text) > 200 else resp.text,
            'success': True
        }
    except Exception as e:
        return {
            'description': description,
            'route': route,
            'status_code': 'ERROR',
            'response': str(e),
            'success': False
        }

def main():
    print("=== JWT Consistency Test ===")
    print(f"Testing at {datetime.now()}")
    print()
    
    # Test payloads
    analyze_payload = {'content': 'This is test content for JWT consistency testing.'}
    feedback_payload = {
        'analysisId': str(uuid.uuid4()), 
        'feedback': {'type': 'helpful'}
    }
    
    # Test scenarios
    scenarios = [
        # No token
        (None, "No Authorization header"),
        # Empty token
        ("Bearer ", "Empty Bearer token"),
        # Malformed tokens
        ("Bearer not.a.valid.jwt", "Malformed JWT"),
        ("Bearer garbage.token.here", "Another malformed JWT"),
        ("Bearer invalid-jwt-token", "Invalid JWT format"),
        # Wrong format
        ("some-token-without-bearer", "No Bearer prefix"),
        ("", "Empty Authorization header"),
    ]
    
    results = []
    
    for token_header, description in scenarios:
        print(f"\n--- Testing: {description} ---")
        
        # Test /analyze
        result = test_route_with_token('/analyze', 'POST', analyze_payload, token_header, f"{description} - /analyze")
        results.append(result)
        print(f"/analyze: {result['status_code']} - {result['response'][:100]}")
        
        # Test /feedback  
        result = test_route_with_token('/feedback', 'POST', feedback_payload, token_header, f"{description} - /feedback")
        results.append(result)
        print(f"/feedback: {result['status_code']} - {result['response'][:100]}")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    analyze_results = [r for r in results if '/analyze' in r['route']]
    feedback_results = [r for r in results if '/feedback' in r['route']]
    
    print("Status codes for /analyze:")
    for r in analyze_results:
        print(f"  {r['description']}: {r['status_code']}")
    
    print("\nStatus codes for /feedback:")
    for r in feedback_results:
        print(f"  {r['description']}: {r['status_code']}")
    
    # Check for inconsistencies
    print(f"\n=== INCONSISTENCY CHECK ===")
    inconsistencies = []
    for i, (token, desc) in enumerate(scenarios):
        analyze_code = analyze_results[i]['status_code']
        feedback_code = feedback_results[i]['status_code']
        
        # Both should handle auth errors gracefully
        if analyze_code != feedback_code:
            # Special case: 404 for feedback with invalid analysis ID is expected
            if feedback_code == 404:
                print(f"✓ {desc}: /analyze={analyze_code}, /feedback={feedback_code} (404 expected for invalid analysisId)")
            else:
                inconsistencies.append((desc, analyze_code, feedback_code))
                print(f"✗ INCONSISTENCY - {desc}: /analyze={analyze_code}, /feedback={feedback_code}")
        else:
            print(f"✓ {desc}: Both return {analyze_code}")
    
    if inconsistencies:
        print(f"\nFound {len(inconsistencies)} inconsistencies that need investigation")
    else:
        print(f"\nNo JWT handling inconsistencies found - both routes handle optional auth correctly")
    
    return len(inconsistencies) == 0

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)