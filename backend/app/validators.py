"""
Input validation utilities for DeceptiScan API.
"""
import re
from typing import Tuple, Optional
from urllib.parse import urlparse


# Validation constants
MIN_CONTENT_LENGTH = 1
MAX_CONTENT_LENGTH = 50000

# URL regex pattern for validation
URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
    r'localhost|'  # localhost
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', 
    re.IGNORECASE
)


class ValidationError:
    """Represents a validation error with code and message."""
    
    def __init__(self, code: str, message: str, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            'error': {
                'code': self.code,
                'message': self.message,
                'details': self.details
            }
        }


def validate_content(content: str) -> Tuple[bool, Optional[ValidationError]]:
    """
    Validate article content length.
    
    Args:
        content: The article text content
        
    Returns:
        Tuple of (is_valid, error)
    """
    if content is None:
        return False, ValidationError(
            code='INVALID_INPUT',
            message='Article content must be between 1 and 50,000 characters',
            details={
                'field': 'content',
                'minLength': MIN_CONTENT_LENGTH,
                'maxLength': MAX_CONTENT_LENGTH
            }
        )
    
    content_str = str(content).strip()
    content_length = len(content_str)
    
    if content_length < MIN_CONTENT_LENGTH:
        return False, ValidationError(
            code='INVALID_INPUT',
            message='Article content must be between 1 and 50,000 characters',
            details={
                'field': 'content',
                'minLength': MIN_CONTENT_LENGTH,
                'maxLength': MAX_CONTENT_LENGTH,
                'actualLength': content_length
            }
        )
    
    if content_length > MAX_CONTENT_LENGTH:
        return False, ValidationError(
            code='INVALID_INPUT',
            message='Article content must be between 1 and 50,000 characters',
            details={
                'field': 'content',
                'minLength': MIN_CONTENT_LENGTH,
                'maxLength': MAX_CONTENT_LENGTH,
                'actualLength': content_length
            }
        )
    
    return True, None


def validate_source_url(url: str) -> Tuple[bool, Optional[ValidationError]]:
    """
    Validate source URL format.
    
    Args:
        url: The source URL string
        
    Returns:
        Tuple of (is_valid, error)
    """
    if url is None or url == '':
        # URL is optional, so empty is valid
        return True, None
    
    url_str = str(url).strip()
    
    if not url_str:
        return True, None
    
    # Check URL format using regex pattern
    if not URL_PATTERN.match(url_str):
        # Also try urlparse as fallback
        try:
            parsed = urlparse(url_str)
            if not parsed.scheme or not parsed.netloc:
                return False, ValidationError(
                    code='INVALID_INPUT',
                    message='Invalid URL format. Please provide a valid URL (e.g., https://example.com)',
                    details={
                        'field': 'sourceUrl',
                        'provided': url_str
                    }
                )
        except Exception:
            return False, ValidationError(
                code='INVALID_INPUT',
                message='Invalid URL format. Please provide a valid URL (e.g., https://example.com)',
                details={
                    'field': 'sourceUrl',
                    'provided': url_str
                }
            )
    
    return True, None


def validate_title(title: str) -> Tuple[bool, Optional[ValidationError]]:
    """
    Validate article title.
    
    Args:
        title: The article title
        
    Returns:
        Tuple of (is_valid, error)
    """
    if title is None or title == '':
        # Title is optional
        return True, None
    
    title_str = str(title).strip()
    
    if len(title_str) > 500:
        return False, ValidationError(
            code='INVALID_INPUT',
            message='Title must not exceed 500 characters',
            details={
                'field': 'title',
                'maxLength': 500,
                'actualLength': len(title_str)
            }
        )
    
    return True, None


