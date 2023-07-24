from typing import List

from models.models import DynamicServiceStatus

from src.rpc.rpc_common import JSONRPCResponse, ErrorResponse
from src.models.models import DynamicServiceStatus
from src.dependencies.start import start_deployment
from fastapi import APIRouter, Request, Query
from src.clients.baseclient import ServerError


import traceback

def start(request: Request, params: list[dict], jrpc_id: int) -> JSONRPCResponse:
    """
    Start a service
    """
    module_name = params[0].get("module_name")
    module_version = params[0].get("version")
    try:
        ssh = start_deployment(request, module_name, module_version)
        return JSONRPCResponse(
            id=jrpc_id,
            result=[ssh]
        )
    except ServerError as e:
        traceback_str = traceback.format_exc()
        return JSONRPCResponse(
            id=jrpc_id,
            error=ErrorResponse(
                message=f"{e.message}",
                code=-32000,
                name="Server error",
                error=f"{traceback_str}"
            )
        )
    except Exception as e:
        #TODO Catch all cases here correctly
        traceback_str = traceback.format_exc()
        return JSONRPCResponse(
            id=jrpc_id,
            error=ErrorResponse(
                message=f"u{e}",
                code=-32601,
                name="API error",
                error=f"{traceback_str}"
            )
        )


