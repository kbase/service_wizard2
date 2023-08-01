from fastapi import APIRouter, Request, Query

from src.configs.settings import Settings
from src.dependencies.status import get_dynamic_service_status_helper, get_all_dynamic_service_statuses, get_service_status_with_retries

router = APIRouter(
    tags=["unauthenticated"],
    responses={404: {"description": "Not found"}},
)


@router.get("/get_service_status")
def get_service_status(request: Request, module_name: str = Query(...), version: str = Query(...)):
    """

    :param request:
    :param module_name: The name of the service module, case-insensitive
    :param version: The version of the service module, which can be either: git commit, semantic version, or release tag
    :return:
    """
    return get_service_status_with_retries(request, module_name, version)


@router.get("/list_service_status")
def list_service_status(request: Request):
    """
    Get all service statuses, this function doesn't take any parameters
    :param request: The request object
    :return: A list of all service statuses
    """
    statuses = get_all_dynamic_service_statuses(request)
    return [statuses]


@router.get("/status")
@router.get("/")
async def status(request: Request):
    settings = request.app.state.settings  # type: Settings
    return [
        {
            "state": "OK",
            "message": "Post requests should be sent here or to /rpc",
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
