from enum import Enum
from functools import cached_property
from typing import List

from pydantic import BaseModel

from src.configs.settings import get_settings


class ServiceLogWebSocket(BaseModel):
    instance_id: str
    socket_url: str


class UserAuthRoles:
    def __init__(self, username: str, roles: list[str]):
        self.username = username
        self.roles = roles

    @cached_property
    def is_admin(self) -> bool:
        settings = get_settings()
        return any(role in settings.admin_roles for role in self.roles)


class CatalogModuleInfo(BaseModel):
    url: str
    version: str
    module_name: str
    release_tags: List[str]
    git_commit_hash: str


from typing import List
from enum import Enum
from pydantic import BaseModel


from typing import List
from enum import Enum
from pydantic import BaseModel


class ServiceHealth(Enum):
    HEALTHY = "healthy"  # All replicas are available and healthy
    UNHEALTHY = "unhealthy"  # At least one replica is available but unhealthy
    DEGRADED = "degraded"  # Some replicas are available but less than the total replicas
    UNKNOWN = "unknown"  # The health status is unknown
    STARTING = "starting"  # The service is starting up
    NONE = "none"  # There are no replicas


class ServiceStatus(Enum):
    RUNNING = "active"  # All replicas are running
    STOPPED = "stopped"  # There are no replicas
    STARTING = "starting"  # At least one replica is starting up
    STOPPING = "stopping"  # At least one replica is stopping
    PAUSED = "paused"  # At least one replica is paused
    ERROR = "error"  # At least one replica is in an error state


class DynamicServiceStatus(BaseModel):
    #ServiceWizard1 Fields
    git_commit_hash: str  # Git commit hash of the service
    status: ServiceStatus  # Service status based on replica counts
    version: str  # Version of the service
    #hash: str to be set to git_commit_hash
    release_tags: List[str]  # List of release tags for the service
    url: str  # URL of the service
    module_name: str  # Name of the service module
    health: ServiceHealth  # Service health based on replica counts
    up: int  # Indicator of whether the service is up (1) or down (0)
    # New Fields
    deployment_name: str  # Name of the deployment
    replicas: int  # Total number of replicas
    updated_replicas: int = 0  # Number of replicas updated to the latest desired state
    ready_replicas: int = 0  # Number of replicas that are ready
    available_replicas: int = 0  # Number of replicas that are available for scaling or updates
    unavailable_replicas: int = 0  # Number of replicas that are unavailable



    @classmethod
    def calculate_up(cls, replicas: int, available_replicas: int) -> int:
        if replicas > 0 and available_replicas > 0:
            return 1
        return 0

    @classmethod
    def calculate_status(cls, replicas: int, available_replicas: int) -> ServiceStatus:
        if replicas == 0:
            return ServiceStatus.STOPPED
        elif replicas > 0 and available_replicas == 0:
            return ServiceStatus.STARTING
        elif replicas > 0 and replicas == available_replicas:
            return ServiceStatus.RUNNING
        else:
            return ServiceStatus.ERROR

    @classmethod
    def calculate_health(cls, replicas: int, available_replicas: int) -> ServiceHealth:
        if replicas == 0:
            return ServiceHealth.NONE
        elif replicas > 0 and replicas == available_replicas:
            return ServiceHealth.HEALTHY
        elif replicas > 0 and 0 < available_replicas < replicas:
            return ServiceHealth.DEGRADED
        else:
            return ServiceHealth.UNHEALTHY

    def __init__(self, **data):
        # Set integer fields to 0 if they are None
        data["replicas"] = data.get("replicas") or 0
        data["updated_replicas"] = data.get("updated_replicas") or 0
        data["ready_replicas"] = data.get("ready_replicas") or 0
        data["available_replicas"] = data.get("available_replicas") or 0
        data["unavailable_replicas"] = data.get("unavailable_replicas") or 0

        # Calculate the 'up', 'status', and 'health' fields based on the provided data
        data["up"] = self.calculate_up(data["replicas"], data["available_replicas"])
        data["status"] = self.calculate_status(data["replicas"], data["available_replicas"])
        data["health"] = self.calculate_health(data["replicas"], data["available_replicas"])

        # Initialize the model using the updated data
        super().__init__(**data)
