import os
from functools import lru_cache
from typing import Any
from dataclasses import dataclass


class EnvironmentVariableError(Exception):
    pass


@dataclass
class Settings:
    namespace: str
    auth_service_url: str
    kbase_endpoint: str
    catalog_url: str
    catalog_admin_token: str
    kubeconfig: str
    admin_roles: list[str]


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    required_variables = [
        "NAMESPACE",
        "AUTH_SERVICE_URL",
        "KBASE_ENDPOINT",
        "CATALOG_URL",
        "CATALOG_ADMIN_TOKEN",
        "KUBECONFIG",
    ]

    for var in required_variables:
        value = os.environ.get(var)
        if not value:
            raise EnvironmentVariableError(f"{var} is not set in the .env file")

    admin_roles = [
        role for role in [
            os.environ.get("KBASE_ADMIN_ROLE"),
            os.environ.get("CATALOG_ADMIN_ROLE"),
            os.environ.get("SERVICE_WIZARD_ROLE")
        ] if role
    ]
    if len(admin_roles) == 0:
        raise EnvironmentVariableError(
            "At least one admin role (KBASE_ADMIN_ROLE, CATALOG_ADMIN_ROLE, or SERVICE_WIZARD_ROLE) must be set in the .env file")

    return Settings(
        namespace=os.environ.get("NAMESPACE"),
        auth_service_url=os.environ.get("AUTH_SERVICE_URL"),
        kbase_endpoint=os.environ.get("KBASE_ENDPOINT"),
        catalog_url=os.environ.get("CATALOG_URL"),
        catalog_admin_token=os.environ.get("CATALOG_ADMIN_TOKEN"),
        kubeconfig=os.environ.get("KUBECONFIG"),
        admin_roles=admin_roles
    )
