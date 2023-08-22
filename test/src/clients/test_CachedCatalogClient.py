from unittest.mock import Mock

import pytest

from src.clients.CachedCatalogClient import CachedCatalogClient, get_module_name_hash
from src.configs.settings import get_settings


@pytest.fixture
def mocked_catalog():
    return Mock()


@pytest.fixture
def client(mocked_catalog):
    ccc = CachedCatalogClient(settings=get_settings(), catalog=mocked_catalog)

    return ccc


def test_get_combined_module_info(client, mocked_catalog):
    mocked_catalog.get_module_version.return_value = {"module_name": "test_module", "git_commit_hash": "abcdef123456", "dynamic_service": 1}
    mocked_catalog.get_module_info.return_value = {"owners": ["user1", "user2"]}

    result = client.get_combined_module_info(module_name="test_module", version="release")
    expected_result = {"module_name": "test_module", "git_commit_hash": "abcdef123456", "dynamic_service": 1, "owners": ["user1", "user2"]}
    assert result == expected_result


def test_list_service_volume_mounts(client, mocked_catalog):
    mocked_catalog.list_volume_mounts.return_value = [{"volume_mounts": [{"path": "/data"}]}]

    result = client.list_service_volume_mounts(module_name="test_module", version="release")
    assert result == [{"path": "/data"}]


def test_get_secure_params(client, mocked_catalog):
    mocked_catalog.get_secure_config_params.return_value = {"param1": "value1", "param2": "value2"}

    result = client.get_secure_params(module_name="test_module", version="release")
    assert result == {"param1": "value1", "param2": "value2"}


def test_get_hash_to_name_mappings(client, mocked_catalog):
    mocked_catalog.list_basic_module_info.return_value = [{"module_name": "test_module", "dynamic_service": 1}, {"module_name": "another_module", "dynamic_service": 0}]

    result = client.get_hash_to_name_mappings()
    assert result == {get_module_name_hash("test_module"): "test_module"}
