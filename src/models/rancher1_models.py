from enum import Enum


class Rancher1ServiceState(Enum):
    ACTIVE = "active"  # Indicates that the service is currently running or active.
    UPGRADING = "upgrading"  # Indicates that the service is in the process of being upgraded.
    UPGRADING_ROLLBACK = "upgrading-rollback"  # Indicates that the service is in the process of rolling back an upgrade.
    DEACTIVATED = "deactivated"  # Indicates that the service is not running or inactive.
    REMOVED = "removed"  # Indicates that the service has been removed.


class Rancher1HealthState(Enum):
    HEALTHY = "healthy"  # Indicates that the service is functioning correctly and in a healthy state.
    UNHEALTHY = "unhealthy"  # Indicates that the service is experiencing issues or is in an unhealthy state.
    INITIALIZING = "initializing"  # Indicates that the service is in the process of initializing.
    INITIALIZING_ROLLBACK = "initializing-rollback"  # Indicates that the service is rolling back the initialization process.
    UPGRADING = "upgrading"  # Indicates that the service is in the process of being upgraded.
    UPGRADING_ROLLBACK = "upgrading-rollback"  # Indicates that the service is rolling back an upgrade.
    UNKNOWN = "unknown"  # Indicates that the health state of the service is not known or cannot be determined.


class ContainerState(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    EXITED = "exited"
    WAITING = "waiting"
    TERMINATED = "terminated"
    CRASH_LOOP_BACK_OFF = "crash-loop-backoff"
    IMAGE_PULL_BACK_OFF = "image-pull-backoff"
    INIT = "init"
    PENDING = "pending"