def validate_analyze_request(data: dict) -> Tuple[bool, Optional[ValidationError]]:
    """
    Validate the full analyze request.
    
    Args:
        data: The request data dictionary
        
    Returns:
        Tuple of (is_valid, error)
    """
    if not data:
        return False, ValidationError(
            code='INVALID_INPUT',
            message='Request body is required',
            details={}
        )
    
    # Validate content (required)
    content = data.get('content') or data.get('text')
    is_valid, error = validate_content(content)
    if not is_valid:
        return False, error
    
    # Validate sourceUrl (optional)
    source_url = data.get('sourceUrl') or data.get('url')
    is_valid, error = validate_source_url(source_url)
    if not is_valid:
        return False, error
    
    # Validate title (optional)
    title = data.get('title')
    is_valid, error = validate_title(title)
    if not is_valid:
        return False, error
    
    return True, None


def validate_feedback_request(data: dict) -> Tuple[bool, Optional[ValidationError]]:
    """
    Validate feedback request data.
    
    Args:
        data: The request data dictionary
        
    Returns:
        Tuple of (is_valid, error)
    """
    if not data:
        return False, ValidationError(
            code='INVALID_INPUT',
            message='Request body is required',
            details={}
        )
    
    # Validate analysis_id (required)
    analysis_id = data.get('analysisId') or data.get('analysis_id')
    if not analysis_id:
        return False, ValidationError(
            code='INVALID_INPUT',
            message='analysisId is required',
            details={'field': 'analysisId'}
        )
    
    # Validate feedback type (required)
    feedback_type = data.get('feedback', {}).get('type') if isinstance(data.get('feedback'), dict) else data.get('type')
    valid_types = ['helpful', 'incorrect', 'disputed']
    if feedback_type not in valid_types:
        return False, ValidationError(
            code='INVALID_INPUT',
            message=f'Feedback type must be one of: {", ".join(valid_types)}',
            details={
                'field': 'feedback.type',
                'validTypes': valid_types,
                'provided': feedback_type
            }
        )
    
    return True, None


def validate_auth_request(data: dict) -> Tuple[bool, Optional[ValidationError]]:
    """
    Validate authentication request data.
    
    Args:
        data: The request data dictionary
        
    Returns:
        Tuple of (is_valid, error)
    """
    if not data:
        return False, ValidationError(
            code='INVALID_INPUT',
            message='Request body is required',
            details={}
        )
    
    # Validate email
    email = data.get('email')
    if not email:
        return False, ValidationError(
            code='INVALID_INPUT',
            message='Email is required',
            details={'field': 'email'}
        )
    
    # Basic email format validation
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(email):
        return False, ValidationError(
            code='INVALID_INPUT',
            message='Invalid email format',
            details={'field': 'email'}
        )
    
    # Validate password
    password = data.get('password')
    if not password:
        return False, ValidationError(
            code='INVALID_INPUT',
            message='Password is required',
            details={'field': 'password'}
        )
    
    # Password length check (minimum 8, maximum 128 characters)
    # Upper bound prevents bcrypt 72-byte silent truncation: two passwords sharing
    # the same first 72 bytes would otherwise both authenticate successfully.
    MAX_PASSWORD_LENGTH = 128
    if len(password) < 8:
        return False, ValidationError(
            code='INVALID_INPUT',
            message='Password must be at least 8 characters',
            details={'field': 'password', 'minLength': 8}
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, ValidationError(
            code='INVALID_INPUT',
            message=f'Password must not exceed {MAX_PASSWORD_LENGTH} characters',
            details={'field': 'password', 'maxLength': MAX_PASSWORD_LENGTH}
        )
    
    # Password security requirements check
    password_errors = []
    if not re.search(r'[A-Z]', password):
        password_errors.append('at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        password_errors.append('at least one lowercase letter')
    if not re.search(r'\d', password):
        password_errors.append('at least one number')
    
    if password_errors:
        return False, ValidationError(
            code='INVALID_INPUT',
            message=f"Password must contain {', '.join(password_errors)}",
            details={'field': 'password', 'requirements': password_errors}
        )
    
    return True, None