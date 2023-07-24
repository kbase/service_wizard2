import json

import pytest
from cacheout import LRUCache
from fastapi.testclient import TestClient
from src.configs.settings import get_settings
from src.factory import create_app
import requests_mock


@pytest.fixture
def app():
    token_cache = LRUCache(maxsize=100, ttl=300)
    catalog_cache = LRUCache(maxsize=100, ttl=300)
    return create_app(token_cache=token_cache, catalog_cache=catalog_cache)


@pytest.fixture
def client_with_authorization(app):
    def _get_client_with_authorization(authorization_value="faketoken", cookies=None):
        client = TestClient(app)
        client.headers["Authorization"] = f"{authorization_value}"
        if cookies:
            client.cookies["kbase_session"] = f"{authorization_value}"
        return client

    return _get_client_with_authorization


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_service_mock(auth_url=None, user="testuser", custom_roles=None):
    if auth_url is None:
        auth_url = get_settings().auth_service_url

    if custom_roles is None:
        custom_roles = list()

    with requests_mock.Mocker() as mocker:
        # Mock the response from the AUTH_SERVICE_URL endpoint
        mocker.get(auth_url, json={"user": user, "customroles": custom_roles}, status_code=200)
        yield mocker


def test_get_bad_token(client_with_authorization, auth_service_mock):
    with client_with_authorization("_bad_token_") as client:
        response = client.get("/get_service_log/123/123")
        assert response.status_code == 422
        assert (
            response.json()
            == {
                "detail": [
                    {
                        "ctx": {"pattern": "^[a-zA-Z0-9]+$"},
                        "loc": ["header", "Authorization"],
                        "msg": 'string does not match regex "^[a-zA-Z0-9]+$"',
                        "type": "value_error.str.regex",
                    }
                ]
            }
            != {"instance_id": "123", "logs": ["log1", "log2"]}
        )


def test_get_service_log(client_with_authorization, auth_service_mock):
    with client_with_authorization() as client:
        response = client.get("/get_service_log/123/123")
        assert response.status_code == 200
        assert response.json() == {"instance_id": "123", "logs": ["log1", "log2"]}


def test_missing_auth(client):
    response = client.get("/get_service_log/123/123")
    assert response.status_code == 400
    assert response.json() == {"detail": "Please provide the 'Authorization' header or 'kbase_session' cookie"}


def test_successful_authentication(client_with_authorization, auth_service_mock):
    with client_with_authorization() as client:
        response = client.get("/get_service_log/123/123")
        assert response.status_code == 200
        assert response.json() == {"instance_id": "123", "logs": ["log1", "log2"]}


def test_token_cache(client_with_authorization, auth_service_mock):
    with client_with_authorization("cachedtoken") as client:
        # Test Token Cache Miss
        response = client.get("/get_service_log/456/456")
        assert auth_service_mock.call_count == 1  # Cache miss, so one call to authentication service
        assert response.status_code == 200
        assert response.json() == {"instance_id": "456", "logs": ["log1", "log2"]}

        # Test Token Cache Hit
        response = client.get("/get_service_log/123/123")
        assert auth_service_mock.call_count == 1  # Cache hit, so no call to authentication service
        assert response.status_code == 200
        assert response.json() == {"instance_id": "123", "logs": ["log1", "log2"]}

    with client_with_authorization("cachedtoken2") as client:
        # Test Token Cache Miss
        response = client.get("/get_service_log/456/456")
        assert auth_service_mock.call_count == 2  # Cache miss, so one call to authentication service
        assert response.status_code == 200
        assert response.json() == {"instance_id": "456", "logs": ["log1", "log2"]}

        # Test Token Cache Hit
        response = client.get("/get_service_log/123/123")
        assert auth_service_mock.call_count == 2  # Cache hit, so no call to authentication service
        assert response.status_code == 200
        assert response.json() == {"instance_id": "123", "logs": ["log1", "log2"]}


# def test_list_service_status_rpc(client_with_authorization, auth_service_mock):
#     #TODO Mock out kubernetes
#     with client_with_authorization() as client:
#         headers = {"Content-Type": "application/json"}  # Set the content type to JSON
#         payload = {
#             "method": "ServiceWizard.list_service_status",
#             "id": 22,
#             "params": [{"module": "onerepotest"}]
#         }
#         response = client.post("/rpc/", data=json.dumps(payload), headers=headers)
#         print(response.json())
