import json
import traceback
from typing import Callable, Any

from fastapi import HTTPException, Request

from clients.CachedAuthClient import UserAuthRoles, CachedAuthClient  # noqa: F401
from clients.baseclient import ServerError
from rpc.error_responses import (
    no_params_passed,
)
from rpc.models import ErrorResponse, JSONRPCResponse


def validate_rpc_request(body):
    """
    Validate the JSON-RPC request body to ensure methods and params are present and of the correct type.
    :param body: The JSON-RPC request body
    :return: The method, params, and jrpc_id which is set to 0 if not provided
    """
    try:
        json_data = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        raise ServerError(
            message=f"Parse error JSON format. Invalid JSON was received by the server. An error occurred on the server while parsing the " f"JSON text.. got {type(body)}",
            code=-32700,
            name="Parse error",
        )

    if not isinstance(json_data, dict):
        raise ServerError(message=f"Invalid Request - The JSON sent is not a valid Request object. {json_data} ", code=-32600, name="Invalid Request")

    method = json_data.get("method", "")
    params = json_data.get("params", [])
    jrpc_id = json_data.get("id", 0)

    if not isinstance(method, str) and not isinstance(params, list):
        raise ServerError(message=f"`method` must be a valid SW1 method string. Params must be a dictionary. {json_data}", code=-32600, name="Invalid Request")
    print(type(method), type(params), type(jrpc_id))
    return method, params, jrpc_id


def validate_rpc_response(response: JSONRPCResponse):
    """
    Validate the JSON-RPC response to ensure that either the error or result is present, but not both.
    :param response: The JSON-RPC response
    :return: The response if valid, otherwise an HTTPException
    """
    try:
        assert isinstance(response, JSONRPCResponse)
        if (response.error is None and response.result is None) or (response.error is not None and response.result is not None):
            raise AssertionError("Both 'error' and 'result' cannot be present or absent together.")
    except AssertionError as e:
        return HTTPException(status_code=500, detail=f"Programming Error: Invalid JSON-RPC response format {e}")
    return response


def get_user_auth_roles(request: Request, jrpc_id: str, method: str) -> tuple[Any, None] | tuple[None, JSONRPCResponse]:
    authorization = request.headers.get("Authorization")
    kbase_session = request.cookies.get("kbase_session")
    try:
        return request.app.state.auth_client.get_user_auth_roles(token=authorization or kbase_session), None
    except HTTPException as e:
        return None, JSONRPCResponse(
            id=jrpc_id,
            error=ErrorResponse(
                message=f"Authentication required for ServiceWizard.{method}",
                code=-32000,
                name="Authentication error",
                error=f"{e.detail}",
            ),
        )
    # Something unexpected happened, but we STILL don't want to authorize the request!


def handle_rpc_request(
    request: Request,
    params: list[dict],
    jrpc_id: str,
    action: Callable,  # This is the function that will be called,  with the signature of (request, module_name, module_version)
) -> JSONRPCResponse:
    method_name = action.__name__
    try:
        params = params[0]
        if not isinstance(params, dict):
            return JSONRPCResponse(
                id=jrpc_id,
                error=ErrorResponse(
                    message=f"Invalid params for ServiceWizard.{method_name}",
                    code=-32602,
                    name="Invalid params",
                    error=f"Params must be a dictionary. Got {type(params)}",
                ),
            )
    except IndexError:
        return no_params_passed(method=method_name, jrpc_id=jrpc_id)

    # This is for backwards compatibility with SW1 logging functions, as they pass in the "service" dictionary instead of the module_name and version
    service = params.get("service", {})
    module_name = service.get("module_name", params.get("module_name"))
    module_version = service.get("version", params.get("version"))

    try:
        result = action(request, module_name, module_version)
        print("ABOUT TO RETURN RESULT", result)
        return JSONRPCResponse(id=jrpc_id, result=[result])
    except ServerError as e:
        traceback_str = traceback.format_exc()
        return JSONRPCResponse(id=jrpc_id, error=ErrorResponse(message=f"{e.message}", code=-32000, name="Server error", error=f"{traceback_str}"))
    except Exception as e:
        traceback_str = traceback.format_exc()
        return JSONRPCResponse(
            id=jrpc_id,
            error=ErrorResponse(
                message=f"{e}",
                code=-32603,
                name="Internal error - An internal error occurred on the server while processing the request",
                error=f"{traceback_str}",
            ),
        )
