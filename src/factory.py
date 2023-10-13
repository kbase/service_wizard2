import logging
import os
from typing import Optional

import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from clients.CachedAuthClient import CachedAuthClient
from clients.CachedCatalogClient import CachedCatalogClient
from clients.KubernetesClients import K8sClients
from configs.settings import get_settings, Settings
from routes.authenticated_routes import router as sw2_authenticated_router
from routes.metrics_routes import router as metrics_router
from routes.rpc import router as sw2_rpc_router
from routes.unauthenticated_routes import router as sw2_unauthenticated_router


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
    :param k8s_clients: An instance of K8sClients
    :param settings: An instance of Settings
    :return:
         Fastapi app and clients saved it its state attribute
    """
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

    if os.environ.get("DOTENV_FILE_LOCATION"):
        load_dotenv(os.environ.get("DOTENV_FILE_LOCATION", ".env"))

    if not settings:
        settings = get_settings()

    if os.environ.get("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=os.environ["SENTRY_DSN"],
            traces_sample_rate=1.0,
            http_proxy=os.environ.get("HTTP_PROXY"),
            environment=settings.external_ds_url,
        )

    app = FastAPI(root_path=settings.root_path)  # type: FastAPI

    # Set up the state of the app with various clients.
    # Note, when running multiple threads, these will each have their own cache
    app.state.settings = settings
    app.state.catalog_client = catalog_client or CachedCatalogClient(settings=settings)
    app.state.k8s_clients = k8s_clients if k8s_clients else K8sClients(settings=settings)
    app.state.auth_client = auth_client if auth_client else CachedAuthClient(settings=settings)

    # Add the routes
    app.include_router(sw2_authenticated_router)
    app.include_router(sw2_unauthenticated_router)
    app.include_router(sw2_rpc_router)

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    if os.environ.get("METRICS_USERNAME") and os.environ.get("METRICS_PASSWORD"):
        app.include_router(router=metrics_router)

    return app
