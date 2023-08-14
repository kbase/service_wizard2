from typing import List, Any

from fastapi.requests import Request

from clients.baseclient import ServerError
from src.dependencies.k8_wrapper import get_logs_for_first_pod_in_deployment
from src.dependencies.status import lookup_module_info
from src.rpc.models import JSONRPCResponse


def get_service_log(request: Request, module_name: str, module_version: str) -> JSONRPCResponse | list[dict[str, Any]] | None:
    """
    Get logs for a service. This only returns the logs for the first pod in the deployment, and will need to be changed if there
    are multiple pods in the deployment.
    The format of the logs are the same as in ServiceWizard
    :param request: The request object
    :param module_name:  The module name
    :param module_version:  The module version, normalization not required
    :return: Logs for a single pod in the deployment
    """
    user_auth_roles = request.state.user_auth_roles  # type: UserAuthRoles
    module_info = lookup_module_info(request, module_name, module_version)
    tags = module_info.release_tags

    if not user_auth_roles.is_admin_or_owner(owners=module_info.owners) or ("dev" in tags and "release" not in tags and "beta" not in tags):
        raise ServerError(code=-32000, message="Only admins can view logs. Owners can view dev logs unless in beta or released.", name="Server Error")
    else:
        pod_name, logs = get_logs_for_first_pod_in_deployment(request=request, module_name=module_name, module_git_commit_hash=module_info.git_commit_hash)
        return [{"instance_id": pod_name, "log": logs}]


def get_service_log_web_socket(request: Request, module_name: str, module_version: str) -> List[dict]:
    """
    Get logs for a service. This isn't used anywhere but can require a dependency on rancher if implemented.

    """
    url = "https://github.com/kbase/kbase-ui-plugin-catalog/blob/d7a7198a470710d7abefc7c1a2f30982840af264/" + "src/plugin/iframe_root/modules/widgets/kbaseCatalogService.js#L399"
    if request or module_name or module_version:
        raise NotImplementedError(f"Not implemented yet. See {url} ")
    else:
        return [{}]
