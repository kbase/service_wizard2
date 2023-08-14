import logging
import os
from typing import Optional

import sentry_sdk
from cacheout import LRUCache  # noqa F401
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
    :param catalog_client: An instance of CachedCatalogClient
    :param auth_client: An instance of CachedAuthClient
    :param k8s_clients:  An instance of K8sClients
    :param settings:  An instance of Settings
    :return:
         Fastapi app and clients saved it its state attribute
    """

    logging.basicConfig(level=logging.DEBUG)
    load_dotenv(os.environ.get("DOTENV_FILE_LOCATION", ".env"))

    # Instrumentation for Sentry connection
    # This is an administrator telemetry setting and should not be used for local development
    if os.environ.get("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=os.environ["SENTRY_DSN"],
            traces_sample_rate=1.0,
            http_proxy=os.environ.get("HTTP_PROXY"),
        )
    if not settings:
        settings = get_settings()
    app = FastAPI(root_path=settings.root_path)  # type: FastAPI

    # Set up the state of the app with various clients. Note, when running multiple threads, these will each have their own cache
    app.state.settings = settings
    app.state.catalog_client = catalog_client or CachedCatalogClient(settings=settings)
    app.state.k8s_clients = k8s_clients if k8s_clients else K8sClients(settings=settings)
    app.state.auth_client = auth_client if auth_client else CachedAuthClient(settings=settings)
    # Add the routes
    app.include_router(sw2_authenticated_router)
    app.include_router(sw2_unauthenticated_router)
    app.include_router(sw2_rpc_router)
    # Middleware Do we need this?
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    # Instrumentation for prometheus metrics
    Instrumentator().instrument(app).expose(app)

    return app
