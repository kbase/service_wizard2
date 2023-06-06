from typing import Annotated

from fastapi import Header, HTTPException, Cookie


def check_token(token: Annotated[str, Header(default=None)]):
    if token != "jessica":
        raise HTTPException(status_code=400, detail="No Jessica token provided")
    return token


def check_cookie(kbase_session_cookie: Annotated[str, Cookie(default=None)]):
    if kbase_session_cookie != "jessica":
        raise HTTPException(status_code=400, detail="No Jessica token provided")
    return kbase_session_cookie


def check_valid_token(token):
    if token != "jessica":
        raise HTTPException(status_code=400, detail="No Jessica token provided")
    return token


async def get_token_header(
        authorized: Annotated[str, Header()] = None,
        kbase_session_cookie: Annotated[str, Cookie()] = None,
):
    if not authorized and not kbase_session_cookie:
        raise HTTPException(status_code=400, detail="Please provide the 'Authorized' header or 'kbase_session_cookie'")

    # Check to see if the token is valid and trhow an exception if it isnt, but also throw a different exception if the auth service is down
    try:
        if authorized:
            username = check_valid_token(authorized)
        else:
            username = check_valid_token(kbase_session_cookie)
    except HTTPException as e:
        if e.status_code == 500:
            raise HTTPException(status_code=400, detail="Auth service is down")
        else:
            # Invalid token with correct status code
            raise HTTPException(status_code=400, detail="Invalid token")

    # Rest of your code
    return {"message": "Valid credentials for username " + username}

# async def get_token_header(Authorization: Annotated[str, Header()]):
#     if Authorization != "fake-super-secret-token":
#         raise HTTPException(status_code=400, detail="Authorization-Token header invalid")
#
#
# async def get_query_token(token: str):
#     if token != "jessica":
#         raise HTTPException(status_code=400, detail="No Jessica token provided")
