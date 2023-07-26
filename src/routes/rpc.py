from http.client import HTTPResponse
from typing import Callable, Union

from fastapi import Request, APIRouter, HTTPException
from fastapi.responses import Response, JSONResponse

from src.rpc.common import validate_rpc_request, validate_rpc_response, rpc_auth
from src.rpc.models import JSONRPCResponse
from src.rpc.error_responses import (
    method_not_found,
    AuthError,
    AuthInvalidTokenError,
    json_rpc_response_to_exception,
    no_authenticated_headers_passed,
    token_validation_failed,
)
from src.rpc import authenticated_routes, unauthenticated_routes

router = APIRouter(
    tags=["rpc"],
    responses={404: {"description": "Not found"}},
)

unauthenticated_routes = {
    "ServiceWizard.list_service_status": unauthenticated_routes.list_service_status,
    "ServiceWizard.status": unauthenticated_routes.status,
}
authenticated_routes = {
    "ServiceWizard.start": authenticated_routes.start,
}

# Combine the dictionaries
known_methods = {**unauthenticated_routes, **authenticated_routes}


@router.post("/rpc", response_model=None)
@router.post("/rpc/", response_model=None)
async def json_rpc(request: Request) -> Response | HTTPException | JSONRPCResponse | JSONResponse:
    method, params, jrpc_id = await validate_rpc_request(request)
    request_function: Callable = known_methods.get(method)
    if request_function is None:
        return method_not_found(method=method, jrpc_id=jrpc_id)

    # If the request function is in the authenticated routes, then we need to check the token and return any error messages
    # That may arise during authentication
    if request_function in authenticated_routes.values():
        authorized = rpc_auth(request, jrpc_id)
        if isinstance(authorized, Response):
            return authorized

    response = await request_function(request, params, jrpc_id)
    return validate_rpc_response(response)
