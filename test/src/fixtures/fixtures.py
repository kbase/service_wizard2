import os
from unittest.mock import MagicMock

import pytest
from fastapi import Request
from kubernetes import client
from kubernetes.client import CoreV1Api, AppsV1Api, NetworkingV1Api
from kubernetes.client import V1Ingress, V1IngressSpec, V1IngressRule

from src.clients.CachedCatalogClient import CachedCatalogClient
from src.clients.KubernetesClients import K8sClients
from src.configs.settings import get_settings
from src.models import DynamicServiceStatus


@pytest.fixture(autouse=True)
def mock_request():
    return get_example_mock_request()


@pytest.fixture(autouse=True)
def example_ingress():
    return get_example_ingress()


@pytest.fixture(autouse=True)
def generate_kubeconfig():
    # Generate a kubeconfig file for testing
    # Overwrite kubeconfig
    os.environ["KUBECONFIG"] = "test_kubeconfig_file"
    kubeconfig_path = os.environ["KUBECONFIG"]

    kubeconfig_content = """\
apiVersion: v1
kind: Config
current-context: test-context
clusters:
- name: test-cluster
  cluster:
    server: https://test-api-server
    insecure-skip-tls-verify: true
contexts:
- name: test-context
  context:
    cluster: test-cluster
    user: test-user
users:
- name: test-user
  user:
    exec:
      command: echo
      apiVersion: client.authentication.k8s.io/v1alpha1
      args:
      - "access_token"
"""

    with open(kubeconfig_path, "w") as kubeconfig_file:
        kubeconfig_file.write(kubeconfig_content.strip())

    yield

    # Clean up the generated kubeconfig file after the tests
    os.remove(kubeconfig_path)


def get_example_mock_request():
    request = MagicMock(spec=Request)
    request.app.state.settings = get_settings()

    mock_module_info = {
        "git_commit_hash": "test_hash",
        "version": "test_version",
        "git_url": "https://github.com/test/repo",
        "module_name": "test_module",
        "release_tags": ["test_tag"],
        "owners": ["test_owner"],
        "docker_img_name": "test_img_name",
    }

    request.app.state.catalog_client = MagicMock(autospec=CachedCatalogClient)
    request.app.state.catalog_client.get_combined_module_info.return_value = mock_module_info
    request.app.state.catalog_client.list_service_volume_mounts.return_value = []
    request.app.state.catalog_client.get_secure_params.return_value = [{"param_name": "test_secure_param_name", "param_value": "test_secure_param_value"}]

    mock_k8s_clients = MagicMock(autospec=K8sClients)
    mock_k8s_clients.network_client = MagicMock(autospec=NetworkingV1Api)
    mock_k8s_clients.app_client = MagicMock(autospec=AppsV1Api)
    mock_k8s_clients.core_client = MagicMock(autospec=CoreV1Api)
    request.app.state.k8s_clients = mock_k8s_clients
    request.app.state.mock_module_info = mock_module_info

    return request


def get_example_ingress():
    settings = get_settings()
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

    ingress_spec.rules = [V1IngressRule(host="ci.kbase.us", http=None)]
    return ingress


@pytest.fixture(autouse=True)
def example_dynamic_service_status_up():
    return get_example_dynamic_service_status(replicas=1)


@pytest.fixture(autouse=True)
def example_dynamic_service_status_down():
    return get_example_dynamic_service_status(replicas=0)


def get_example_dynamic_service_status(replicas=1):
    return DynamicServiceStatus(
        url="test_url",
        version="test_version",
        module_name="test_module_name",
        release_tags=["test_tag"],
        git_commit_hash="test_hash",
        deployment_name="test_deployment_name",
        replicas=replicas,
        updated_replicas=1,
        ready_replicas=1,
        available_replicas=1,
        unavailable_replicas=1,
    )
