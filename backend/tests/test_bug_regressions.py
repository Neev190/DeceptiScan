"""
Regression tests for three specific bugs fixed in this session.

BUG 1 — Unbounded password length (bcrypt 72-byte truncation)
BUG 2 — Non-UUID analysisId causing 500 instead of clean 404
BUG 3 — Username field accepts non-string types via blind str() coercion
"""
import uuid
import pytest
from flask_jwt_extended import create_access_token
from app import create_app, db
from models.user import User


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
def auth_headers(app, client):
    """Create a user and return valid auth headers."""
    with app.app_context():
        user = User(id=uuid.uuid4(), email='bugtest@example.com', is_active=True)
        user.set_password('BugTest123')
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.id))
        return {'Authorization': f'Bearer {token}'}


# ---------------------------------------------------------------------------
# BUG 1 — Unbounded password length (bcrypt 72-byte truncation)
# ---------------------------------------------------------------------------

class TestPasswordMaxLength:
    """
    bcrypt silently truncates at 72 bytes. Without an explicit upper bound,
    two passwords sharing the same first 72 bytes would both authenticate.
    Fix: validator rejects passwords longer than 128 characters.
    """

    MAX = 128

    def _pw(self, length):
        """Build a password of exactly `length` chars that meets complexity rules."""
        # Start with a valid prefix that satisfies upper/lower/digit requirements
        prefix = 'Aa1'
        filler = 'x' * (length - len(prefix))
        return prefix + filler

    def test_password_at_max_length_succeeds(self, client):
        """Password of exactly 128 chars must register successfully."""
        password = self._pw(self.MAX)
        assert len(password) == self.MAX
        resp = client.post('/api/v1/auth/register', json={
            'email': 'maxpw@example.com',
            'password': password,
        })
        assert resp.status_code == 201, (
            f"Expected 201 for password at max length, got {resp.status_code}: "
            f"{resp.get_json()}"
        )

    def test_password_one_over_max_fails_400(self, client):
        """Password of 129 chars must be rejected with 400 INVALID_INPUT."""
        password = self._pw(self.MAX + 1)
        assert len(password) == self.MAX + 1
        resp = client.post('/api/v1/auth/register', json={
            'email': 'overmaxpw@example.com',
            'password': password,
        })
        assert resp.status_code == 400, (
            f"Expected 400 for password over max length, got {resp.status_code}"
        )
        data = resp.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
        assert '128' in data['error']['message']

    def test_validator_unit_max_length(self):
        """validate_auth_request unit check: 129-char password fails."""
        from app.validators import validate_auth_request
        is_valid, error = validate_auth_request({
            'email': 'unit@example.com',
            'password': self._pw(self.MAX + 1),
        })
        assert is_valid is False
        assert error.code == 'INVALID_INPUT'
        assert '128' in error.message

    def test_validator_unit_at_max_length(self):
        """validate_auth_request unit check: 128-char password passes."""
        from app.validators import validate_auth_request
        is_valid, error = validate_auth_request({
            'email': 'unit2@example.com',
            'password': self._pw(self.MAX),
        })
        assert is_valid is True, f"Expected valid, got error: {error.message if error else None}"


# ---------------------------------------------------------------------------
# BUG 2 — Non-UUID analysisId causing 500 instead of clean 404
# ---------------------------------------------------------------------------

class TestNonUuidAnalysisId:
    """
    Passing a non-UUID string as analysisId must return 404 (or 400),
    not a 500 from an unhandled UUID parse exception.
    """

    def test_path_traversal_string_returns_404(self, client):
        """'../../../etc/passwd' as analysisId must not cause a 500."""
        resp = client.post('/api/v1/feedback', json={
            'analysisId': '../../../etc/passwd',
            'feedback': {'type': 'helpful'},
        })
        assert resp.status_code in (400, 404), (
            f"Expected 400 or 404 for path-traversal analysisId, got {resp.status_code}"
        )
        assert resp.status_code != 500

    def test_plain_garbage_string_returns_404(self, client):
        """'not-a-uuid' as analysisId must not cause a 500."""
        resp = client.post('/api/v1/feedback', json={
            'analysisId': 'not-a-uuid',
            'feedback': {'type': 'helpful'},
        })
        assert resp.status_code in (400, 404), (
            f"Expected 400 or 404 for garbage analysisId, got {resp.status_code}"
        )
        data = resp.get_json()
        assert 'error' in data
        assert resp.status_code != 500

    def test_sql_injection_string_returns_404(self, client):
        """SQL injection style analysisId must not cause a 500."""
        resp = client.post('/api/v1/feedback', json={
            'analysisId': "'; DROP TABLE analysis_records; --",
            'feedback': {'type': 'helpful'},
        })
        assert resp.status_code in (400, 404), (
            f"Expected 400 or 404 for SQL-injection analysisId, got {resp.status_code}"
        )
        assert resp.status_code != 500

    def test_empty_string_analysisId_returns_400(self, client):
        """Empty string analysisId is caught by the validator (existing behaviour)."""
        resp = client.post('/api/v1/feedback', json={
            'analysisId': '',
            'feedback': {'type': 'helpful'},
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'

    def test_valid_uuid_nonexistent_returns_404(self, client):
        """A well-formed UUID that doesn't exist in DB must still return 404 (unchanged)."""
        resp = client.post('/api/v1/feedback', json={
            'analysisId': '00000000-0000-0000-0000-000000000000',
            'feedback': {'type': 'helpful'},
        })
        assert resp.status_code == 404
        data = resp.get_json()
        assert data['error']['code'] == 'NOT_FOUND'


# ---------------------------------------------------------------------------
# BUG 3 — Username field accepts non-string types via blind str() coercion
# ---------------------------------------------------------------------------

class TestUsernameTypeSafety:
    """
    PATCH /api/v1/auth/me with a non-string username must be rejected with 400.
    Previously, str(True) → "True" and str(123) → "123" were silently stored.
    """

    def test_boolean_true_username_rejected(self, client, auth_headers):
        """{'username': true} must return 400, not store 'True'."""
        resp = client.patch('/api/v1/auth/me', json={'username': True}, headers=auth_headers)
        assert resp.status_code == 400, (
            f"Expected 400 for boolean username, got {resp.status_code}: {resp.get_json()}"
        )
        data = resp.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'
        assert data['error']['details'].get('field') == 'username'

    def test_boolean_false_username_rejected(self, client, auth_headers):
        """{'username': false} must return 400, not store 'False'."""
        resp = client.patch('/api/v1/auth/me', json={'username': False}, headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'

    def test_integer_username_rejected(self, client, auth_headers):
        """{'username': 12345} must return 400, not store '12345'."""
        resp = client.patch('/api/v1/auth/me', json={'username': 12345}, headers=auth_headers)
        assert resp.status_code == 400, (
            f"Expected 400 for integer username, got {resp.status_code}: {resp.get_json()}"
        )
        data = resp.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'

    def test_list_username_rejected(self, client, auth_headers):
        """{'username': ['a', 'b']} must return 400."""
        resp = client.patch('/api/v1/auth/me', json={'username': ['a', 'b']}, headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['code'] == 'INVALID_INPUT'

    def test_valid_string_username_still_accepted(self, client, auth_headers):
        """Valid string username must still work — the fix must not break the happy path."""
        resp = client.patch('/api/v1/auth/me', json={'username': 'AgentZero'}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['username'] == 'AgentZero'

    def test_null_username_accepted_clears_value(self, client, auth_headers):
        """{'username': null} must be accepted and clear the username (existing behaviour)."""
        resp = client.patch('/api/v1/auth/me', json={'username': None}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['username'] is None
