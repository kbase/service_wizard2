from typing import Callable

from fastapi import Request, Response, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from rpc.common import validate_rpc_request, get_user_auth_roles
from rpc.error_responses import method_not_found
from rpc.handlers import unauthenticated_handlers, authenticated_handlers
from rpc.models import JSONRPCResponse

# No KBase Token Required
unauthenticated_routes_mapping = {
    "ServiceWizard.list_service_status": unauthenticated_handlers.list_service_status,
    "ServiceWizard.status": unauthenticated_handlers.status,
    "ServiceWizard.version": unauthenticated_handlers.version,
    "ServiceWizard.get_service_status_without_restart": unauthenticated_handlers.get_service_status_without_restart,
    "ServiceWizard.start": unauthenticated_handlers.start,
    "ServiceWizard.get_service_status": unauthenticated_handlers.start,
}

# Valid KBase Token and Admin or username in [owners] in kbase.yaml required
admin_or_owner_required = {
    "ServiceWizard.get_service_log": authenticated_handlers.get_service_log,
    "ServiceWizard.stop": authenticated_handlers.stop,
}
# Use star unpacking to create a mapping of known routes
known_methods = {**unauthenticated_routes_mapping, **admin_or_owner_required}


def json_rpc_helper(request: Request, body: bytes) -> Response | HTTPException | JSONRPCResponse | JSONResponse:
    method, params, jrpc_id = validate_rpc_request(body)
    request_function: Callable = known_methods.get(method)
    if request_function is None:
        mnf_response = jsonable_encoder(method_not_found(method=method, jrpc_id=jrpc_id))
        return JSONResponse(content=mnf_response, status_code=500)

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
