from typing import List

from src.dependencies.k8_wrapper import get_logs_for_first_pod_in_deployment
from src.rpc.models import JSONRPCResponse
from src.dependencies.status import lookup_module_info
from fastapi.requests import Request


def get_service_log(request: Request, module_name: str, module_version: str):
    """
    Get logs for a service
    """

    module_info = lookup_module_info(request, module_name, module_version)
    pod_name, logs = get_logs_for_first_pod_in_deployment(
        request=request, module_name=module_name, module_git_commit_hash=module_info.git_commit_hash
    )

    return [{"instance_id": pod_name, "log": logs}]


def get_service_log_web_socket(request: Request, module_name: str, module_version: str) -> List[dict]:
    """
    Get logs for a service
    """
    module_info = lookup_module_info(request, module_name, module_version)
    socket = {}
    return [socket]
