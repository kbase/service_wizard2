import pytest
from unittest.mock import patch, Mock
from fastapi import FastAPI

from factory import create_app

from factory import create_app, sw2_authenticated_router, sw2_unauthenticated_router, sw2_rpc_router
from routes.metrics_routes import router as metrics_router


@pytest.fixture
def mock_env_vars(monkeypatch):
    # Mock some environment variables
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("SENTRY_DSN", "mock_sentry_dsn")
    monkeypatch.setenv("METRICS_USERNAME", "user")
    monkeypatch.setenv("METRICS_PASSWORD", "password")
    monkeypatch.setenv("DOTENV_FILE_LOCATION", ".env")


@pytest.fixture
def mock_clients():
    return {
        "catalog_client": Mock(),
        "auth_client": Mock(),
        "k8s_clients": Mock(),
    }


def test_create_app_with_defaults(mock_env_vars, mock_clients):
    with patch("factory.CachedCatalogClient", return_value=mock_clients["catalog_client"]), patch("factory.CachedAuthClient", return_value=mock_clients["auth_client"]), patch(
        "factory.K8sClients", return_value=mock_clients["k8s_clients"]
    ), patch("sentry_sdk.init") as mock_sentry_init:
        app = create_app()

    assert isinstance(app, FastAPI)
    # Test clients initialization in app's state
    assert app.state.catalog_client == mock_clients["catalog_client"]
    assert app.state.auth_client == mock_clients["auth_client"]
    assert app.state.k8s_clients == mock_clients["k8s_clients"]

    all_paths = [route.path for route in app.routes]
    for path in sw2_authenticated_router.routes:
        assert path.path in all_paths

    for path in sw2_unauthenticated_router.routes:
        assert path.path in all_paths

    for path in sw2_rpc_router.routes:
        assert path.path in all_paths

    for path in metrics_router.routes:
        assert path.path in all_paths


def test_create_app_without_metrics(mock_env_vars, mock_clients, monkeypatch):
    monkeypatch.delenv("METRICS_USERNAME", raising=False)
    monkeypatch.delenv("METRICS_PASSWORD", raising=False)

    with patch("factory.CachedCatalogClient", return_value=mock_clients["catalog_client"]), patch("factory.CachedAuthClient", return_value=mock_clients["auth_client"]), patch(
        "factory.K8sClients", return_value=mock_clients["k8s_clients"]
    ), patch("sentry_sdk.init") as mock_sentry_init:
        app = create_app()

    # Test the inclusion of routers
    router_names = [r.name for r in app.routes]
    assert "metrics_router" not in router_names


# You can expand with more test functions or scenarios as needed
