import json
import pytest
from app import create_app, db
from models.analysis import AnalysisRecord


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


def test_analyze_endpoint_success(client):
    response = client.post('/api/v1/analyze', json={
        'content': 'Breaking news: Scientists discover new planet with liquid water and mild atmosphere.'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'id' in data
    assert 'authenticityScore' in data
    assert 0 <= data['authenticityScore'] <= 100
    assert 'classification' in data
    assert 'sentenceAnalysis' in data


def test_analyze_endpoint_empty_content(client):
    response = client.post('/api/v1/analyze', json={'content': ''})
    assert response.status_code == 400
    data = response.get_json()
    assert data['error']['code'] == 'INVALID_INPUT'


def test_get_analysis_by_id(client):
    # Analyze text to save record
    post_res = client.post('/api/v1/analyze', json={
        'content': 'Researchers publish study on renewable energy efficiency.'
    })
    analysis_id = post_res.get_json()['id']

    get_res = client.get(f'/api/v1/analyze/{analysis_id}')
    assert get_res.status_code == 200
    detail = get_res.get_json()
    assert detail['id'] == analysis_id
    assert 'authenticityScore' in detail


def test_get_analysis_not_found(client):
    res = client.get('/api/v1/analyze/00000000-0000-0000-0000-000000000000')
    assert res.status_code == 404
    data = res.get_json()
    assert data['error']['code'] == 'NOT_FOUND'


def test_recent_analyses_endpoint_unauthenticated(client):
    res = client.get('/api/v1/analyses/recent')
    assert res.status_code == 401


def test_recent_analyses_endpoint_authenticated(client, app):
    from models.user import User
    from flask_jwt_extended import create_access_token
    import uuid

    with app.app_context():
        user = User(
            id=uuid.uuid4(),
            email='recent@example.com',
            is_active=True
        )
        user.set_password('SecurePass123')
        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=str(user.id))
        headers = {'Authorization': f'Bearer {token}'}

        client.post('/api/v1/analyze', json={'content': 'Test document one for recent test.'}, headers=headers)
        client.post('/api/v1/analyze', json={'content': 'Test document two for recent test.'}, headers=headers)

        res = client.get('/api/v1/analyses/recent?limit=5', headers=headers)
        assert res.status_code == 200
        data = res.get_json()
        assert 'items' in data
        assert len(data['items']) == 2
        assert data['count'] == 2
