"""
Unit and integration tests for avatar upload endpoint (POST /api/v1/auth/me/avatar).
"""
import io
import uuid
import pytest
from unittest.mock import patch
from flask_jwt_extended import create_access_token
from app import create_app, db
from models.user import User


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key-deceptiscan-32b!'
    
    with app.app_context():
        db.session.rollback()
        db.create_all()
        yield app
        db.session.remove()
        try:
            for table in reversed(db.metadata.sorted_tables):
                if table.name != 'claim_embeddings':
                    db.session.execute(table.delete())
            db.session.commit()
        except Exception:
            db.session.rollback()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_user(app):
    """Create a test user and return (user, auth_headers)."""
    with app.app_context():
        user = User(
            id=uuid.uuid4(),
            email=f"avatar_test_{uuid.uuid4().hex[:8]}@example.com",
            username="AgentAvatar",
            is_active=True
        )
        user.set_password("SecurePass123!")
        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=str(user.id))
        headers = {'Authorization': f'Bearer {token}'}
        return user, headers


class TestAvatarUploadValidation:
    """Test validation logic on POST /api/v1/auth/me/avatar."""

    def test_unauthenticated_returns_401(self, client):
        res = client.post('/api/v1/auth/me/avatar')
        assert res.status_code == 401

    def test_missing_file_returns_400(self, client, auth_user):
        _, headers = auth_user
        res = client.post(
            '/api/v1/auth/me/avatar',
            data={},
            content_type='multipart/form-data',
            headers=headers
        )
        assert res.status_code == 400
        data = res.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
        assert 'No image file provided' in data['error']['message']

    def test_invalid_extension_txt_returns_400(self, client, auth_user):
        _, headers = auth_user
        file_data = (io.BytesIO(b"not an image"), 'test.txt')
        res = client.post(
            '/api/v1/auth/me/avatar',
            data={'file': file_data},
            content_type='multipart/form-data',
            headers=headers
        )
        assert res.status_code == 400
        data = res.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
        assert 'Invalid file format' in data['error']['message']

    def test_invalid_extension_exe_returns_400(self, client, auth_user):
        _, headers = auth_user
        file_data = (io.BytesIO(b"\x4d\x5a\x90\x00"), 'malware.exe')
        res = client.post(
            '/api/v1/auth/me/avatar',
            data={'file': file_data},
            content_type='multipart/form-data',
            headers=headers
        )
        assert res.status_code == 400
        data = res.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'

    def test_empty_file_returns_400(self, client, auth_user):
        _, headers = auth_user
        file_data = (io.BytesIO(b""), 'empty.png')
        res = client.post(
            '/api/v1/auth/me/avatar',
            data={'file': file_data},
            content_type='multipart/form-data',
            headers=headers
        )
        assert res.status_code == 400
        data = res.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
        assert 'empty' in data['error']['message'].lower()

    def test_oversized_file_returns_400(self, client, auth_user):
        _, headers = auth_user
        # 5.5MB dummy content
        oversized = io.BytesIO(b"x" * (5 * 1024 * 1024 + 500 * 1024))
        res = client.post(
            '/api/v1/auth/me/avatar',
            data={'file': (oversized, 'huge.jpg')},
            content_type='multipart/form-data',
            headers=headers
        )
        assert res.status_code == 400
        data = res.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
        assert '5MB' in data['error']['message']


class TestAvatarUploadCloudinaryIntegration:
    """Test Cloudinary integration, DB persistence, and error handling."""

    @patch('cloudinary.uploader.upload')
    @patch.dict('os.environ', {
        'CLOUDINARY_CLOUD_NAME': 'test-cloud',
        'CLOUDINARY_API_KEY': '123456789',
        'CLOUDINARY_API_SECRET': 'test-secret'
    })
    def test_upload_success_stores_avatar_url(self, mock_upload, client, app, auth_user):
        user, headers = auth_user
        mock_upload.return_value = {
            'secure_url': 'https://res.cloudinary.com/test-cloud/image/upload/v1234/deceptiscan/avatars/test_avatar.jpg',
            'public_id': 'avatar_123'
        }

        fake_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4'
        res = client.post(
            '/api/v1/auth/me/avatar',
            data={'file': (io.BytesIO(fake_png), 'avatar.png')},
            content_type='multipart/form-data',
            headers=headers
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data['avatarUrl'] == 'https://res.cloudinary.com/test-cloud/image/upload/v1234/deceptiscan/avatars/test_avatar.jpg'
        assert data['avatar_url'] == 'https://res.cloudinary.com/test-cloud/image/upload/v1234/deceptiscan/avatars/test_avatar.jpg'
        assert data['message'] == 'Avatar updated successfully'

        # Verify persistence in database
        with app.app_context():
            updated = User.query.get(user.id)
            assert updated.avatar_url == 'https://res.cloudinary.com/test-cloud/image/upload/v1234/deceptiscan/avatars/test_avatar.jpg'

        # Verify GET /auth/me returns avatarUrl
        get_res = client.get('/api/v1/auth/me', headers=headers)
        assert get_res.status_code == 200
        get_data = get_res.get_json()
        assert get_data['avatarUrl'] == 'https://res.cloudinary.com/test-cloud/image/upload/v1234/deceptiscan/avatars/test_avatar.jpg'

    @patch('cloudinary.uploader.upload')
    @patch.dict('os.environ', {
        'CLOUDINARY_CLOUD_NAME': 'test-cloud',
        'CLOUDINARY_API_KEY': '123456789',
        'CLOUDINARY_API_SECRET': 'test-secret'
    })
    def test_upload_failure_returns_502(self, mock_upload, client, auth_user):
        _, headers = auth_user
        mock_upload.side_effect = Exception("Cloudinary connection timeout")

        fake_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        res = client.post(
            '/api/v1/auth/me/avatar',
            data={'file': (io.BytesIO(fake_png), 'avatar.png')},
            content_type='multipart/form-data',
            headers=headers
        )
        assert res.status_code == 502
        data = res.get_json()
        assert data['error']['code'] == 'UPLOAD_FAILED'
        assert 'Failed to upload avatar image' in data['error']['message']

    @patch.dict('os.environ', {
        'CLOUDINARY_CLOUD_NAME': '',
        'CLOUDINARY_API_KEY': '',
        'CLOUDINARY_API_SECRET': ''
    })
    def test_unconfigured_cloudinary_returns_503(self, client, auth_user):
        _, headers = auth_user
        fake_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        res = client.post(
            '/api/v1/auth/me/avatar',
            data={'file': (io.BytesIO(fake_png), 'avatar.png')},
            content_type='multipart/form-data',
            headers=headers
        )
        assert res.status_code == 503
        data = res.get_json()
        assert data['error']['code'] == 'CONFIG_ERROR'
        assert 'storage is not configured' in data['error']['message']
