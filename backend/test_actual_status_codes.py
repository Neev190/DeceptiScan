#!/usr/bin/env python3
"""
Test script to determine actual status codes returned by all protected routes
when using expired JWT tokens. This will help determine if there's real
inconsistency or if all routes consistently return 401.
"""
import sys
import os
import uuid
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app import create_app, db
from models.user import User
from models.analysis import AnalysisRecord


def create_expired_token(app, user_id):
    """Create an access token that expired 1 hour ago."""
    with app.app_context():
        return create_access_token(
            identity=user_id, 
            expires_delta=timedelta(hours=-1)
        )


def test_actual_status_codes():
    """Test all protected routes with expired tokens and report actual status codes."""
    
    # Create test app
    app = create_app('testing')
    client = app.test_client()
    
    with app.app_context():
        # Set up test data
        db.create_all()
        
        # Create test user
        user_id = str(uuid.uuid4())
        user = User(id=uuid.UUID(user_id), email='status-test@example.com', is_active=True)
        user.set_password('StatusTest123')
        db.session.add(user)
        
        # Create test analysis
        analysis_id = str(uuid.uuid4())
        analysis = AnalysisRecord(
            id=uuid.UUID(analysis_id),
            user_id=uuid.UUID(user_id),
            input_text='Test analysis for status code verification',
            authenticity_score=75.0,
            confidence=0.8,
            classification='reliable',
            sentence_results=[],
            processing_time=100.0,
            model_version='test-1.0.0'
        )
        db.session.add(analysis)
        db.session.commit()
        
        # Create expired token
        expired_token = create_expired_token(app, user_id)
        headers = {'Authorization': f'Bearer {expired_token}'}
        
        print("=" * 80)
        print("ACTUAL STATUS CODE ANALYSIS FOR EXPIRED TOKENS")
        print("=" * 80)
        print()
        
        # Test all protected routes
        routes_to_test = [
            ('GET', '/api/v1/auth/me', None),
            ('PATCH', '/api/v1/auth/me', {'username': 'NewName'}),
            ('POST', '/api/v1/auth/logout', None),
            ('GET', '/api/v1/analyses/recent', None),
            ('GET', '/api/v1/history', None),
            ('GET', f'/api/v1/history/{analysis_id}', None),
            ('DELETE', f'/api/v1/history/{analysis_id}', None),
            ('POST', '/api/v1/auth/refresh', None),  # This should use refresh token, but testing with access token
        ]
        
        status_codes = []
        
        print(f"{'Route':<35} | {'Method':<6} | {'Actual Status Code'}")
        print("-" * 70)
        
        for method, route, payload in routes_to_test:
            try:
                if method == 'GET':
                    resp = client.get(route, headers=headers)
                elif method == 'POST':
                    resp = client.post(route, headers=headers, json=payload)
                elif method == 'PATCH':
                    resp = client.patch(route, headers=headers, json=payload)
                elif method == 'DELETE':
                    resp = client.delete(route, headers=headers)
                
                status_codes.append((route, method, resp.status_code))
                print(f"{route:<35} | {method:<6} | {resp.status_code}")
                
                # Also check if response is JSON and what error message is provided
                try:
                    data = resp.get_json()
                    if data and 'error' in data:
                        error_msg = str(data['error'])[:50] + "..." if len(str(data['error'])) > 50 else str(data['error'])
                        print(f"{'':>44}   └─ Error: {error_msg}")
                except:
                    print(f"{'':>44}   └─ Non-JSON response")
                    
            except Exception as e:
                print(f"{route:<35} | {method:<6} | ERROR: {str(e)}")
                status_codes.append((route, method, f"ERROR: {str(e)}"))
        
        print()
        print("=" * 80)
        print("ANALYSIS SUMMARY")
        print("=" * 80)
        
        # Analyze consistency
        actual_codes = [code for _, _, code in status_codes if isinstance(code, int)]
        unique_codes = set(actual_codes)
        
        print(f"Unique status codes found: {sorted(unique_codes)}")
        print()
        
        if len(unique_codes) == 1:
            print("✅ CONSISTENT: All routes return the same status code for expired tokens")
            print(f"   All routes return: {list(unique_codes)[0]}")
        else:
            print("❌ INCONSISTENT: Routes return different status codes for expired tokens")
            print("   Breakdown by status code:")
            for code in sorted(unique_codes):
                routes_with_code = [(route, method) for route, method, c in status_codes if c == code]
                print(f"   {code}: {len(routes_with_code)} routes")
                for route, method in routes_with_code:
                    print(f"      {method} {route}")
        
        print()
        print("RECOMMENDATION:")
        if len(unique_codes) == 1 and 401 in unique_codes:
            print("✅ All routes consistently return 401 for expired tokens.")
            print("   The original test expectation of 422 was likely incorrect.")
            print("   Tests should be updated to expect 401 consistently.")
        elif len(unique_codes) == 1 and 422 in unique_codes:
            print("⚠️  All routes consistently return 422 for expired tokens.")
            print("   This is unusual but consistent. Tests expecting 401 should be updated.")
        else:
            print("❌ There is real inconsistency that needs to be fixed in the backend code.")
            print("   Routes should be updated to return consistent status codes.")
        
        # Clean up
        db.session.remove()
        for table in reversed(db.metadata.sorted_tables):
            if table.name != 'claim_embeddings':
                db.session.execute(table.delete())
        db.session.commit()


if __name__ == '__main__':
    test_actual_status_codes()