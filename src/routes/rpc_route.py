from fastapi import Request, APIRouter, HTTPException, Depends
from fastapi.responses import Response, JSONResponse

from rpc.handlers.json_rpc_handler import json_rpc_helper
from rpc.models import JSONRPCResponse

router = APIRouter(
    tags=["rpc"],
    responses={404: {"description": "Not found"}},
)


async def get_body(request: Request):
    return await request.body()


@router.post("/rpc", response_model=None)
@router.post("/rpc/", response_model=None)
@router.post("/", response_model=None)
def json_rpc(request: Request, body: bytes = Depends(get_body)) -> Response | HTTPException | JSONRPCResponse | JSONResponse:
    response = json_rpc_helper(request, body)
    return response
