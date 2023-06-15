import os
from unittest.mock import patch

import pytest

from src.configs.settings import EnvironmentVariableError, get_settings


def test_get_settings_success(setup_env_variables):
    # Test case for successful retrieval of settings
    settings = get_settings()

    assert settings.namespace == "test_namespace"
    assert settings.auth_service_url == "http://test_auth_service"
    assert settings.kbase_endpoint == "http://test_kbase"
    assert settings.catalog_url == "http://test_catalog"
    assert settings.catalog_admin_token == "test_catalog_token"
    assert settings.kubeconfig == "/path/to/kubeconfig"
    assert settings.admin_roles == ["kbase_admin", "catalog_admin", "service_wizard"]


@patch.dict(os.environ, clear=True)
def test_get_settings_missing_variables():
    # Test case for missing environment variables
    with pytest.raises(EnvironmentVariableError):
        get_settings()


def test_get_settings_missing_admin_roles(setup_env_variables):
    # Test case for missing admin roles
    os.environ.pop("KBASE_ADMIN_ROLE")
    os.environ.pop("CATALOG_ADMIN_ROLE")
    os.environ.pop("SERVICE_WIZARD_ROLE")

    with pytest.raises(EnvironmentVariableError):
        get_settings()


def test_get_settings_empty_admin_roles(setup_env_variables):
    # Test case for empty admin roles
    os.environ["KBASE_ADMIN_ROLE"] = ""
    os.environ["CATALOG_ADMIN_ROLE"] = ""
    os.environ["SERVICE_WIZARD_ROLE"] = ""

    with pytest.raises(EnvironmentVariableError):
        get_settings()


def test_get_settings_single_admin_role(setup_env_variables):
    # Test case for setting only one admin role
    os.environ["KBASE_ADMIN_ROLE"] = "kbase_admin"
    os.environ["CATALOG_ADMIN_ROLE"] = ""
    os.environ["SERVICE_WIZARD_ROLE"] = ""

    settings = get_settings()

    assert settings.admin_roles == ["kbase_admin"]





@pytest.fixture(autouse=True)
def setup_env_variables():
    # Clear the cache for get_settings() to ensure that the environment variables are reloaded
    get_settings.cache_clear()

    # Set up the required environment variables for testing
    os.environ["NAMESPACE"] = "test_namespace"
    os.environ["AUTH_SERVICE_URL"] = "http://test_auth_service"
    os.environ["KBASE_ENDPOINT"] = "http://test_kbase"
    os.environ["CATALOG_URL"] = "http://test_catalog"
    os.environ["CATALOG_ADMIN_TOKEN"] = "test_catalog_token"
    os.environ["KUBECONFIG"] = "/path/to/kubeconfig"
    os.environ["KBASE_ADMIN_ROLE"] = "kbase_admin"
    os.environ["CATALOG_ADMIN_ROLE"] = "catalog_admin"
    os.environ["SERVICE_WIZARD_ROLE"] = "service_wizard"

    yield

    # Clean up the environment variables after testing
    os.environ.pop("NAMESPACE", None)
    os.environ.pop("AUTH_SERVICE_URL", None)
    os.environ.pop("KBASE_ENDPOINT", None)
    os.environ.pop("CATALOG_URL", None)
    os.environ.pop("CATALOG_ADMIN_TOKEN", None)
    os.environ.pop("KUBECONFIG", None)
    os.environ.pop("KBASE_ADMIN_ROLE", None)
    os.environ.pop("CATALOG_ADMIN_ROLE", None)
    os.environ.pop("SERVICE_WIZARD_ROLE", None)
