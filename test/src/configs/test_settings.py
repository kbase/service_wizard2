import os

import pytest

from src.configs.settings import get_settings, EnvironmentVariableError


@pytest.fixture
def cleared_settings():
    """Fixture to clear the cache of the get_settings function and then return the Settings object."""
    get_settings.cache_clear()
    return get_settings()


def test_get_settings_from_env(cleared_settings):
    """Keep this test in sync with the .env file"""
    assert cleared_settings.namespace == "staging-dynamic-services"
    assert cleared_settings.auth_service_url == "https://ci.kbase.us/services/auth/api/V2/me"
    assert cleared_settings.auth_legacy_url == "https://ci.kbase.us/services/auth/api/legacy/KBase/Sessions/Login"
    assert cleared_settings.kbase_root_endpoint == "https://ci.kbase.us"
    assert cleared_settings.kbase_services_endpoint == "https://ci.kbase.us/services"
    assert cleared_settings.catalog_url == "https://ci.kbase.us/services/catalog"
    assert cleared_settings.catalog_admin_token == "REDACTED"
    assert cleared_settings.kubeconfig == "test_kubeconfig_file"
    assert cleared_settings.admin_roles == ["KBASE_ADMIN", "CATALOG_ADMIN", "SERVICE_WIZARD_ADMIN"]
    assert cleared_settings.external_ds_url == "https://ci.kbase.us/dynamic_services"
    assert cleared_settings.external_sw_url == "https://ci.kbase.us/services/service_wizard"
    assert cleared_settings.git_url == "https://github.com/kbase/service_wizard2"
    assert cleared_settings.root_path == "/"
    assert cleared_settings.use_incluster_config is False
    assert cleared_settings.vcs_ref == os.environ.get("GIT_COMMIT_HASH")


def test_missing_env(cleared_settings):
    env_vars_and_expected_errors = {
        "AUTH_SERVICE_URL": "AUTH_SERVICE_URL is not set in the .env file",
        "AUTH_LEGACY_URL": "AUTH_LEGACY_URL is not set in the .env file",
        "CATALOG_ADMIN_TOKEN": "CATALOG_ADMIN_TOKEN is not set in the .env file",
        "CATALOG_URL": "CATALOG_URL is not set in the .env file",
        "EXTERNAL_DS_URL": "EXTERNAL_DS_URL is not set in the .env file",
        "EXTERNAL_SW_URL": "EXTERNAL_SW_URL is not set in the .env file",
        "KBASE_ROOT_ENDPOINT": "KBASE_ROOT_ENDPOINT is not set in the .env file",
        "KBASE_SERVICES_ENDPOINT": "KBASE_SERVICES_ENDPOINT is not set in the .env file",
        "NAMESPACE": "NAMESPACE is not set in the .env file",
        "ROOT_PATH": "ROOT_PATH is not set in the .env file",
    }

    for env_var, expected_error in env_vars_and_expected_errors.items():
        original_value = os.environ.get(env_var)
        os.environ.pop(env_var, None)  # Temporarily remove the env variable to simulate it being missing

        # Clear the cache for get_settings
        get_settings.cache_clear()

        with pytest.raises(EnvironmentVariableError, match=expected_error):
            get_settings()
        if original_value:  # Restore the original value after the test for this variable
            os.environ[env_var] = original_value


def test_missing_admin_roles():
    admin_roles_vars = ["KBASE_ADMIN_ROLE", "CATALOG_ADMIN_ROLE", "SERVICE_WIZARD_ADMIN_ROLE"]
    admin_roles_values = ["KBASE_ADMIN", "CATALOG_ADMIN", "SERVICE_WIZARD_ADMIN"]
    expected_error = "At least one admin role (KBASE_ADMIN_ROLE, CATALOG_ADMIN_ROLE, or SERVICE_WIZARD_ADMIN_ROLE) must be set in the .env file"

    # Test for cases where 0, 1, or 2 of the admin roles are set
    for i in range(3):
        # Clear all the admin roles first
        for role_var in admin_roles_vars:
            if role_var in os.environ:
                os.environ.pop(role_var)

        # Set i number of admin roles
        for j in range(i):
            os.environ[admin_roles_vars[j]] = admin_roles_values[j]

        # Clear the cache for get_settings
        get_settings.cache_clear()

        # If no roles are set, an error should be raised. Otherwise, get_settings should succeed.
        if i == 0:
            with pytest.raises(EnvironmentVariableError) as exc_info:
                get_settings()
            assert str(exc_info.value) == expected_error
        else:
            settings = get_settings()
            assert settings.admin_roles == admin_roles_values[:i]

    # Restore the original admin roles after testing
    for role_var in admin_roles_vars:
        original_value = os.environ.get(role_var)
        if original_value:
            os.environ[role_var] = original_value
