from typing import List

from fastapi import Request, HTTPException

from src.configs.settings import get_settings
from src.models.models import DynamicServiceStatus, CatalogModuleInfo
from src.dependencies.catalog_wrapper import get_hash_to_name_mapping, get_get_module_version
from src.dependencies.k8_wrapper import get_all_pods


def lookup_module_info(request: Request, module_name: str, git_commit: str) -> CatalogModuleInfo:
    """
    Retrieve information about a module from the catalog.

    :param request: The request object used to retrieve module information.
    :param module_name: The name of the module.
    :param git_commit:The Git commit hash of the module.
    :return:
    """
    try:
        mv = get_get_module_version(request, module_name, git_commit)
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
        url=f"{get_settings().kbase_endpoint}/services/dynserv/{git_commit}.{module_name}",
        version=mv["version"],
        module_name=mv["module_name"],
        release_tags=mv["release_tags"],
        git_commit_hash=mv["git_commit_hash"],
    )
    return module_info


def list_service_status(request: Request) -> List[DynamicServiceStatus]:
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
        raise HTTPException(status_code=404, detail="No pods found in kubernetes cluster!")

    dynamic_service_statuses = []
    for pod_status in pod_statuses:
        print("Lookng up", pod_status)
        module_info = lookup_module_info(request=request,
                                         module_name=pod_status.kb_module_name,
                                         git_commit=pod_status.git_commit)
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
