from functools import cached_property

import requests
from cacheout import LRUCache
from fastapi import HTTPException

from configs.settings import Settings, get_settings



class UserAuthRoles:
    def __init__(self, username: str, roles: list[str], admin_roles: list[str]):
        self.username = username
        self.roles = roles
        self.admin_roles = admin_roles

    @cached_property
    def is_admin(self) -> bool:
        return any(role in self.admin_roles for role in self.roles)


class CachedAuthClient:
    valid_tokens = LRUCache(ttl=10)

    def __init__(self, settings: Settings):
        """
        Initialize the CachedAuthClient
        :param settings: The settings to use, or use the default settings if not provided
        """
        self.settings = get_settings() if not settings else settings
        self.auth_url = self.settings.auth_service_url
        self.admin_roles = self.settings.admin_roles

    def is_authorized(self, token) -> bool:
        """
        A token is authorized if it is valid
        :param token:
        :return: True if the token is valid, False otherwise
        :raises: HTTPException if the token is invalid or the auth service is down
        """
        return bool(self.get_user_auth_roles(token) is not None)

    def is_admin(self, token) -> bool:
        """
        A token is authorized if is valid and the user has an admin role
        :return: True if the token is valid, False otherwise
        :raises: HTTPException if the token is invalid or the auth service is down
        """
        return self.get_user_auth_roles(token).is_admin

    def get_user_auth_roles(self, token) -> UserAuthRoles:
        """
        Get the user auth roles for the given token. If the token is not cached, it will be validated and cached.
        :param token:  The token to get the user auth roles for
        :return: The user auth roles for the given token
        :raises: HTTPException if the token is invalid, expired, or the auth service is down or the auth URL is incorrect
        """
        key = token
        user_auth_roles = self.valid_tokens.get(key=key, default=None)
        if not user_auth_roles:
            token_info = self._validate_token(token)
            self.valid_tokens.set(key=token, value=token_info)
        return user_auth_roles

    def _validate_token(self, token) -> UserAuthRoles:
        """
        Will either return a UserAuthRoles object or throw an exception because the token is invalid, expired,
        or the auth service is down or the auth URL is incorrect
        :param token: The token to validate
        :return: A UserAuthRoles object representing the user and their auth roles
        :raises: HTTPException if the token is invalid, expired, or the auth service is down or the auth URL is incorrect
        """
        # TODO Try catch validate errors, auth service URL is bad, etc
        username, roles = self.validate_and_get_username_roles(token)
        return CachedAuthClient.UserAuthRoles(self, username=username, user_roles=roles, admin_roles=self.admin_roles)

    def validate_and_get_username_roles(self, token):
        """
        This calls out the auth service to validate the token and get the username and auth roles
        :param token: The token to validate
        :return: A tuple of the username and auth roles
        :raises: HTTPException if the token is invalid, expired, or the auth service is down or the auth URL is incorrect
        """
        try:
            response = requests.get(url=self.auth_url, headers={"Authorization": token})
        except Exception:
            raise HTTPException(status_code=500, detail="Auth service is down or bad request")
        if response.status_code == 200:
            return response.json()["user"], response.json()["customroles"]
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Auth URL not configured correctly")
        else:
            raise HTTPException(status_code=response.status_code, detail=response.json()["error"])


