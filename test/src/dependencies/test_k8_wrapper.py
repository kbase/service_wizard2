from unittest.mock import Mock, patch, MagicMock, call

import pytest
from kubernetes import client
from kubernetes.client import ApiException

from dependencies.k8_wrapper import (
    create_clusterip_service,
    sanitize_deployment_name,
    update_ingress_to_point_to_service,
    create_and_launch_deployment,
    query_k8s_deployment_status,
    get_k8s_deployments,
    delete_deployment,
    scale_replicas,
    get_logs_for_first_pod_in_deployment,
    get_k8s_deployment_status_from_label,
    get_pods_in_namespace,
)

# Sample Data
sample_module_name = "test_module"
sample_git_commit_hash = "1234567"
sample_image = "test_image"
sample_labels = {"test_label": "label_value"}
sample_annotations = {"test_annotation": "annotation_value"}
sample_env = {"TEST_ENV": "value"}
sample_mounts = ["/host/path:/container/path:ro"]


# Create and set up the mock objects
@pytest.fixture(autouse=True)
def mock_ingress():
    mock_ingress = Mock()
    mock_spec = Mock()
    mock_rule = Mock()
    mock_rule.http = None
    mock_spec.rules = [mock_rule]
    mock_ingress.spec = mock_spec
    return mock_ingress


# New Tests
@patch("dependencies.k8_wrapper.get_k8s_core_client")
def test_create_clusterip_service(mock_get_k8s_core_client):
    mock_get_k8s_core_client.return_value.create_namespaced_service.return_value = "success"
    result = create_clusterip_service(Mock(), sample_module_name, sample_git_commit_hash, sample_labels)
    assert result == "success"


@patch("dependencies.k8_wrapper._update_ingress_with_retries")
@patch("dependencies.k8_wrapper.sanitize_deployment_name", return_value=("deployment_name", "service_name"))
@patch("dependencies.k8_wrapper._ensure_ingress_exists")
def test_update_ingress_to_point_to_service(mock_ensure_ingress_exists, mock_sanitize_deployment_name, mock_update_ingress_with_retries, mock_request, mock_ingress):
    mock_ensure_ingress_exists.return_value = mock_ingress
    mock_request.app.state.settings.external_ds_url = "https://example.com/ds"
    update_ingress_to_point_to_service(mock_request, sample_module_name, sample_git_commit_hash)
    assert mock_sanitize_deployment_name.called_with(sample_module_name, sample_git_commit_hash)
    assert mock_update_ingress_with_retries.called_with(mock_request, mock_ingress, "service_name", "deployment_name", "https://example.com/ds")


@patch("dependencies.k8_wrapper.sanitize_deployment_name", return_value=("deployment_name", "service_name"))
@patch("dependencies.k8_wrapper._ensure_ingress_exists", side_effect=ApiException(status=409, reason="Conflict"))
@patch("time.sleep", Mock())  # Disable sleep
def test_update_ingress_to_point_to_service_with_exception(mock_ensure_ingress_exists, mock_sanitize_deployment_name, mock_request, mock_ingress):
    mock_ensure_ingress_exists.return_value = mock_ingress
    mock_request.app.state.settings.external_ds_url = "https://example.com/ds"
    # Second call which should raise exception
    with pytest.raises(ApiException):
        update_ingress_to_point_to_service(mock_request, sample_module_name, sample_git_commit_hash)


@patch("dependencies.k8_wrapper.get_k8s_app_client")
def test_create_and_launch_deployment(mock_get_k8s_app_client):
    mock_get_k8s_app_client.return_value.create_namespaced_deployment.return_value = "success"
    result = create_and_launch_deployment(Mock(), sample_module_name, sample_git_commit_hash, sample_image, sample_labels, sample_annotations, sample_env, sample_mounts)
    assert isinstance(result, client.V1LabelSelector)


