from kubernetes.client import V1DeploymentStatus, V1LabelSelector, V1PodTemplateSpec, V1ObjectMeta, V1DeploymentSpec, V1Deployment

from configs.settings import get_settings
from models.models import DynamicServiceStatus, CatalogModuleInfo


def get_running_deployment(deployment_name) -> DynamicServiceStatus:
    module_info = _create_sample_module_info()
    deployment = create_sample_deployment(deployment_name=deployment_name, ready_replicas=1, replicas=1, available_replicas=1, unavailable_replicas=0)
    deployment_status = _create_deployment_status(module_info, deployment)
    return deployment_status


def get_stopped_deployment(deployment_name) -> DynamicServiceStatus:
    module_info = _create_sample_module_info()
    deployment = create_sample_deployment(deployment_name=deployment_name, ready_replicas=0, available_replicas=0, unavailable_replicas=1, replicas=0)
    deployment_status = _create_deployment_status(module_info, deployment)
    return deployment_status


def _create_deployment_status(module_info, deployment) -> DynamicServiceStatus:
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


def create_sample_deployment(deployment_name, replicas, ready_replicas, available_replicas, unavailable_replicas):
    deployment_status = V1DeploymentStatus(
        updated_replicas=replicas, ready_replicas=ready_replicas, available_replicas=available_replicas, unavailable_replicas=unavailable_replicas
    )

    selector = V1LabelSelector(match_labels={"app": deployment_name})

    pod_template = V1PodTemplateSpec(metadata=V1ObjectMeta(labels={"app": deployment_name}))

    deployment_spec = V1DeploymentSpec(replicas=replicas, selector=selector, template=pod_template)

    deployment = V1Deployment(metadata=V1ObjectMeta(name=deployment_name), spec=deployment_spec, status=deployment_status)
    return deployment


def _create_sample_module_info(module_name="test_module", git_commit_hash="test_hash", version="test_version", release_tags=None, owners=None) -> CatalogModuleInfo:
    if owners is None:
        owners = ["test_owner"]
    if release_tags is None:
        release_tags = list("test_tag")

    settings = get_settings()
    m_info = {"module_name": module_name, "git_commit_hash": git_commit_hash, "version": version, "release_tags": release_tags, "owners": owners}
    return CatalogModuleInfo(
        # Need to sync this URL with kubernetes methods
        url=f"{settings.external_ds_url}/{m_info['module_name']}.{m_info['git_commit_hash']}",
        version=m_info["version"],
        module_name=m_info["module_name"],
        release_tags=m_info["release_tags"],
        git_commit_hash=m_info["git_commit_hash"],
        owners=m_info["owners"],
    )
