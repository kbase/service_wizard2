from fastapi.responses import JSONResponse

from rpc.models import ErrorResponse, JSONRPCResponse


def method_not_found(method, jrpc_id) -> JSONRPCResponse:
    return JSONRPCResponse(id=jrpc_id, error=ErrorResponse(message=f"Method '{method}' not found", code=-32601, name="Method not found", error=None))


def no_params_passed(method, jrpc_id):
    return JSONRPCResponse(
        id=jrpc_id,
        error=ErrorResponse(
            message=f"No params passed to method {method}",
            code=-32602,
            name="Invalid params",
            error=None,
        ),
    )


def not_enough_params(method, jrpc_id):
    return JSONRPCResponse(
        id=jrpc_id,
        error=ErrorResponse(
            message=f"Not enough params passed to method {method}",
            code=-32602,
            name="Invalid params",
            error=None,
        ),
    )


def invalid_params(method, jrpc_id):
    return JSONRPCResponse(
        id=jrpc_id,
        error=ErrorResponse(
            message=f"Invalid params passed method {method}, see the spec for more details",
            code=-32602,
            name="Invalid params",
            error=None,
        ),
    )


def no_authenticated_headers_passed(jrpc_id):
    return JSONRPCResponse(
        id=jrpc_id,
        error=ErrorResponse(
            message="Token validation failed: Must supply token: Authentication required for ServiceWizard2 but no authentication header or " "kbase_session cookie was passed",
            code=-32000,
            name="Server error",
            error=None,
        ),
    )


def token_validation_failed(jrpc_id):
    return JSONRPCResponse(
        id=jrpc_id,
        error=ErrorResponse(
            message="Token validation failed: Error connecting to auth service: 401 Unauthorized\n10020 Invalid token",
            code=-32000,
            name="Server error",
            error=None,
        ),
    )


def json_rpc_response_to_exception(content: JSONRPCResponse, status_code=500):
    return JSONResponse(content=content.model_dump(), status_code=status_code)
