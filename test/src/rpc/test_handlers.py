from unittest.mock import Mock, patch

from fastapi.requests import Request

from rpc.handlers import authenticated_handlers, unauthenticated_handlers

from dependencies import logs, status, lifecycle
from dependencies.lifecycle import stop_deployment

# Mocking the Request object
mock_request = Mock(spec=Request)

# Common mock params and id
mock_params = [{}]
mock_jrpc_id = "test_id"


@patch("rpc.handlers.authenticated_handlers.handle_rpc_request")
def test_stop(mock_handle_rpc):
    authenticated_handlers.stop(mock_request, mock_params, mock_jrpc_id)
    mock_handle_rpc.assert_called_once_with(mock_request, mock_params, mock_jrpc_id, stop_deployment)


@patch("rpc.handlers.authenticated_handlers.handle_rpc_request")
def test_get_service_log(mock_handle_rpc):
    authenticated_handlers.get_service_log(mock_request, mock_params, mock_jrpc_id)
    mock_handle_rpc.assert_called_once_with(mock_request, mock_params, mock_jrpc_id, logs.get_service_log)


@patch("rpc.handlers.authenticated_handlers.handle_rpc_request")
def test_get_service_log_web_socket(mock_handle_rpc):
    authenticated_handlers.get_service_log_web_socket(mock_request, mock_params, mock_jrpc_id)
    mock_handle_rpc.assert_called_once_with(mock_request, mock_params, mock_jrpc_id, logs.get_service_log_web_socket)


@patch("rpc.handlers.unauthenticated_handlers.handle_rpc_request")
def test_list_service_status(mock_handle_rpc):
    unauthenticated_handlers.list_service_status(mock_request, mock_params, mock_jrpc_id)
    mock_handle_rpc.assert_called_once_with(mock_request, mock_params, mock_jrpc_id, status.get_all_dynamic_service_statuses)


@patch("rpc.handlers.unauthenticated_handlers.handle_rpc_request")
def test_get_service_status_without_restart(mock_handle_rpc):
    unauthenticated_handlers.get_service_status_without_restart(mock_request, mock_params, mock_jrpc_id)
    mock_handle_rpc.assert_called_once_with(mock_request, mock_params, mock_jrpc_id, status.get_service_status_one_try)


@patch("rpc.handlers.unauthenticated_handlers.handle_rpc_request")
def test_start(mock_handle_rpc):
    unauthenticated_handlers.start(mock_request, mock_params, mock_jrpc_id)
    mock_handle_rpc.assert_called_once_with(mock_request, mock_params, mock_jrpc_id, lifecycle.start_deployment)


@patch("rpc.handlers.unauthenticated_handlers.handle_rpc_request")
def test_status(mock_handle_rpc):
    unauthenticated_handlers.status(mock_request, mock_params, mock_jrpc_id)
    mock_handle_rpc.assert_called_once_with(mock_request, mock_params, mock_jrpc_id, status.get_status)


@patch("rpc.handlers.unauthenticated_handlers.handle_rpc_request")
def test_version(mock_handle_rpc):
    unauthenticated_handlers.version(mock_request, mock_params, mock_jrpc_id)
    mock_handle_rpc.assert_called_once_with(mock_request, mock_params, mock_jrpc_id, status.get_version)
