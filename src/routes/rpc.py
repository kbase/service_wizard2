from typing import Callable

from fastapi import Request, APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response, JSONResponse

from src.clients.baseclient import ServerError
from src.rpc import authenticated_routes, unauthenticated_routes
from src.rpc.common import validate_rpc_request, rpc_auth, AuthException
from src.rpc.error_responses import (
    method_not_found,
)
from src.rpc.models import JSONRPCResponse, ErrorResponse

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
}
# Valid KBase Token Required
kbase_token_required = {
    "ServiceWizard.start": authenticated_routes.start,
    "ServiceWizard.get_service_status": authenticated_routes.start,
}
# Valid KBase Token and Admin or username in [owners] in kbase.yaml required
admin_or_owner_required = {
    "ServiceWizard.get_service_log": authenticated_routes.get_service_log,
    "ServiceWizard.stop": authenticated_routes.stop,
}

authenticated_routes_mapping = {**kbase_token_required, **admin_or_owner_required}

# Combine the dictionaries
known_methods = {**unauthenticated_routes_mapping, **authenticated_routes_mapping}


async def get_body(request: Request):
    return await request.body()


@router.post("/rpc", response_model=None)
@router.post("/rpc/", response_model=None)
@router.post("/", response_model=None)
def json_rpc(request: Request, body: bytes = Depends(get_body)) -> Response | HTTPException | JSONRPCResponse | JSONResponse:
    method, params, jrpc_id = validate_rpc_request(body)
    request_function: Callable = known_methods.get(method)
    if request_function is None:
        return method_not_found(method=method, jrpc_id=jrpc_id)

    try:
        if request_function in authenticated_routes_mapping.values():
            request.state.user_auth_roles = rpc_auth(request, jrpc_id)
    except (AuthException, HTTPException, ServerError) as e:
        auth_error = JSONRPCResponse(
            id=jrpc_id,
            error=ErrorResponse(
                message=f"Authentication required for ServiceWizard.{method}",
                code=-32000,
                name="Authentication error",
                error=f"{e.detail}",
            ),
        )
        return JSONResponse(content=jsonable_encoder(auth_error), status_code=500)
    except:  # noqa E722
        raise

    valid_response = request_function(request, params, jrpc_id)  # type:JSONRPCResponse
    converted_response = jsonable_encoder(valid_response)
    if "error" in converted_response:
        return JSONResponse(content=converted_response, status_code=500)
    return JSONResponse(content=converted_response, status_code=200)
