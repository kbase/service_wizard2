import pytest
from fastapi.testclient import TestClient

from factory import create_app


@pytest.fixture
def app():
    return create_app()


def test_status(app):
    client = TestClient(app)
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"git_commit_hash": "1.2.3", "git_url": "https://github.com/kbase/service_wizard2", "message": "", "state": "OK", "version": "1.2.3"}
    # Version is 'None' in pycharm if you don't set env var


def test_version(app):
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == ["1.2.3"]  # 'None' in pycharm
