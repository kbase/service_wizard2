from src.rpc.models import ErrorResponse, JSONRPCResponse


def request_path_not_found(method, jrpc_id) -> JSONRPCResponse:
    return JSONRPCResponse(id=jrpc_id, error=ErrorResponse(message=f"Method '{method}' not found", code=-32601, name="Method not found", error=None))


def no_authenticated_headers_passed(jrpc_id):
    return JSONRPCResponse(
        id=jrpc_id,
        error=ErrorResponse(
            message="Authentication required for ServiceWizard2 but no authentication header or kbase_session cookie " "was passed",
            code=-32000,
            name="Server error",
            error=None,
        ),
    )
