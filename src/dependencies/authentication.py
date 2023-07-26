import requests
from cacheout import LRUCache
from fastapi import Header, Cookie, Depends
from starlette.requests import Request
from fastapi import HTTPException
from src.configs.settings import get_settings
from src.models.models import UserAuthRoles

# Constants
ALPHANUMERIC_PATTERN = r"^[a-zA-Z0-9]+$"

# Cache
global_token_cache = LRUCache(maxsize=100, ttl=300)


# Utility Functions
def check_or_cache_token(token, token_cache):
    """
    If the token is in the cache, we are good.
    If not, cache it.
    Will either return a UserAuthRoles object or throw an exception because the token is invalid, expired,
    or the auth service is down or the auth URL is incorrect.
    :param token:
    :param token_cache:
    :return:
    """
    if token not in token_cache:
        token_cache.set(token, validate_token(token))


def validate_and_get_username_roles(token):
    """
    This calls out the auth service to validate the token and get the username and auth roles
    :param token:
    :return:
    """
    auth_url = get_settings().auth_service_url
    try:
        response = requests.get(url=auth_url, headers={"Authorization": token})
    except Exception:
        raise HTTPException(status_code=500, detail="Auth service is down or bad request")

    if response.status_code == 200:
        return response.json()["user"], response.json()["customroles"]
    elif response.status_code == 404:
        raise HTTPException(status_code=404, detail="Auth URL not configured correctly")
    else:
        raise HTTPException(status_code=response.status_code, detail=response.json()["error"])


async def get_token_cache(request: Request) -> LRUCache:
    return request.app.state.global_token_cache


def validate_token(token):
    """
    Will either return a UserAuthRoles object or throw an exception because the token is invalid, expired,
    or the auth service is down or the auth URL is incorrect
    :param token:
    :return:
    """
    # TODO Try catch validate errors, auth service URL is bad, etc
    username, roles = validate_and_get_username_roles(token)
    return UserAuthRoles(username=username, roles=roles)


# FastAPI Endpoint Dependency
async def authenticated_user(
    authorization: str = Header(
        None,
        regex=ALPHANUMERIC_PATTERN,
        alias="Authorization",
        description="KBase auth token",
    ),
    kbase_session: str = Cookie(None, regex=ALPHANUMERIC_PATTERN),
    auth_token_cache: LRUCache = Depends(get_token_cache),
):
    if not authorization and not kbase_session:
        raise HTTPException(
            status_code=400,
            detail="Please provide the 'Authorization' header or 'kbase_session' cookie",
        )

    # Check to see if the token is valid and throw an exception if it isn't,
    # but also throw a different exception if the auth service is down
    try:
        check_or_cache_token(
            token=authorization if authorization else kbase_session,
            token_cache=auth_token_cache,
        )
    except HTTPException as e:
        if e.status_code == 401:
            raise e
        elif e.status_code == 500:
            raise HTTPException(status_code=500, detail="Auth service is down")
        elif e.status_code == 404:
            raise e
        else:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
