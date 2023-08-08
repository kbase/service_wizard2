import logging
import traceback
from typing import Callable
from fastapi import Request
from src.dependencies import logs
from src.clients.baseclient import ServerError
from src.dependencies.lifecycle import start_deployment, stop_deployment

from src.rpc.models import ErrorResponse, JSONRPCResponse

logging.basicConfig(level=logging.INFO)


def handle_request(
    request: Request,
    params: list[dict],
    jrpc_id: int,
    action: Callable,
) -> JSONRPCResponse:
    # This is for backwards compatibility with SW1 logging functions
    service = params[0].get("service")
    if service:
        module_name = service["module_name"]
        module_version = service["version"]
    else:
        # All other functions expect input like this
        module_name = params[0].get("module_name")
        module_version = params[0].get("version")

    try:
        result = action(request, module_name, module_version)
        return JSONRPCResponse(id=jrpc_id, result=[result])
    except ServerError as e:
        traceback_str = traceback.format_exc()
        return JSONRPCResponse(id=jrpc_id, error=ErrorResponse(message=f"{e.message}", code=-32000, name="Server error", error=f"{traceback_str}"))
    except Exception as e:
        traceback_str = traceback.format_exc()
        return JSONRPCResponse(
            id=jrpc_id,
            error=ErrorResponse(
                message=f"{e}",
                code=-32603,
                name="Internal error - An internal error occurred on the server while processing the request",
                error=f"{traceback_str}",
            ),
        )


def start(request: Request, params: list[dict], jrpc_id: int) -> JSONRPCResponse:
    return handle_request(request, params, jrpc_id, start_deployment)


def stop(request: Request, params: list[dict], jrpc_id: int) -> JSONRPCResponse:
    return handle_request(request, params, jrpc_id, stop_deployment)


def get_service_log(request: Request, params: list[dict], jrpc_id: int) -> JSONRPCResponse:
    return handle_request(request, params, jrpc_id, logs.get_service_log)


def get_service_log_web_socket(request: Request, params: list[dict], jrpc_id: int) -> JSONRPCResponse:
    return handle_request(request, params, jrpc_id, logs.get_service_log_web_socket)
