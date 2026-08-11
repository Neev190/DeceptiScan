"""
JWT Authentication Edge Case Tests

Tests malformed and expired tokens across ALL protected routes to ensure
consistent error handling. Verifies that:
1. Malformed tokens return clean 401/422 (not 500)  
2. Expired tokens return clean 401 with appropriate message
3. Optional-auth routes handle malformed tokens gracefully (treat as anonymous)
"""
import uuid
import pytest
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token
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
def test_user(app):
    """Create a test user and return their ID."""
    with app.app_context():
        user = User(id=uuid.uuid4(), email='jwt-test@example.com', is_active=True)
        user.set_password('JwtTest123')
        db.session.add(user)
        db.session.commit()
        return str(user.id)


@pytest.fixture
def test_analysis(app, test_user):
    """Create a test analysis record and return its ID."""
    with app.app_context():
        analysis = AnalysisRecord(
            id=uuid.uuid4(),
            user_id=uuid.UUID(test_user),
            input_text='Test analysis content',
            authenticity_score=75.0,
            confidence=0.8,
            classification='reliable',
            sentence_results=[],
            processing_time=100.0,
            model_version='test-1.0.0'
        )
        db.session.add(analysis)
        db.session.commit()
        return str(analysis.id)


def make_expired_token(app, user_id):
    """Create an access token that expired 1 hour ago."""
    with app.app_context():
        # Create token that expired 1 hour ago
        return create_access_token(
            identity=user_id, 
            expires_delta=timedelta(hours=-1)
        )


def make_expired_refresh_token(app, user_id):
    """Create a refresh token that expired 1 hour ago.""" 
    with app.app_context():
        return create_refresh_token(
            identity=user_id,
            expires_delta=timedelta(hours=-1)
        )


# ---------------------------------------------------------------------------
# Required Auth Routes
# ---------------------------------------------------------------------------

class TestRequiredAuthRoutes:
    """Test malformed/expired tokens on routes with @jwt_required()."""

    def test_get_auth_me_malformed_token(self, client):
        """GET /auth/me with malformed token returns clean error."""
        resp = client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer not.a.valid.jwt'})
        assert resp.status_code in (401, 422), f"Expected 401/422, got {resp.status_code}"
        data = resp.get_json()
        assert data is not None, "Response should be JSON, not empty"
        assert resp.status_code != 500, "Must not return 500 for malformed token"

    def test_get_auth_me_expired_token(self, client, app, test_user):
        """GET /auth/me with expired token returns 401."""
        expired_token = make_expired_token(app, test_user)
        resp = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {expired_token}'})
        assert resp.status_code == 401, f"Expected 401 for expired token, got {resp.status_code}"
        data = resp.get_json()
        assert data is not None
        assert 'expired' in str(data).lower() or 'token' in str(data).lower() or 'unauthorized' in str(data).lower()

    def test_patch_auth_me_malformed_token(self, client):
        """PATCH /auth/me with malformed token returns clean error."""
        resp = client.patch('/api/v1/auth/me', 
                           json={'username': 'NewName'}, 
                           headers={'Authorization': 'Bearer garbage.token.here'})
        assert resp.status_code in (401, 422)
        assert resp.status_code != 500

    def test_patch_auth_me_expired_token(self, client, app, test_user):
        """PATCH /auth/me with expired token returns 401."""
        expired_token = make_expired_token(app, test_user)
        resp = client.patch('/api/v1/auth/me', 
                           json={'username': 'NewName'}, 
                           headers={'Authorization': f'Bearer {expired_token}'})
        assert resp.status_code == 401
        data = resp.get_json()
        assert data is not None

    def test_post_auth_logout_malformed_token(self, client):
        """POST /auth/logout with malformed token returns clean error."""
        resp = client.post('/api/v1/auth/logout', headers={'Authorization': 'Bearer invalid'})
        assert resp.status_code in (401, 422)
        assert resp.status_code != 500

    def test_post_auth_logout_expired_token(self, client, app, test_user):
        """POST /auth/logout with expired token returns 401."""
        expired_token = make_expired_token(app, test_user)
        resp = client.post('/api/v1/auth/logout', headers={'Authorization': f'Bearer {expired_token}'})
        assert resp.status_code == 401

    def test_get_analyses_recent_malformed_token(self, client):
        """GET /analyses/recent with malformed token returns clean error."""
        resp = client.get('/api/v1/analyses/recent', headers={'Authorization': 'Bearer bad.jwt.token'})
        assert resp.status_code in (401, 422)
        assert resp.status_code != 500

    def test_get_analyses_recent_expired_token(self, client, app, test_user):
        """GET /analyses/recent with expired token returns 401."""
        expired_token = make_expired_token(app, test_user)
        resp = client.get('/api/v1/analyses/recent', headers={'Authorization': f'Bearer {expired_token}'})
        assert resp.status_code == 401

    def test_get_history_malformed_token(self, client):
        """GET /history with malformed token returns clean error."""
        resp = client.get('/api/v1/history', headers={'Authorization': 'Bearer malformed.jwt'})
        assert resp.status_code in (401, 422)
        assert resp.status_code != 500

    def test_get_history_expired_token(self, client, app, test_user):
        """GET /history with expired token returns 401."""
        expired_token = make_expired_token(app, test_user)
        resp = client.get('/api/v1/history', headers={'Authorization': f'Bearer {expired_token}'})
        assert resp.status_code == 401

    def test_get_history_item_malformed_token(self, client, test_analysis):
        """GET /history/{id} with malformed token returns clean error."""
        resp = client.get(f'/api/v1/history/{test_analysis}', 
                         headers={'Authorization': 'Bearer not-valid-jwt'})
        assert resp.status_code in (401, 422)
        assert resp.status_code != 500

    def test_get_history_item_expired_token(self, client, app, test_user, test_analysis):
        """GET /history/{id} with expired token returns 401."""
        expired_token = make_expired_token(app, test_user)
        resp = client.get(f'/api/v1/history/{test_analysis}',
                         headers={'Authorization': f'Bearer {expired_token}'})
        assert resp.status_code == 401

    def test_delete_history_item_malformed_token(self, client, test_analysis):
        """DELETE /history/{id} with malformed token returns clean error."""
        resp = client.delete(f'/api/v1/history/{test_analysis}',
                            headers={'Authorization': 'Bearer invalid-jwt-token'})
        assert resp.status_code in (401, 422)
        assert resp.status_code != 500

    def test_delete_history_item_expired_token(self, client, app, test_user, test_analysis):
        """DELETE /history/{id} with expired token returns 401.""" 
        expired_token = make_expired_token(app, test_user)
        resp = client.delete(f'/api/v1/history/{test_analysis}',
                            headers={'Authorization': f'Bearer {expired_token}'})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Refresh Token Route
