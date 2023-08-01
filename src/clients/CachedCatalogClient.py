import hashlib

from cacheout import LRUCache

from clients.CatalogClient import Catalog
from configs.settings import Settings, get_settings


def get_module_name_hash(module_name: str = None):
    """
    Calculate the MD5 hash of a module name and return the first 20 characters of the hexadecimal digest.
    This is not a valid DNS name as it doesn't guarantee to start or end with an alphanumeric character.
    :param module_name: The name of the module.
    :return: The MD5 hash of the module name.
    """
    return hashlib.md5(module_name.encode()).hexdigest()[:20]


class CachedCatalogClient:
    module_info_cache = LRUCache(ttl=10)
    module_volume_mount_cache = LRUCache(ttl=10)
    secure_config_cache = LRUCache(ttl=10)
    module_hash_mapppings_cache = LRUCache(ttl=10)

    cc: Catalog

    def __init__(self, settings: Settings, catalog: Catalog = None):
        settings = get_settings() if not settings else settings
        self.cc = Catalog(url=settings.catalog_url, token=settings.catalog_admin_token) if not catalog else catalog

    def get_module_info(self, module_name: str, version: str, require_dynamic_service: bool = False) -> dict:
        """
        Retrieve the module info from the KBase Catalog
        :param module_name:     The name of the module.
        :param version:       The version of the module.
        :param require_dynamic_service:  If True, the module must be marked as a dynamic service.
        :return: The module info from the KBase Catalog
        """
        key = module_name + "-" + version
        module_info = self.module_info_cache.get(key=key, default=None)
        if not module_info:
            module_info = self.cc.get_module_version({"module_name": module_name, "version": version})
            self.module_info_cache.set(key=key, value=module_info)
        if require_dynamic_service:
            if "dynamic_service" not in module_info:
                raise ValueError(
                    "Specified module is not marked as a dynamic service. (" + module_info["module_name"] + "-" + module_info["git_commit_hash"] + ")"
                )
            if module_info["dynamic_service"] != 1:
                raise ValueError(
                    "Specified module is not marked as a dynamic service. (" + module_info["module_name"] + "-" + module_info["git_commit_hash"] + ")"
                )
        return module_info

    def list_service_volume_mounts(self, module_name: str, version: str) -> list[dict]:
        """
        Retrieve the volume mounts for a service from the catalog.
        :param module_name: The name of the module.
        :param version: The version of the module.
        :return: A list of volume mounts for the service.
        """
        key = module_name + "-" + version
        mounts = self.module_volume_mount_cache.get(key=key, default=None)
        if not mounts:
            mounts_list = self.cc.list_volume_mounts(
                filter={"module_name": module_name, "version": version, "client_group": "service", "function_name": "service"}
            )
            mounts = []
            if len(mounts_list) > 0:
                mounts = mounts_list[0]["volume_mounts"]
            self.module_volume_mount_cache.set(key=key, value=mounts)
        return mounts

    def get_secure_params(self, module_name: str, version: str):
        """
        Retrieve the secure config parameters for a module from the catalog.
        :param module_name: The name of the module.
        :param version: The version of the module.
        :return: A dictionary of secure config parameters for the module.
        """
        key = module_name + "-" + version
        secure_config_params = self.secure_config_cache.get(key=key, default=None)
        if not secure_config_params:
            secure_config_params = self.cc.get_secure_config_params({"module_name": module_name, "version": version})
            self.secure_config_cache.set(key=key, value=secure_config_params)
        return secure_config_params

    def get_hash_to_name_mappings(self):
        """
        Retrieve the hashes of dynamic service modules from the catalog.
        Connects to the catalog using the provided request, retrieves the list of basic module
        information, filters for dynamic service modules, and returns a dictionary mapping module name hashes
        to their corresponding module names.

        :param request: The request object used to connect to the catalog.
        :return: A dictionary mapping module name hashes to their corresponding module names.
        """
        key = "module_hash_mappings"
        module_hash_mapppings = self.module_hash_mapppings_cache.get(key=key, default={})
        if not module_hash_mapppings:
            basic_module_info = self.cc.list_basic_module_info({"include_released": 1, "include_unreleased": 1})
            for m in basic_module_info:
                if "dynamic_service" not in m or m["dynamic_service"] != 1:
                    continue
                module_hash_mapppings[get_module_name_hash(m["module_name"])] = m["module_name"]
            self.module_hash_mapppings_cache.set(key=key, value=module_hash_mapppings)
        return module_hash_mapppings
