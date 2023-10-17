import logging
import time
from typing import List, Dict, Optional, Any

from fastapi import Request, HTTPException

from clients.baseclient import ServerError
from configs.settings import get_settings
from dependencies.k8_wrapper import query_k8s_deployment_status, get_k8s_deployments, DuplicateLabelsException
from models import DynamicServiceStatus, CatalogModuleInfo


def lookup_module_info(request: Request, module_name: str, git_commit: str) -> CatalogModuleInfo:
    """
    Retrieve information about a module from the KBase Catalog.

    :param request: The request object used to retrieve module information.
    :param module_name: The name of the module.
    :param git_commit: The Git commit hash of the module. This does not need to be normalized.
    :return: The module information.
    """
    settings = request.app.state.settings
    try:
        m_info = request.app.state.catalog_client.get_combined_module_info(module_name, git_commit)
    except ServerError as e:
        raise HTTPException(status_code=500, detail=e)
    except Exception as e:
        return CatalogModuleInfo(
            url=f"No Valid URL Found, or possible programming error {e}",
            version=git_commit,
            module_name=module_name,
            release_tags=[],
            git_commit_hash=git_commit,
            owners=["Unknown"],
        )
    return CatalogModuleInfo(
        # Need to sync this URL with kubernetes methods
        url=f"{settings.external_ds_url}/{m_info['module_name']}.{m_info['git_commit_hash']}",
        version=m_info["version"],
        module_name=m_info["module_name"],
        release_tags=m_info["release_tags"],
        git_commit_hash=m_info["git_commit_hash"],
        owners=m_info["owners"],
    )


def get_service_status_without_retries(request, module_name, version) -> DynamicServiceStatus:
    """
    Convenience method to get the service status without retries.
    """
    return get_service_status_with_retries(request, module_name, version, retries=0)


def get_service_status_with_retries(request, module_name, version, retries=10) -> DynamicServiceStatus:
    """
    Retrieve the status of a service based on the module version and git commit hash.
    First check the catalog, and cache the results, then check kubernetes.
    :param request:
    :param module_name:
    :param version:
    :param retries:
    :return:
    """
    # Validate request in catalog first
    lookup_module_info(request=request, module_name=module_name, git_commit=version)
    # Then check kubernetes
    for _ in range(retries):
        try:
            status = get_dynamic_service_status_helper(request, module_name, version)
            # The deployment is up
            if status.up == 1:
                return status
            # The deployment is stopped
            if status.replicas == 0:
                return status
        except ServerError as e:
            raise HTTPException(status_code=500, detail=e)
        except DuplicateLabelsException:
            raise HTTPException(status_code=500, detail="Duplicate labels found in deployment, an admin screwed something up!")
        except Exception:
            # The deployment had more than one replica, but not even one was ready
            pass
        time.sleep(2)

    raise Exception("Failed to get service status after maximum retries")


def get_dynamic_service_status_helper(request, module_name, version) -> DynamicServiceStatus:
    """
    Retrieve the status of a service based on the module version and git commit hash.
    :param request: The request object used to retrieve module information.
    :param version: The version of the module requested (not normalized).
    :param module_name: The name of the module.
    :return: The service status.
    :raises HTTPException: If the service is not found with the given module name and version.
    """

    module_info = lookup_module_info(request=request, module_name=module_name, git_commit=version)

    deployment = query_k8s_deployment_status(request, module_name=module_name, module_git_commit_hash=module_info.git_commit_hash)
    if deployment:
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

    else:
        raise HTTPException(status_code=404, detail=f"No dynamic service found with module_name={module_name} and version={version}")


class IncompleteDeploymentAnnotationError(Exception):
    def __init__(self, deployment_name):
        super().__init__(f"Deployment '{deployment_name}' has missing or None 'module_name' or 'git_commit_hash' annotations.")


def get_all_dynamic_service_statuses(request: Request, module_name, module_version) -> List[DynamicServiceStatus]:
    if module_name or module_version:
        logging.debug("dropping list_service_status params since SW1 doesn't use them")

    if not request.app.state.catalog_client.get_hash_to_name_mappings():
        raise HTTPException(status_code=404, detail="No dynamic services found in catalog!")

    deployment_statuses = get_k8s_deployments(request)  # type List[V1Deployment]
    if len(deployment_statuses) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No deployments found in kubernetes cluster with namespace={get_settings().namespace} and labels=dynamic-service=true!",
        )

    # TODO see if you need to get the list based on running deployments or based on the catalog
    dynamic_service_statuses = []
    for deployment in deployment_statuses:
        deployment = deployment
        try:
            module_name = deployment.metadata.annotations.get("module_name")
            git_commit = deployment.metadata.annotations.get("git_commit_hash")
            if not module_name or not git_commit:
                raise IncompleteDeploymentAnnotationError(deployment.metadata.name)
        except IncompleteDeploymentAnnotationError:
            # If someone deployed a bad service into this namespace, this will protect this query from failing
            continue

        module_info = lookup_module_info(request=request, module_name=module_name, git_commit=git_commit)
        dynamic_service_statuses.append(
            DynamicServiceStatus(
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
        )

    # Deployments were found, but none of them had the correct annotations, they were missing
    # deployment.metadata.annotations.get("module_name")
    # deployment.metadata.annotations.get("git_commit_hash")
    if len(dynamic_service_statuses) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No dynamic services found in kubernetes cluster with namespace={get_settings().namespace} and labels=dynamic-service=true! Or "
            f"they were found and they were missing the module_name and git_commit_hash annotations!",
        )

    return dynamic_service_statuses


def get_status(request: Request, module_name: Optional[Any] = None, version: Optional[Any] = None) -> Dict:
    if module_name or version:
        logging.debug("dropping get_status params since SW1 doesn't use them")

    return {
        "git_commit_hash": request.app.state.settings.vcs_ref,
        "state": "OK",
        "version": request.app.state.settings.vcs_ref,
        "message": "",
        "git_url": "https://github.com/kbase/service_wizard2",
    }


def get_version(request: Request, module_name: Optional[Any] = None, version: Optional[Any] = None) -> List[str]:
    if module_name or version:
        logging.debug("dropping get_version params since SW1 doesn't use them")

    return [str(request.app.state.settings.vcs_ref)]
