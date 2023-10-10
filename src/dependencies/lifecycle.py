import logging
import re
import traceback
from typing import Dict, Tuple

from fastapi import HTTPException
from fastapi import Request
from kubernetes.client import ApiException

from clients.baseclient import ServerError
from configs.settings import Settings  # noqa: F401
from dependencies.k8_wrapper import (
    create_and_launch_deployment,
    create_clusterip_service,
    update_ingress_to_point_to_service,
    scale_replicas,
)
from dependencies.status import get_service_status_with_retries, lookup_module_info
from models import DynamicServiceStatus


def get_env(request, module_name, module_version) -> Dict[str, str]:
    """
    Get the environment variables for a module and set it up for the container to use.
    By default, the KBase endpoint and auth service URLs are set.
    In addition, the secure config params are set as environment variables which are prefixed with KBASE_SECURE_CONFIG_PARAM_ and
    are retrieved from the KBase Catalog.

    :param request: The request object
    :param module_name: The module name
    :param module_version: The module version, normalization not required
    :return: A map of environment variables to be used by the container.
    """
    settings = request.app.state.settings  # type: Settings
    environ_map = {
        "KBASE_ENDPOINT": settings.kbase_services_endpoint,
        "AUTH_SERVICE_URL": settings.auth_legacy_url,
        "AUTH_SERVICE_URL_ALLOW_INSECURE": "false",
    }
    secure_param_list = request.app.state.catalog_client.get_secure_params(module_name, module_version)
    for secure_param in secure_param_list:
        param_name = secure_param["param_name"]
        param_value = secure_param["param_value"]
        environ_map["KBASE_SECURE_CONFIG_PARAM_" + param_name] = param_value
    return environ_map


def get_volume_mounts(request, module_name, module_version) -> list[str]:
    """
    Get the volume mounts from the KBase Catalog for a module and set it up for the container to use.
    :param request:  The request object
    :param module_name:  The module name
    :param module_version:  The module version, normalization not required
    :return:
    """
    volume_mounts = request.app.state.catalog_client.list_service_volume_mounts(module_name, module_version)
    if len(volume_mounts) > 0:
        mounts = []
        for vol in volume_mounts:
            mount_type = "ro" if vol["read_only"] > 0 else "rw"
            mounts.append(f"{vol['host_dir']}:{vol['container_dir']}:{mount_type}")
        return mounts


def _setup_metadata(module_name, requested_module_version, git_commit_hash, version, git_url) -> Tuple[Dict, Dict]:
    """
    Convenience method to set up the labels and annotations for a deployment.

    :param module_name: Module name that comes from the web request
    :param requested_module_version: Module version that comes from the web request
    :param git_commit_hash: Hash that comes from KBase Catalog
    :param version: Module Version that comes from KBase Catalog
    :param git_url: Git URL from KBase Catalog
    :return: labels, annotations
    """
    # Warning, if any of these don't follow k8 regex filter conventions, the deployment will fail
    labels = {
        "us.kbase.dynamicservice": "true",
        "us.kbase.module.git_commit_hash": git_commit_hash,
        "us.kbase.module.module_name": module_name.lower(),
    }
    annotations = {
        "git_commit_hash": git_commit_hash,
        "module_name": module_name,
        "module_version_from_request": requested_module_version,
        "us.kbase.catalog.moduleversion": version,
        "description": re.sub(r"^(https?://)", "", git_url),
        "k8s_deployment_name": "to_be_overwritten",
        "k8s_service_name": "to_be_overwritten",
    }
    return labels, annotations


def _create_and_launch_deployment_helper(
    annotations: Dict,
    env: Dict,
    image: str,
    labels: Dict,
    module_git_commit_hash: str,
    module_name: str,
    mounts: list[str],
    request: Request,
):
    """
    Helper method to create and launch a deployment.
    It will attempt to create the deployment and if it already exists, it will log a warning and continue.
    It will return True if it already exists
    Else, it will implicitly return None
    :return:
    """
    try:
        create_and_launch_deployment(
            request=request,
            module_name=module_name,
            module_git_commit_hash=module_git_commit_hash,
            image=image,
            labels=labels,
            annotations=annotations,
            env=env,
            mounts=mounts,
        )
        return False
    except ApiException as e:
        if e.status == 409:  # AlreadyExistsError
            return True
        else:
            detail = traceback.format_exc()
            raise HTTPException(status_code=e.status, detail=detail) from e


