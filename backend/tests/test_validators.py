"""
Tests for input validation module.
"""
import pytest
from app.validators import (
    validate_content,
    validate_source_url,
    validate_title,
    validate_analyze_request,
    validate_feedback_request,
    validate_auth_request,
    ValidationError,
    MIN_CONTENT_LENGTH,
    MAX_CONTENT_LENGTH
)


class TestValidateContent:
    """Tests for content validation."""
    
    def test_valid_content_length(self):
        """Valid content within range should pass."""
        content = "This is valid content for analysis."
        is_valid, error = validate_content(content)
        assert is_valid is True
        assert error is None
    
    def test_empty_content(self):
        """Empty content should fail with INVALID_INPUT."""
        is_valid, error = validate_content("")
        assert is_valid is False
        assert error is not None
        assert error.code == 'INVALID_INPUT'
        assert "1 and 50,000 characters" in error.message
    
    def test_whitespace_only_content(self):
        """Whitespace-only content should fail."""
        is_valid, error = validate_content("   \n\t  ")
        assert is_valid is False
        assert error.code == 'INVALID_INPUT'
    
    def test_content_at_min_length(self):
        """Content at minimum length (1 char) should pass."""
        is_valid, error = validate_content("a")
        assert is_valid is True
        assert error is None
    
    def test_content_at_max_length(self):
        """Content at maximum length should pass."""
        content = "x" * MAX_CONTENT_LENGTH
        is_valid, error = validate_content(content)
        assert is_valid is True
        assert error is None
    
    def test_content_exceeds_max_length(self):
        """Content exceeding max length should fail."""
        content = "x" * (MAX_CONTENT_LENGTH + 1)
        is_valid, error = validate_content(content)
        assert is_valid is False
        assert error.code == 'INVALID_INPUT'
        assert "50,000 characters" in error.message
    
    def test_none_content(self):
        """None content should fail."""
        is_valid, error = validate_content(None)
        assert is_valid is False
        assert error.code == 'INVALID_INPUT'
    
    def test_content_with_unicode(self):
        """Content with unicode characters should be valid."""
        content = "This contains unicode: café, naïve, résumé"
        is_valid, error = validate_content(content)
        assert is_valid is True
    
    def test_very_long_content(self):
        """Very long content near max should be valid."""
        content = "a" * MAX_CONTENT_LENGTH  # Exactly 50000 chars
        assert len(content) == MAX_CONTENT_LENGTH
        is_valid, error = validate_content(content)
        assert is_valid is True


class TestValidateSourceUrl:
    """Tests for source URL validation."""
    
    def test_valid_https_url(self):
        """Valid HTTPS URL should pass."""
        is_valid, error = validate_source_url("https://example.com/article")
        assert is_valid is True
        assert error is None
    
    def test_valid_http_url(self):
        """Valid HTTP URL should pass."""
        is_valid, error = validate_source_url("http://example.com/article")
        assert is_valid is True
    
    def test_valid_url_with_port(self):
        """Valid URL with port should pass."""
        is_valid, error = validate_source_url("https://example.com:8080/article")
        assert is_valid is True
    
    def test_valid_localhost_url(self):
        """Localhost URL should pass."""
        is_valid, error = validate_source_url("http://localhost:3000")
        assert is_valid is True
    
    def test_invalid_url_no_protocol(self):
        """URL without protocol should fail."""
        is_valid, error = validate_source_url("example.com")
        assert is_valid is False
        assert error.code == 'INVALID_INPUT'
        assert "Invalid URL format" in error.message
    
    def test_invalid_url_random_string(self):
        """Random string should fail as URL."""
        is_valid, error = validate_source_url("not a url")
        assert is_valid is False
        assert error.code == 'INVALID_INPUT'
    
    def test_empty_url(self):
        """Empty URL should be valid (optional field)."""
        is_valid, error = validate_source_url("")
        assert is_valid is True
        assert error is None
    
    def test_none_url(self):
        """None URL should be valid (optional field)."""
        is_valid, error = validate_source_url(None)
        assert is_valid is True
    
    def test_valid_url_with_query_params(self):
        """URL with query parameters should pass."""
        is_valid, error = validate_source_url(
            "https://example.com/search?q=test&page=1"
        )
        assert is_valid is True
    
    def test_valid_ip_url(self):
        """URL with IP address should pass."""
        is_valid, error = validate_source_url("http://192.168.1.1/article")
        assert is_valid is True


class TestValidateTitle:
    """Tests for title validation."""
    
    def test_valid_title(self):
        """Valid title should pass."""
        is_valid, error = validate_title("Breaking News: Something Happened")
        assert is_valid is True
        assert error is None
    
    def test_empty_title(self):
        """Empty title should be valid (optional)."""
        is_valid, error = validate_title("")
        assert is_valid is True
    
    def test_none_title(self):
        """None title should be valid (optional)."""
        is_valid, error = validate_title(None)
        assert is_valid is True
    
    def test_title_exceeds_max_length(self):
        """Title exceeding 500 chars should fail."""
        title = "x" * 501
        is_valid, error = validate_title(title)
        assert is_valid is False
        assert error.code == 'INVALID_INPUT'
        assert "500 characters" in error.message
    
    def test_title_at_max_length(self):
        """Title at max length should pass."""
        title = "x" * 500
        is_valid, error = validate_title(title)
        assert is_valid is True


