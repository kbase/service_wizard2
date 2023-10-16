import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from factory import create_app
from clients import CachedAuthClient, CachedCatalogClient, KubernetesClients


@pytest.fixture
def app():
    return create_app(
        auth_client=MagicMock(autospec=CachedAuthClient.CachedAuthClient),
        catalog_client=MagicMock(autospec=CachedCatalogClient.CachedCatalogClient),
        k8s_clients=MagicMock(autospec=KubernetesClients.K8sClients),
    )


@pytest.fixture
def test_client(app):
    return TestClient(app)


def test_unauthenticated_routes(test_client):
    methods_to_functions = {
        "ServiceWizard.list_service_status": "list_service_status",
        "ServiceWizard.status": "status",
        "ServiceWizard.version": "version",
        "ServiceWizard.get_service_status_without_restart": "get_service_status_without_restart",
        "ServiceWizard.start": "start",
        "ServiceWizard.get_service_status": "start",  # Note: This points to the "start" function, as per your mapping
    }

    for method, function in methods_to_functions.items():
        with patch(f"rpc.unauthenticated_handlers.{function}") as mocked_function:
            test_client.post("/rpc", json={"method": method, "params": [{}], "id": 1})
            assert mocked_function.called, f"{function} was not called for {method}"
