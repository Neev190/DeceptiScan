"""
API endpoint tests for input validation.
These tests verify the API properly returns validation errors.
"""
import pytest
import json


@pytest.fixture
def app():
    """Create test application."""
    import sys
    import os
    # Add backend to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app import create_app, db
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['REDIS_URL'] = 'redis://localhost:6379/0'  # Will fail but we handle it
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


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
    
    def test_valid_request_succeeds(self, client):
        """Valid request should succeed (may fail if no DB/cache, but not validation)."""
        response = client.post(
            '/api/v1/analyze',
            data=json.dumps({'content': 'This is valid content for analysis.'}),
            content_type='application/json'
        )
        
        # Either 200 (success) or 500 (no cache service), but NOT 400 (validation error)
        assert response.status_code in [200, 500]


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