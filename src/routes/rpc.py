from typing import Callable

from fastapi import Request, APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response, JSONResponse

from src.rpc import authenticated_routes, unauthenticated_routes
from src.rpc.common import validate_rpc_request, validate_rpc_response, rpc_auth
from src.rpc.error_responses import (
    method_not_found,
    json_exception,
)
from src.rpc.models import JSONRPCResponse

router = APIRouter(
    tags=["rpc"],
    responses={404: {"description": "Not found"}},
)

unauthenticated_routes = {
    "ServiceWizard.list_service_status": unauthenticated_routes.list_service_status,
    "ServiceWizard.status": unauthenticated_routes.status,
    "ServiceWizard.version": unauthenticated_routes.version,
    "ServiceWizard.get_service_status_without_restart": unauthenticated_routes.get_service_status_without_restart,
}
authenticated_routes = {
    "ServiceWizard.start": authenticated_routes.start,
    "ServiceWizard.get_service_status": authenticated_routes.start,
    "ServiceWizard.stop": authenticated_routes.stop,
    "ServiceWizard.get_service_log": authenticated_routes.get_service_log,
}

# Combine the dictionaries
known_methods = {**unauthenticated_routes, **authenticated_routes}


async def get_body(request: Request):
    return await request.body()


@router.post("/rpc", response_model=None)
@router.post("/rpc/", response_model=None)
@router.post("/", response_model=None)
def json_rpc(request: Request, body: bytes = Depends(get_body)) -> Response | HTTPException | JSONRPCResponse | JSONResponse:
    try:
        method, params, jrpc_id = validate_rpc_request(request, body)
    except Exception as e:
        return JSONResponse(content=jsonable_encoder(json_exception(e)), status_code=500)

    request_function: Callable = known_methods.get(method)
    if request_function is None:
        return method_not_found(method=method, jrpc_id=jrpc_id)

    if request_function in authenticated_routes.values():
        authorized = rpc_auth(request, jrpc_id)
        # print("Authorized is", authorized.body)
        if isinstance(authorized, Response):
            return authorized

    valid_response = request_function(request, params, jrpc_id)  # type:JSONRPCResponse
    converted_response = jsonable_encoder(valid_response)
    if "error" in converted_response:
        return JSONResponse(content=valid_response, status_code=500)
    return JSONResponse(content=converted_response, status_code=200)
