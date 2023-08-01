import logging
import time

from pprint import pprint
from typing import List

from fastapi import Request, HTTPException

from src.configs.settings import get_settings
from src.dependencies.k8_wrapper import query_k8s_deployment_status, get_k8s_deployments, DuplicateLabelsException
from src.models.models import DynamicServiceStatus, CatalogModuleInfo


def lookup_module_info(request: Request, module_name: str, git_commit: str) -> CatalogModuleInfo:
    """
    Retrieve information about a module from the catalog.

    :param request: The request object used to retrieve module information.
    :param module_name: The name of the module.
    :param git_commit:The Git commit hash of the module.
    :return:
    """
    try:
        # logging.info(f"Looking up module_name{module_name} and git_commit{git_commit}")
        mv = request.app.state.catalog_client.get_module_info(module_name, git_commit)
    except:
        return CatalogModuleInfo(
            url=f"No Valid URL Found, or possible programming error",
            version=git_commit,
            module_name=module_name,
            release_tags=[],
            git_commit_hash=git_commit,
        )

    module_info = CatalogModuleInfo(
        # TODO GET URL FROM THE SERVICE INSTEAD OF GUESSING IT?
        url=f"{get_settings().external_ds_url}/{mv['git_commit_hash']}.{mv['module_name']}",
        version=mv["version"],
        module_name=mv["module_name"],
        release_tags=mv["release_tags"],
        git_commit_hash=mv["git_commit_hash"],
    )
    return module_info


def get_service_status_with_retries(request, module_name, version, retries=10) -> DynamicServiceStatus:
    # if there is some delay in starting up, then give it a couple seconds
    for _ in range(retries):
        try:
            status = get_dynamic_service_status_helper(request, module_name, version)
            if status.up == 1:
                return status
        except DuplicateLabelsException:
            raise HTTPException(status_code=500, detail="Duplicate labels found in deployment, an admin screwed something up!")
        except Exception as e:
            logging.error(e)
            pass
        time.sleep(2)

    raise Exception("Failed to get service status after maximum retries")


def get_dynamic_service_status_helper(request, module_name, version) -> DynamicServiceStatus:
    """
    Retrieve the status of a service based on the module version and git commit hash.
    :param request: The request object used to retrieve module information.
    :param version:
    :param module_name:

    :return: The service status.
    """

    module_info = lookup_module_info(request=request, module_name=module_name, git_commit=version)  # type: 'CatalogModuleInfo'
    deployment = query_k8s_deployment_status(
        request, module_name=module_name, module_git_commit_hash=module_info.git_commit_hash
    )  # type: 'V1Deployment'
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


def get_all_dynamic_service_statuses(request: Request) -> List[DynamicServiceStatus]:
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
        deployment = deployment  # type: 'V1Deployment'
        pprint(deployment.metadata.annotations)
        try:
            module_name = deployment.metadata.annotations["module_name"]
            git_commit = deployment.metadata.annotations["git_commit_hash"]
        except KeyError:
            # If someone deployed a bad service into this namespace, this will protect this query from failing
            continue
        module_info = lookup_module_info(request=request, module_name=module_name, git_commit=git_commit)  # type: 'CatalogModuleInfo'
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
    return dynamic_service_statuses
