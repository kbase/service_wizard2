import hashlib

from cacheout import LRUCache
from fastapi import Request

from src.clients.CatalogClient import Catalog


def get_catalog_cache(request: Request) -> LRUCache:
    return request.app.state.catalog_cache


def get_catalog_client(request: Request) -> Catalog:
    return request.app.state.catalog_client


def get_module_name_hash(module_name):
    """
    Calculate the MD5 hash of a module name and return the first 20 characters of the hexadecimal digest.
    :param module_name: The name of the module.
    :return: The MD5 hash of the module name.
    """
    return hashlib.md5(module_name.encode()).hexdigest()[:20]


def get_get_module_version(request, module_name, git_commit):
    cc = get_catalog_client(request)
    return cc.get_module_version({"module_name": module_name, "version": git_commit})


def get_hash_to_name_mapping(request):
    """
    Retrieve the hashes of dynamic service modules from the catalog.
    Connects to the catalog using the provided request, retrieves the list of basic module
    information, filters for dynamic service modules, and returns a dictionary mapping module name hashes
    to their corresponding module names.

    :param request: The request object used to connect to the catalog.
    :return: A dictionary mapping module name hashes to their corresponding module names.
    """
    cc = get_catalog_client(request)

    # Retrieve the list of basic module info from the catalog
    modules = cc.list_basic_module_info({"include_released": 1, "include_unreleased": 1})
    module_hash_lookup = {}

    for m in modules:
        # Check if the module is a dynamic service
        if "dynamic_service" not in m or m["dynamic_service"] != 1:
            continue
        module_hash_lookup[get_module_name_hash(m["module_name"])] = m["module_name"]

    # Return the module_hash_lookup dictionary
    return module_hash_lookup
