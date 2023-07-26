import logging

from fastapi.requests import Request

from src.dependencies.status import get_all_dynamic_service_statuses
from src.rpc.models import JSONRPCResponse


async def list_service_status(request: Request, params: dict, jrpc_id: str) -> JSONRPCResponse:
    if params:
        logging.debug(f"dropping list_service_status params since SW1 doesn't use them: {params}")
    #TODO Catch HTTP Exceptions and return them as JSONRPCResponse errors

    statuses = get_all_dynamic_service_statuses(request)
    return JSONRPCResponse(id=jrpc_id, result=statuses)


async def status(request: Request, params: dict, jrpc_id: str) -> dict:
    pass
