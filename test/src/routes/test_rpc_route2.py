from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from clients import KubernetesClients
from clients.CachedAuthClient import CachedAuthClient
from clients.CachedCatalogClient import CachedCatalogClient
from factory import create_app
from rpc.handlers.json_rpc_handler import known_methods, admin_or_owner_required


@pytest.fixture
def app():
    with patch("rpc.handlers.authenticated_handlers.stop_deployment") as mock_stop:
        mock_stop.__name__ = "stop_deployment"  # Set the __name__ attribute
        yield create_app(
            auth_client=MagicMock(autospec=CachedAuthClient),
            catalog_client=MagicMock(autospec=CachedCatalogClient),
            k8s_clients=MagicMock(autospec=KubernetesClients.K8sClients),
        )


@pytest.fixture
def test_client(app):
    return TestClient(app)


def test_unknown_method(test_client):
    # Mocking validate_rpc_request to return 'unknown_method' as the method
    with patch("rpc.handlers.json_rpc_handler.validate_rpc_request", return_value=("unknown_method", {}, 1)):
        response = test_client.post("/rpc", json={"jsonrpc": "2.0", "method": "unknown_method", "id": 1})
        assert response.status_code == 500


def test_unauthenticated_route():
    method = next(iter(known_methods.keys()))  # Get the first known method
    if method in admin_or_owner_required:
        return  # skip if it's an authenticated route
    with patch("rpc.handlers.json_rpc_handler.validate_rpc_request", return_value=(method, {}, 1)):
        app = create_app(
            auth_client=MagicMock(autospec=CachedAuthClient),
            catalog_client=MagicMock(autospec=CachedCatalogClient),
            k8s_clients=MagicMock(autospec=KubernetesClients.K8sClients),
        )
        test_client = TestClient(app)
        response = test_client.post("/rpc", json={"jsonrpc": "2.0", "method": method, "id": 1})
        assert response.status_code == 200  # Assuming the handler function for this method returns a successful response
