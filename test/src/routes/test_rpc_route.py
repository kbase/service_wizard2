# import json
# from unittest.mock import patch, PropertyMock, MagicMock
#
# import pytest
# from fastapi.testclient import TestClient
#
# from src.routes import rpc_route
# from clients import CachedAuthClient, CachedCatalogClient, KubernetesClients
# from factory import create_app
#
#
# @pytest.fixture
# def app():
#     with patch("rpc.authenticated_handlers.stop_deployment") as mock_stop:
#         mock_stop.__name__ = "stop_deployment"  # Set the __name__ attribute
#         yield create_app(
#             auth_client=MagicMock(autospec=CachedAuthClient.CachedAuthClient),
#             catalog_client=MagicMock(autospec=CachedCatalogClient.CachedCatalogClient),
#             k8s_clients=MagicMock(autospec=KubernetesClients.K8sClients),
#         )
#
#
# @pytest.fixture
# def test_client(app):
#     return TestClient(app)
#
#
# @patch("rpc_route.validate_rpc_request")
# @patch("rpc_route.get_user_auth_roles")
# @patch("rpc_route.method_not_found")
# @patch("rpc_route.known_methods", new_callable=PropertyMock)
# def test_json_rpc_direct_call(mock_known_methods, mock_method_not_found, mock_get_user_auth_roles, mock_validate_rpc_request, mock_request):
#     # Create a MagicMock to use as the return value for validate_rpc_request
#     mock_validate_rpc_request.return_value = ("ServiceWizard.stop", [{"module_name": "sample_module", "version": "sample_version"}], "1")
#
#     # Create a MagicMock to use as the return value for known_methods.get
#     mock_request_function = MagicMock()
#
#     # Mock the __getitem__ method of the return value
#     mock_request_function.__getitem__.return_value = MagicMock()
#
#     # Configure the get method of known_methods to return the MagicMock
#     mock_known_methods.get.return_value = mock_request_function
#
#     # Create a MagicMock to use as the return value for get_user_auth_roles
#     mock_user_auth_roles = MagicMock()
#     mock_get_user_auth_roles.return_value = (mock_user_auth_roles, None)
#
#     # Create a MagicMock to use as the return value for method_not_found
#     mock_method_not_found.return_value = MagicMock()
#
#     # Define the sample request data
#     data = {"method": "ServiceWizard.stop", "params": [{"module_name": "sample_module", "version": "sample_version"}], "id": "1"}
#
#     # Encode data to bytes
#     data_bytes = json.dumps(data).encode()
#
#     # Call the json_rpc function directly with the encoded data
#     response = rpc_route.json_rpc(mock_request, data_bytes)
#
#     # Verify the response and other assertions
#     assert response.status_code == 200
#
#     # Assertions on the mock dependencies being called
#     mock_validate_rpc_request.assert_called_once_with(data_bytes)
#     mock_known_methods.get.assert_called_once_with("ServiceWizard.stop")
#     mock_request_function.assert_called_once()
#     mock_get_user_auth_roles.assert_not_called()  # Since the method is not in admin_or_owner_required
#     mock_method_not_found.assert_not_called()  # Since the method exists
#
#     # Now set up the test to be in admin_or_owner_required
#     mock_known_methods.get.return_value = MagicMock(return_value=handlers.authenticated_handlers.stop_deployment)
#     mock_get_user_auth_roles.return_value = (mock_user_auth_roles, None)
#
#
# def test_method_not_found(mock_request):
#     with patch("rpc_route.validate_rpc_request", return_value=("Unknown.method", [], "1")), patch("rpc_route.known_methods", {}):
#         response = rpc_route.json_rpc(mock_request, b"{}")
#         assert response.error.code == -32601
#         assert "Method '' not found" in response.error.message
#