def _create_cluster_ip_service_helper(request, module_name, catalog_git_commit_hash, labels):
    """
    Helper method to create a cluster IP service for a deployment.
    It will attempt to create the service and if it already exists, it will log a warning and continue.
    """
    try:
        create_clusterip_service(request, module_name, catalog_git_commit_hash, labels)
    except ApiException as e:
        if e.status == 409:
            logging.warning("Service already exists, skipping creation")
        else:
            detail = traceback.format_exc()
            raise HTTPException(status_code=e.status, detail=detail) from e


def _update_ingress_for_service_helper(request, module_name, git_commit_hash):
    """
    Helper method to update the ingress for a service.
    It will attempt to update the ingress and if it already exists, it will log a warning and continue.
    """
    try:
        update_ingress_to_point_to_service(request, module_name, git_commit_hash)
    except ApiException as e:
        if e.status == 409:
            logging.warning("Ingress already exists, skipping creation")
        else:
            detail = traceback.format_exc()
            raise HTTPException(status_code=e.status, detail=detail) from e


def start_deployment(request: Request, module_name, module_version, replicas=1) -> DynamicServiceStatus:
    """
    Start a deployment for a given module name and version.
    Then create a service and ingress for it.
    Then return the status of the deployment.

    If the deployment already exists, it will attempt to scale it up to the requested number of replicas, but it is always 1 replica at the moment.

    :param request:  The request object
    :param module_name:  The module name
    :param module_version:  The module version, normalization not required
    :param replicas: Number of replicas to start, no way to set it from the API at the moment.
    :return:
    """

    module_info = request.app.state.catalog_client.get_combined_module_info(module_name, module_version)
    labels, annotations = _setup_metadata(
        module_name=module_name,
        requested_module_version=module_version,
        git_commit_hash=module_info["git_commit_hash"],
        version=module_info["version"],
        git_url=module_info["git_url"],
    )

    mounts = get_volume_mounts(request, module_name, module_version)
    env = get_env(request, module_name, module_version)

    deployment_already_exists = _create_and_launch_deployment_helper(
        annotations=annotations,
        env=env,
        image=module_info["docker_img_name"],
        labels=labels,
        module_git_commit_hash=module_info["git_commit_hash"],
        module_name=module_name,
        mounts=mounts,
        request=request,
    )

    if deployment_already_exists:
        scale_replicas(request=request, module_name=module_name, module_git_commit_hash=module_info["git_commit_hash"], replicas=replicas)

    _create_cluster_ip_service_helper(request, module_name, module_info["git_commit_hash"], labels)
    _update_ingress_for_service_helper(request, module_name, module_info["git_commit_hash"])

    return get_service_status_with_retries(request, module_name, module_version)


def stop_deployment(request: Request, module_name, module_version) -> DynamicServiceStatus:
    """
    Stop a deployment for a given module name and version. This will scale the deployment down to 0 replicas.
    It does not delete the deployment, service or ingress.

    :param request: The request object
    :param module_name:  The module name
    :param module_version:  The module version, normalization not required
    :return:
    """
    # TODO Do we need to add logic here to make sure you are an owner or admin before you are able to stop it?
    module_info = lookup_module_info(request, module_name, module_version)
    if request.state.user_auth_roles.is_admin_or_owner(module_info.owners):
        deployment = scale_replicas(request=request, module_name=module_name, module_git_commit_hash=module_info.git_commit_hash, replicas=0)
    else:
        raise ServerError(code=-32000, message="Only admins or module owners can stop dynamic services", name="Server Error")

    return DynamicServiceStatus(
        url=module_info.url,
        version=module_info.version,
        module_name=module_info.module_name,
        release_tags=module_info.release_tags,
        git_commit_hash=module_info.git_commit_hash,
        deployment_name=deployment.metadata.name,
        replicas=deployment.spec.replicas,
        updated_replicas=deployment.status.updated_replicas,
        ready_replicas=deployment.status.ready_replicas,
        available_replicas=deployment.status.available_replicas,
        unavailable_replicas=deployment.status.unavailable_replicas,
    )
