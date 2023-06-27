from fastapi import APIRouter, Request, Depends

from src.dependencies import status

# from src.dependencies.deps import get_token_header

router = APIRouter(
    tags=["unauthenticated"],
    responses={404: {"description": "Not found"}},
)

@router.get("/list_service_status")
async def list_service_status(request: Request):
    return status.list_service_status(request)


@router.get("/status")
async def status(r: Request):
    return "status"


# @router.get(
#     "/selections/{selection_id}",
#     # response_model=models.SelectionVerbose,
#     # summary="Get a selection",
#     # description="Get the status and contents of a selection."
# )
# def hello(
#         r: Request,
#         selection_id: str = "123",
#         verbose: bool = False,
# ):  # -> models.SelectionVerbose:
#     # return await processing_selections.get_selection(
#     #     app_state.get_app_state(r), selection_id, verbose=verbose
#     # )
#     return 123
