import json
import pytest
from app import create_app, db
from models.analysis import AnalysisRecord


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


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
