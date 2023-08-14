import logging

from fastapi import Request

from src.dependencies import logs
from src.dependencies.lifecycle import start_deployment, stop_deployment
from src.rpc.common import handle_rpc_request
from src.rpc.models import JSONRPCResponse

logging.basicConfig(level=logging.INFO)


def start(request: Request, params: list[dict], jrpc_id: str) -> JSONRPCResponse:
    return handle_rpc_request(request, params, jrpc_id, start_deployment)


def stop(request: Request, params: list[dict], jrpc_id: str) -> JSONRPCResponse:
    return handle_rpc_request(request, params, jrpc_id, stop_deployment)


def get_service_log(request: Request, params: list[dict], jrpc_id: str) -> JSONRPCResponse:
    return handle_rpc_request(request, params, jrpc_id, logs.get_service_log)


def get_service_log_web_socket(request: Request, params: list[dict], jrpc_id: str) -> JSONRPCResponse:
    return handle_rpc_request(request, params, jrpc_id, logs.get_service_log_web_socket)
