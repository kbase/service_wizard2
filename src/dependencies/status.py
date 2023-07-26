from datetime import time
from pprint import pprint
from typing import List

from fastapi import Request, HTTPException
from kubernetes import client

from src.configs.settings import get_settings
from src.models.models import DynamicServiceStatus, CatalogModuleInfo
from src.dependencies.catalog_wrapper import get_hash_to_name_mapping, get_module_version
from src.dependencies.k8_wrapper import get_all_pods, get_k8s_deployment_status_from_label, query_k8s_deployment_status, get_k8s_deployments
import logging


def lookup_module_info(request: Request, module_name: str, git_commit: str) -> CatalogModuleInfo:
    """
    Retrieve information about a module from the catalog.

    :param request: The request object used to retrieve module information.
    :param module_name: The name of the module.
    :param git_commit:The Git commit hash of the module.
    :return:
    """
    try:
        logging.info(f"Looking up module_name{module_name} and git_commit{git_commit}")
        mv = get_module_version(request, module_name, git_commit)
    except Exception as e:
        print(f"Looking up module_name{module_name} and git_commit{git_commit} failed with error {e}")
        return CatalogModuleInfo(
            # TODO GET URL FROM THE SERVICE INSTEAD OF GUESSING IT?
            url=f"No Valid URL Found",
            version=git_commit,
            module_name=module_name,
            release_tags=[],
            git_commit_hash=git_commit,
        )

    module_info = CatalogModuleInfo(
        # TODO GET URL FROM THE SERVICE INSTEAD OF GUESSING IT?
        url=f"{get_settings().external_ds_url}/{mv['git_commit_hash']}.{mv['module_name']}.",
        version=mv["version"],
        module_name=mv["module_name"],
        release_tags=mv["release_tags"],
        git_commit_hash=mv["git_commit_hash"],
    )
    return module_info


def get_deployment_status(request, label_selector: client.V1LabelSelector):
    """
    Retrieve the status of a deployment based on the module version and git commit hash.

    :param module_version: The module version.
    :param git_commit_hash: The git commit hash.
    :return: The deployment status.
    """
    # Specify the deployment spec
    # import ipdb;
    # ipdb.set_trace()

    deployment_status = get_k8s_deployment_status_from_label(request, label_selector=label_selector)
    for item in deployment_status:
        print("Deployment status is")
        print(item)
    return []


import time


def get_service_status_with_retries(request, module_name, version, retries=5) -> DynamicServiceStatus:
    # if there is some delay in starting up, then give it a couple seconds
    for _ in range(retries):
        try:
            status = get_service_status_helper(request, module_name, version)
            if status.up == 1:
                return status
        except Exception:
            pass
        time.sleep(2)

    raise Exception("Failed to get service status after maximum retries")


def get_service_status_helper(request, module_name, version) -> DynamicServiceStatus:
    """
    Retrieve the status of a service based on the module version and git commit hash.

    :param module_version: The module version.
    :param git_commit_hash: The git commit hash.
    :return: The service status.
    """
    # Specify the deployment spec
    # import ipdb;
    # ipdb.set_trace()
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
    module_hash_lookup = get_hash_to_name_mapping(request)
    if len(module_hash_lookup) == 0:
        raise HTTPException(status_code=404, detail="No dynamic services found in catalog!")

    deployment_statuses = get_k8s_deployments(request)  # type List[V1Deployment]
    if len(deployment_statuses) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No deployments found in kubernetes cluster with namespace={get_settings().namespace} and " "labels=dynamic-service=true!",
        )

    # TODO see if you need to get the list based on running deployments or based on the catalog
    dynamic_service_statuses = []
    for deployment in deployment_statuses:
        deployment = deployment  # type: V1Deployment
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


def list_service_status_helper(request: Request) -> List[DynamicServiceStatus]:
    """
    Retrieve the list of dynamic service statuses based on the Kubernetes pods and module information.

    Args:
        request (Request): The request object used to retrieve Kubernetes client and other information.


    Raises:
        HTTPException: If no dynamic services or pods are found
    :param request: FASTApi request
    :return: List[DynamicServiceStatus]: A list of DynamicServiceStatus objects, each representing a dynamic service status.
    """

    module_hash_lookup = get_hash_to_name_mapping(request)
    if len(module_hash_lookup) == 0:
        raise HTTPException(status_code=404, detail="No dynamic services found in catalog!")

    pod_statuses = get_all_pods(request)
    if len(pod_statuses) == 0:
        raise HTTPException(status_code=404, detail="No pods found in kubernetes cluster with label dynamic-service=true!")

    dynamic_service_statuses = []
    for pod_status in pod_statuses:
        print("Lookng up", pod_status)
        module_info = lookup_module_info(request=request, module_name=pod_status.kb_module_name, git_commit=pod_status.git_commit)
        dynamic_service_statuses.append(
            DynamicServiceStatus(
                status=pod_status,
                url=module_info.url,
                version=module_info.version,
                module_name=module_info.module_name,
                release_tags=module_info.release_tags,
                git_commit_hash=module_info.git_commit_hash,
            )
        )

    return dynamic_service_statuses

    # Not sure if this is needed right now, need to do further resting
    ##            except:
    # this will occur if the module version is not registered with the catalog, or if the module
    # was not marked as a service, or if something was started in Rancher directly and pulled
    # # from somewhere else, or an old version of the catalog was used to start this service
    # es["url"] = "https://{0}:{1}/dynserv/{3}.{2}".format(self.SVC_HOSTNAME, self.NGINX_PORT, rs[0], rs[1])
    # es["version"] = ""
    # es["release_tags"] = []
    # es["git_commit_hash"] = ""
    # es["module_name"] = "!" + rs[0] + ""
