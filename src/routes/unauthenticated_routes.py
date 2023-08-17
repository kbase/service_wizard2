from fastapi import APIRouter, Request

from src.dependencies.status import get_version, get_status
from src.configs.settings import Settings  # noqa: F401

router = APIRouter(
    tags=["unauthenticated"],
    responses={404: {"description": "Not found"}},
)


@router.get("/status")
@router.get("/")
def status(request: Request):
    return get_status(request, module_name="", version="")


@router.get("/version")
def version(request: Request):
    return get_version(request, module_name="", version="")


@router.get("/sentry-debug")
async def trigger_error():
    # This endpoint is used to test the Sentry integration.
    division_by_zero = 1 / 0  # noqa: F841
