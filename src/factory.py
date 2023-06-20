import logging
import os

import sentry_sdk
from cacheout import LRUCache
from dotenv import load_dotenv
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.routes.authenticated_routes import router as sw2_authenticated_router
from src.routes.unauthenticated_routes import router as sw2_unauthenticated_router


def create_app(token_cache=LRUCache(maxsize=100, ttl=300), catalog_cache=LRUCache(maxsize=100, ttl=300), openapi_url="/openapi.json"):
    logging.basicConfig(level=logging.DEBUG)
    load_dotenv()  # Load environment variables from .env file

    if os.environ.get('SENTRY_DSN'):
        # Monkeypatch here
        # Will require socks proxy for local development
        sentry_sdk.init(
            dsn=os.environ['SENTRY_DSN'],
            traces_sample_rate=1.0,
            http_proxy=os.environ.get('HTTP_PROXY')
        )
    #TODO openapi_url="/services/service_wizard2/openapi.json"
    app = FastAPI(openapi_url=openapi_url)
    app.state.token_cache = token_cache
    app.state.catalog_cache = catalog_cache

    app.include_router(sw2_authenticated_router,)
    app.include_router(sw2_unauthenticated_router)
    Instrumentator().instrument(app).expose(app)

    return app
