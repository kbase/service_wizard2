import json
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from clients.baseclient import ServerError
from rpc.common import validate_rpc_request, validate_rpc_response, get_user_auth_roles, handle_rpc_request
from rpc.models import JSONRPCResponse, ErrorResponse


def test_validate_rpc_request_invalid_json():
    with pytest.raises(ServerError, match="Parse error JSON format"):
        validate_rpc_request(b"invalid json")


def test_validate_rpc_request_invalid_request():
    with pytest.raises(ServerError, match="Invalid Request"):
        validate_rpc_request(json.dumps([]).encode("utf-8"))


def test_validate_rpc_request_valid_json():
    method, params, jrpc_id = validate_rpc_request(json.dumps({"method": "test_method", "params": [], "id": 1}).encode("utf-8"))
    assert method == "test_method"
    assert params == []
    assert jrpc_id == 1


def test_validate_rpc_response_invalid_response():
    response = JSONRPCResponse(id=1)
    result = validate_rpc_response(response)
    assert isinstance(result, HTTPException)
    assert result.status_code == 500
    assert "Programming Error: Invalid JSON-RPC response format" in result.detail


def test_validate_rpc_response_valid_response():
    response = validate_rpc_response(JSONRPCResponse(id=1, result="test_result"))
    assert response.id == 1
    assert response.result == "test_result"


def test_get_user_auth_roles_auth_error():
    request = MagicMock()
    request.headers = {"Authorization": None}
    request.cookies = {"kbase_session": None}
    request.app.state.auth_client.get_user_auth_roles.side_effect = HTTPException(status_code=401, detail="Unauthorized")
    _, error = get_user_auth_roles(request, "1", "test_method")
    assert error.id == "1"
    assert isinstance(error.error, ErrorResponse)


def test_handle_rpc_request_invalid_params():
    request = MagicMock()
    response = handle_rpc_request(request, [], "1", lambda req, module_name, module_version: "test_result")
    assert response.id == "1"
    assert isinstance(response.error, ErrorResponse)


def test_handle_rpc_request_server_error():
    request = MagicMock()
    action = MagicMock()
    action.__name__ = "test_action"
    action.side_effect = ServerError(name="name", message="test server error", code=500)
    response = handle_rpc_request(request, [{"module_name": "test_module", "version": "1.0"}], "1", action)
    assert response.id == "1"
    assert isinstance(response.error, ErrorResponse)


def test_handle_rpc_request_success():
    request = MagicMock()
    action = MagicMock(return_value="test_result")
    action.__name__ = "test_action"
    response = handle_rpc_request(request, [{"module_name": "test_module", "version": "1.0"}], "1", action)
    assert response.id == "1"
    assert response.result == ["test_result"]


def mock_action(request, module_name, module_version):
    return {"test": "data"}


# 1. Test when params is an empty list:
def test_handle_rpc_request_no_params():
    response = handle_rpc_request(request=MagicMock(), params=[], jrpc_id="1", action=mock_action)
    assert response.error is not None
    assert response.error.name == "Invalid params"
    assert response.error.message == "No params passed to method mock_action"


# 2. Test when the first item in params is not a dictionary:
def test_handle_rpc_request_invalid_params2():
    response = handle_rpc_request(request=MagicMock(), params=["invalid"], jrpc_id="1", action=mock_action)
    assert response.error is not None
    assert response.error.name == "Invalid params"
    assert response.error.message == "Invalid params for ServiceWizard.mock_action"


# 3. Test for unexpected exception:
def mock_action_with_exception(request, module_name, module_version):
    raise ValueError("Unexpected error")


def test_handle_rpc_request_unexpected_exception():
    response = handle_rpc_request(request=MagicMock(), params=[{"module_name": "test", "version": "1.0"}], jrpc_id="1", action=mock_action_with_exception)
    assert response.error is not None
    assert response.error.name == "Internal error - An internal error occurred on the server while processing the request"
    assert "Unexpected error" in response.error.message


def test_validate_rpc_request_invalid_method_and_params():
    with pytest.raises(ServerError) as exc_info:
        validate_rpc_request(body=json.dumps({"method": 123, "params": "not_a_list", "id": 1}).encode("utf-8"))

    error = exc_info.value
    assert error.code == -32600
    assert error.name == "Invalid Request"
    assert "`method` must be a valid SW1 method string. Params must be a dictionary." in error.message
