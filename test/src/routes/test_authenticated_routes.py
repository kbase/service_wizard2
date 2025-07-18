from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from clients.CachedAuthClient import CachedAuthClient
from factory import create_app


# Create app fixture
@pytest.fixture
def app():
    return create_app()


def test_whoami_without_auth(app):
    test_client = TestClient(app)
    response = test_client.get("/whoami/")
    assert response.status_code == 401


def test_whoami_with_bad_auth(app):
    test_client = TestClient(app)
    response = test_client.get("/whoami/", cookies={"kbase_session": "invalid_session"})
    assert response.status_code == 422
    expected_response = {
        "detail": [
            {
                "type": "string_pattern_mismatch",
                "loc": ["cookie", "kbase_session"],
                "msg": "String should match pattern '^[" "a-zA-Z0-9]+$'",
                "input": "invalid_session",
                "ctx": {"pattern": "^[a-zA-Z0-9]+$"},
                "url": "https://errors.pydantic.dev/2.11/v/string_pattern_mismatch",
            },
            {
                "type": "string_pattern_mismatch",
                "loc": ["cookie", "kbase_session"],
                "msg": "String should match pattern '^[a-zA-Z0-9]+$'",
                "input": "invalid_session",
                "ctx": {"pattern": "^[a-zA-Z0-9]+$"},
                "url": "https://errors.pydantic.dev/2.11/v/string_pattern_mismatch",
            },
        ]
    }

    assert response.json() == expected_response

    # Test with authorization header
    test_client.headers["Authorization"] = "invalid_header"
    response = test_client.get(
        "/whoami/",
    )
    assert response.status_code == 422

    expected_response["detail"][0]["input"] = "invalid_header"
    expected_response["detail"][1]["input"] = "invalid_header"

    expected_response["detail"][0]["loc"] = ["header", "Authorization"]
    expected_response["detail"][1]["loc"] = ["header", "Authorization"]

    assert response.json() == expected_response


def test_whoami_with_mocked_auth_client():
    mock_auth_client = MagicMock(spec=CachedAuthClient)

    app_with_mock_auth = create_app(auth_client=mock_auth_client)
    test_client = TestClient(app_with_mock_auth)
    response = test_client.get("/whoami/", cookies={"kbase_session": "invalid_session"})
    assert response.status_code == 422

    response = test_client.get("/whoami/", cookies={"kbase_session": "validsession"})
    assert response.status_code == 200

    mock_auth_client.validate_and_get_username_auth_roles.assert_called_with(token="validsession")


def test_get_metrics():
    TEST_USERNAME = "testuser"
    TEST_PASSWORD = "testpass"

    with patch.dict("os.environ", {"METRICS_USERNAME": TEST_USERNAME, "METRICS_PASSWORD": TEST_PASSWORD}):
        test_client = TestClient(create_app())

        # Test with correct credentials
        response = test_client.get("/metrics", auth=(TEST_USERNAME, TEST_PASSWORD))
        assert response.status_code == 200

        # Test with incorrect credentials
        response = test_client.get("/metrics", auth=("wrongusername", "wrongpassword"))
        assert response.status_code == 401

        # Test without credentials
        response = test_client.get("/metrics")
        assert response.status_code == 401
