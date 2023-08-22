import pytest
from unittest.mock import Mock, patch
from kubernetes import client
from src.dependencies.k8_wrapper import (
    create_clusterip_service,
    _sanitize_deployment_name,
    update_ingress_to_point_to_service,
    create_and_launch_deployment,
    query_k8s_deployment_status,
    get_k8s_deployments,
    delete_deployment,
    scale_replicas,
    get_logs_for_first_pod_in_deployment,
)

# Sample Data
sample_module_name = "test_module"
sample_git_commit_hash = "1234567"
sample_image = "test_image"
sample_labels = {"test_label": "label_value"}
sample_annotations = {"test_annotation": "annotation_value"}
sample_env = {"TEST_ENV": "value"}
sample_mounts = ["/host/path:/container/path:ro"]


# New Tests
@patch("src.dependencies.k8_wrapper.get_k8s_core_client")
def test_create_clusterip_service(mock_get_k8s_core_client):
    mock_get_k8s_core_client.return_value.create_namespaced_service.return_value = "success"
    result = create_clusterip_service(Mock(), sample_module_name, sample_git_commit_hash, sample_labels)
    assert result == "success"


@patch("src.dependencies.k8_wrapper._ensure_ingress_exists")
@patch("src.dependencies.k8_wrapper.get_k8s_networking_client")
def test_update_ingress_to_point_to_service(mock_get_k8s_networking_client, mock_ensure_ingress_exists):
    mock_ingress = Mock()
    mock_rule = Mock()
    mock_rule.http = None
    mock_ingress.spec.rules = [mock_rule]

    mock_ensure_ingress_exists.return_value = mock_ingress

    mock_request = Mock()
    mock_request.app.state.settings.external_ds_url = "https://example.com/ds"

    update_ingress_to_point_to_service(mock_request, sample_module_name, sample_git_commit_hash)

    mock_get_k8s_networking_client.assert_called_once()


@patch("src.dependencies.k8_wrapper.get_k8s_app_client")
def test_create_and_launch_deployment(mock_get_k8s_app_client):
    mock_get_k8s_app_client.return_value.create_namespaced_deployment.return_value = "success"
    result = create_and_launch_deployment(Mock(), sample_module_name, sample_git_commit_hash, sample_image, sample_labels, sample_annotations, sample_env, sample_mounts)
    assert isinstance(result, client.V1LabelSelector)


@patch("src.dependencies.k8_wrapper._get_k8s_service_status_cache")
@patch("src.dependencies.k8_wrapper.get_k8s_app_client")
def test_query_k8s_deployment_status(mock_get_k8s_app_client, mock_get_k8s_service_status_cache):
    # Mock the service status cache to return None
    mock_cache = Mock()
    mock_cache.get.return_value = None
    mock_get_k8s_service_status_cache.return_value = mock_cache

    # Mock the Kubernetes client to return the deployment
    mock_get_k8s_app_client.return_value.list_namespaced_deployment.return_value.items = ["deployment1"]

    result = query_k8s_deployment_status(Mock(), sample_module_name, sample_git_commit_hash)
    assert result == "deployment1"


@patch("src.dependencies.k8_wrapper._get_k8s_all_service_status_cache")
@patch("src.dependencies.k8_wrapper.get_k8s_app_client")
def test_get_k8s_deployments(mock_get_k8s_app_client, mock_get_k8s_all_service_status_cache):
    # Mock the all service status cache to return None
    mock_cache = Mock()
    mock_cache.get.return_value = None
    mock_get_k8s_all_service_status_cache.return_value = mock_cache

    # Mock the Kubernetes client to return the deployments
    mock_get_k8s_app_client.return_value.list_namespaced_deployment.return_value.items = ["deployment1", "deployment2"]

    result = get_k8s_deployments(Mock())
    assert len(result) == 2


@patch("src.dependencies.k8_wrapper.get_k8s_app_client")
def test_delete_deployment(mock_get_k8s_app_client):
    mock_get_k8s_app_client.return_value.delete_namespaced_deployment.return_value = "success"
    result = delete_deployment(Mock(), sample_module_name, sample_git_commit_hash)
    assert result.startswith("d-test-module-1234567")


@patch("src.dependencies.k8_wrapper.get_k8s_app_client")
@patch("src.dependencies.k8_wrapper.query_k8s_deployment_status")
def test_scale_replicas(mock_query_k8s_deployment_status, mock_get_k8s_app_client):
    # Mocking the deployment returned by query_k8s_deployment_status
    mock_deployment = Mock(spec=client.V1Deployment)
    mock_deployment.spec.replicas = 1
    mock_query_k8s_deployment_status.return_value = mock_deployment

    # Mocking the deployment returned by replace_namespaced_deployment to have 2 replicas
    mock_updated_deployment = Mock(spec=client.V1Deployment)
    mock_updated_deployment.spec.replicas = 2
    mock_get_k8s_app_client.return_value.replace_namespaced_deployment.return_value = mock_updated_deployment

    result = scale_replicas(Mock(), sample_module_name, sample_git_commit_hash, 2)
    assert result.spec.replicas == 2


@patch("src.dependencies.k8_wrapper.get_k8s_core_client")
def test_get_logs_for_first_pod_in_deployment(mock_get_k8s_core_client):
    mock_pod = Mock()
    mock_pod.metadata.name = "pod1"
    mock_get_k8s_core_client.return_value.list_namespaced_pod.return_value.items = [mock_pod]
    mock_get_k8s_core_client.return_value.read_namespaced_pod_log.return_value = "Line1 Line2"
    pod_name, logs = get_logs_for_first_pod_in_deployment(Mock(), sample_module_name, sample_git_commit_hash)
    assert pod_name == "pod1"
    assert logs == ["Line1 Line2"]


@pytest.mark.parametrize(
    "module_name, git_commit_hash, expected_deployment_name",
    [
        ("test_module", "1234567", "d-test-module-1234567-d"),
        ("test.module", "7654321", "d-test-module-7654321-d"),
        ("TEST_MODULE", "abcdefg", "d-test-module-abcdefg-d"),
        ("test@module", "7654321", "d-test-module-7654321-d"),
        ("test!module", "7654321", "d-test-module-7654321-d"),
        ("test*module", "7654321", "d-test-module-7654321-d"),
        ("test.module.with.many.dots", "7654321", "d-test-module-with-many-dots-7654321-d"),
        ("a" * 64, "1234567", "d-" + "a" * (63 - len(["d", "-", "-", "-", "d"]) - 7) + "-1234567-d"),
        ("", "1234567", "d--1234567-d"),
    ],
)
def test_sanitize_deployment_name(module_name, git_commit_hash, expected_deployment_name):
    # When we sanitize the deployment name
    deployment_name, _ = _sanitize_deployment_name(module_name, git_commit_hash)
    # Then the deployment name should match the expected format
    assert deployment_name == expected_deployment_name
    assert len(deployment_name) <= 63


# THESE TESTS SUCK, AND SHOULD BE INTEGRATION TESTS INSTEAD
