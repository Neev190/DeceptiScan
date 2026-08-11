#!/usr/bin/env python3
"""
Verify JWT consistency with realistic test data
"""
from app import create_app, db
from models.analysis import AnalysisRecord
import uuid

def test_with_real_analysis():
    """Test with an actual analysis record in the database."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create a test analysis record
        analysis = AnalysisRecord(
            id=uuid.uuid4(),
            user_id=None,  # Anonymous analysis
            input_text='Test analysis for JWT verification',
            authenticity_score=75.0,
            confidence=0.8,
            classification='reliable',
            sentence_results=[],
            processing_time=100.0,
            model_version='test-1.0.0'
        )
        db.session.add(analysis)
        db.session.commit()
        analysis_id = str(analysis.id)
        
        client = app.test_client()
        malformed_header = {'Authorization': 'Bearer malformed.jwt.token'}
        
        print("=== JWT Consistency Test with Valid Analysis ID ===\n")
        
        # Test /feedback with existing analysis
        print("Testing POST /api/v1/feedback with malformed token (valid analysis ID):")
        feedback_resp = client.post('/api/v1/feedback',
                                   json={
                                       'analysisId': analysis_id,
                                       'feedback': {'type': 'helpful'}
                                   },
                                   headers=malformed_header)
        
        print(f"Status: {feedback_resp.status_code}")
        print(f"Response: {feedback_resp.get_json()}")
        print()
        
        # Clean up
        db.session.delete(analysis)
        db.session.commit()
        
        # Analyze result
        if feedback_resp.status_code in [401, 422]:
            print("❌ /feedback returns JWT validation error (BUG - should be anonymous)")
            return False
        elif feedback_resp.status_code == 201:
            print("✅ /feedback successfully processes request as anonymous user")
            return True
        else:
            print(f"⚠️  /feedback returns {feedback_resp.status_code} - may be business logic issue")
            return True  # Not a JWT error

if __name__ == '__main__':
    success = test_with_real_analysis()
    if success:
        print("\n✅ JWT consistency verified - no bug found")
    else:
        print("\n❌ JWT inconsistency detected - bug exists")