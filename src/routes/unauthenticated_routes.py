from fastapi import APIRouter, Request

from src.configs.settings import Settings  # noqa: F401

router = APIRouter(
    tags=["unauthenticated"],
    responses={404: {"description": "Not found"}},
)


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
