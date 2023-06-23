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


class ServiceHealth(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    STARTING = "starting"
    NONE = "none"


class ServiceStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    PAUSED = "paused"
    ERROR = "error"


class PodStatus(BaseModel):
    git_commit: str
   # health: ServiceHealth
    hash: str
    kb_module_name: str
    name: str
    # status: ServiceStatus
    up: int

    @classmethod
    def from_pod(cls, pod_name: str, pod_status: str, pod_health: str, git_commit: str,
                 kb_module_name: str) -> "PodStatus":
        return cls(
            git_commit=git_commit,
           # health=ServiceHealth(pod_health.lower()),
            hash=git_commit,
            kb_module_name=kb_module_name,
            name=pod_name,
            # status=ServiceStatus(pod_status.lower()),
            up=1 if pod_status.lower() == "running" else 0,
        )


class DynamicServiceStatus(BaseModel):
    #status: PodStatus
    url: str
    version: str
    module_name: str
    release_tags: List[str]
    git_commit_hash: str


class CatalogModuleInfo(BaseModel):
    url: str
    version: str
    module_name: str
    release_tags: List[str]
    git_commit_hash: str
