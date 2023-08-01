import json
import logging
import re
import traceback
from typing import Dict, Tuple

from fastapi import HTTPException
from fastapi import Request
from kubernetes.client import ApiException
from starlette.responses import JSONResponse

from clients.baseclient import ServerError
from src.rpc.models import JSONRPCResponse
from src.configs.settings import Settings

from src.dependencies.k8_wrapper import create_and_launch_deployment, create_clusterip_service, update_ingress_to_point_to_service
from src.dependencies.status import get_service_status_with_retries
from src.models.models import DynamicServiceStatus


class ServiceAlreadyExistsException(HTTPException):
    pass


def get_env(request, module_name, module_version) -> Dict[str, str]:
    """
    Get the environment variables for a module and set it up for the container to use.
    :param request:
    :param module_name:
    :param module_version:
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


def get_volume_mounts(request, module_name, module_version):
    volume_mounts = request.app.state.catalog_client.list_service_volume_mounts(module_name, module_version)
    if len(volume_mounts) > 0:
        mounts = []
        for vol in volume_mounts:
            mount_type = "ro" if vol["read_only"] > 0 else "rw"
            mounts.append(f"{vol['host_dir']}:{vol['container_dir']}:{mount_type}")
        return mounts


"""
Using Pods directly gives you fine-grained control over the individual containers,
 including their lifecycles, networking, and resource configurations. 
 However, keep in mind that managing Pods individually requires more manual effort for scaling, rolling updates, 
 and self-healing compared to higher-level resources like Deployments.
"""


def _setup_metdata(module_name, requested_module_version, git_commit_hash, version, git_url) -> Tuple[Dict, Dict]:
    """
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
    except ApiException as e:
        if e.status == 409:  # AlreadyExistsError
            logging.warning(e.body)
        else:
            detail = traceback.format_exc()
            raise HTTPException(status_code=e.status, detail=detail) from e


def _create_cluster_ip_service_helper(request, module_name, catalog_git_commit_hash, labels):
    try:
        create_clusterip_service(request, module_name, catalog_git_commit_hash, labels)
    except ApiException as e:
        if e.status == 409:
            logging.warning("Service already exists, skipping creation")
        else:
            detail = traceback.format_exc()
            raise HTTPException(status_code=e.status, detail=detail) from e


def _update_ingress_for_service_helper(request, module_name, git_commit_hash):
    try:
        update_ingress_to_point_to_service(request, module_name, git_commit_hash)
    except ApiException as e:
        if e.status == 409:
            logging.warning("Ingress already exists, skipping creation")
        else:
            detail = traceback.format_exc()
            raise HTTPException(status_code=e.status, detail=detail) from e


def start_deployment(request: Request, module_name, module_version) -> DynamicServiceStatus:

    logging.info("BEGIN")

    module_info = request.app.state.catalog_client.get_module_info(module_name, module_version, require_dynamic_service=True)
    labels, annotations = _setup_metdata(
        module_name=module_name,
        requested_module_version=module_version,
        git_commit_hash=module_info["git_commit_hash"],
        version=module_info["version"],
        git_url=module_info["git_url"],
    )

    mounts = get_volume_mounts(request, module_name, module_version)
    env = get_env(request, module_name, module_version)


    _create_and_launch_deployment_helper(
        annotations=annotations,
        env=env,
        image=module_info["docker_img_name"],
        labels=labels,
        module_git_commit_hash=module_info["git_commit_hash"],
        module_name=module_name,
        mounts=mounts,
        request=request,
    )

    _create_cluster_ip_service_helper(request, module_name, module_info["git_commit_hash"], labels)
    _update_ingress_for_service_helper(request, module_name, module_info["git_commit_hash"])

    return get_service_status_with_retries(request, module_name, module_version)