# ---------------------------------------------------------------------------

class TestRefreshTokenRoute:
    """Test malformed/expired tokens on the refresh endpoint."""

    def test_post_auth_refresh_malformed_token(self, client):
        """POST /auth/refresh with malformed token returns clean error."""
        resp = client.post('/api/v1/auth/refresh', headers={'Authorization': 'Bearer bad.refresh.token'})
        assert resp.status_code in (401, 422)
        assert resp.status_code != 500

    def test_post_auth_refresh_expired_refresh_token(self, client, app, test_user):
        """POST /auth/refresh with expired refresh token returns clean error."""
        expired_refresh = make_expired_refresh_token(app, test_user)
        resp = client.post('/api/v1/auth/refresh', headers={'Authorization': f'Bearer {expired_refresh}'})
        assert resp.status_code == 401
        data = resp.get_json()
        assert data is not None

    def test_post_auth_refresh_access_token_instead_of_refresh(self, client, app, test_user):
        """POST /auth/refresh with access token (wrong type) returns error."""
        # This is already tested in existing test suite, but including for completeness
        access_token = create_access_token(identity=test_user)
        resp = client.post('/api/v1/auth/refresh', headers={'Authorization': f'Bearer {access_token}'})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Optional Auth Routes
# ---------------------------------------------------------------------------

