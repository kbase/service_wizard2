import os
from unittest.mock import patch
import pytest

from src.configs.settings import EnvironmentVariableError, get_settings, Settings
from dotenv import load_dotenv

# These tests are not quite working. Removing stuff from the .env and they still pass.
# def test_get_settings_missing_auth_service_url():
#     # Test case for missing AUTH_SERVICE_URL environment variable
#     os.environ["NAMESPACE"] = "test_namespace"
#     os.environ["KBASE_ENDPOINT"] = "http://test_kbase"
#     os.environ["CATALOG_URL"] = "http://test_catalog"
#     os.environ["CATALOG_ADMIN_TOKEN"] = "test_catalog_token"
#     os.environ["KUBECONFIG"] = "/path/to/kubeconfig"
#     os.environ["KBASE_ADMIN_ROLE"] = "kbase_admin"
#     os.environ["CATALOG_ADMIN_ROLE"] = "catalog_admin"
#     # os.environ["SERVICE_WIZARD_ROLE"] = "service_wizard"
#
#     with pytest.raises(EnvironmentVariableError):
#         get_settings()
#
#     get_settings.cache_clear()
#     load_dotenv()
#     get_settings()

def test_dotenv_settings():
    #TODO FIX THIS TEST
    load_dotenv("/Users/bsadkhin/modules/kbase/service_wizard2/.env")
    print(os.environ['NAMESPACE'])
    get_settings.cache_clear()
    s = get_settings()
    assert s.namespace == "staging-dynamic-services"
    print(s)

@pytest.fixture(autouse=True)
def clear_cache():
    # Clear the cache for get_settings() to ensure that the environment variables are reloaded
    get_settings.cache_clear()
