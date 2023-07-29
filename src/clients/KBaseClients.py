import hashlib

from cacheout import LRUCache

from clients.CachedCatalogClient import CachedCatalogClient
from clients.CatalogClient import Catalog
from configs.settings import Settings





def KBaseClients:

    cc : CachedCatalogClient
    def __init__(self, settings: Settings):
        cc = CachedCatalogClient(settings)