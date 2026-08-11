"""
JWT Optional Auth Regression Tests

Ensures consistent behavior across optional-auth routes when handling malformed/expired tokens.
Both /analyze and /feedback should treat JWT errors gracefully and proceed as anonymous requests.

This test suite specifically prevents regression of the JWT consistency issue.
"""
import uuid
import pytest
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from app import create_app, db
from models.user import User
from models.analysis import AnalysisRecord


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        for table in reversed(db.metadata.sorted_tables):
            if table.name != 'claim_embeddings':
                db.session.execute(table.delete())
        db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def test_user_and_analysis(app):
    """Create a test user and analysis record."""
    with app.app_context():
        user = User(id=uuid.uuid4(), email='jwt-regression-test@example.com', is_active=True)
        user.set_password('TestPass123')
        
        analysis = AnalysisRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            input_text='Test analysis for JWT regression test',
            authenticity_score=75.0,
            confidence=0.8,
            classification='reliable',
            sentence_results=[],
            processing_time=100.0,
            model_version='test-1.0.0'
        )
        
        db.session.add(user)
        db.session.add(analysis)
        db.session.commit()
        
        return str(user.id), str(analysis.id)


def make_expired_token(app, user_id):
    """Create an access token that expired 1 hour ago."""
    with app.app_context():
        return create_access_token(
            identity=user_id, 
            expires_delta=timedelta(hours=-1)
        )


