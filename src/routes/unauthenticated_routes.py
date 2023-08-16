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
    return get_status(request)


@router.get("/version")
def version(request: Request):
    return get_version(request)
