from typing import Callable

from fastapi import Request, APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response, JSONResponse

from src.rpc import authenticated_routes, unauthenticated_routes
from src.rpc.common import validate_rpc_request, get_user_auth_roles
from src.rpc.error_responses import (
    method_not_found,
)
from src.rpc.models import JSONRPCResponse

router = APIRouter(
    tags=["rpc"],
    responses={404: {"description": "Not found"}},
)

# No KBase Token Required
unauthenticated_routes_mapping = {
    "ServiceWizard.list_service_status": unauthenticated_routes.list_service_status,
    "ServiceWizard.status": unauthenticated_routes.status,
    "ServiceWizard.version": unauthenticated_routes.version,
    "ServiceWizard.get_service_status_without_restart": unauthenticated_routes.get_service_status_without_restart,
    "ServiceWizard.start": unauthenticated_routes.start,
    "ServiceWizard.get_service_status": unauthenticated_routes.start,
}

# Valid KBase Token and Admin or username in [owners] in kbase.yaml required
admin_or_owner_required = {
    "ServiceWizard.get_service_log": authenticated_routes.get_service_log,
    "ServiceWizard.stop": authenticated_routes.stop,
}

known_methods = {**unauthenticated_routes_mapping, **admin_or_owner_required}


async def get_body(request: Request):
    return await request.body()


@router.post("/rpc", response_model=None)
@router.post("/rpc/", response_model=None)
@router.post("/", response_model=None)
def json_rpc(request: Request, body: bytes = Depends(get_body)) -> Response | HTTPException | JSONRPCResponse | JSONResponse:
    print(f"Original Request Payload  {body.decode()}")

    method, params, jrpc_id = validate_rpc_request(body)
    request_function: Callable = known_methods.get(method)
    if request_function is None:
        return method_not_found(method=method, jrpc_id=jrpc_id)

    if request_function in admin_or_owner_required.values():
        user_auth_roles, auth_error = get_user_auth_roles(request, jrpc_id, method)
        if auth_error:
            return JSONResponse(content=jsonable_encoder(auth_error), status_code=500)
        else:
            request.state.user_auth_roles = user_auth_roles

    valid_response = request_function(request, params, jrpc_id)  # type:JSONRPCResponse
    converted_response = jsonable_encoder(valid_response)
    if "error" in converted_response:
        return JSONResponse(content=converted_response, status_code=500)
    return JSONResponse(content=converted_response, status_code=200)
