from typing import List

from fastapi import Request
from kubernetes import client

from src.configs.settings import get_settings
from src.models.models import PodStatus


def get_k8s_client(request: Request) -> client.CoreV1Api:
    return request.app.state.k8s_client


def get_pods_in_namespace(
        k8s_client: client.CoreV1Api,
        field_selector=None,
        label_selector="dynamic-service=true",
) -> client.V1PodList:
    """
    Retrieve a list of pods in a specific namespace based on the provided field and label selectors.
    :param k8s_client: k8s_client (client.CoreV1Api): The Kubernetes CoreV1Api client instance.
    :param field_selector: field_selector (str, optional): Field selector used to filter pods. Defaults to "metadata.name,metadata.git_commit,metadata.kb_module_name,status.phase".
    :param label_selector: label_selector (str, optional): Label selector used to filter pods. Defaults to "dynamic-service=true".
    :return: client.V1PodList: A list of pod objects that match the given selectors.
    """
    # "metadata.name,metadata.git_commit,metadata.kb_module_name,status.phase"
    pod_list = k8s_client.list_namespaced_pod(get_settings().namespace, field_selector=field_selector,
                                              label_selector=label_selector)
    return pod_list


def get_all_pods(request: Request) -> List[PodStatus]:
    """
    Retrieve information about all services based on the Kubernetes pods in the specified namespace.
    :param request: The request object used to retrieve Kubernetes client and namespace information.
    :return: List[ServiceInfo]: A list of ServiceInfo, each representing a service with its extracted information.
    """
    # TODO - Move "running" into a constant
    pods = get_pods_in_namespace(k8s_client=get_k8s_client(request))
    service_list: List[PodStatus] = []
    for pod in pods.items:
        pod_health = "unknown"
        for condition in pod.status.conditions:
            if condition.type == "Ready":
                pod_health = "healthy" if condition.status == "True" else "unhealthy"
                break

        git_commit = pod.metadata.annotations.get("git_commit") or ""
        kb_module_name = pod.metadata.annotations.get("kb_module_name") or ""

        pod_status = PodStatus.from_pod(
            pod_name=pod.metadata.name,
            pod_status=pod.status.phase,
            pod_health=pod_health,
            git_commit=git_commit,
            kb_module_name=kb_module_name,
        )
        service_list.append(pod_status)
    return service_list
