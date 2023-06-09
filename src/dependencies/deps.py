import logging
from typing import Annotated

from cacheout import LRUCache
from fastapi import Header, HTTPException, Cookie


from src.models.models import UserAuthRoles

token_cache = LRUCache(maxsize=100, ttl=300)
catalog_cache = LRUCache(maxsize=100, ttl=300)
ALPHANUMERIC_PATTERN = r"^[a-zA-Z0-9]+$"

def get_toke_cache():
    return token_cache


def get_catalog_cache():
    return catalog_cache


def check_or_cache_token(token):
    """
    If the token is in the cache, we are good.

    If not, cache it.

    Will either return a UserAuthRoles object or throw an exception because the token is invalid, expired, or the auth
    service is down or the auth url is incorrect.
    :param token:
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
    return "test", ["test"]

def validate_token(token):
    """
    Will either return a UserAuthRoles object or throw an exception because the
    token is invalid, expired, or the auth service is down or the auth url is incorrect
    :param token:
    :return:
    """
    #TODO Try catch validate errors, auth service URL is bad, etc
    username, roles = validate_and_get_username_roles(token)
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
            check_or_cache_token(token=authorized)
        else:
            check_or_cache_token(token=kbase_session_cookie)
    except HTTPException as e:
        if e.status_code == 500:
            raise HTTPException(status_code=400, detail="Auth service is down")
        else:
            # Invalid token with correct status code
            raise HTTPException(status_code=400, detail="Invalid token")

