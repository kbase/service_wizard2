from fastapi import Request

from dependencies import logs
from dependencies.lifecycle import stop_deployment
from rpc.common import handle_rpc_request
from rpc.models import JSONRPCResponse


def stop(request: Request, params: list[dict], jrpc_id: str) -> JSONRPCResponse:
    return handle_rpc_request(request, params, jrpc_id, stop_deployment)


def get_service_log(request: Request, params: list[dict], jrpc_id: str) -> JSONRPCResponse:
    return handle_rpc_request(request, params, jrpc_id, logs.get_service_log)


def get_service_log_web_socket(request: Request, params: list[dict], jrpc_id: str) -> JSONRPCResponse:
    return handle_rpc_request(request, params, jrpc_id, logs.get_service_log_web_socket)
