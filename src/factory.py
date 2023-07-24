import logging
import os

import sentry_sdk
from cacheout import LRUCache
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from kubernetes import client, config
from prometheus_fastapi_instrumentator import Instrumentator

from src.configs.settings import get_settings
from src.routes.authenticated_routes import router as sw2_authenticated_router
from src.routes.unauthenticated_routes import router as sw2_unauthenticated_router
from src.routes.rpc import router as sw2_rpc_router
from src.clients.CatalogClient import Catalog


def create_app(
    token_cache=LRUCache(maxsize=100, ttl=300),
    catalog_cache=LRUCache(maxsize=100, ttl=300),
    catalog_client=None,
    k8s_core_client=None,
    k8s_app_client=None,
):
    logging.basicConfig(level=logging.DEBUG)
    load_dotenv("/Users/bsadkhin/modules/kbase/service_wizard2/.env")  # Load environment variables from .env file
    settings = get_settings()
    if catalog_client is None:
        catalog_client = Catalog(url=settings.catalog_url, token=settings.catalog_admin_token)

    # Don't allow potentially different clients to be passed in
    if (k8s_core_client is not None) ^ (k8s_app_client is not None):
        raise ValueError("Both k8s_core_client and k8s_app_client should either be both None or both filled in.")

    if k8s_core_client is None:
        if settings.use_incluster_config is True:
            # Use a service account token if running in a k8s cluster
            logging.info("Loading in-cluster k8s config")
            config.load_incluster_config()
        else:
            # Use the kubeconfig file, useful for local development and testing
            logging.info(f"Loading k8s config from {settings.kubeconfig}")
            config.load_kube_config(config_file=settings.kubeconfig)
        k8s_core_client = client.CoreV1Api()
        k8s_app_client = client.AppsV1Api()

    if os.environ.get("SENTRY_DSN"):
        # Monkeypatch here
        # Will require socks proxy for local development
        sentry_sdk.init(
            dsn=os.environ["SENTRY_DSN"],
            traces_sample_rate=1.0,
            http_proxy=os.environ.get("HTTP_PROXY"),
        )

    app = FastAPI(root_path=settings.root_path)

    app.state.settings = settings
    app.state.token_cache = token_cache
    app.state.catalog_cache = catalog_cache
    app.state.catalog_client = catalog_client
    app.state.k8s_core_client = k8s_core_client
    app.state.k8s_app_client = k8s_app_client

    app.include_router(sw2_authenticated_router)
    app.include_router(sw2_unauthenticated_router)
    app.include_router(sw2_rpc_router)

    Instrumentator().instrument(app).expose(app)

    return app
