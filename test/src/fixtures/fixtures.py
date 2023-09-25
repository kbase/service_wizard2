import os
from unittest.mock import Mock

import pytest
from dotenv import load_dotenv
from fastapi import Request

from src.clients.CachedCatalogClient import CachedCatalogClient
from src.clients.KubernetesClients import K8sClients
from src.configs.settings import get_settings


@pytest.fixture(autouse=True)
def mock_request():
    return get_example_mock_request()




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
    request = Mock(spec=Request)
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

    request.app.state.catalog_client = Mock(spec=CachedCatalogClient)
    request.app.state.catalog_client.get_combined_module_info.return_value = mock_module_info
    request.app.state.catalog_client.list_service_volume_mounts.return_value = []
    request.app.state.catalog_client.get_secure_params.return_value = [{"param_name": "test_secure_param_name", "param_value": "test_secure_param_value"}]
    request.app.state.k8s_clients = Mock(spec=K8sClients)
    request.app.state.mock_module_info = mock_module_info


    return request
