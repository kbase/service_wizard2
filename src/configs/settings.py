import os
from dataclasses import dataclass
from functools import lru_cache


class EnvironmentVariableError(Exception):
    """
    Raised when an environment variable is not set.
    """

    pass


@dataclass
class Settings:
    """
    A class to hold the settings for the service wizard.
    Read more about these in the README.md file.
    """

    admin_roles: list[str]
    auth_service_url: str
    auth_legacy_url: str
    catalog_admin_token: str
    catalog_url: str
    external_ds_url: str
    external_sw_url: str
    git_url: str
    kbase_root_endpoint: str
    kbase_services_endpoint: str
    kubeconfig: str
    namespace: str
    root_path: str
    use_incluster_config: bool
    vcs_ref: str


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    """
    Get the settings for the service wizard. These are read from environment variables and then cached.
    All variables should be strings. To read more about the variables, see the README.md file.
    :return: A Settings object
    """
    required_variables = [
        "NAMESPACE",
        "AUTH_SERVICE_URL",
        "AUTH_LEGACY_URL",
        "CATALOG_URL",
        "CATALOG_ADMIN_TOKEN",
        "EXTERNAL_SW_URL",
        "EXTERNAL_DS_URL",
        "ROOT_PATH",
        "KBASE_ROOT_ENDPOINT",
        "KBASE_SERVICES_ENDPOINT",
    ]
    for var in required_variables:
        value = os.environ.get(var)
        if not value:
            raise EnvironmentVariableError(f"{var} is not set in the .env file")

    admin_roles = [
        role
        for role in [
            os.environ.get("KBASE_ADMIN_ROLE"),
            os.environ.get("CATALOG_ADMIN_ROLE"),
            os.environ.get("SERVICE_WIZARD_ADMIN_ROLE"),
        ]
        if role
    ]

    if len(admin_roles) == 0:
        raise EnvironmentVariableError("At least one admin role (KBASE_ADMIN_ROLE, CATALOG_ADMIN_ROLE, or SERVICE_WIZARD_ADMIN_ROLE) must be set in the .env file")

    if "KUBECONFIG" not in os.environ and "USE_INCLUSTER_CONFIG" not in os.environ:
        raise EnvironmentVariableError("At least one of the environment variables 'KUBECONFIG' or 'USE_INCLUSTER_CONFIG' must be set")

    return Settings(
        admin_roles=admin_roles,
        auth_service_url=os.environ.get("AUTH_SERVICE_URL"),
        auth_legacy_url=os.environ.get("AUTH_LEGACY_URL"),
        catalog_admin_token=os.environ.get("CATALOG_ADMIN_TOKEN"),
        catalog_url=os.environ.get("CATALOG_URL"),
        external_ds_url=os.environ.get("EXTERNAL_DS_URL"),
        external_sw_url=os.environ.get("EXTERNAL_SW_URL"),
        git_url="https://github.com/kbase/service_wizard2",
        kbase_root_endpoint=os.environ.get("KBASE_ROOT_ENDPOINT"),
        kbase_services_endpoint=os.environ.get("KBASE_SERVICES_ENDPOINT"),
        kubeconfig=os.environ.get("KUBECONFIG"),
        namespace=os.environ.get("NAMESPACE"),
        root_path=os.environ.get("ROOT_PATH"),
        use_incluster_config=os.environ.get("USE_INCLUSTER_CONFIG", "").lower() == "true",
        vcs_ref=os.environ.get("GIT_COMMIT_HASH"),
    )
