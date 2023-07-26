from fastapi.responses import JSONResponse

from src.rpc.models import ErrorResponse, JSONRPCResponse


class ServiceWizardException(Exception):
    pass


class AuthError(ServiceWizardException):
    pass


class AuthInvalidTokenError(ServiceWizardException):
    pass


def method_not_found(method, jrpc_id) -> JSONRPCResponse:
    return JSONRPCResponse(id=jrpc_id, error=ErrorResponse(message=f"Method '{method}' not found", code=-32601, name="Method not found", error=None))

def json_exception(exception: Exception) -> JSONRPCResponse:
    return JSONRPCResponse(id=None, error=ErrorResponse(message=f"{exception}", code=-32700, name="No JSON object could be decoded", error=None))

def no_authenticated_headers_passed(jrpc_id):
    return JSONRPCResponse(
        id=jrpc_id,
        error=ErrorResponse(
            message="Token validation failed: Must supply token: Authentication required for ServiceWizard2 but no authentication header or "
                    "kbase_session cookie was passed",
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
    return JSONResponse(content=content.dict(), status_code=status_code)
