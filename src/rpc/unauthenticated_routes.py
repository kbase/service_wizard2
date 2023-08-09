import logging

from fastapi.requests import Request

from src.dependencies.status import get_all_dynamic_service_statuses, get_service_status_with_retries
from src.rpc.common import handle_rpc_request
from src.rpc.models import JSONRPCResponse


def list_service_status(request: Request, params: list[dict], jrpc_id: int) -> JSONRPCResponse:
    if params:
        logging.debug(f"dropping list_service_status params since SW1 doesn't use them: {params}")
    return handle_rpc_request(request, params, jrpc_id, get_all_dynamic_service_statuses)


def get_service_status_without_restart(request: Request, params: list[dict], jrpc_id: str) -> JSONRPCResponse:
    return handle_rpc_request(request, params, jrpc_id, get_service_status_with_retries)


def status(request: Request, params: dict, jrpc_id: str) -> JSONRPCResponse:
    if params:
        logging.debug(f"dropping status params since SW1 doesn't use them: {params}")

    service_wizard_status = (
        [
            {
                "git_commit_hash": request.app.state.settings.vcs_ref,
                "state": "OK",
                "version": request.app.state.settings.vcs_ref,
                "message": "",
                "git_url": "https://github.com/kbase/service_wizard2",
            }
        ],
    )
    return JSONRPCResponse(id=jrpc_id, result=service_wizard_status)


async def version(request: Request, params: dict, jrpc_id: str) -> JSONRPCResponse:
    if params:
        logging.debug(f"dropping version params since SW1 doesn't use them: {params}")

    service_wizard_status = [str(request.app.state.settings.vcs_ref)]
    return JSONRPCResponse(id=jrpc_id, result=service_wizard_status)