@patch("dependencies.k8_wrapper._get_deployment_status")
@patch("dependencies.k8_wrapper.check_service_status_cache")
def test_query_k8s_deployment_status(mock_check_service_status_cache, mock__get_deployment_status, mock_request):
    # Mock the service status cache to return "deployment1"
    mock_check_service_status_cache.return_value = "deployment1"
    # Mock the _get_deployment_status to return "deployment1"
    mock__get_deployment_status.return_value = "deployment1"

    # Call the function and assert its result
    request_obj = mock_request
    result = query_k8s_deployment_status(request_obj, sample_module_name, sample_git_commit_hash)
    assert result == "deployment1"

    expected_label1 = f"us.kbase.module.module_name={sample_module_name.lower()},us.kbase.module.git_commit_hash={sample_git_commit_hash}"
    mock__get_deployment_status.assert_called_with(request_obj, expected_label1)

    # Create a label selector
    selector = client.V1LabelSelector(match_labels={"app": "d-test-module-1234567"})
    result = get_k8s_deployment_status_from_label(request_obj, selector)
    assert result == "deployment1"

    expected_label2 = "app=d-test-module-1234567"
    mock__get_deployment_status.assert_called_with(request_obj, expected_label2)

    # Assert that _get_deployment_status was called twice
    assert mock__get_deployment_status.call_count == 2


@patch("dependencies.k8_wrapper._get_deployment_status")
@patch("dependencies.k8_wrapper.check_service_status_cache")
def test_combined_query_k8s_deployment_status(mock_check_service_status_cache, mock__get_deployment_status):
    # Mock the service status cache to return "deployment1"
    mock_check_service_status_cache.return_value = "deployment1"

    # Mock the _get_deployment_status to return "deployment1"
    mock__get_deployment_status.return_value = "deployment1"

    # Call the function and assert its result
    request_obj = Mock()
    result = query_k8s_deployment_status(request_obj, sample_module_name, sample_git_commit_hash)
    assert result == "deployment1"

    expected_label1 = f"us.kbase.module.module_name={sample_module_name.lower()},us.kbase.module.git_commit_hash={sample_git_commit_hash}"
    mock__get_deployment_status.assert_called_with(request_obj, expected_label1)

    # Create a label selector
    selector = client.V1LabelSelector(match_labels={"app": "d-test-module-1234567"})
    result = get_k8s_deployment_status_from_label(request_obj, selector)
    assert result == "deployment1"

    expected_label2 = "app=d-test-module-1234567"
    mock__get_deployment_status.assert_called_with(request_obj, expected_label2)

    # Assert that _get_deployment_status was called twice
    assert mock__get_deployment_status.call_count == 2


@patch("dependencies.k8_wrapper.get_k8s_all_service_status_cache")
@patch("dependencies.k8_wrapper.get_k8s_app_client")
def test_get_k8s_deployments(mock_get_k8s_app_client, mock_get_k8s_all_service_status_cache):
    # Mock the all service status cache to return None
    mock_cache = Mock()
    mock_cache.get.return_value = None
    mock_get_k8s_all_service_status_cache.return_value = mock_cache

    # Mock the Kubernetes client to return the deployments
    mock_get_k8s_app_client.return_value.list_namespaced_deployment.return_value.items = ["deployment1", "deployment2"]

    result = get_k8s_deployments(Mock())
    assert len(result) == 2


@patch("dependencies.k8_wrapper.get_k8s_app_client")
def test_delete_deployment(mock_get_k8s_app_client):
    mock_get_k8s_app_client.return_value.delete_namespaced_deployment.return_value = "success"
    result = delete_deployment(Mock(), sample_module_name, sample_git_commit_hash)
    assert result.startswith("d-test-module-1234567")


@patch("dependencies.k8_wrapper.get_k8s_app_client")
@patch("dependencies.k8_wrapper.query_k8s_deployment_status")
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


@patch("dependencies.k8_wrapper.get_k8s_core_client")
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
        ("a" * 64, "1234567", "d-" + "a" * (63 - len("d---d") - 7) + "-1234567-d"),
        ("", "1234567", "d--1234567-d"),
    ],
)
def test_sanitize_deployment_name(module_name, git_commit_hash, expected_deployment_name):
    # When we sanitize the deployment name
    deployment_name, _ = sanitize_deployment_name(module_name, git_commit_hash)
    # Then the deployment name should match the expected format
    assert deployment_name == expected_deployment_name
    assert len(deployment_name) <= 63


def test_get_pods_in_namespace(mock_request):
    field_selector = "test-field_selector"
    label_selector = "test-label-selector"
    namespace = mock_request.app.state.settings.namespace
    corev1api = MagicMock(autospec=client.CoreV1Api)
    get_pods_in_namespace(corev1api, field_selector=field_selector, label_selector=label_selector)
    assert corev1api.list_namespaced_pod.call_args == call(namespace, field_selector="test-field_selector", label_selector="test-label-selector")
