import logging
import re
import time
from typing import Optional, List

from cacheout import LRUCache
from fastapi import Request
from kubernetes import client
from kubernetes.client import (
    V1Service,
    V1ServiceSpec,
    V1ServicePort,
    V1Ingress,
    V1IngressSpec,
    V1IngressRule,
    ApiException,
    CoreV1Api,
    AppsV1Api,
    NetworkingV1Api,
    V1HTTPIngressPath,
    V1IngressBackend,
    V1Deployment,
    V1HTTPIngressRuleValue,
    V1Toleration,
)

from src.configs.settings import get_settings


def get_k8s_core_client(request: Request) -> CoreV1Api:
    return request.app.state.k8s_clients.core_client


def get_k8s_app_client(request: Request) -> AppsV1Api:
    return request.app.state.k8s_clients.app_client


def get_k8s_networking_client(request: Request) -> NetworkingV1Api:
    return request.app.state.k8s_clients.network_client


def _get_k8s_service_status_cache(request: Request) -> LRUCache:
    return request.app.state.k8s_clients.service_status_cache


def _get_k8s_all_service_status_cache(request: Request) -> LRUCache:
    return request.app.state.k8s_clients.all_service_status_cache


def check_service_status_cache(request: Request, label_selector_text) -> V1Deployment:
    cache = _get_k8s_service_status_cache(request)
    return cache.get(label_selector_text, None)


def populate_service_status_cache(request: Request, label_selector_text, data: list):
    _get_k8s_service_status_cache(request).set(label_selector_text, data)


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
            volumes.append(client.V1Volume(name=f"volume-{i}", host_path=client.V1HostPathVolumeSource(path=mount_parts[0])))  # This is your host path
            volume_mounts.append(client.V1VolumeMount(name=f"volume-{i}", mount_path=mount_parts[1], read_only=bool(mount_parts[2] == "ro")))  # This is your container path

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

    deployment_name = f"d-{sanitized_module_name}-{short_git_sha}-d".lower()
    service_name = f"s-{sanitized_module_name}-{short_git_sha}-s".lower()

    # If the deployment name is too long, shorten it
    if len(deployment_name) > 63:
        excess_length = len(deployment_name) - 63
        deployment_name = f"d-{sanitized_module_name[:-excess_length]}-{short_git_sha}-d"
        service_name = f"s-{sanitized_module_name[:-excess_length]}-{short_git_sha}-s"

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
    settings = request.app.state.settings
    networking_v1_api = get_k8s_networking_client(request)
    ingress_spec = V1IngressSpec(rules=[V1IngressRule(host=settings.kbase_root_endpoint.replace("https://", "").replace("https://", ""), http=None)])  # no paths specified
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
        return networking_v1_api.read_namespaced_ingress(name="dynamic-services", namespace=settings.namespace)
    except ApiException as e:
        if e.status == 404:
            return networking_v1_api.create_namespaced_ingress(namespace=settings.namespace, body=ingress)
        else:
            raise


def _path_exists_in_ingress(ingress, path):
    """Check if a path already exists in an ingress with one rule only"""
    if ingress.spec.rules[0].http:
        for existing_path in ingress.spec.rules[0].http.paths:
            if existing_path.path == path:
                return True
    return False


class InvalidIngressError(Exception):
    pass


def _update_ingress_with_retries(request, new_path, namespace, retries=3):
    for retry in range(retries):
        try:
            ingress = _ensure_ingress_exists(request)
            # Initialize http attribute with an empty paths list if it is None
            if ingress.spec.rules[0].http is None:
                ingress.spec.rules[0].http = V1HTTPIngressRuleValue(paths=[])
            # Only append the path if it doesn't exist already
            if not _path_exists_in_ingress(ingress, new_path.path):
                ingress.spec.rules[0].http.paths.append(new_path)
            get_k8s_networking_client(request).replace_namespaced_ingress(name=ingress.metadata.name, namespace=namespace, body=ingress)
            break  # if the operation was successful, break the retry loop
        except ApiException as e:
            if e.status not in {409, 422} or retry == retries - 1:
                # re-raise the exception on the last retry, or if the error is not a conflict
                raise
            else:
                time.sleep(1)


def update_ingress_to_point_to_service(request: Request, module_name: str, git_commit_hash: str):
    settings = request.app.state.settings
    namespace = settings.namespace
    deployment_name, service_name = _sanitize_deployment_name(module_name, git_commit_hash)
    # Need to sync this with Status methods
    path = f"/{settings.external_ds_url.split('/')[-1]}/{module_name}.{git_commit_hash}(/|$)(.*)"
    new_path = V1HTTPIngressPath(path=path, path_type="ImplementationSpecific", backend=V1IngressBackend(service={"name": service_name, "port": {"number": 5000}}))
    _update_ingress_with_retries(request=request, new_path=new_path, namespace=namespace)


