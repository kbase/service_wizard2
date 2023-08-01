import logging

from fastapi.requests import Request

from src.rpc.error_responses import not_enough_params, invalid_params
from src.dependencies.status import get_all_dynamic_service_statuses, get_service_status_with_retries
from src.rpc.models import JSONRPCResponse


async def list_service_status(request: Request, params: dict, jrpc_id: str) -> JSONRPCResponse:
    if params:
        logging.debug(f"dropping list_service_status params since SW1 doesn't use them: {params}")
    # TODO Catch HTTP Exceptions and return them as JSONRPCResponse errors

    all_service_statuses = get_all_dynamic_service_statuses(request)
    return JSONRPCResponse(id=jrpc_id, result=[all_service_statuses])


async def get_service_status_without_restart(request: Request, params: dict, jrpc_id: str) -> JSONRPCResponse:
    try:
        if len(params):
            module_name = params[0].get("module_name")
            module_version = params[0].get("version")
        else:
            return not_enough_params(method='get_service_status_without_restart', jrpc_id=jrpc_id)
    except:
        return invalid_params(method='get_service_status_without_restart', jrpc_id=jrpc_id)

    service_status = get_service_status_with_retries(request, module_name, module_version)
    return JSONRPCResponse(id=jrpc_id, result=service_status)


async def status(request: Request, params: dict, jrpc_id: str) -> JSONRPCResponse:
    if params:
        logging.debug(f"dropping status params since SW1 doesn't use them: {params}")

    service_wizard_status = [
        {
            "git_commit_hash": request.app.state.settings.vcs_ref,
            "state": "OK",
            "version": request.app.state.settings.vcs_ref,
            "message": "",
            "git_url": "https://github.com/kbase/service_wizard2"
        }
    ],
    return JSONRPCResponse(id=jrpc_id, result=service_wizard_status)


async def version(request: Request, params: dict, jrpc_id: str) -> JSONRPCResponse:
    if params:
        logging.debug(f"dropping version params since SW1 doesn't use them: {params}")

    service_wizard_status = [str(request.app.state.settings.vcs_ref)]
    return JSONRPCResponse(id=jrpc_id, result=service_wizard_status)
