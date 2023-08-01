from fastapi import HTTPException, Request
from fastapi import Header, Cookie

from clients.CachedAuthClient import CachedAuthClient

# Constants
ALPHANUMERIC_PATTERN = r"^[a-zA-Z0-9]+$"


async def is_authorized(
    request: Request,
    authorization: str = Header(
        None,
        regex=ALPHANUMERIC_PATTERN,
        alias="Authorization",
        description="KBase auth token",
    ),
    kbase_session: str = Cookie(None, regex=ALPHANUMERIC_PATTERN),
):
    if not authorization and not kbase_session:
        raise HTTPException(
            status_code=400,
            detail="Please provide the 'Authorization' header or 'kbase_session' cookie",
        )

    # Check to see if the token is valid and throw an exception if it isn't,
    # but also throw a different exception if the auth service is down
    try:
        ac = request.app.state.auth_client  # type: CachedAuthClient
        print("About to check", authorization, kbase_session)
        return ac.is_authorized(token=authorization if authorization else kbase_session)
    except HTTPException as e:
        if e.status_code == 401:
            raise e
        elif e.status_code == 500:
            raise HTTPException(status_code=500, detail="Auth service is down")
        elif e.status_code == 404:
            raise e
        else:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
