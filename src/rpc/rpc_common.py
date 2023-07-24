from typing import Optional, List

from fastapi import HTTPException
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    message: str
    code: int
    name: str
    error: str = None


class JSONRPCResponse(BaseModel):
    version: str = "1.0"
    error: Optional[ErrorResponse]
    result: Optional[List[dict]] = Field(default_factory=lambda: None)
    id: int

    def dict(self, *args, **kwargs):
        # Remove 'result' from the dictionary if it's None
        response_dict = super().dict(*args, **kwargs)
        if self.result is None:
            response_dict.pop('result', None)
        if self.error is None:
            response_dict.pop('error', None)
            # TODO: Check this functionality
            response_dict.pop('version', None)

        return response_dict


def request_path_not_found(method, jrpc_id) -> JSONRPCResponse:
    return JSONRPCResponse(
        id=jrpc_id,
        error=ErrorResponse(
            message=f"Method '{method}' not found",
            code=-32601,
            name="Method not found",
            error=None
        )
    )


async def validate_rpc_request(request):
    json_data =  await request.json()

    if not isinstance(json_data, dict):
        raise ValueError(f"Invalid JSON format, got {type(json_data)}")

    method = json_data.get("method")
    params = json_data.get("params")
    # We don't actually care about the jrpc_id
    jrpc_id = json_data.get("id", 0)

    if not isinstance(method, str) or not isinstance(params, list):
        raise ValueError(
            f"Invalid JSON-RPC request format {type(method)} {type(params)}",
        )
    return method, params, jrpc_id


def validate_rpc_response(response: JSONRPCResponse):
    try:
        assert isinstance(response, JSONRPCResponse)
        if (response.error is None and response.result is None) or (
                response.error is not None and response.result is not None):
            raise AssertionError("Both 'error' and 'result' cannot be present or absent together.")
    except AssertionError as e:
        return HTTPException(status_code=500, detail=f"Programming Error: Invalid JSON-RPC response format {e}")
    return response
