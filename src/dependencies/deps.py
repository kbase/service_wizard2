from typing import Annotated

from cacheout import LRUCache
from fastapi import Header, HTTPException, Cookie

from models.models import UserAuthRoles

token_cache = LRUCache(maxsize=100, ttl=300)
catalog_cache = LRUCache(maxsize=100, ttl=300)
ALPHANUMERIC_PATTERN = r"^[a-zA-Z0-9]+$"

def get_toke_cache():
    return token_cache


def get_catalog_cache():
    return catalog_cache


def check_token(token):
    if token in token_cache:
        return token_cache.get(token)
    else:
        token_cache.set(token, validate_token(token))


def get_user_info(token):
    pass


def validate_token(token):
    """
    Will either return a UserAuthRoles object or throw an exception because the
    token is invalid, expired, or the auth service is down or the auth url is incorrect
    :param token:
    :return:
    """
    #TODO Try catch validate errors, auth service URL is bad, etc
    username, roles = "boris", ["admin"]
    return UserAuthRoles(username=username, roles=roles)


async def authenticated_user(
        authorized: Annotated[str, Header(regex=ALPHANUMERIC_PATTERN)] = None,
        kbase_session_cookie: Annotated[str, Cookie(regex=ALPHANUMERIC_PATTERN)] = None,
):
    if not authorized and not kbase_session_cookie:
        raise HTTPException(status_code=400, detail="Please provide the 'Authorized' header or 'kbase_session_cookie'")

    # Check to see if the token is valid and trhow an exception if it isnt, but also throw a different exception if the auth service is down
    try:
        if authorized:
            validate_token(token=authorized)
        else:
            validate_token(token=kbase_session_cookie)
    except HTTPException as e:
        if e.status_code == 500:
            raise HTTPException(status_code=400, detail="Auth service is down")
        else:
            # Invalid token with correct status code
            raise HTTPException(status_code=400, detail="Invalid token")

