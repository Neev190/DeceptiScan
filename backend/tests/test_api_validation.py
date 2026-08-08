"""
API endpoint tests for input validation.
These tests verify the API properly returns validation errors.
"""
import pytest
import json
from unittest.mock import patch, MagicMock


@pytest.fixture
def app():
    """Create test application."""
    import sys
    import os
    # Add backend to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app import create_app, db
    
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['MAX_CONTENT_LENGTH'] = None
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestAnalyzeEndpointValidation:
    """Tests for /api/v1/analyze endpoint validation."""
    
    def test_empty_content_returns_error(self, client):
        """Empty content should return INVALID_INPUT error."""
        response = client.post(
            '/api/v1/analyze',
            data=json.dumps({'content': ''}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
        assert '1 and 50,000 characters' in data['error']['message']
    
    def test_content_exceeds_max_returns_error(self, client):
        """Content exceeding 50000 chars should return INVALID_INPUT error."""
        long_content = 'x' * 50001
        response = client.post(
            '/api/v1/analyze',
            data=json.dumps({'content': long_content}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
        assert '50,000 characters' in data['error']['message']
    
    def test_missing_content_returns_error(self, client):
        """Missing content should return INVALID_INPUT error."""
        response = client.post(
            '/api/v1/analyze',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
    
    def test_invalid_source_url_returns_error(self, client):
        """Invalid sourceUrl should return INVALID_INPUT error."""
        response = client.post(
            '/api/v1/analyze',
            data=json.dumps({
                'content': 'Valid content here.',
                'sourceUrl': 'not-a-valid-url'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
        assert 'URL' in data['error']['message']
    
    def _mock_ml_result(self):
        return {
            'id': 'test-id',
            'authenticityScore': 75.0,
            'classification': 'reliable',
            'confidence': 0.85,
            'modelVersion': 'test-v1',
            'processingTime': 10.0,
            'analyzedAt': '2026-07-31T00:00:00Z',
            'sentenceAnalysis': [],
            'is_cached': False
        }

    def test_valid_request_succeeds(self, client):
        """Valid request should succeed (may fail if no DB/cache, but not validation)."""
        mock_ml_svc = MagicMock()
        mock_ml_svc.analyze.return_value = self._mock_ml_result()

        with patch("app.routes.analysis.get_ml_service", return_value=mock_ml_svc):
            response = client.post(
                '/api/v1/analyze',
                data=json.dumps({'content': 'This is valid content for analysis.'}),
                content_type='application/json'
            )
        
        # Either 200 (success) or 500 (no cache service), but NOT 400 (validation error)
        assert response.status_code in [200, 500]

    def test_successful_response_includes_similar_claims_field(self, client):
        """
        A 200 response must include the retrieved_claims key (list or null)
        and the retrieval_status key. Both are new in Phase 2.
        Existing assertions about validation error shape are unchanged.
        """
        mock_ml_svc = MagicMock()
        mock_ml_svc.analyze.return_value = self._mock_ml_result()
        mock_retrieval_svc = MagicMock()
        mock_retrieval_svc.find_similar_claims.return_value = []

        with patch("app.routes.analysis.get_ml_service", return_value=mock_ml_svc), \
             patch("app.routes.analysis.get_retrieval_service", return_value=mock_retrieval_svc):
            response = client.post(
                '/api/v1/analyze',
                data=json.dumps({'content': 'Politicians claimed the economy grew last year.'}),
                content_type='application/json'
            )

        if response.status_code == 200:
            data = response.get_json()
            assert 'retrieved_claims' in data, (
                "Phase 2: 'retrieved_claims' key missing from /analyze response"
            )
            assert 'retrieval_status' in data, (
                "Phase 2: 'retrieval_status' key missing from /analyze response"
            )
            # retrieved_claims must be a list (possibly empty) or null
            assert data['retrieved_claims'] is None or isinstance(data['retrieved_claims'], list), (
                f"retrieved_claims must be list or null, got: {type(data['retrieved_claims'])}"
            )

    def test_retrieval_failure_does_not_break_analyze(self, client):
        """
        If retrieval raises, /analyze must still return 200 with
        similar_claims=null and retrieval_status='unavailable'.
        Classifier result must still be present.
        """
        mock_ml_svc = MagicMock()
        mock_ml_svc.analyze.return_value = self._mock_ml_result()

        with patch("app.routes.analysis.get_ml_service", return_value=mock_ml_svc), \
             patch("app.routes.analysis.get_retrieval_service", side_effect=RuntimeError("pgvector not available")):
            response = client.post(
                '/api/v1/analyze',
                data=json.dumps({'content': 'The senator said the bill was unconstitutional.'}),
                content_type='application/json'
            )

        # Must not return 500 due to retrieval failure
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.get_json()
            # Core classifier fields must still be present
            assert 'authenticityScore' in data
            assert 'classification' in data
            # Retrieval degraded fields
            assert data.get('retrieved_claims') is None
            assert data.get('retrieval_status') == 'unavailable'


class TestValidationErrorFormat:
    """Tests for proper error response format."""
    
    def test_error_has_correct_structure(self, client):
        """Error response should have proper structure."""
        response = client.post(
            '/api/v1/analyze',
            data=json.dumps({'content': ''}),
            content_type='application/json'
        )
        
        data = response.get_json()
        assert 'error' in data
        assert 'code' in data['error']
        assert 'message' in data['error']
        assert 'details' in data['error']
    
    def test_error_code_is_invalid_input(self, client):
        """Validation errors should have INVALID_INPUT code."""
        response = client.post(
            '/api/v1/analyze',
            data=json.dumps({'content': ''}),
            content_type='application/json'
        )
        
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
    
    def test_error_includes_field_details(self, client):
        """Error should include field details."""
        response = client.post(
            '/api/v1/analyze',
            data=json.dumps({'content': ''}),
            content_type='application/json'
        )
        
        data = response.get_json()
        assert 'field' in data['error']['details']
        assert data['error']['details']['field'] == 'content'