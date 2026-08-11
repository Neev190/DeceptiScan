#!/usr/bin/env python3
"""
Test script to determine actual status codes returned by all protected routes
when using malformed JWT tokens.
"""
import sys
import os
import uuid

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app import create_app, db
from models.user import User
from models.analysis import AnalysisRecord


def test_malformed_status_codes():
    """Test all protected routes with malformed tokens and report actual status codes."""
    
    # Create test app
    app = create_app('testing')
    client = app.test_client()
    
    with app.app_context():
        # Set up test data
        db.create_all()
        
        # Create test user and analysis (for routes that need IDs)
        user_id = str(uuid.uuid4())
        user = User(id=uuid.UUID(user_id), email='malformed-test@example.com', is_active=True)
        user.set_password('MalformedTest123')
        db.session.add(user)
        
        analysis_id = str(uuid.uuid4())
        analysis = AnalysisRecord(
            id=uuid.UUID(analysis_id),
            user_id=uuid.UUID(user_id),
            input_text='Test analysis for malformed token verification',
            authenticity_score=60.0,
            confidence=0.7,
            classification='mixed',
            sentence_results=[],
            processing_time=120.0,
            model_version='test-1.0.0'
        )
        db.session.add(analysis)
        db.session.commit()
        
        # Test different types of malformed tokens
        malformed_tokens = [
            ('not.a.valid.jwt', 'Standard malformed JWT'),
            ('invalid-jwt-token', 'No dots in token'),
            ('Bearer extra.spaced.token', 'Double Bearer prefix'),  # This will create "Bearer Bearer extra.spaced.token"
            ('', 'Empty token after Bearer'),
        ]
        
        print("=" * 80)
        print("ACTUAL STATUS CODE ANALYSIS FOR MALFORMED TOKENS")
        print("=" * 80)
        print()
        
        # Test all protected routes with each malformed token type
        routes_to_test = [
            ('GET', '/api/v1/auth/me', None),
            ('PATCH', '/api/v1/auth/me', {'username': 'NewName'}),
            ('POST', '/api/v1/auth/logout', None),
            ('GET', '/api/v1/analyses/recent', None),
            ('GET', '/api/v1/history', None),
            ('GET', f'/api/v1/history/{analysis_id}', None),
            ('DELETE', f'/api/v1/history/{analysis_id}', None),
            ('POST', '/api/v1/auth/refresh', None),
        ]
        
        for token, token_desc in malformed_tokens:
            print(f"TESTING WITH: {token_desc}")
            print("-" * 40)
            
            headers = {'Authorization': f'Bearer {token}'}
            status_codes = []
            
            print(f"{'Route':<35} | {'Method':<6} | {'Status'}")
            print("-" * 50)
            
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
                    
                except Exception as e:
                    print(f"{route:<35} | {method:<6} | ERROR: {str(e)}")
                    status_codes.append((route, method, f"ERROR: {str(e)}"))
            
            # Analyze this token type
            actual_codes = [code for _, _, code in status_codes if isinstance(code, int)]
            unique_codes = set(actual_codes)
            
            print(f"\nUnique status codes for {token_desc}: {sorted(unique_codes)}")
            if len(unique_codes) == 1:
                print(f"✅ Consistent: All routes return {list(unique_codes)[0]}")
            else:
                print(f"❌ Inconsistent: {len(unique_codes)} different status codes")
            
            print("\n" + "=" * 80 + "\n")
        
        # Clean up
        db.session.remove()
        for table in reversed(db.metadata.sorted_tables):
            if table.name != 'claim_embeddings':
                db.session.execute(table.delete())
        db.session.commit()


if __name__ == '__main__':
    test_malformed_status_codes()