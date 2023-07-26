import json
import logging
import re
import time
import traceback

from typing import Dict, Tuple
from fastapi import Request, HTTPException

from fastapi import Request
from kubernetes.client import ApiException

from src.models.models import DynamicServiceStatus
from src.configs.settings import Settings
from src.dependencies.catalog_wrapper import get_module_version, list_service_volume_mounts, get_catalog_secure_params
from src.dependencies.k8_wrapper import create_and_launch_deployment
from src.dependencies.status import get_service_status_with_retries


class ServiceAlreadyExistsException(HTTPException):
    pass


def get_env(request, module_name, module_version) -> Dict[str, str]:
    settings = request.app.state.settings  # type: Settings
    environ_map = {
        "KBASE_ENDPOINT": settings.kbase_endpoint,
        "AUTH_SERVICE_URL": f"{settings.kbase_endpoint}/auth/api/legacy/KBase/Sessions/Login",
        "AUTH_SERVICE_URL_ALLOW_INSECURE": "false",
    }

    secure_param_list = get_catalog_secure_params(request, module_name, module_version)

    for secure_param in secure_param_list:
        param_name = secure_param["param_name"]
        param_value = secure_param["param_value"]
        environ_map["KBASE_SECURE_CONFIG_PARAM_" + param_name] = param_value
    return environ_map


def get_volume_mounts(request, module_name, module_version):
    volume_mounts = list_service_volume_mounts(request, module_name, module_version)
    print("Volume mounts are", volume_mounts)
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


def _setup_metdata(module_name, git_commit_hash, module_version, catalog_version, catalog_git_url) -> Tuple[Dict, Dict]:
    # Warning, if any of these don't follow k8 regex filter conventions, the deployment will fail
    labels = {
        "us.kbase.dynamicservice": "true",
        "us.kbase.module.git_commit_hash": git_commit_hash,
        "us.kbase.module.module_name": module_name.lower(),
    }
    annotations = {
        "git_commit_hash": git_commit_hash,
        "module_name": module_name,
        "module_version_from_request": module_version,
        "us.kbase.catalog.moduleversion": catalog_version,
        "description": re.sub(r"^(https?://)", "", catalog_git_url),
    }
    return labels, annotations
    # labels = {
    #     "us.kbase.dynamicservice": "true",
    #     "us.kbase.module.git_commit_hash": catalog_module_version["git_commit_hash"],
    #     "us.kbase.module.module_name": module_name.lower(),
    # }
    #
    # annotations = {
    #     "git_commit_hash": catalog_module_version["git_commit_hash"],
    #     "module_name": module_name,
    #     "module_version_from_request": module_version,
    #     "us.kbase.catalog.moduleversion": catalog_module_version["version"],
    #     "description": re.sub(r"^(https?://)", "", catalog_module_version["git_url"]),
    # }


def start_deployment(request: Request, module_name, module_version) -> DynamicServiceStatus:
    catalog_module_version = get_module_version(request, module_name, module_version, require_dynamic_service=True)
    labels, annotations = _setup_metdata(
        module_name=module_name,
        git_commit_hash=catalog_module_version["git_commit_hash"],
        module_version=module_version,
        catalog_version=catalog_module_version["version"],
        catalog_git_url=catalog_module_version["git_url"],
    )
    env = get_env(request, module_name, module_version)
    mounts = get_volume_mounts(request, module_name, module_version)
    try:
        create_and_launch_deployment(
            request=request,
            module_name=module_name,
            module_git_commit_hash=catalog_module_version["git_commit_hash"],
            image=catalog_module_version["docker_img_name"],
            labels=labels,
            annotations=annotations,
            env=env,
            mounts=mounts,
        )
    except ApiException as e:
        if e.status == 409:  # AlreadyExistsError
            error_message = (
                f"The deployment with name '{module_name}' and version '{module_version}' already exists. "
                + f"Commit:{catalog_module_version['git_commit_hash']} Version:{catalog_module_version['version']} "
                + f"Kubernetes ApiException: {json.dumps(e.body, indent=2, ensure_ascii=False) if e.body else str(e)}".replace("\\", "")
            )
            logging.warning(error_message)
        else:
            detail = traceback.format_exc()
            raise HTTPException(status_code=e.status, detail=detail) from e
    # TODO Create service here! Or add it into above function?

    return get_service_status_with_retries(request, module_name, module_version)
