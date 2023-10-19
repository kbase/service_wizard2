import pytest
from fastapi import HTTPException

from dependencies.middleware import is_authorized


@pytest.mark.parametrize(
    "authorization, kbase_session, auth_client_response, expected",
    [
        (None, None, None, HTTPException(401, detail="Please provide the 'Authorization' header or 'kbase_session' cookie for None payload: None ")),
        ("validToken", None, True, True),  # Valid token, no kbase_session, auth_client returns True
        (None, "validSession", True, True),  # No token, valid kbase_session, auth_client returns True
        ("validToken", None, HTTPException(401), HTTPException(401)),  # auth_client raises 401
        ("validToken", None, HTTPException(500), HTTPException(500, detail="Auth service is down")),  # auth_client raises 500
        ("validToken", None, HTTPException(404), HTTPException(404)),  # auth_client raises 404
        ("validToken", None, HTTPException(403), HTTPException(400, detail="Invalid or expired token")),  # auth_client raises any other status code
    ],
)
def test_is_authorized(authorization, kbase_session, auth_client_response, expected, mock_request):
    if isinstance(auth_client_response, HTTPException):
        mock_request.app.state.auth_client.is_authorized.side_effect = auth_client_response
    else:
        mock_request.app.state.auth_client.is_authorized.return_value = auth_client_response

    if isinstance(expected, HTTPException):
        with pytest.raises(HTTPException) as exc_info:
            is_authorized(mock_request, authorization, kbase_session)
        assert exc_info.value.status_code == expected.status_code
        assert exc_info.value.detail == expected.detail
    else:
        assert is_authorized(mock_request, authorization, kbase_session) == expected
