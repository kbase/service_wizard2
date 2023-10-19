from unittest.mock import patch, Mock

import pytest
from cacheout import LRUCache
from fastapi import HTTPException

from clients.CachedAuthClient import CachedAuthClient, UserAuthRoles
from configs.settings import get_settings


@pytest.fixture
def valid_tokens_cache():
    # Using a real cache, mocking the cache seems like its not helpful
    # note, bool(MagicMock) == False
    # would have to client.valid_tokens.get.side_effect = [None, MagicMock()] to simulate cache behavior
    cache = LRUCache(ttl=10)
    return cache


@pytest.fixture
def client(valid_tokens_cache):
    settings = get_settings()
    client = CachedAuthClient(settings=settings, valid_tokens_cache=valid_tokens_cache)
    # Note: If valid_tokens is a MagicMock, this clear() call will be mocked and won't raise any errors.
    # If it's an actual LRUCache instance, it will execute the clear() method of LRUCache.
    client.valid_tokens.clear()
    return client


# No Cache
def test_validate_and_get_username_auth_roles_valid_token(client):
    with patch("requests.get", return_value=Mock(status_code=200, json=lambda: {"user": "testuser", "customroles": ["user", "admin"]})):
        username, roles = client.validate_and_get_username_auth_roles(token="valid_token")
        uar = UserAuthRoles(username=username, user_roles=roles, admin_roles=get_settings().admin_roles, token="valid_token")

        assert username == "testuser"
        assert roles == ["user", "admin"]
        assert uar.is_admin is False
        assert uar.is_admin_or_owner(owners=["testuser"]) is True


# No Cache
def test_validate_and_get_username_auth_roles_invalid_token(client):
    with patch("requests.get", return_value=Mock(status_code=401, json=lambda: {"error": "Invalid token"})):
        with pytest.raises(HTTPException) as excinfo:
            client.validate_and_get_username_auth_roles(token="invalid_token")
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Invalid token"


# No Cache
def test_validate_and_get_username_auth_roles_auth_service_down(client):
    with patch("requests.get", side_effect=Exception("Auth service error")):
        with pytest.raises(HTTPException) as excinfo:
            client.validate_and_get_username_auth_roles(token="any_token")
        assert excinfo.value.status_code == 500
        assert excinfo.value.detail == "Auth service is down or bad request"


# No Cache
def test_validate_and_get_username_auth_roles_bad_url(client):
    with patch("requests.get", return_value=Mock(status_code=404, json=lambda: {"error": "Not Found"})):
        with pytest.raises(HTTPException) as excinfo:
            client.validate_and_get_username_auth_roles(token="any_token")
        assert excinfo.value.status_code == 404
        assert excinfo.value.detail == "Auth URL not configured correctly"


def test_is_authorized_invalid_token(client):
    with patch("requests.get", return_value=Mock(status_code=401, json=lambda: {"error": "Invalid token"})):
        with pytest.raises(HTTPException) as excinfo:
            client.is_authorized(token="invalid_token")
            assert excinfo.value.status_code == 401
            assert excinfo.value.detail == "Invalid token"


def test_is_admin_valid_token_admin_role(client: CachedAuthClient):
    with patch("requests.get", return_value=Mock(status_code=200, json=lambda: {"user": "adminuser", "customroles": ["user", get_settings().admin_roles[0]]})):
        assert client.is_admin(token="valid_token")


def test_is_admin_valid_token_non_admin_role(client):
    with patch("requests.get", return_value=Mock(status_code=200, json=lambda: {"user": "regularuser", "customroles": ["user"]})):
        assert not client.is_admin(token="valid_token")


def test_get_user_auth_roles_cached(client):
    # Mocking a cached entry for this token
    client.valid_tokens.set("cached_token", UserAuthRoles(username="cacheduser", user_roles=["user"], admin_roles=["admin"], token="cached_token"))

    user_auth_roles = client.get_user_auth_roles("cached_token")
    assert user_auth_roles.username == "cacheduser"
    assert "user" in user_auth_roles.user_roles


def test_get_user_auth_roles_not_cached(client):
    with patch("requests.get", return_value=Mock(status_code=200, json=lambda: {"user": "testuser", "customroles": ["user", "admin"]})):
        user_auth_roles = client.get_user_auth_roles("new_token")
        assert user_auth_roles.username == "testuser"
        assert "admin" in user_auth_roles.user_roles


def test_get_user_auth_roles_with_invalid_token(client):
    with patch("requests.get", return_value=Mock(status_code=401, json=lambda: {"error": "Invalid token"})):
        with pytest.raises(HTTPException) as excinfo:
            client.get_user_auth_roles(token="invalid_token")
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Invalid token"
