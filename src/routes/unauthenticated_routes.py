from fastapi import APIRouter, Request

from src.configs.settings import Settings
from src.dependencies.status import list_service_status_helper

router = APIRouter(
    tags=["unauthenticated"],
    responses={404: {"description": "Not found"}},
)


@router.get("/list_service_status")
def list_service_status(request: Request):
    return list_service_status_helper(request)


@router.get("/")
@router.get("/status")
async def status(request: Request):
    settings = request.app.state.settings  # type: Settings
    return [
        {
            "state": "OK",
            "message": "What's up, doc?",
            "git_url": settings.git_url,
            "git_commit_hash": settings.vcs_ref,
        }
    ]


@router.get("/version")
async def version(request: Request):
    return [request.app.state.settings.version]

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
