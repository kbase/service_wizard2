import hashlib
from unittest.mock import Mock

import pytest

from src.clients.CatalogClient import Catalog
from src.clients.CachedCatalogClient import CachedCatalogClient, get_module_name_hash, _get_key, _clean_version
from src.configs.settings import get_settings


@pytest.fixture
def mocked_catalog():
    return Mock()


@pytest.fixture
def client(mocked_catalog):
    ccc = CachedCatalogClient(settings=get_settings(), catalog=mocked_catalog)
    ccc.module_hash_mappings_cache.clear()
    ccc.module_info_cache.clear()
    ccc.module_volume_mount_cache.clear()
    ccc.secure_config_cache.clear()
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


def test_get_combined_module_info_not_dynamic_service(client, mocked_catalog):
    mocked_catalog.get_module_version.return_value = {"module_name": "test_module", "git_commit_hash": "abcdef123456", "dynamic_service": 0}
    mocked_catalog.get_module_info.return_value = {"owners": ["user1", "user2"]}

    with pytest.raises(ValueError, match="not marked as a dynamic service"):
        client.get_combined_module_info(module_name="test_module", version="release")


def test_get_combined_module_info_cached(client, mocked_catalog):
    cached_info = {"module_name": "cached_module", "git_commit_hash": "abcdef123456", "dynamic_service": 1, "owners": ["user1", "user2"]}
    client.module_info_cache.set(key="cached_module-release", value=cached_info)

    result = client.get_combined_module_info(module_name="cached_module", version="release")
    assert result == cached_info


def test_list_service_volume_mounts_no_mounts(client, mocked_catalog):
    mocked_catalog.list_volume_mounts.return_value = []
    result = client.list_service_volume_mounts(module_name="test_module", version="release")
    assert result == []


def test_list_service_volume_mounts_cached(client, mocked_catalog):
    cached_mounts = [{"path": "/cached_data"}]
    client.module_volume_mount_cache.set(key="cached_module-release", value=cached_mounts)

    result = client.list_service_volume_mounts(module_name="cached_module", version="release")
    assert result == cached_mounts


def test_get_secure_params_cached(client, mocked_catalog):
    cached_params = {"param1": "cached_value1", "param2": "cached_value2"}
    client.secure_config_cache.set(key="cached_module-release", value=cached_params)

    result = client.get_secure_params(module_name="cached_module", version="release")
    assert result == cached_params


def test_get_hash_to_name_mappings_cached(client, mocked_catalog):
    cached_mappings = {get_module_name_hash("cached_module"): "cached_module"}
    client.module_hash_mappings_cache.set(key="module_hash_mappings", value=cached_mappings)

    result = client.get_hash_to_name_mappings()
    assert result == cached_mappings


def test_clean_version():
    assert _clean_version(None) == "release"
    assert _clean_version("dev") == "dev"


def test_get_key():
    assert _get_key("module_name", "version") == "module_name-version"
    assert _get_key("module_name") == "module_name-release"


def test_get_module_name_hash():
    result = get_module_name_hash("test_module")
    expected_result = hashlib.md5("test_module".encode()).hexdigest()[:20]
    assert result == expected_result


def test_cached_catalog_client_default_init(mocked_catalog):
    ccc = CachedCatalogClient(settings=None)
    assert isinstance(ccc.cc, Catalog)


def test_cached_catalog_client_custom_catalog(mocked_catalog):
    ccc = CachedCatalogClient(settings=get_settings(), catalog=mocked_catalog)
    assert ccc.cc == mocked_catalog
