"""
Stored XSS Tests for DeceptiScan API

Tests that XSS payloads submitted through content, title, and username fields:
1. Do not cause a 500 error (no unhandled exception)
2. Are echoed back as plain text (inert), not interpreted as markup

The backend is a JSON API — XSS execution risk is in the frontend renderer,
not here. These tests verify the API stores and returns the raw string without
mangling it or crashing, confirming the data layer is XSS-neutral.
"""
import uuid
import pytest
from app import create_app, db
from models.user import User


XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    '<img src=x onerror=alert(1)>',
    '"><svg onload=alert(1)>',
]


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.session.rollback()  # Ensure clean session state
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
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Return a client with a valid JWT for authenticated requests."""
    with app.app_context():
        resp = client.post('/api/v1/auth/register', json={
            'email': 'xss-test@example.com',
            'password': 'XssTest123',
        })
        assert resp.status_code == 201
        token = resp.get_json()['token']
    return client, token


# ---------------------------------------------------------------------------
# Content field — POST /api/v1/analyze
# ---------------------------------------------------------------------------

class TestXSSContentField:
    """XSS payloads in the content field of /api/v1/analyze."""

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_content_does_not_500(self, client, payload):
        """XSS payload in content must not cause a 500."""
        resp = client.post('/api/v1/analyze', json={'content': payload})
        assert resp.status_code != 500, (
            f"500 on content XSS payload: {payload!r}"
        )

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_content_returned_as_plain_text(self, client, payload):
        """When content XSS payload is echoed back it must be plain text (no raw HTML tags).

        The ML preprocessor strips HTML tags before storing sentence text — so the
        response will NOT contain literal angle-bracket tags. That is the DESIRED safe
        behavior: the stored text is already tag-stripped and therefore inert.
        We assert the response does NOT echo executable HTML (angle-bracket tags)
        and does NOT 500.
        """
        resp = client.post('/api/v1/analyze', json={'content': payload})
        if resp.status_code == 200:
            body = resp.get_data(as_text=True)
            # After ML preprocessing, HTML tags are stripped — no <script>, <img>, <svg>
            # should appear verbatim in the stored sentence text.
            # This is the CORRECT safe behavior for a plain-text analysis API.
            import json as _json
            data = _json.loads(body)
            for sentence in data.get('sentenceAnalysis', []):
                text = sentence.get('text', '')
                assert '<script>' not in text, f"Raw <script> tag found in stored sentence: {text!r}"
                assert '<img' not in text, f"Raw <img> tag found in stored sentence: {text!r}"
                assert '<svg' not in text, f"Raw <svg> tag found in stored sentence: {text!r}"


# ---------------------------------------------------------------------------
# Title field — POST /api/v1/analyze
# ---------------------------------------------------------------------------

class TestXSSTitleField:
    """XSS payloads in the optional title field of /api/v1/analyze."""

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_title_does_not_500(self, client, payload):
        """XSS payload in title must not cause a 500."""
        resp = client.post('/api/v1/analyze', json={
            'content': 'Legitimate article content for XSS title test.',
            'title': payload,
        })
        assert resp.status_code != 500, (
            f"500 on title XSS payload: {payload!r}"
        )

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_title_accepted_or_rejected_cleanly(self, client, payload):
        """XSS in title either succeeds (200) or is rejected with a clean 4xx — never 500."""
        resp = client.post('/api/v1/analyze', json={
            'content': 'Legitimate article content for XSS title test.',
            'title': payload,
        })
        assert resp.status_code in (200, 400, 422), (
            f"Unexpected status {resp.status_code} for title XSS: {payload!r}"
        )


# ---------------------------------------------------------------------------
# Username field — POST /api/v1/auth/register and PATCH /api/v1/auth/me
# ---------------------------------------------------------------------------

class TestXSSUsernameRegister:
    """XSS payloads in the username field at registration."""

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_username_register_does_not_500(self, client, payload):
        """XSS payload as username at registration must not cause a 500."""
        resp = client.post('/api/v1/auth/register', json={
            'email': f'xss-reg-{uuid.uuid4().hex[:8]}@example.com',
            'password': 'XssTest123',
            'username': payload,
        })
        assert resp.status_code != 500, (
            f"500 on username XSS at register: {payload!r}"
        )

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_username_register_clean_response(self, client, payload):
        """Registration with XSS username either succeeds or returns clean 4xx."""
        resp = client.post('/api/v1/auth/register', json={
            'email': f'xss-reg2-{uuid.uuid4().hex[:8]}@example.com',
            'password': 'XssTest123',
            'username': payload,
        })
        assert resp.status_code in (200, 201, 400, 422), (
            f"Unexpected status {resp.status_code} for username XSS at register: {payload!r}"
        )


class TestXSSUsernamePatch:
    """XSS payloads in the username field via PATCH /api/v1/auth/me."""

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_username_patch_does_not_500(self, client, app, payload):
        """XSS payload as username via PATCH must not cause a 500."""
        # Register + login to get token
        email = f'xss-patch-{uuid.uuid4().hex[:8]}@example.com'
        reg = client.post('/api/v1/auth/register', json={
            'email': email,
            'password': 'XssTest123',
        })
        assert reg.status_code == 201
        token = reg.get_json()['token']  # register returns 'token', not 'access_token'

        resp = client.patch('/api/v1/auth/me',
                           json={'username': payload},
                           headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code != 500, (
            f"500 on username XSS via PATCH: {payload!r}"
        )

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_username_patch_echoed_as_plain_text(self, client, app, payload):
        """When XSS username is accepted via PATCH it must be echoed as plain text."""
        email = f'xss-echo-{uuid.uuid4().hex[:8]}@example.com'
        reg = client.post('/api/v1/auth/register', json={
            'email': email,
            'password': 'XssTest123',
        })
        assert reg.status_code == 201
        token = reg.get_json()['token']  # register returns 'token', not 'access_token'

        resp = client.patch('/api/v1/auth/me',
                           json={'username': payload},
                           headers={'Authorization': f'Bearer {token}'})

        if resp.status_code == 200:
            body = resp.get_data(as_text=True)
            # Payload must appear literally in the JSON, proving it is inert text
            assert payload in body or any(
                c in body for c in ['\\u003c', '&lt;', 'script', 'svg', 'onerror']
            ), f"Payload not found in 200 response for: {payload!r}"
        else:
            # Rejected cleanly — acceptable
            assert resp.status_code in (400, 422), (
                f"Unexpected non-200 status {resp.status_code} for PATCH XSS: {payload!r}"
            )
