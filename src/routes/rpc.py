from typing import Callable

from fastapi import Request, APIRouter

from src.rpc.rpc_common import validate_rpc_request, validate_rpc_response, request_path_not_found, JSONRPCResponse
from src.rpc import authenticated_rpc_routes, unauthenticated_rpc_routes

router = APIRouter(
    tags=["rpc"],
    responses={404: {"description": "Not found"}},
)





request_path_lookup = {
    "ServiceWizard.list_service_status": unauthenticated_rpc_routes.list_service_status,
    "ServiceWizard.status": unauthenticated_rpc_routes.status,
    "ServiceWizard.start": authenticated_rpc_routes.start,
    # Add more methods and their corresponding lambda functions as needed
}


@router.post("/rpc")
@router.post("/rpc/")
async def json_rpc(request: Request) -> JSONRPCResponse:
    method, params, jrpc_id = await validate_rpc_request(request)
    request_function = request_path_lookup.get(method)
    if request_function is None:
        return request_path_not_found(method=method, jrpc_id=jrpc_id)
    response = request_function(request, params, jrpc_id)
    return validate_rpc_response(response)