class TestJWTOptionalAuthRegression:
    """
    Regression tests ensuring optional-auth routes handle JWT errors consistently.
    
    CRITICAL BEHAVIOR: Both /analyze and /feedback must treat malformed/expired 
    tokens gracefully by proceeding as anonymous requests, NOT returning JWT 
    validation errors (401/422).
    """

    def test_malformed_tokens_handled_gracefully_analyze(self, client):
        """
        /analyze with malformed token should proceed as anonymous (not return JWT errors).
        
        Expected behavior:
        - Status: 200 (success) or 503 (service error)  
        - NOT 401/422 (JWT validation errors)
        - NOT 500 (crash)
        """
        # Mock the services to avoid ML service complexity
        from unittest.mock import patch, MagicMock
        
        mock_cache = MagicMock()
        mock_cache.compute_content_hash.return_value = 'test-hash'
        mock_cache.get_analysis.return_value = None
        mock_cache.set_analysis.return_value = None
        
        mock_ml = MagicMock()
        mock_result = MagicMock()
        mock_result.authenticity_score = 60.0
        mock_result.confidence = 0.7
        mock_result.classification = 'mixed'
        mock_result.warning = None
        mock_result.sentence_analysis = []
        mock_result.model_version = 'test-v1'
        mock_result.processing_time_ms = 10
        mock_ml.is_loaded = True
        mock_ml.analyze.return_value = mock_result
        
        mock_recency = MagicMock()
        mock_recency.process_recency_routing.return_value = (False, None)
        
        mock_retrieval = MagicMock()
        mock_retrieval.find_similar_claims.return_value = []

        with patch('app.routes.analysis.get_cache_service', return_value=mock_cache), \
             patch('app.routes.analysis.get_ml_service', return_value=mock_ml), \
             patch('services.recency_service.get_recency_service', return_value=mock_recency), \
             patch('app.routes.analysis.get_retrieval_service', return_value=mock_retrieval):
            
            resp = client.post('/api/v1/analyze',
                              json={'content': 'Test content for malformed token regression test'},
                              headers={'Authorization': 'Bearer definitely.not.a.valid.jwt'})
        
        # REGRESSION PREVENTION: Must not return JWT validation errors
        assert resp.status_code not in [401, 422], \
            f"REGRESSION: /analyze returned JWT error {resp.status_code} for malformed token"
        
        # REGRESSION PREVENTION: Must not crash 
        assert resp.status_code != 500, \
            f"REGRESSION: /analyze crashed (500) on malformed token"
        
        # Should succeed or fail with service error (not JWT error)
        assert resp.status_code in [200, 201, 503], \
            f"/analyze returned unexpected status {resp.status_code}"

    def test_malformed_tokens_handled_gracefully_feedback(self, client, test_user_and_analysis):
        """
        /feedback with malformed token should proceed as anonymous (not return JWT errors).
        
        Expected behavior:
        - Status: 201 (success) or 404 (analysis not found)
        - NOT 401/422 (JWT validation errors) 
        - NOT 500 (crash)
        """
        user_id, analysis_id = test_user_and_analysis
        
        resp = client.post('/api/v1/feedback',
                          json={
                              'analysisId': analysis_id,
                              'feedback': {'type': 'helpful'}
                          },
                          headers={'Authorization': 'Bearer totally.malformed.jwt.token'})
        
        # REGRESSION PREVENTION: Must not return JWT validation errors
        assert resp.status_code not in [401, 422], \
            f"REGRESSION: /feedback returned JWT error {resp.status_code} for malformed token"
        
        # REGRESSION PREVENTION: Must not crash
        assert resp.status_code != 500, \
            f"REGRESSION: /feedback crashed (500) on malformed token"
        
        # Should succeed or fail with business logic error (not JWT error)
        assert resp.status_code in [201, 404], \
            f"/feedback returned unexpected status {resp.status_code}"

    def test_expired_tokens_handled_gracefully_analyze(self, client, app, test_user_and_analysis):
        """
        /analyze with expired token should proceed as anonymous (not return JWT errors).
        """
        user_id, analysis_id = test_user_and_analysis
        expired_token = make_expired_token(app, user_id)
        
        # Same mocking as above
        from unittest.mock import patch, MagicMock
        mock_cache = MagicMock()
        mock_cache.compute_content_hash.return_value = 'test-hash'
        mock_cache.get_analysis.return_value = None
        mock_cache.set_analysis.return_value = None
        
        mock_ml = MagicMock()
        mock_result = MagicMock()
        mock_result.authenticity_score = 60.0
        mock_result.confidence = 0.7
        mock_result.classification = 'mixed'
        mock_result.warning = None
        mock_result.sentence_analysis = []
        mock_result.model_version = 'test-v1'
        mock_result.processing_time_ms = 10
        mock_ml.is_loaded = True
        mock_ml.analyze.return_value = mock_result
        
        mock_recency = MagicMock()
        mock_recency.process_recency_routing.return_value = (False, None)
        
        mock_retrieval = MagicMock()
        mock_retrieval.find_similar_claims.return_value = []

        with patch('app.routes.analysis.get_cache_service', return_value=mock_cache), \
             patch('app.routes.analysis.get_ml_service', return_value=mock_ml), \
             patch('services.recency_service.get_recency_service', return_value=mock_recency), \
             patch('app.routes.analysis.get_retrieval_service', return_value=mock_retrieval):
            
            resp = client.post('/api/v1/analyze',
                              json={'content': 'Test content for expired token regression test'},
                              headers={'Authorization': f'Bearer {expired_token}'})
        
        # REGRESSION PREVENTION: Must not return JWT validation errors
        assert resp.status_code not in [401, 422], \
            f"REGRESSION: /analyze returned JWT error {resp.status_code} for expired token"
        
        assert resp.status_code != 500, \
            f"REGRESSION: /analyze crashed (500) on expired token"

    def test_expired_tokens_handled_gracefully_feedback(self, client, app, test_user_and_analysis):
        """
        /feedback with expired token should proceed as anonymous (not return JWT errors).
        """
        user_id, analysis_id = test_user_and_analysis
        expired_token = make_expired_token(app, user_id)
        
        resp = client.post('/api/v1/feedback',
                          json={
                              'analysisId': analysis_id,
                              'feedback': {'type': 'helpful'}
                          },
                          headers={'Authorization': f'Bearer {expired_token}'})
        
        # REGRESSION PREVENTION: Must not return JWT validation errors
        assert resp.status_code not in [401, 422], \
            f"REGRESSION: /feedback returned JWT error {resp.status_code} for expired token"
        
        assert resp.status_code != 500, \
            f"REGRESSION: /feedback crashed (500) on expired token"

    def test_consistent_behavior_across_routes(self, client, test_user_and_analysis):
        """
        Both optional-auth routes should handle JWT errors the same way.
        
        This test specifically checks that the behavior is consistent between
        /analyze and /feedback when presented with malformed tokens.
        """
        user_id, analysis_id = test_user_and_analysis
        malformed_header = {'Authorization': 'Bearer malformed.jwt'}
        
        # Test /analyze (with mocking)
        from unittest.mock import patch, MagicMock
        mock_cache = MagicMock()
        mock_cache.compute_content_hash.return_value = 'test-hash'
        mock_cache.get_analysis.return_value = None
        mock_cache.set_analysis.return_value = None
        
        mock_ml = MagicMock()
        mock_result = MagicMock()
        mock_result.authenticity_score = 60.0
        mock_result.confidence = 0.7
        mock_result.classification = 'mixed'
        mock_result.warning = None
        mock_result.sentence_analysis = []
        mock_result.model_version = 'test-v1'
        mock_result.processing_time_ms = 10
        mock_ml.is_loaded = True
        mock_ml.analyze.return_value = mock_result
        
        mock_recency = MagicMock()
        mock_recency.process_recency_routing.return_value = (False, None)
        
        mock_retrieval = MagicMock()
        mock_retrieval.find_similar_claims.return_value = []

        with patch('app.routes.analysis.get_cache_service', return_value=mock_cache), \
             patch('app.routes.analysis.get_ml_service', return_value=mock_ml), \
             patch('services.recency_service.get_recency_service', return_value=mock_recency), \
             patch('app.routes.analysis.get_retrieval_service', return_value=mock_retrieval):
            
            analyze_resp = client.post('/api/v1/analyze',
                                      json={'content': 'Test consistency check'},
                                      headers=malformed_header)
        
        # Test /feedback
        feedback_resp = client.post('/api/v1/feedback',
                                   json={
                                       'analysisId': analysis_id,
                                       'feedback': {'type': 'helpful'}
                                   },
                                   headers=malformed_header)
        
        # Both must avoid JWT validation errors
        assert analyze_resp.status_code not in [401, 422, 500], \
            f"/analyze returned JWT/crash error {analyze_resp.status_code}"
        
        assert feedback_resp.status_code not in [401, 422, 500], \
            f"/feedback returned JWT/crash error {feedback_resp.status_code}"
        
        # Both should succeed with business logic (not JWT errors)
        analyze_ok = analyze_resp.status_code in [200, 201, 503]
        feedback_ok = feedback_resp.status_code in [200, 201, 404]
        
        assert analyze_ok, f"/analyze unexpected status {analyze_resp.status_code}"
        assert feedback_ok, f"/feedback unexpected status {feedback_resp.status_code}"
        
        print(f"Consistency verified: /analyze={analyze_resp.status_code}, /feedback={feedback_resp.status_code}")

    def test_empty_bearer_tokens_handled_gracefully(self, client, test_user_and_analysis):
        """
        Empty Bearer tokens ('Bearer ') should be handled gracefully by both routes.
        """
        user_id, analysis_id = test_user_and_analysis
        empty_bearer_header = {'Authorization': 'Bearer '}
        
        # Test /feedback with empty bearer
        feedback_resp = client.post('/api/v1/feedback',
                                   json={
                                       'analysisId': analysis_id,
                                       'feedback': {'type': 'helpful'}
                                   },
                                   headers=empty_bearer_header)
        
        # Must not crash or return JWT errors
        assert feedback_resp.status_code not in [401, 422, 500], \
            f"REGRESSION: /feedback failed on empty Bearer token: {feedback_resp.status_code}"
        
        # Should handle as anonymous request
        assert feedback_resp.status_code in [201, 404], \
            f"/feedback unexpected status for empty Bearer: {feedback_resp.status_code}"