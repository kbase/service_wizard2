import os
from functools import lru_cache
from typing import Any

from pydantic import BaseSettings


class EnvironmentVariableError(Exception):
    pass


class Settings(BaseSettings):
    namespace: str
    auth_service_url: str
    kbase_endpoint: str
    catalog_url: str
    catal_admin_token: str
    kubeconfig: str
    admin_roles: list[str]

    def __init__(self, **values: Any):
        required_variables = [
            "NAMESPACE",
            "AUTH_SERVICE_URL",
            "KBASE_ENDPOINT",
            "CATALOG_URL",
            "CATALOG_ADMIN_TOKEN",
            "KUBECONFIG",
            "KBASE_ADMIN_ROLE",
            "CATALOG_ADMIN_ROLE",
            "SERVICE_WIZARD_ROLE"
        ]

        for var in required_variables:
            value = os.environ.get(var)
            if not value:
                raise EnvironmentVariableError(f"{var} is not set in the .env file")
            setattr(self, var.lower(), value)

        self.admin_roles = [
            os.environ.get("KBASE_ADMIN_ROLE"),
            os.environ.get("CATALOG_ADMIN_ROLE"),
            os.environ.get("SERVICE_WIZARD_ROLE")
        ]
        if not all(self.admin_roles):
            raise EnvironmentVariableError(
                "KBASE_ADMIN_ROLE, CATALOG_ADMIN_ROLE, or SERVICE_WIZARD_ROLE is not set in the .env file")

        super().__init__(**values)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
