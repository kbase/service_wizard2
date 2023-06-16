import os
from unittest.mock import patch
import pytest

from src.configs.settings import EnvironmentVariableError, get_settings, Settings
from dotenv import load_dotenv


def test_missing_roles_and_clear_settings_cache():
    get_settings()

    del os.environ["KBASE_ADMIN_ROLE"]
    del os.environ["CATALOG_ADMIN_ROLE"]
    del os.environ["SERVICE_WIZARD_ROLE"]
    get_settings.cache_clear()
    with pytest.raises(EnvironmentVariableError):
        get_settings()

    # Load environment again
    load_dotenv()
    get_settings()




@pytest.fixture(autouse=True)
def clear_cache():
    # Clear the cache for get_settings() to ensure that the environment variables are reloaded
    get_settings.cache_clear()