def create_and_launch_deployment(request, module_name, module_git_commit_hash, image, labels, annotations, env, mounts) -> client.V1LabelSelector:
    deployment_name, service_name = _sanitize_deployment_name(module_name, module_git_commit_hash)
    namespace = request.app.state.settings.namespace

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

    toleration = V1Toleration(effect="NoSchedule", key=namespace, operator="Exists")

    template = client.V1PodTemplateSpec(metadata=metadata, spec=client.V1PodSpec(containers=[container], volumes=volumes, tolerations=[toleration]))
    selector = client.V1LabelSelector(match_labels={"us.kbase.module.module_name": module_name.lower(), "us.kbase.module.git_commit_hash": module_git_commit_hash})
    spec = client.V1DeploymentSpec(replicas=1, template=template, selector=selector)
    deployment = client.V1Deployment(api_version="apps/v1", kind="Deployment", metadata=metadata, spec=spec)
    get_k8s_app_client(request).create_namespaced_deployment(body=deployment, namespace=namespace)
    return selector


class DuplicateLabelsException(Exception):
    pass


def _get_deployment_status(request, label_selector_text) -> Optional[client.V1Deployment]:
    deployment_status = check_service_status_cache(request, label_selector_text)
    if deployment_status is not None:
        return deployment_status

    # Fetch from Kubernetes if cache is empty
    apps_v1_api = get_k8s_app_client(request)
    deployment_statuses = apps_v1_api.list_namespaced_deployment(get_settings().namespace, label_selector=label_selector_text).items

    # Raise exception if multiple deployments exist with the same labels, else set deployment_status
    if len(deployment_statuses) > 1:
        raise DuplicateLabelsException("Too many deployments with the same labels.")
    deployment_status = None if len(deployment_statuses) == 0 else deployment_statuses[0]

    # Update the cache
    populate_service_status_cache(request=request, label_selector_text=label_selector_text, data=deployment_status)

    return deployment_status


def query_k8s_deployment_status(request, module_name, module_git_commit_hash) -> client.V1Deployment:
    label_selector_text = f"us.kbase.module.module_name={module_name.lower()}," + f"us.kbase.module.git_commit_hash={module_git_commit_hash}"
    return _get_deployment_status(request, label_selector_text)


def get_k8s_deployment_status_from_label(request, label_selector: client.V1LabelSelector) -> client.V1Deployment:
    label_selector_text = ",".join([f"{key}={value}" for key, value in label_selector.match_labels.items()])
    return _get_deployment_status(request, label_selector_text)


def get_k8s_deployments(request, label_selector="us.kbase.dynamicservice=true") -> List[client.V1Deployment]:
    """
    Get all deployments with the given label selector. This is cached for 5 minutes.
    :param request: Request object
    :param label_selector: The label selector to use. Defaults to "us.kbase.dynamicservice=true"
    :return: A list of deployments
    """

    cache = _get_k8s_all_service_status_cache(request)
    cached_deployments = cache.get(label_selector, None)
    if cached_deployments is not None:
        return cached_deployments

    apps_v1_api = get_k8s_app_client(request)
    deployments = apps_v1_api.list_namespaced_deployment(get_settings().namespace, label_selector=label_selector).items

    cache.set(label_selector, deployments)

    return deployments


def delete_deployment(request, module_name, module_git_commit_hash) -> str:
    deployment_name, _ = _sanitize_deployment_name(module_name, module_git_commit_hash)
    namespace = request.app.state.settings.namespace
    get_k8s_app_client(request).delete_namespaced_deployment(name=deployment_name, namespace=namespace)
    return deployment_name


def scale_replicas(request, module_name, module_git_commit_hash, replicas: int) -> client.V1Deployment:
    deployment = query_k8s_deployment_status(request, module_name, module_git_commit_hash)
    namespace = request.app.state.settings.namespace
    deployment.spec.replicas = replicas
    return get_k8s_app_client(request).replace_namespaced_deployment(name=deployment.metadata.name, namespace=namespace, body=deployment)


def get_logs_for_first_pod_in_deployment(request, module_name, module_git_commit_hash):
    deployment_name, _ = _sanitize_deployment_name(module_name, module_git_commit_hash)
    namespace = request.app.state.settings.namespace
    label_selector_text = f"us.kbase.module.module_name={module_name.lower()}," + f"us.kbase.module.git_commit_hash={module_git_commit_hash}"

    pod_list = get_k8s_core_client(request).list_namespaced_pod(namespace, label_selector=label_selector_text)

    if pod_list.items:
        # Convert the string into a list of strings, but keep the "\n" at the end of each line like in SW1
        pod_name = pod_list.items[0].metadata.name
        logs = get_k8s_core_client(request).read_namespaced_pod_log(name=pod_name, namespace=namespace, timestamps=True).splitlines(keepends=True)
        return pod_name, logs

    return (f"No Matching Pods in namespace:{namespace} could be found with label_selector={label_selector_text}",) * 2
