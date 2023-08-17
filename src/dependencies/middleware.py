import logging

from fastapi import HTTPException, Request
from fastapi import Header, Cookie

from src.clients.CachedAuthClient import CachedAuthClient  # noqa: F401

# Constants
ALPHANUMERIC_PATTERN = r"^[a-zA-Z0-9]+$"


def is_authorized(
    request: Request,
    authorization: str = Header(
        None,
        regex=ALPHANUMERIC_PATTERN,
        alias="Authorization",
        description="KBase auth token",
    ),
    kbase_session: str = Cookie(None, regex=ALPHANUMERIC_PATTERN),
    method: str = None,
) -> bool:
    """
    Check if the user is authorized to access the endpoint in general.
    This does not check if the user is authorized to STOP or VIEW LOGS for specific services.
    :param request: The request to check
    :param authorization: The authorization header
    :param kbase_session: The kbase_session cookie
    :return: A boolean indicating if the user is authorized or not
    """
    if not authorization and not kbase_session:
        logging.warning(f"No authorization header or kbase_session cookie provided { ' Method: ' + method if method else ''}")
        raise HTTPException(
            status_code=400,
            detail="Please provide the 'Authorization' header or 'kbase_session' cookie",
        )
    try:
        ac = request.app.state.auth_client  # type: CachedAuthClient
        return ac.is_authorized(token=authorization if authorization else kbase_session)
    except HTTPException as e:
        if e.status_code == 401:
            raise e
        elif e.status_code == 500:
            raise HTTPException(status_code=500, detail="Auth service is down")
        elif e.status_code == 404:
            raise e
        else:
            logging.warning("Invalid or expired token")
            raise HTTPException(status_code=400, detail="Invalid or expired token")
