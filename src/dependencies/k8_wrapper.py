import logging
from pprint import pprint
from typing import List

from fastapi import Request
from kubernetes import client

from src.configs.settings import get_settings


def get_k8s_core_client(request: Request) -> client.CoreV1Api:
    return request.app.state.k8s_core_client


def get_k8s_app_client(request: Request) -> client.AppsV1Api:
    return request.app.state.k8s_app_client


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
    pod_list = k8s_client.list_namespaced_pod(get_settings().namespace, field_selector=field_selector, label_selector=label_selector)
    return pod_list


def get_all_pods(request: Request) -> List:
    """
    Retrieve information about all services based on the Kubernetes pods in the specified namespace.
    :param request: The request object used to retrieve Kubernetes client and namespace information.
    :return: List[ServiceInfo]: A list of ServiceInfo, each representing a service with its extracted information.
    """
    # TODO - Move "running" into a constant
    pods = get_pods_in_namespace(k8s_client=get_k8s_core_client(request))
    service_list: List = []
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


def v1_volume_mount_factory(mounts):
    volumes = []
    volume_mounts = []

    if mounts:
        for i, mount in enumerate(mounts):
            mount_parts = mount.split(":")
            if len(mount_parts) != 3:
                logging.error(f"Invalid mount format: {mount}")
            volumes.append(
                client.V1Volume(name=f"volume-{i}", host_path=client.V1HostPathVolumeSource(path=mount_parts[0]))
            )  # This is your host path
            volume_mounts.append(
                client.V1VolumeMount(
                    name=f"volume-{i}", mount_path=mount_parts[1], read_only=bool(mount_parts[2] == "ro")
                )  # This is your container path
            )

    return volumes, volume_mounts


def create_and_launch_deployment(request, module_name, module_git_commit_hash, image, labels, annotations, env, mounts) -> client.V1LabelSelector:
    # Specify the deployment metadata
    deployment_name = f"{module_name}-{module_git_commit_hash}".lower()

    print("Labels are")
    pprint(labels)
    metadata = client.V1ObjectMeta(name=deployment_name, labels=labels, annotations=annotations)

    # Specify the container details
    logging.info("Mounts are??????")
    print("Mounts are??????")
    volumes, volume_mounts = v1_volume_mount_factory(mounts)
    print("Mounts gotten??????")

    container = client.V1Container(
        name=deployment_name,
        image=image,
        env=[client.V1EnvVar(name=k, value=v) for k, v in env.items()],
        volume_mounts=volume_mounts,
    )

    # Specify the pod template
    template = client.V1PodTemplateSpec(metadata=metadata, spec=client.V1PodSpec(containers=[container], volumes=volumes))

    # Specify the deployment spec
    selector = client.V1LabelSelector(
        match_labels={"us.kbase.module.module_name": module_name.lower(), "us.kbase.module.git_commit_hash": module_git_commit_hash}
    )

    spec = client.V1DeploymentSpec(replicas=1, template=template, selector=selector)

    # Create the deployment object
    deployment = client.V1Deployment(api_version="apps/v1", kind="Deployment", metadata=metadata, spec=spec)

    # Create the deployment
    print(f"About to create deployment {deployment} in {get_settings().namespace}")
    get_k8s_app_client(request).create_namespaced_deployment(body=deployment, namespace=get_settings().namespace)
    print("Done creating deployment")
    return selector


def _get_deployment_status(request, label_selector_text) -> client.V1Deployment:
    apps_v1_api = get_k8s_app_client(request)
    deployment_statuses = apps_v1_api.list_namespaced_deployment(get_settings().namespace, label_selector=label_selector_text).items
    if len(deployment_statuses) > 1:
        raise Exception("Something went wrong, there are too many deployments with the same labels, and there should only ever be one!")
    elif len(deployment_statuses) == 0:
        return None
    return deployment_statuses[0]


def query_k8s_deployment_status(request, module_name, module_git_commit_hash) -> client.V1Deployment:
    label_selector_text = f"us.kbase.module.module_name={module_name.lower()}," + f"us.kbase.module.git_commit_hash={module_git_commit_hash}"
    return _get_deployment_status(request, label_selector_text)


def get_k8s_deployment_status_from_label(request, label_selector: client.V1LabelSelector) -> client.V1Deployment:
    label_selector_text = ",".join([f"{key}={value}" for key, value in label_selector.match_labels.items()])
    return _get_deployment_status(request, label_selector_text)


def get_k8s_deployments(request, label_selector="dynamic-service=true"):
    # TODO Cache this for 5 seconds, so all requests within that time don't query the k8 api
    apps_v1_api = get_k8s_app_client(request)
    return apps_v1_api.list_namespaced_deployment(get_settings().namespace,).items
