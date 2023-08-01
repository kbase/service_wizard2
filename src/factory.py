import logging
import os
from typing import Optional

import sentry_sdk
from cacheout import LRUCache
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.clients.CachedAuthClient import CachedAuthClient
from src.clients.CachedCatalogClient import CachedCatalogClient
from src.clients.KubernetesClients import K8sClients
from src.configs.settings import get_settings, Settings
from src.routes.authenticated_routes import router as sw2_authenticated_router
from src.routes.rpc import router as sw2_rpc_router
from src.routes.unauthenticated_routes import router as sw2_unauthenticated_router


def create_app(
    catalog_client: Optional[CachedCatalogClient] = None,
    auth_client: Optional[CachedAuthClient] = None,
    k8s_clients: K8sClients = None,
    settings: Optional[Settings] = None,
) -> FastAPI:
    """
    Create the app with the required dependencies.

    Parameters:
        token_cache (LRUCache): LRUCache for tokens.
        catalog_cache (LRUCache): LRUCache for catalog data.
        catalog_client (Optional[Catalog]): Optional existing Catalog client.
        k8s_core_client (Optional[client.CoreV1Api]): Optional existing CoreV1Api client.
        k8s_app_client (Optional[client.AppsV1Api]): Optional existing AppsV1Api client.
        k8s_network_client (Optional[client.NetworkingV1Api]): Optional existing NetworkingV1Api client.
        settings (Optional[Settings]): Optional settings object containing configuration details.

    Returns:
         Fastapi app and clients saved it its state attribute
    """
    logging.basicConfig(level=logging.DEBUG)
    load_dotenv(os.environ.get("DOTENV_FILE_LOCATION", ".env"))

    if os.environ.get("SENTRY_DSN"):
        # Monkeypatch here
        # Will require socks proxy for local development
        sentry_sdk.init(
            dsn=os.environ["SENTRY_DSN"],
            traces_sample_rate=1.0,
            http_proxy=os.environ.get("HTTP_PROXY"),
        )
    if not settings:
        settings = get_settings()
    app = FastAPI(root_path=settings.root_path)  # type: FastAPI

    # TODO Combine the cache and catalog client together into a class called CatalogClient
    # Change the client to be that, and remove the caches from the state object

    # Settings
    app.state.settings = settings
    app.state.catalog_client = catalog_client or CachedCatalogClient(settings=settings)
    app.state.k8s_clients = k8s_clients if k8s_clients else K8sClients(settings=settings)
    app.state.auth_client = auth_client if auth_client else CachedAuthClient(settings=settings)
    app.include_router(sw2_authenticated_router)
    app.include_router(sw2_unauthenticated_router)
    app.include_router(sw2_rpc_router)

    # Middleware Do we need this?
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    Instrumentator().instrument(app).expose(app)

    return app