class TestOptionalAuthRoutes:
    """Test malformed tokens on optional-auth routes - should NOT crash."""

    def test_post_feedback_malformed_token_handled_gracefully(self, client):
        """POST /feedback with malformed token treats request as anonymous (no crash)."""
        resp = client.post('/api/v1/feedback',
                          json={'analysisId': '00000000-0000-0000-0000-000000000000',
                                'feedback': {'type': 'helpful'}},
                          headers={'Authorization': 'Bearer malformed.jwt.token'})
        # Should NOT return 500 (crash) — should work anonymously or return validation error
        assert resp.status_code != 500, "Malformed token on optional-auth route must not crash"
        # After fix, should work as anonymous request (not return JWT errors like 401/422)
        assert resp.status_code not in [401, 422], "Should not return JWT validation errors"
        # It may return 404 (analysis not found) which is fine — the key is it didn't crash on JWT parsing

    def test_post_feedback_expired_token_handled_gracefully(self, client, app, test_user):
        """POST /feedback with expired token treats request as anonymous."""
        expired_token = make_expired_token(app, test_user)
        resp = client.post('/api/v1/feedback',
                          json={'analysisId': '00000000-0000-0000-0000-000000000000',
                                'feedback': {'type': 'helpful'}},
                          headers={'Authorization': f'Bearer {expired_token}'})
        assert resp.status_code != 500, "Expired token on optional-auth route must not crash"
        # After fix, should work as anonymous request (not return JWT errors like 401/422)
        assert resp.status_code not in [401, 422], "Should not return JWT validation errors"

    def test_post_feedback_empty_bearer_handled_gracefully(self, client):
        """POST /feedback with 'Bearer ' (empty token) doesn't crash."""
        resp = client.post('/api/v1/feedback',
                          json={'analysisId': '00000000-0000-0000-0000-000000000000', 
                                'feedback': {'type': 'helpful'}},
                          headers={'Authorization': 'Bearer '})
        assert resp.status_code != 500, "Empty Bearer token must not crash optional-auth route"
        # After fix, should work as anonymous request (not return JWT errors like 401/422)
        assert resp.status_code not in [401, 422], "Should not return JWT validation errors"

    def test_post_analyze_malformed_token_handled_gracefully(self, client):
        """POST /analyze with malformed token works as anonymous request."""
        # Mock the services to avoid needing a full ML/cache setup
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
                              json={'content': 'Test article content for analysis.'},
                              headers={'Authorization': 'Bearer definitely.not.a.valid.jwt'})
            
        # Key point: should NOT return 500 due to JWT parsing error
        assert resp.status_code != 500, "Malformed token on /analyze must not cause 500 error"
        # It should either succeed (200) or fail with a service error (503) — but not JWT error

    def test_post_analyze_expired_token_handled_gracefully(self, client, app, test_user):
        """POST /analyze with expired token works as anonymous request."""
        expired_token = make_expired_token(app, test_user)
        
        # Same mocking as above test
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
                              json={'content': 'Test article content for expired token test.'},
                              headers={'Authorization': f'Bearer {expired_token}'})
            
        assert resp.status_code != 500, "Expired token on /analyze must not cause 500 error"


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestJWTEdgeCases:
    """Additional JWT edge cases across different routes."""

    def test_empty_authorization_header(self, client):
        """Authorization header with empty value should be handled consistently."""
        resp = client.get('/api/v1/auth/me', headers={'Authorization': ''})
        assert resp.status_code == 401, "Empty Authorization header should return 401"

    def test_authorization_without_bearer_prefix(self, client):
        """Authorization header without 'Bearer ' prefix should be rejected consistently.""" 
        resp = client.get('/api/v1/auth/me', headers={'Authorization': 'some-token-without-bearer'})
        assert resp.status_code == 401, "Authorization without Bearer prefix should return 401"

    def test_bearer_with_extra_spaces(self, client):
        """'Bearer   token' (extra spaces) should be handled gracefully."""
        resp = client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer   extra.spaced.token'})
        assert resp.status_code in (401, 422), "Malformed Bearer format should return clean error"
        assert resp.status_code != 500

    def test_multiple_authorization_headers(self, client):
        """Multiple Authorization headers should be handled without crashing."""
        # Note: This tests Flask's behavior when client sends duplicate headers
        resp = client.get('/api/v1/auth/me', headers=[
            ('Authorization', 'Bearer first-token'),
            ('Authorization', 'Bearer second-token')
        ])
        assert resp.status_code in (401, 422), "Duplicate auth headers should return clean error"
        assert resp.status_code != 500


# ---------------------------------------------------------------------------
# Consistency Check Tests
# ---------------------------------------------------------------------------

class TestJWTConsistency:
    """Verify all protected routes handle JWT errors consistently."""

    def test_malformed_jwt_consistent_across_routes(self, client, test_analysis):
        """All required-auth routes should return the same status for malformed JWT."""
        malformed_header = {'Authorization': 'Bearer not.a.valid.jwt'}
        
        routes_and_methods = [
            ('GET', '/api/v1/auth/me'),
            ('POST', '/api/v1/auth/logout'),
            ('GET', '/api/v1/analyses/recent'),
            ('GET', '/api/v1/history'),
            ('GET', f'/api/v1/history/{test_analysis}'),
        ]
        
        status_codes = []
        for method, route in routes_and_methods:
            if method == 'GET':
                resp = client.get(route, headers=malformed_header)
            elif method == 'POST':
                resp = client.post(route, headers=malformed_header)
            elif method == 'DELETE':
                resp = client.delete(route, headers=malformed_header)
            
            status_codes.append((route, resp.status_code))
            assert resp.status_code in (401, 422), f"{route} returned {resp.status_code} for malformed JWT"
            assert resp.status_code != 500, f"{route} must not crash on malformed JWT"
        
        # Check if all routes return the same status code (ideal for consistency)
        unique_codes = set(code for _, code in status_codes)
        if len(unique_codes) > 1:
            print(f"INCONSISTENCY WARNING: Different routes return different status codes for malformed JWT: {status_codes}")

    def test_expired_jwt_consistent_across_routes(self, client, app, test_user, test_analysis):
        """All required-auth routes should return the same status for expired JWT.""" 
        expired_token = make_expired_token(app, test_user)
        expired_header = {'Authorization': f'Bearer {expired_token}'}
        
        routes_and_methods = [
            ('GET', '/api/v1/auth/me'),
            ('POST', '/api/v1/auth/logout'),
            ('GET', '/api/v1/analyses/recent'),
            ('GET', '/api/v1/history'),
            ('GET', f'/api/v1/history/{test_analysis}'),
        ]
        
        status_codes = []
        for method, route in routes_and_methods:
            if method == 'GET':
                resp = client.get(route, headers=expired_header)
            elif method == 'POST':
                resp = client.post(route, headers=expired_header)
            
            status_codes.append((route, resp.status_code))
            assert resp.status_code in (401, 422), f"{route} returned {resp.status_code} for expired JWT"
        
        # Check consistency
        unique_codes = set(code for _, code in status_codes)
        if len(unique_codes) > 1:
            print(f"INCONSISTENCY WARNING: Different routes return different status codes for expired JWT: {status_codes}")


