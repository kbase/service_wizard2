from fastapi import FastAPI, Request, APIRouter, Body, params
from fastapi.responses import JSONResponse
# from fastapi.f
from pydantic import Field, BaseModel

from src.routes.unauthenticated_routes import list_service_status


empty_request_response = {
    "error": {"code": -32700, "name": "Parse error", "message": "Expecting value: line 1 column 1 (char 0)",
              "error": None}, "version": "1.1"}

not_found_404 = {
            "jsonrpc": "1.1",
            "id": None,
            "error": {"code": -32601, "message": "Method not found"},
        }

router = APIRouter(
    tags=["json rpc"],
    responses={500: empty_request_response, 404 : not_found_404},
)

def result_wrapper(result, jrpc_id=None, error=None):
    # TODO raise exception if both error and result are None
    return {
        "result": result,
        "error": error,
        "id": jrpc_id,
        "version": "1.1",
    }


@router.get("/rpc")
async def json_rpc_get(request: Request):
    return JSONResponse(content=empty_request_response, status_code=500)


# class JsonRPCRequest(BaseModel):
#     id: int = Field(..., example=1, description="JSON-RPC request ID")
#     method: str = Field(..., example="ServiceWizard.get_service_log", description="JSON-RPC method")
#     params: str = Field(..., example={ #sadly this cannot be a dict
#         "service": "example_service",
#         "instance_id": 1234
#     }, description="JSON-RPC parameters")
#
# class JsonRPCParams(BaseModel):
#     module: str = Field(..., example="onerepotest")
#
# class JsonRPCRequest(BaseModel):
#     id: int = Field(..., example=22, description="JSON-RPC request ID")
#     method: str = Field(..., example="ServiceWizard.list_service_status", description="JSON-RPC method")
#     params: JsonRPCParams

@router.post("/rpc")
async def json_rpc(request: Request, ):
    """
    This ignores JSON-RPC version
    :param request:
    :param body: JSON-RPC request body
    :return:
    """
    return 123
    jrpc_id = body.get("id")
    method = body.get("method")
    params = body.get("params")



    if method == "ServiceWizard.get_service_log":
        service = params.get("service")
        instance_id = params.get("instance_id")
        # Implement your logic to handle the "ServiceWizard.get_service_log" method
        # using the provided `service` and `instance_id` parameters
        # Return the appropriate response

    elif method == "ServiceWizard.get_service_log_web_socket":
        instance_id = params.get("instance_id")
        socket_url = params.get("socket_url")
        # Implement your logic to handle the "ServiceWizard.get_service_log_web_socket" method
        # using the provided `instance_id` and `socket_url` parameters
        # Return the appropriate response

    elif method == "ServiceWizard.list_service_status":
        try:
            return result_wrapper(result=list_service_status(request), jrpc_id=jrpc_id)
        except Exception as e:
            return result_wrapper(None, jrpc_id=jrpc_id, error={"code": -32000, "message": str(e)})

    else:
        return {
            "jsonrpc": "1.1",
            "id": jrpc_id,
            "error": {"code": -32601, "message": "Method not found"},
        }




# Note Could Do this instead
# from fastapi_jsonrpc import methods
#
# @methods.add
# def list_service_status(module: str):
#     # Your implementation logic here
#     # This function will handle the "ServiceWizard.list_service_status" JSON-RPC method
#     # It accepts a "module" parameter and returns the appropriate response
#
# @methods.add
# def status():
#     # Your implementation logic here
#     # This function will handle the "status" JSON-RPC method
#     # It does not accept any parameters and returns the appropriate response
#
# @app.post("/json-rpc")
# async def json_rpc(request: Request):
#     json_rpc_methods = methods.Methods()
#     return await json_rpc_methods.dispatch(request)
