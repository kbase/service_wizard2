"""
Could test the following:
    Test Case: Missing Authorization Header and Cookie
        Description: Verify that the server returns an appropriate error response when both the Authorization header and kbase_session_cookie are missing.
        Expected Behavior: The server should respond with a 400 (Bad Request) status code and an error message indicating the missing authentication information.

    Test Case: Authentication Service Unavailable
        Description: Ensure that the server handles the scenario when the authentication service is down or returns a 500 status code.
        Expected Behavior: The server should return a 500 (Internal Server Error) status code and an error message indicating the unavailability of the authentication service.

    Test Case: Invalid or Expired Token
        Description: Validate the behavior when an invalid or expired token is provided.
        Expected Behavior: The server should respond with a 400 (Bad Request) status code and an error message indicating an invalid or expired token.

    Test Case: Successful Token Authentication
        Description: Verify that the server successfully authenticates a request with a valid token.
        Expected Behavior: The server should return a 200 (OK) status code and the expected response JSON when the token authentication is successful.

"""

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
    def _get_client_with_authorization(authorization_value="faketoken",cookies=None):
        client = TestClient(app)
        client.headers["Authorization"] = f"{authorization_value}"
        if cookies:
            client.cookies["kbase_session"] = f"{authorization_value}"
        return client

    return _get_client_with_authorization


@pytest.fixture
def auth_service_mock(auth_url=None, user="testuser", custom_roles=None):
    if auth_url is None:
        auth_url = get_settings().auth_service_url

    if custom_roles is None:
        custom_roles = list()

    with requests_mock.Mocker() as mocker:
        # Mock the response from the AUTH_SERVICE_URL endpoint
        mocker.get(
            auth_url,
            json={"user": user, "customroles": custom_roles},
            status_code=200
        )
        yield mocker



def test_get_bad_token(client_with_authorization, auth_service_mock):
    with client_with_authorization("_bad_token_") as client:
        response = client.get("/get_service_log/123/123")
        assert response.status_code == 422
        assert response.json() == {'detail': [{'ctx': {'pattern': '^[a-zA-Z0-9]+$'},
             'loc': ['header', 'Authorization'],
             'msg': 'string does not match regex "^[a-zA-Z0-9]+$"',
             'type': 'value_error.str.regex'}]} != {'instance_id': '123', 'logs': ['log1', 'log2']}



def test_get_service_log(client_with_authorization, auth_service_mock):
    with client_with_authorization() as client:
        response = client.get("/get_service_log/123/123")
        assert response.status_code == 200
        assert response.json() == {"instance_id": "123", "logs": ["log1", "log2"]}


