import hashlib

from cacheout import LRUCache

from src.clients.CatalogClient import Catalog
from src.configs.settings import Settings, get_settings


def get_module_name_hash(module_name: str = None):
    """
    Calculate the MD5 hash of a module name and return the first 20 characters of the hexadecimal digest.
    This is not a valid DNS name as it doesn't guarantee to start or end with an alphanumeric character.
    This doesn't actually get used anywhere, its just here because it was like this in SW1
    :param module_name: The name of the module.
    :return: The MD5 hash of the module name.
    """
    return hashlib.md5(module_name.encode()).hexdigest()[:20]


def _clean_version(version) -> str:
    if version is None:
        version = "release"

    return str(version)


def _get_key(module_name: str, version: str = "release") -> str:
    return str(module_name) + "-" + str(_clean_version(version))


class CachedCatalogClient:
    module_info_cache = LRUCache(ttl=10)
    module_volume_mount_cache = LRUCache(ttl=10)
    secure_config_cache = LRUCache(ttl=10)
    module_hash_mappings_cache = LRUCache(ttl=10)

    cc: Catalog

    def __init__(self, settings: Settings, catalog: Catalog = None):
        settings = get_settings() if not settings else settings
        self.cc = Catalog(url=settings.catalog_url, token=settings.catalog_admin_token) if not catalog else catalog

    def get_combined_module_info(self, module_name: str, version: str = "release") -> dict:
        """
        Retrieve the module info from the KBase Catalog
        This is a combination of two KBase Catalog methods:

        - get_module_version - all module information
        - get_module_info - a subset of just ownership information

        :param module_name:     The name of the module.
        :param version:       The version of the module.
        :return: The module info from the KBase Catalog
        """
        print(f"About to look up, {module_name}, {version}, {_clean_version(version), type(_clean_version(version))}")
        key = _get_key(module_name, version)
        combined_module_info = self.module_info_cache.get(key=key, default=None)
        if not combined_module_info:
            combined_module_info = self.cc.get_module_version({"module_name": module_name, "version": _clean_version(version)})
            combined_module_info["owners"] = self.cc.get_module_info({"module_name": module_name})["owners"]
            self.module_info_cache.set(key=key, value=combined_module_info)
        if combined_module_info.get("dynamic_service") != 1:
            module_info_str = f'{combined_module_info["module_name"]}-{combined_module_info["git_commit_hash"]}'
            raise ValueError(f"Specified module is not marked as a dynamic service. ({module_info_str})")
        return combined_module_info

    def list_service_volume_mounts(self, module_name: str, version: str = "release") -> list[dict]:
        """
        Retrieve the volume mounts for a service from the catalog.
        :param module_name: The name of the module.
        :param version: The version of the module.
        :return: A list of volume mounts for the service.
        """
        key = _get_key(module_name, version)
        mounts = self.module_volume_mount_cache.get(key=key, default=None)
        if not mounts:
            mounts_list = self.cc.list_volume_mounts(filter={"module_name": module_name, "version": _clean_version(version), "client_group": "service", "function_name": "service"})
            mounts = []
            if len(mounts_list) > 0:
                mounts = mounts_list[0]["volume_mounts"]
            self.module_volume_mount_cache.set(key=key, value=mounts)
        return mounts

    def get_secure_params(self, module_name: str, version: str = "release"):
        """
        Retrieve the secure config parameters for a module from the catalog.
        :param module_name: The name of the module.
        :param version: The version of the module.
        :return: A dictionary of secure config parameters for the module.
        """
        key = _get_key(module_name, version)
        secure_config_params = self.secure_config_cache.get(key=key, default=None)
        if not secure_config_params:
            secure_config_params = self.cc.get_secure_config_params({"module_name": module_name, "version": _clean_version(version)})
            self.secure_config_cache.set(key=key, value=secure_config_params)
        return secure_config_params

    def get_hash_to_name_mappings(self):
        """
        Retrieve the hashes of dynamic service modules from the catalog.
        Connects to the catalog using the provided request, retrieves the list of basic module
        information, filters for dynamic service modules, and returns a dictionary mapping module name hashes
        to their corresponding module names.

        :return: A dictionary mapping module name hashes to their corresponding module names.
        """
        key = "module_hash_mappings"
        module_hash_mapppings = self.module_hash_mappings_cache.get(key=key, default={})
        if not module_hash_mapppings:
            basic_module_info = self.cc.list_basic_module_info({"include_released": 1, "include_unreleased": 1})
            for m in basic_module_info:
                if "dynamic_service" not in m or m["dynamic_service"] != 1:
                    continue
                module_hash_mapppings[get_module_name_hash(m["module_name"])] = m["module_name"]
            self.module_hash_mappings_cache.set(key=key, value=module_hash_mapppings)
        return module_hash_mapppings