class TestValidateAnalyzeRequest:
    """Tests for full analyze request validation."""
    
    def test_valid_request(self):
        """Valid request should pass."""
        data = {
            'content': 'This is article content for analysis.'
        }
        is_valid, error = validate_analyze_request(data)
        assert is_valid is True
        assert error is None
    
    def test_valid_request_with_all_fields(self):
        """Request with all fields should pass."""
        data = {
            'content': 'Article content here.',
            'sourceUrl': 'https://example.com/article',
            'title': 'Test Article'
        }
        is_valid, error = validate_analyze_request(data)
        assert is_valid is True
    
    def test_valid_request_with_text_field(self):
        """Request using 'text' instead of 'content' should pass."""
        data = {
            'text': 'Article content here.'
        }
        is_valid, error = validate_analyze_request(data)
        assert is_valid is True
    
    def test_empty_content_fails(self):
        """Empty content should fail."""
        data = {
            'content': ''
        }
        is_valid, error = validate_analyze_request(data)
        assert is_valid is False
        assert "content" in error.details.get('field', '')
    
    def test_too_long_content_fails(self):
        """Content exceeding max should fail."""
        data = {
            'content': 'x' * 50001
        }
        is_valid, error = validate_analyze_request(data)
        assert is_valid is False
    
    def test_invalid_url_fails(self):
        """Invalid sourceUrl should fail."""
        data = {
            'content': 'Valid content here.',
            'sourceUrl': 'not-a-url'
        }
        is_valid, error = validate_analyze_request(data)
        assert is_valid is False
        assert error.details.get('field') == 'sourceUrl'
    
    def test_missing_content_fails(self):
        """Missing content should fail."""
        data = {
            'title': 'Test'
        }
        is_valid, error = validate_analyze_request(data)
        assert is_valid is False
    
    def test_none_data_fails(self):
        """None data should fail."""
        is_valid, error = validate_analyze_request(None)
        assert is_valid is False
    
    def test_empty_dict_fails(self):
        """Empty dict should fail."""
        is_valid, error = validate_analyze_request({})
        assert is_valid is False


class TestValidateFeedbackRequest:
    """Tests for feedback request validation."""
    
    def test_valid_feedback(self):
        """Valid feedback should pass."""
        data = {
            'analysisId': '123e4567-e89b-12d3-a456-426614174000',
            'feedback': {
                'type': 'helpful'
            }
        }
        is_valid, error = validate_feedback_request(data)
        assert is_valid is True
    
    def test_invalid_feedback_type(self):
        """Invalid feedback type should fail."""
        data = {
            'analysisId': '123e4567-e89b-12d3-a456-426614174000',
            'feedback': {
                'type': 'invalid_type'
            }
        }
        is_valid, error = validate_feedback_request(data)
        assert is_valid is False
        assert error.code == 'INVALID_INPUT'
    
    def test_missing_analysis_id(self):
        """Missing analysisId should fail."""
        data = {
            'feedback': {
                'type': 'helpful'
            }
        }
        is_valid, error = validate_feedback_request(data)
        assert is_valid is False
    
    def test_all_valid_feedback_types(self):
        """All valid feedback types should pass."""
        valid_types = ['helpful', 'incorrect', 'disputed']
        for feedback_type in valid_types:
            data = {
                'analysisId': '123e4567-e89b-12d3-a456-426614174000',
                'feedback': {
                    'type': feedback_type
                }
            }
            is_valid, error = validate_feedback_request(data)
            assert is_valid is True, f"Type {feedback_type} should be valid"


class TestValidateAuthRequest:
    """Tests for authentication request validation."""
    
    def test_valid_registration(self):
        """Valid registration data should pass."""
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123'  # Meets all security requirements
        }
        is_valid, error = validate_auth_request(data)
        assert is_valid is True
    
    def test_invalid_email_format(self):
        """Invalid email format should fail."""
        data = {
            'email': 'not-an-email',
            'password': 'securepassword123'
        }
        is_valid, error = validate_auth_request(data)
        assert is_valid is False
        assert "email" in error.details.get('field', '')
    
    def test_missing_email(self):
        """Missing email should fail."""
        data = {
            'password': 'securepassword123'
        }
        is_valid, error = validate_auth_request(data)
        assert is_valid is False
    
    def test_missing_password(self):
        """Missing password should fail."""
        data = {
            'email': 'test@example.com'
        }
        is_valid, error = validate_auth_request(data)
        assert is_valid is False
    
    def test_password_too_short(self):
        """Password too short should fail."""
        data = {
            'email': 'test@example.com',
            'password': 'short'
        }
        is_valid, error = validate_auth_request(data)
        assert is_valid is False
        assert "8 characters" in error.message
    
    def test_password_at_minimum_length(self):
        """Password at minimum length should pass."""
        data = {
            'email': 'test@example.com',
            'password': '12345678Aa'  # 10 chars, meets all requirements
        }
        is_valid, error = validate_auth_request(data)
        assert is_valid is True


class TestValidationError:
    """Tests for ValidationError class."""
    
    def test_error_to_dict(self):
        """Error should convert to dict correctly."""
        error = ValidationError(
            code='INVALID_INPUT',
            message='Test error',
            details={'field': 'test'}
        )
        result = error.to_dict()
        assert result['error']['code'] == 'INVALID_INPUT'
        assert result['error']['message'] == 'Test error'
        assert result['error']['details']['field'] == 'test'
    
    def test_error_without_details(self):
        """Error without details should work."""
        error = ValidationError(
            code='INVALID_INPUT',
            message='Test error'
        )
        result = error.to_dict()
        assert result['error']['details'] == {}