"""
Unit tests for authentication endpoints.
"""
import uuid
import pytest
from flask import Flask
from flask_jwt_extended import create_access_token
from app import create_app, db
from app.validators import validate_auth_request, ValidationError
from models.user import User


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key'
    
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
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create a test user in the database."""
    with app.app_context():
        user = User(
            id=uuid.uuid4(),
            email='test@example.com',
            is_active=True
        )
        user.set_password('SecurePass123')
        db.session.add(user)
        db.session.commit()
        return str(user.id)


class TestRegisterEndpoint:
    """Tests for /api/v1/auth/register endpoint."""
    
    def test_register_success(self, client, app):
        """Test successful user registration."""
        with app.app_context():
            response = client.post('/api/v1/auth/register', json={
                'email': 'newuser@example.com',
                'password': 'SecurePass123'
            })
            
            assert response.status_code == 201
            data = response.get_json()
            assert 'userId' in data
            assert 'token' in data
            assert 'refreshToken' in data
    
    def test_register_existing_email(self, client, app):
        """Test registration with existing email fails."""
        with app.app_context():
            # Create existing user
            user = User(
                id=uuid.uuid4(),
                email='existing@example.com',
                is_active=True
            )
            user.set_password('SecurePass123')
            db.session.add(user)
            db.session.commit()
            
            # Try to register with same email
            response = client.post('/api/v1/auth/register', json={
                'email': 'existing@example.com',
                'password': 'SecurePass123'
            })
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['error']['code'] == 'INVALID_INPUT'
            assert 'already registered' in data['error']['message'].lower()
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email format fails."""
        response = client.post('/api/v1/auth/register', json={
            'email': 'invalid-email',
            'password': 'SecurePass123'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
        assert 'email' in data['error']['message'].lower()
    
    def test_register_weak_password(self, client):
        """Test registration with weak password fails."""
        response = client.post('/api/v1/auth/register', json={
            'email': 'test@example.com',
            'password': 'weak'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
    
    def test_register_password_missing_uppercase(self, client):
        """Test registration with password missing uppercase fails."""
        response = client.post('/api/v1/auth/register', json={
            'email': 'test@example.com',
            'password': 'lowercase123'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'uppercase' in data['error']['message'].lower()
    
    def test_register_password_missing_lowercase(self, client):
        """Test registration with password missing lowercase fails."""
        response = client.post('/api/v1/auth/register', json={
            'email': 'test@example.com',
            'password': 'UPPERCASE123'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'lowercase' in data['error']['message'].lower()
    
    def test_register_password_missing_number(self, client):
        """Test registration with password missing number fails."""
        response = client.post('/api/v1/auth/register', json={
            'email': 'test@example.com',
            'password': 'NoNumbersHere'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'number' in data['error']['message'].lower()
    
    def test_register_missing_email(self, client):
        """Test registration without email fails."""
        response = client.post('/api/v1/auth/register', json={
            'password': 'SecurePass123'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
    
    def test_register_missing_password(self, client):
        """Test registration without password fails."""
        response = client.post('/api/v1/auth/register', json={
            'email': 'test@example.com'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'


class TestLoginEndpoint:
    """Tests for /api/v1/auth/login endpoint."""
    
    def test_login_success(self, client, app):
        """Test successful user login."""
        with app.app_context():
            # Create test user
            user = User(
                id=uuid.uuid4(),
                email='login@example.com',
                is_active=True
            )
            user.set_password('SecurePass123')
            db.session.add(user)
            db.session.commit()
            
            response = client.post('/api/v1/auth/login', json={
                'email': 'login@example.com',
                'password': 'SecurePass123'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'token' in data
            assert 'refreshToken' in data
            assert 'user' in data
            assert data['user']['email'] == 'login@example.com'
    
    def test_login_wrong_password(self, client, app):
        """Test login with wrong password fails."""
        with app.app_context():
            user = User(
                id=uuid.uuid4(),
                email='wrongpass@example.com',
                is_active=True
            )
            user.set_password('CorrectPass123')
            db.session.add(user)
            db.session.commit()
            
            response = client.post('/api/v1/auth/login', json={
                'email': 'wrongpass@example.com',
                'password': 'WrongPass123'
            })
            
            assert response.status_code == 401
            data = response.get_json()
            assert data['error']['code'] == 'INVALID_INPUT'
            assert 'invalid' in data['error']['message'].lower()
    
    def test_login_nonexistent_email(self, client):
        """Test login with non-existent email fails."""
        response = client.post('/api/v1/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'SecurePass123'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'invalid' in data['error']['message'].lower()
    
    def test_login_missing_email(self, client):
        """Test login without email fails."""
        response = client.post('/api/v1/auth/login', json={
            'password': 'SecurePass123'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'email' in data['error']['message'].lower()
    
    def test_login_missing_password(self, client):
        """Test login without password fails."""
        response = client.post('/api/v1/auth/login', json={
            'email': 'test@example.com'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'password' in data['error']['message'].lower()


class TestMeEndpoint:
    """Tests for /api/v1/auth/me endpoint."""
    
    def test_me_unauthenticated(self, client):
        """Test /me endpoint without token fails."""
        response = client.get('/api/v1/auth/me')
        assert response.status_code == 401
    
    def test_me_authenticated(self, client, app):
        """Test /me endpoint with valid token."""
        with app.app_context():
            # Create test user and get token
            user = User(
                id=uuid.uuid4(),
                email='me@example.com',
                is_active=True
            )
            user.set_password('SecurePass123')
            db.session.add(user)
            db.session.commit()
            
            access_token = create_access_token(identity=str(user.id))
            
            response = client.get(
                '/api/v1/auth/me',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['email'] == 'me@example.com'
            assert 'id' in data
            assert 'isAdmin' in data

    def test_patch_me_success(self, client, app):
        """Test updating username via PATCH /api/v1/auth/me."""
        with app.app_context():
            user = User(
                id=uuid.uuid4(),
                email='patchme@example.com',
                is_active=True
            )
            user.set_password('SecurePass123')
            db.session.add(user)
            db.session.commit()

            access_token = create_access_token(identity=str(user.id))

            response = client.patch(
                '/api/v1/auth/me',
                headers={'Authorization': f'Bearer {access_token}'},
                json={'username': 'AgentVesper'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['username'] == 'AgentVesper'

    def test_patch_me_username_collision(self, client, app):
        """Test updating username to an already existing username returns 400 error."""
        with app.app_context():
            user1 = User(
                id=uuid.uuid4(),
                email='user1@example.com',
                username='CipherZero',
                is_active=True
            )
            user1.set_password('SecurePass123')

            user2 = User(
                id=uuid.uuid4(),
                email='user2@example.com',
                is_active=True
            )
            user2.set_password('SecurePass123')
            db.session.add_all([user1, user2])
            db.session.commit()

            access_token = create_access_token(identity=str(user2.id))

            response = client.patch(
                '/api/v1/auth/me',
                headers={'Authorization': f'Bearer {access_token}'},
                json={'username': 'CipherZero'}
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data['error']['code'] == 'INVALID_INPUT'


class TestRefreshEndpoint:
    """Tests for /api/v1/auth/refresh endpoint."""
    
    def test_refresh_success(self, client, app):
        """Test successful token refresh."""
        with app.app_context():
            # Create test user and get refresh token
            from flask_jwt_extended import create_refresh_token
            
            user = User(
                id=uuid.uuid4(),
                email='refresh@example.com',
                is_active=True
            )
            user.set_password('SecurePass123')
            db.session.add(user)
            db.session.commit()
            
            refresh_token = create_refresh_token(identity=str(user.id))
            
            response = client.post(
                '/api/v1/auth/refresh',
                headers={'Authorization': f'Bearer {refresh_token}'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'token' in data
    
    def test_refresh_without_token(self, client):
        """Test refresh without token fails."""
        response = client.post('/api/v1/auth/refresh')
        assert response.status_code == 401
    
    def test_refresh_with_access_token(self, client, app):
        """Test refresh with access token instead of refresh token fails."""
        with app.app_context():
            from flask_jwt_extended import create_access_token
            
            user = User(
                id=uuid.uuid4(),
                email='wrongtoken@example.com',
                is_active=True
            )
            user.set_password('SecurePass123')
            db.session.add(user)
            db.session.commit()
            
            access_token = create_access_token(identity=str(user.id))
            
            response = client.post(
                '/api/v1/auth/refresh',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            assert response.status_code == 422


class TestLogoutEndpoint:
    """Tests for /api/v1/auth/logout endpoint."""
    
    def test_logout_unauthenticated(self, client):
        """Test logout without token fails."""
        response = client.post('/api/v1/auth/logout')
        assert response.status_code == 401
    
    def test_logout_authenticated(self, client, app):
        """Test logout with valid token succeeds."""
        with app.app_context():
            user = User(
                id=uuid.uuid4(),
                email='logout@example.com',
                is_active=True
            )
            user.set_password('SecurePass123')
            db.session.add(user)
            db.session.commit()
            
            access_token = create_access_token(identity=str(user.id))
            
            response = client.post(
                '/api/v1/auth/logout',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'logged out' in data['message'].lower()


class TestPasswordValidation:
    """Tests for password validation in validators."""
    
    def test_valid_password(self):
        """Valid password should pass."""
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123'
        }
        is_valid, error = validate_auth_request(data)
        assert is_valid is True
    
    def test_password_no_uppercase(self):
        """Password without uppercase should fail."""
        data = {
            'email': 'test@example.com',
            'password': 'lowercase123'
        }
        is_valid, error = validate_auth_request(data)
        assert is_valid is False
        assert 'uppercase' in error.message.lower()
    
    def test_password_no_lowercase(self):
        """Password without lowercase should fail."""
        data = {
            'email': 'test@example.com',
            'password': 'UPPERCASE123'
        }
        is_valid, error = validate_auth_request(data)
        assert is_valid is False
        assert 'lowercase' in error.message.lower()
    
    def test_password_no_number(self):
        """Password without number should fail."""
        data = {
            'email': 'test@example.com',
            'password': 'NoNumbersHere'
        }
        is_valid, error = validate_auth_request(data)
        assert is_valid is False
        assert 'number' in error.message.lower()
    
    def test_password_too_short(self):
        """Password too short should fail."""
        data = {
            'email': 'test@example.com',
            'password': 'Aa1'
        }
        is_valid, error = validate_auth_request(data)
        assert is_valid is False
        assert '8 characters' in error.message
    
    def test_password_all_requirements(self):
        """Password meeting all requirements should pass."""
        data = {
            'email': 'test@example.com',
            'password': 'MyPassword123'
        }
        is_valid, error = validate_auth_request(data)
        assert is_valid is True