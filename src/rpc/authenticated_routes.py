import traceback

from fastapi import Request

from src.clients.baseclient import ServerError
from src.dependencies.start import start_deployment
from src.rpc.models import ErrorResponse, JSONRPCResponse


async def start(request: Request, params: list[dict], jrpc_id: int) -> JSONRPCResponse:
    """
    Start a service
    """
    module_name = params[0].get("module_name")
    module_version = params[0].get("version")
    # TODO: Throw -32602: Invalid params - Invalid method parameters. if module_name or version is not passed in or not correct

    try:
        ssh = start_deployment(request, module_name, module_version)
        return JSONRPCResponse(id=jrpc_id, result=[ssh])
    except ServerError as e:
        traceback_str = traceback.format_exc()
        return JSONRPCResponse(id=jrpc_id, error=ErrorResponse(message=f"{e.message}", code=-32000, name="Server error", error=f"{traceback_str}"))
    except Exception as e:
        # TODO Catch all cases here correctly
        # TODO make this into a reusable function?
        traceback_str = traceback.format_exc()
        return JSONRPCResponse(
            id=jrpc_id,
            error=ErrorResponse(
                message=f"{e}",
                code=-32603,
                name="Internal error - An internal error occurred on the server while processing the request.",
                error=f"{traceback_str}",
            ),
        )
