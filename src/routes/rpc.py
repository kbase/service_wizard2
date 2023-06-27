from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# from src.routes.unauthenticated_routes import list_service_status, status
from src.dependencies import status

router = APIRouter(
    tags=["rpc"],
    responses={404: {"description": "Not found"}},
)


class JSONRequest(BaseModel):
    version: str = "1.1"
    method: str
    params: dict
    id: int


@router.post("/rpc")
@router.post("/rpc/")
async def json_rpc(request: Request):
    try:
        json_data = await request.json()

        if not isinstance(json_data, dict):
            raise ValueError("Invalid JSON format")

        method = json_data.get("method")
        params = json_data.get("params")
        jrpc_id = json_data.get("id")

        if not isinstance(method, str) or not isinstance(params, list):
            raise ValueError(f"Invalid JSON-RPC request format {type(method)} {type(params)}", )

        """
        * Could do a lookup table here
        * Not able to call other routes here due to 
        {"error": "'function' object has no attribute 'list_service_status'"}
        """
        if method == "ServiceWizard.list_service_status":
            return {"result": [status.list_service_status(request)], "id": jrpc_id}
        elif method == "ServiceWizard.status":
            return {"result": {}, "id": jrpc_id}

        else:

            return JSONResponse(
                status_code=400,
                content={"error": "Method not found", "id": jrpc_id},
            )

    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )
