import logging
import re
import time

from fastapi import Request
from kubernetes import client
from kubernetes.client import (
    V1Service,
    V1ServiceSpec,
    V1ServicePort,
    V1Ingress,
    V1IngressSpec,
    V1HTTPIngressRuleValue,
    V1HTTPIngressPath,
    V1IngressBackend,
    V1IngressRule,
    ApiException,
)

from src.configs.settings import get_settings


def get_k8s_core_client(request: Request) -> client.CoreV1Api:
    return request.app.state.k8s_core_client


def get_k8s_app_client(request: Request) -> client.AppsV1Api:
    return request.app.state.k8s_app_client


def get_k8s_networking_client(request: Request) -> client.NetworkingV1Api:
    return request.app.state.k8s_network_client


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


def _sanitize_deployment_name(module_name, module_git_commit_hash):
    """
    Create a deployment name based on the module name and git commit hash. But adhere to kubernetes api naming rules and be a valid DNS label
    :param module_name:
    :param module_git_commit_hash:
    :return:
    """

    sanitized_module_name = re.sub(r"[^a-zA-Z0-9]", "-", module_name)
    short_git_sha = module_git_commit_hash[:7]
    epoch_seconds = int(time.time())
    deployment_name = f"d-{sanitized_module_name}-{short_git_sha}-{epoch_seconds}".lower()
    service_name = f"s-{sanitized_module_name}-{short_git_sha}-{epoch_seconds}".lower()

    # If the deployment name is too long, shorten it
    if len(deployment_name) > 63:
        excess_length = len(deployment_name) - 63
        deployment_name = f"d-{sanitized_module_name[:-excess_length]}-{short_git_sha}-{epoch_seconds}"
        service_name = f"s-{sanitized_module_name[:-excess_length]}-{short_git_sha}-{epoch_seconds}"

    return deployment_name, service_name

    # TODO: Add a test for this function
    # TODO: add documentation about maximum length of deployment name being 63 characters,
    # Test the function with a very long module name and a git commit hash
    # sanitize_deployment_name("My_Module_Name"*10, "7f6d03cf556b2a1e610fd70b68924a2f6700ae44")


def create_clusterip_service(request, module_name, module_git_commit_hash, labels) -> client.V1Service:
    core_v1_api = get_k8s_core_client(request)
    deployment_name, service_name = _sanitize_deployment_name(module_name, module_git_commit_hash)

    # Define the service
    service = V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(
            name=service_name,
            labels=labels,
        ),
        spec=V1ServiceSpec(
            selector=labels,
            ports=[V1ServicePort(port=5000, target_port=5000)],
            type="ClusterIP",
        ),
    )
    return core_v1_api.create_namespaced_service(namespace=get_settings().namespace, body=service)


def _ensure_ingress_exists(request):
    # This ensures that the main service wizard ingress exists, and if it doesn't, creates it.
    # This should only ever be called once, or if in case someone deletes the ingress for it
    settings = request.settings
    networking_v1_api = get_k8s_networking_client(request)
    ingress_spec = V1IngressSpec(
        rules=[V1IngressRule(host=settings.kbase_root_endpoint.replace("http://", "").replace("https://", ""), http=None)]  # no paths specified
    )
    ingress = V1Ingress(
        api_version="networking.k8s.io/v1",
        kind="Ingress",
        metadata=client.V1ObjectMeta(
            name="dynamic-services",
            annotations={
                "nginx.ingress.kubernetes.io/rewrite-target": "/$2",
            },
        ),
        spec=ingress_spec,
    )
    try:
        networking_v1_api.read_namespaced_ingress(name="dynamic-services", namespace=settings.namespace)
    except ApiException as e:
        if e.status == 404:
            networking_v1_api.create_namespaced_ingress(namespace=settings.namespace, body=ingress)
        else:
            raise


def update_ingress_to_point_to_service(request, deployment_name, module_name, git_commit_hash):
    _ensure_ingress_exists(request)


def create_and_launch_deployment(request, module_name, module_git_commit_hash, image, labels, annotations, env, mounts) -> client.V1LabelSelector:
    deployment_name, service_name = _sanitize_deployment_name(module_name, module_git_commit_hash)

    annotations["k8s_deployment_name"] = deployment_name
    annotations["k8s_service_name"] = service_name
    metadata = client.V1ObjectMeta(name=deployment_name, labels=labels, annotations=annotations)

    volumes, volume_mounts = v1_volume_mount_factory(mounts)
    container = client.V1Container(
        name=deployment_name,
        image=image,
        env=[client.V1EnvVar(name=k, value=v) for k, v in env.items()],
        volume_mounts=volume_mounts,
    )

    template = client.V1PodTemplateSpec(metadata=metadata, spec=client.V1PodSpec(containers=[container], volumes=volumes))
    selector = client.V1LabelSelector(
        match_labels={"us.kbase.module.module_name": module_name.lower(), "us.kbase.module.git_commit_hash": module_git_commit_hash}
    )
    spec = client.V1DeploymentSpec(replicas=1, template=template, selector=selector)
    deployment = client.V1Deployment(api_version="apps/v1", kind="Deployment", metadata=metadata, spec=spec)
    get_k8s_app_client(request).create_namespaced_deployment(body=deployment, namespace=get_settings().namespace)
    return selector


def _get_deployment_status(request, label_selector_text) -> client.V1Deployment | None:
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


def get_k8s_deployments(request, label_selector="us.kbase.dynamicservice=true"):
    # TODO Cache this for 5 seconds, so all requests within that time don't query the k8 api
    apps_v1_api = get_k8s_app_client(request)
    return apps_v1_api.list_namespaced_deployment(get_settings().namespace, label_selector=label_selector).items
