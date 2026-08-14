import pytest
from app import create_app, db


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


def test_full_integration_flow(client):
    # 1. Register User
    reg_resp = client.post('/api/v1/auth/register', json={
        'email': 'e2e_user@example.com',
        'password': 'Password123!',
        'confirmPassword': 'Password123!'
    })
    assert reg_resp.status_code == 201
    token = reg_resp.get_json()['token']
    auth_headers = {'Authorization': f'Bearer {token}'}

    # 2. Login User
    login_resp = client.post('/api/v1/auth/login', json={
        'email': 'e2e_user@example.com',
        'password': 'Password123!'
    })
    assert login_resp.status_code == 200

    # 3. Get Current User profile
    me_resp = client.get('/api/v1/auth/me', headers=auth_headers)
    assert me_resp.status_code == 200
    assert me_resp.get_json()['email'] == 'e2e_user@example.com'

    # 4. Submit Article for Analysis
    article_text = 'Breaking report: Global renewable power capacity grew by 50 percent last year.'
    analyze_resp = client.post('/api/v1/analyze', json={
        'content': article_text
    }, headers=auth_headers)
    assert analyze_resp.status_code == 200
    analysis_data = analyze_resp.get_json()
    analysis_id = analysis_data['id']
    assert 0 <= analysis_data['authenticityScore'] <= 100

    # 5. Submit Second Analysis (validates repeat request)
    cached_resp = client.post('/api/v1/analyze', json={
        'content': article_text
    }, headers=auth_headers)
    assert cached_resp.status_code == 200
    assert cached_resp.get_json()['authenticityScore'] == analysis_data['authenticityScore']

    # 6. Retrieve Analysis by ID
    get_resp = client.get(f'/api/v1/analyze/{analysis_id}', headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.get_json()['id'] == analysis_id

    # 7. Submit Feedback
    feedback_resp = client.post('/api/v1/feedback', json={
        'analysisId': analysis_id,
        'feedback': {'type': 'helpful'}
    }, headers=auth_headers)
    assert feedback_resp.status_code == 201
    assert 'feedbackId' in feedback_resp.get_json()

    # 8. Check Analysis History
    history_resp = client.get('/api/v1/history', headers=auth_headers)
    assert history_resp.status_code == 200
    history_data = history_resp.get_json()
    assert len(history_data['data']) >= 1

    # 9. Delete Analysis Record
    del_resp = client.delete(f'/api/v1/history/{analysis_id}', headers=auth_headers)
    assert del_resp.status_code == 200

    # 10. Verify Deletion
    get_after_del = client.get(f'/api/v1/analyze/{analysis_id}', headers=auth_headers)
    assert get_after_del.status_code == 404
