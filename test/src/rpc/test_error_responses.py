import pytest
from fastapi.responses import JSONResponse

from rpc.error_responses import (
    json_rpc_response_to_exception,
    method_not_found,
    no_params_passed,
    not_enough_params,
    invalid_params,
    no_authenticated_headers_passed,
    token_validation_failed,
)
from rpc.models import ErrorResponse, JSONRPCResponse


# Functions under test should be imported.


@pytest.mark.parametrize(
    "func, method, jrpc_id, expected_message, expected_code",
    [
        (method_not_found, "testMethod", "1", "Method 'testMethod' not found", -32601),
        (no_params_passed, "testMethod", "2", "No params passed to method testMethod", -32602),
        (not_enough_params, "testMethod", "3", "Not enough params passed to method testMethod", -32602),
        (invalid_params, "testMethod", "4", "Invalid params passed method testMethod, see the spec for more details", -32602),
        (
            no_authenticated_headers_passed,
            None,
            "5",
            "Token validation failed: Must supply token: Authentication required for ServiceWizard2 but no authentication header or kbase_session cookie was passed",
            -32000,
        ),
        (token_validation_failed, None, "6", "Token validation failed: Error connecting to auth service: 401 Unauthorized\n10020 Invalid token", -32000),
    ],
)
def test_error_functions(func, method, jrpc_id, expected_message, expected_code):
    if method:
        response = func(method, jrpc_id)
    else:
        response = func(jrpc_id)
    assert isinstance(response, JSONRPCResponse)
    assert response.id == jrpc_id
    assert response.error.message == expected_message
    assert response.error.code == expected_code


def test_json_rpc_response_to_exception():
    error_response = ErrorResponse(message="Test Error", code=-32000, name="Server error")
    jrpc_response = JSONRPCResponse(id="7", error=error_response)

    response = json_rpc_response_to_exception(jrpc_response)
    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    # assert response.body == b'{"version":"1.0","id": "7", "error": {"message": "Test Error", "code": -32000, "name": "Server error"}}'
    assert response.body == b'{"version":"1.0","id":"7","error":{"message":"Test Error","code":-32000,"name":"Server error","error":null}}'
