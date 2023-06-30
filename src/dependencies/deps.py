from typing import Annotated

from cacheout import LRUCache
from fastapi import Header, HTTPException, Cookie, Depends, Request

from src.dependencies.authentication import ALPHANUMERIC_PATTERN, check_or_cache_token


async def get_token_cache(request: Request) -> LRUCache:
    return request.app.state.token_cache


async def authenticated_user(
    authorization: str = Header(
        None,
        regex=ALPHANUMERIC_PATTERN,
        alias="Authorization",
        description="KBase auth token",
    ),
    kbase_session_cookie: str = Cookie(None, regex=ALPHANUMERIC_PATTERN),
    token_cache: LRUCache = Depends(get_token_cache),
):
    if not authorization and not kbase_session_cookie:
        raise HTTPException(
            status_code=400,
            detail="Please provide the 'Authorization' header or 'kbase_session_cookie'",
        )

    # Check to see if the token is valid and trhow an exception if it isnt, but also throw a different exception if the auth service is down
    try:
        check_or_cache_token(
            token=authorization if authorization else kbase_session_cookie,
            token_cache=token_cache,
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
