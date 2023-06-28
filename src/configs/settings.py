import os
from dataclasses import dataclass
from functools import lru_cache


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
    use_incluster_config: bool


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    required_variables = [
        "NAMESPACE",
        "AUTH_SERVICE_URL",
        "KBASE_ENDPOINT",
        "CATALOG_URL",
        "CATALOG_ADMIN_TOKEN",
    ]

    # Treat all variables as strings
    for var in required_variables:
        value = os.environ.get(var)
        if not value:
            raise EnvironmentVariableError(f"{var} is not set in the .env file")

    admin_roles = [
        role
        for role in [
            os.environ.get("KBASE_ADMIN_ROLE"),
            os.environ.get("CATALOG_ADMIN_ROLE"),
            os.environ.get("SERVICE_WIZARD_ROLE"),
        ]
        if role
    ]

    # At least one required admin role must be set
    if len(admin_roles) == 0:
        raise EnvironmentVariableError(
            "At least one admin role (KBASE_ADMIN_ROLE, CATALOG_ADMIN_ROLE, or SERVICE_WIZARD_ROLE) must be set in the .env file"
        )

    # USE_INCLUSTER_CONFIG is a boolean that takes precedence over KUBECONFIG
    if "KUBECONFIG" not in os.environ and "USE_INCLUSTER_CONFIG" not in os.environ:
        raise EnvironmentVariableError("At least one of the environment variables 'KUBECONFIG' or 'USE_INCLUSTER_CONFIG' must be set")

    return Settings(
        namespace=os.environ.get("NAMESPACE"),
        auth_service_url=os.environ.get("AUTH_SERVICE_URL"),
        kbase_endpoint=os.environ.get("KBASE_ENDPOINT"),
        catalog_url=os.environ.get("CATALOG_URL"),
        catalog_admin_token=os.environ.get("CATALOG_ADMIN_TOKEN"),
        kubeconfig=os.environ.get("KUBECONFIG"),
        admin_roles=admin_roles,
        use_incluster_config=os.environ.get("USE_INCLUSTER_CONFIG", "").lower() == "true",
    )