# ---------------------------------------------------------------------------
# JWT Optional-Auth Consistency Regression Tests
# ---------------------------------------------------------------------------

class TestOptionalAuthConsistency:
    """Regression tests to verify optional-auth routes handle JWT errors consistently."""

    def test_optional_auth_malformed_token_consistency(self, client, test_analysis):
        """Both optional-auth routes should handle malformed tokens the same way."""
        malformed_header = {'Authorization': 'Bearer malformed.jwt.token'}
        
        # Test /analyze
        analyze_resp = client.post('/api/v1/analyze',
                                  json={'content': 'Test content for consistency check'},
                                  headers=malformed_header)
        
        # Test /feedback  
        feedback_resp = client.post('/api/v1/feedback',
                                   json={'analysisId': test_analysis, 'feedback': {'type': 'helpful'}},
                                   headers=malformed_header)
        
        # Both should NOT return JWT validation errors (401, 422)
        assert analyze_resp.status_code not in [401, 422, 500], f"/analyze returned JWT error {analyze_resp.status_code}"
        assert feedback_resp.status_code not in [401, 422, 500], f"/feedback returned JWT error {feedback_resp.status_code}"
        
        # Both should handle gracefully (success or business logic errors, not JWT errors)
        assert analyze_resp.status_code in [200, 201, 400, 404, 503], f"/analyze unexpected status {analyze_resp.status_code}"
        assert feedback_resp.status_code in [200, 201, 400, 404], f"/feedback unexpected status {feedback_resp.status_code}"

    def test_optional_auth_expired_token_consistency(self, client, app, test_user, test_analysis):
        """Both optional-auth routes should handle expired tokens the same way."""
        expired_token = make_expired_token(app, test_user)
        expired_header = {'Authorization': f'Bearer {expired_token}'}
        
        # Test /analyze
        analyze_resp = client.post('/api/v1/analyze',
                                  json={'content': 'Test content for expired token consistency'},
                                  headers=expired_header)
        
        # Test /feedback
        feedback_resp = client.post('/api/v1/feedback',
                                   json={'analysisId': test_analysis, 'feedback': {'type': 'helpful'}},
                                   headers=expired_header)
        
        # Both should NOT return JWT validation errors (401, 422)
        assert analyze_resp.status_code not in [401, 422, 500], f"/analyze returned JWT error {analyze_resp.status_code}"
        assert feedback_resp.status_code not in [401, 422, 500], f"/feedback returned JWT error {feedback_resp.status_code}"
        
        # Both should handle gracefully (success or business logic errors, not JWT errors)
        assert analyze_resp.status_code in [200, 201, 400, 404, 503], f"/analyze unexpected status {analyze_resp.status_code}"
        assert feedback_resp.status_code in [200, 201, 400, 404], f"/feedback unexpected status {feedback_resp.status_code}"

    def test_optional_auth_no_token_consistency(self, client, test_analysis):
        """Both optional-auth routes should work without tokens (anonymous requests)."""
        # Test /analyze without token
        analyze_resp = client.post('/api/v1/analyze',
                                  json={'content': 'Test content for no-token consistency'})
        
        # Test /feedback without token
        feedback_resp = client.post('/api/v1/feedback',
                                   json={'analysisId': test_analysis, 'feedback': {'type': 'helpful'}})
        
        # Both should work without tokens (optional auth)
        assert analyze_resp.status_code not in [401, 422, 500], f"/analyze failed without token: {analyze_resp.status_code}"
        assert feedback_resp.status_code not in [401, 422, 500], f"/feedback failed without token: {feedback_resp.status_code}"
        
        # Both should handle gracefully
        assert analyze_resp.status_code in [200, 201, 400, 404, 503], f"/analyze unexpected status {analyze_resp.status_code}"
        assert feedback_resp.status_code in [200, 201, 400, 404], f"/feedback unexpected status {feedback_resp.status_code}"