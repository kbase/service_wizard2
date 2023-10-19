from unittest.mock import MagicMock, ANY
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
    with patch("rpc.handlers.json_rpc_handler.validate_rpc_request", return_value=("unknown_method", {}, 1)):
        response = test_client.post("/rpc", json={"jsonrpc": "2.0", "method": "unknown_method", "id": 1})
        assert response.status_code == 500


def mock_request_function(*args, **kwargs):
    return {"result": "mocked_response"}


def test_unauthenticated_route():
    method = next(iter(known_methods.keys()))  # Get the first known method
    # if method in admin_or_owner_required:
    #     return  # skip if it's an authenticated route

    # Mock the known_methods dictionary to return the mock_request_function for the given method
    with patch.dict("rpc.handlers.json_rpc_handler.known_methods", {method: mock_request_function}):
        app = create_app(
            auth_client=MagicMock(autospec=CachedAuthClient),
            catalog_client=MagicMock(autospec=CachedCatalogClient),
            k8s_clients=MagicMock(autospec=KubernetesClients.K8sClients),
        )
        test_client = TestClient(app)
        payload_with_params = {"jsonrpc": "2.0", "method": method, "params": [{"module_name": "sample_module", "version": "sample_version"}], "id": 1}
        response = test_client.post("/rpc", json=payload_with_params)
        assert response.status_code == 200  # Assuming the handler function for this method returns a successful response
        assert response.json() == {"result": "mocked_response"}


def test_authenticated_route_no_auth(test_client):
    method = next(iter(admin_or_owner_required.keys()))  # Get the first authenticated method
    # Mocking validate_rpc_request and get_user_auth_roles (to return an auth error)
    with patch("rpc.handlers.json_rpc_handler.validate_rpc_request", return_value=(method, {}, 1)):
        with patch("rpc.handlers.json_rpc_handler.get_user_auth_roles", return_value=(None, "Auth Error")):
            response = test_client.post("/rpc", json={"jsonrpc": "2.0", "method": method, "id": 1})
            assert response.status_code == 500


def test_authenticated_route_with_auth(test_client):
    method = next(iter(admin_or_owner_required.keys()))  # Get the first authenticated method
    # Mocking validate_rpc_request and get_user_auth_roles (to return valid auth roles)
    with patch("rpc.handlers.json_rpc_handler.validate_rpc_request", return_value=(method, {}, 1)):
        with patch("rpc.handlers.json_rpc_handler.get_user_auth_roles", return_value=(["admin"], None)):
            with patch.dict("rpc.handlers.json_rpc_handler.known_methods", {method: mock_request_function}):
                response = test_client.post("/rpc", json={"jsonrpc": "2.0", "method": method, "id": 1})
                assert response.status_code == 200
                assert response.json() == {"result": "mocked_response"}


def test_known_method_error_response(test_client):
    method = next(iter(known_methods.keys()))  # Get the first known method

    def mock_error_function(*args, **kwargs):
        return {"error": "Some error occurred."}

    with patch.dict("rpc.handlers.json_rpc_handler.known_methods", {method: mock_error_function}):
        response = test_client.post("/rpc", json={"jsonrpc": "2.0", "method": method, "id": 1})
        assert response.status_code == 500
        assert response.json() == {"error": "Some error occurred."}


def test_request_function_called_correctly(test_client):
    method = next(iter(known_methods.keys()))  # Get the first known method
    # Mock the request_function to track its calls
    mock_function = MagicMock(return_value={"result": "mocked_response"})
    with patch.dict("rpc.handlers.json_rpc_handler.known_methods", {method: mock_function}):
        with patch("rpc.handlers.json_rpc_handler.validate_rpc_request", return_value=(method, {"param1": "value1"}, 1)):
            test_client.post("/rpc", json={"jsonrpc": "2.0", "method": method, "id": 1})
            mock_function.assert_called_once_with(ANY, {"param1": "value1"}, 1)  # Using 'anything()' to ignore matching the request argument


def test_request_function_sets_user_auth_roles(test_client):
    method = next(iter(admin_or_owner_required.keys()))  # Get the first authenticated method

    # Mocking validate_rpc_request to return the method and get_user_auth_roles to return valid auth roles and no errors
    with patch("rpc.handlers.json_rpc_handler.validate_rpc_request", return_value=(method, {}, 1)):
        with patch("rpc.handlers.json_rpc_handler.get_user_auth_roles", return_value=(["admin"], None)):
            # Mock the known_methods dictionary to use the side_effect_check for this method
            with patch.dict("rpc.handlers.json_rpc_handler.known_methods", {method: mock_request_function}):
                response = test_client.post("/rpc", json={"jsonrpc": "2.0", "method": method, "id": 1})
                assert response.status_code == 200
                assert response.json() == {"result": "mocked_response"}


def test_authenticated_route(test_client):
    method = next(iter(admin_or_owner_required.keys()))  # Get the first authenticated method

    # Scenario 1: Test with an auth error
    with patch("rpc.handlers.json_rpc_handler.validate_rpc_request", return_value=(method, {}, 1)):
        with patch("rpc.handlers.json_rpc_handler.get_user_auth_roles", return_value=(None, {"error": "Authentication failed."})):
            with patch("rpc.handlers.json_rpc_handler.function_requires_auth", return_value=True):  # Mock to return that function requires authentication
                response = test_client.post("/rpc", json={"jsonrpc": "2.0", "method": method, "id": 1})
                assert response.status_code == 500
                assert response.json() == {"error": "Authentication failed."}

    # Scenario 2: Test with successful authentication
    with patch("rpc.handlers.json_rpc_handler.validate_rpc_request", return_value=(method, {}, 1)):
        with patch("rpc.handlers.json_rpc_handler.get_user_auth_roles", return_value=(["admin"], None)):
            with patch("rpc.handlers.json_rpc_handler.function_requires_auth", return_value=True):  # Mock to return that function requires authentication
                with patch.dict("rpc.handlers.json_rpc_handler.known_methods", {method: mock_request_function}):
                    response = test_client.post("/rpc", json={"jsonrpc": "2.0", "method": method, "id": 1})
                    assert response.status_code == 200
                    assert response.json() == {"result": "mocked_response"}
