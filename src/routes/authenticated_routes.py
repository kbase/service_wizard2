from fastapi import APIRouter, Depends, Request, Header, Cookie

from dependencies.middleware import is_authorized, ALPHANUMERIC_PATTERN

router = APIRouter(
    tags=["authenticated"],
    dependencies=[Depends(is_authorized)],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
        409: {"description": "AlreadyExistsError"},
    },
)


@router.get("/whoami/")
def whoami(
    request: Request,
    authorization: str = Header(
        None,
        regex=ALPHANUMERIC_PATTERN,
        alias="Authorization",
        description="KBase auth token",
    ),
    kbase_session: str = Cookie(None, regex=ALPHANUMERIC_PATTERN),
):
    cac = request.app.state.auth_client

    return cac.validate_and_get_username_auth_roles(token=authorization if authorization else kbase_session)
