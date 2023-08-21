from fastapi.requests import Request

from src.dependencies.lifecycle import start_deployment
from src.dependencies.status import get_all_dynamic_service_statuses, get_service_status_without_retries, get_version, get_status
from src.rpc.common import handle_rpc_request
from src.rpc.models import JSONRPCResponse


def list_service_status(request: Request, params: list[dict], jrpc_id: str) -> JSONRPCResponse:
    return handle_rpc_request(request, params, jrpc_id, get_all_dynamic_service_statuses)


def get_service_status_without_restart(request: Request, params: list[dict], jrpc_id: str) -> JSONRPCResponse:
    return handle_rpc_request(request, params, jrpc_id, get_service_status_without_retries)


def start(request: Request, params: list[dict], jrpc_id: str) -> JSONRPCResponse:
    return handle_rpc_request(request, params, jrpc_id, start_deployment)


def status(request: Request, params: list[dict], jrpc_id: str) -> JSONRPCResponse:
    if not params:
        params = [{}]
    return handle_rpc_request(request, params, jrpc_id, get_status)


def version(request: Request, params: list[dict], jrpc_id: str) -> JSONRPCResponse:
    if not params:
        params = [{}]
    return handle_rpc_request(request, params, jrpc_id, get_version)
