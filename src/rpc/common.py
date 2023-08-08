import json

from fastapi import HTTPException, Request

from src.dependencies.middleware import is_authorized
from src.rpc.error_responses import (
    no_authenticated_headers_passed,
    token_validation_failed,
    json_rpc_response_to_exception,
)
from src.rpc.models import JSONRPCResponse


def validate_rpc_request(request, body):
    # Instead of request.json()
    json_data = json.loads(body.decode("utf-8"))

    if not isinstance(json_data, dict):
        raise ValueError(f"Invalid JSON format, got {type(json_data)}")
        # TODO: This should actually return
        # -32600: Invalid Request - The JSON sent is not a valid Request object.
        # -32700: Parse error - Invalid JSON was received by the server. An error occurred on the server while parsing the JSON text.

    method = json_data.get("method")
    params = json_data.get("params")
    # We don't actually care about the jrpc_id
    jrpc_id = json_data.get("id", 0)

    if not isinstance(method, str) or not isinstance(params, list):
        raise ValueError(
            f"Invalid JSON-RPC request format {type(method)} {type(params)}",
        )
    return method, params, jrpc_id


def validate_rpc_response(response: JSONRPCResponse):
    try:
        assert isinstance(response, JSONRPCResponse)
        if (response.error is None and response.result is None) or (response.error is not None and response.result is not None):
            raise AssertionError("Both 'error' and 'result' cannot be present or absent together.")
    except AssertionError as e:
        return HTTPException(status_code=500, detail=f"Programming Error: Invalid JSON-RPC response format {e}")
    return response


def rpc_auth(request: Request, jrpc_id: str):
    # Extract the Authorization header and the kbase_session cookie
    authorization = request.headers.get("Authorization")
    kbase_session = request.cookies.get("kbase_session")

    # If no authorization provided, raise exception

    if not authorization and not kbase_session:
        raise json_rpc_response_to_exception(no_authenticated_headers_passed(jrpc_id))

    # Call the authenticated_user function
    try:
        authorized = is_authorized(request=request, kbase_session=kbase_session, authorization=authorization)
        if not authorized:
            return json_rpc_response_to_exception(token_validation_failed(jrpc_id))
    except:
        raise
