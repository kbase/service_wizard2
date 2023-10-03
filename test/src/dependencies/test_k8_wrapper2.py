# from unittest.mock import Mock, patch
#
# import pytest
# from kubernetes import client
#
# from dependencies.k8_wrapper import (
#     create_clusterip_service,
#     sanitize_deployment_name,
#     update_ingress_to_point_to_service,
#     create_and_launch_deployment,
#     query_k8s_deployment_status,
#     get_k8s_deployments,
#     delete_deployment,
#     scale_replicas,
#     get_logs_for_first_pod_in_deployment,
#     get_k8s_deployment_status_from_label,
# )
#
# # Sample Data
# sample_module_name = "test_module"
# sample_git_commit_hash = "1234567"
# sample_image = "test_image"
# sample_labels = {"test_label": "label_value"}
# sample_annotations = {"test_annotation": "annotation_value"}
# sample_env = {"TEST_ENV": "value"}
# sample_mounts = ["/host/path:/container/path:ro"]
#
#
# # New Tests
# @patch("dependencies.k8_wrapper.get_k8s_core_client")
# def test_create_clusterip_service(mock_get_k8s_core_client):
#     mock_get_k8s_core_client.return_value.create_namespaced_service.return_value = "success"
#     result = create_clusterip_service(Mock(), sample_module_name, sample_git_commit_hash, sample_labels)
#     assert result == "success"
#
#
# @patch("dependencies.k8_wrapper._ensure_ingress_exists")
# @patch("dependencies.k8_wrapper.get_k8s_networking_client")
# def test_update_ingress_to_point_to_service(mock_get_k8s_networking_client, mock_ensure_ingress_exists):
#     mock_ingress = Mock()
#     mock_rule = Mock()
#     mock_rule.http = None
#     mock_ingress.spec.rules = [mock_rule]
#
#     mock_ensure_ingress_exists.return_value = mock_ingress
#
#     mock_request = Mock()
#     mock_request.app.state.settings.external_ds_url = "https://example.com/ds"
#
#     update_ingress_to_point_to_service(mock_request, sample_module_name, sample_git_commit_hash)
#
#     mock_get_k8s_networking_client.assert_called_once()
#
#
# @patch("dependencies.k8_wrapper.get_k8s_app_client")
# def test_create_and_launch_deployment(mock_get_k8s_app_client):
#     mock_get_k8s_app_client.return_value.create_namespaced_deployment.return_value = "success"
#     result = create_and_launch_deployment(Mock(), sample_module_name, sample_git_commit_hash, sample_image, sample_labels, sample_annotations, sample_env, sample_mounts)
#     assert isinstance(result, client.V1LabelSelector)
#
# #
# # @patch("dependencies.k8_wrapper.check_service_status_cache")
# # @patch("dependencies.k8_wrapper._get_deployment_status")
# # def test_query_k8s_deployment_status(
# #     mock__get_deployment_status,
# #     mock_check_service_status_cache,
# #     mock_request,
# # ):
# #     module_info = mock_request.app.state.mock_module_info
# #     module_name = module_info["module_name"]
# #     module_git_commit_hash = module_info["git_commit_hash"]
# #     result = query_k8s_deployment_status(mock_request, module_name, module_git_commit_hash)
# #     assert mock__get_deployment_status.call_count == 1
# #     assert mock__get_deployment_status.called_with(mock_request, module_name, module_git_commit_hash)
# #
# #     assert result == module_info
# #     # ls = label_selector: client.V1Labe    lSelector
# #     selector = client.V1LabelSelector(match_labels={"app": "d-test-module-1234567"})
# #     result = get_k8s_deployment_status_from_label(Mock(), selector)
# #     assert result == "deployment1"
# #     # Assert that _get_deployment_status was called with the deployment
# #     """
# #     def query_k8s_deployment_status(request, module_name, module_git_commit_hash) -> client.V1Deployment:
# #     label_selector_text = f"us.kbase.module.module_name={module_name.lower()}," + f"us.kbase.module.git_commit_hash={module_git_commit_hash}"
# #     return _get_deployment_status(request, label_selector_text)
# #
# #
# #     def get_k8s_deployment_status_from_label(request, label_selector: client.V1LabelSelector) -> client.V1Deployment:
# #         label_selector_text = ",".join([f"{key}={value}" for key, value in label_selector.match_labels.items()])
# #         return _get_deployment_status(request, label_selector_text)
# #
# #     """
# #     assert mock__get_deployment_status.call_count == 2
# #
# #     # Mock the service status cache to return None
# #
# #     # mock_check_service_status_cache.return_value = "deployment1"
# #     # mock__get_deployment_status.return_value = LRUCache(ttl=10)
# #
# #     # Mock the Kubernetes client to return the deployment
# #
# #     # mock_get_k8s_app_client.return_value.list_namespaced_deployment.return_value.items = ["deployment1"]
# #
#
# @patch("dependencies.k8_wrapper._get_deployment_status")
# @patch("dependencies.k8_wrapper.check_service_status_cache")
# def test_query_k8s_deployment_status2(mock_check_service_status_cache, mock__get_deployment_status):
#     # Mock the service status cache to return "deployment1"
#     mock_check_service_status_cache.return_value = "deployment1"
#
#     # Mock the _get_deployment_status to return "deployment1"
#     mock__get_deployment_status.return_value = "deployment1"
#
#     # Call the function and assert its result
#     request_obj = Mock()
#     result = query_k8s_deployment_status(request_obj, sample_module_name, sample_git_commit_hash)
#     assert result == "deployment1"
#
#     expected_label1 = f"us.kbase.module.module_name={sample_module_name.lower()},us.kbase.module.git_commit_hash={sample_git_commit_hash}"
#     mock__get_deployment_status.assert_called_with(request_obj, expected_label1)
#
#     # Create a label selector
#     selector = client.V1LabelSelector(match_labels={"app": "d-test-module-1234567"})
#     result = get_k8s_deployment_status_from_label(request_obj, selector)
#     assert result == "deployment1"
#
#     expected_label2 = "app=d-test-module-1234567"
#     mock__get_deployment_status.assert_called_with(request_obj, expected_label2)
#
#     # Assert that _get_deployment_status was called twice
#     assert mock__get_deployment_status.call_count == 2
#
#
# @patch("dependencies.k8_wrapper._get_deployment_status")
# @patch("dependencies.k8_wrapper.check_service_status_cache")
# def test_combined_query_k8s_deployment_status(mock_check_service_status_cache, mock__get_deployment_status):
#     # Mock the service status cache to return "deployment1"
#     mock_check_service_status_cache.return_value = "deployment1"
#
#     # Mock the _get_deployment_status to return "deployment1"
#     mock__get_deployment_status.return_value = "deployment1"
#
#     # Call the function and assert its result
#     request_obj = Mock()
#     result = query_k8s_deployment_status(request_obj, sample_module_name, sample_git_commit_hash)
#     assert result == "deployment1"
#
#     expected_label1 = f"us.kbase.module.module_name={sample_module_name.lower()},us.kbase.module.git_commit_hash={sample_git_commit_hash}"
#     mock__get_deployment_status.assert_called_with(request_obj, expected_label1)
#
#     # Create a label selector
#     selector = client.V1LabelSelector(match_labels={"app": "d-test-module-1234567"})
#     result = get_k8s_deployment_status_from_label(request_obj, selector)
#     assert result == "deployment1"
#
#     expected_label2 = "app=d-test-module-1234567"
#     mock__get_deployment_status.assert_called_with(request_obj, expected_label2)
#
#     # Assert that _get_deployment_status was called twice
#     assert mock__get_deployment_status.call_count == 2
#
#
# @patch("dependencies.k8_wrapper.get_k8s_all_service_status_cache")
# @patch("dependencies.k8_wrapper.get_k8s_app_client")
# def test_get_k8s_deployments(mock_get_k8s_app_client, mock_get_k8s_all_service_status_cache):
#     # Mock the all service status cache to return None
#     mock_cache = Mock()
#     mock_cache.get.return_value = None
#     mock_get_k8s_all_service_status_cache.return_value = mock_cache
#
#     # Mock the Kubernetes client to return the deployments
#     mock_get_k8s_app_client.return_value.list_namespaced_deployment.return_value.items = ["deployment1", "deployment2"]
#
#     result = get_k8s_deployments(Mock())
#     assert len(result) == 2
#
#
# @patch("dependencies.k8_wrapper.get_k8s_app_client")
# def test_delete_deployment(mock_get_k8s_app_client):
#     mock_get_k8s_app_client.return_value.delete_namespaced_deployment.return_value = "success"
#     result = delete_deployment(Mock(), sample_module_name, sample_git_commit_hash)
#     assert result.startswith("d-test-module-1234567")
#
#
# @patch("dependencies.k8_wrapper.get_k8s_app_client")
# @patch("dependencies.k8_wrapper.query_k8s_deployment_status")
# def test_scale_replicas(mock_query_k8s_deployment_status, mock_get_k8s_app_client):
#     # Mocking the deployment returned by query_k8s_deployment_status
#     mock_deployment = Mock(spec=client.V1Deployment)
#     mock_deployment.spec.replicas = 1
#     mock_query_k8s_deployment_status.return_value = mock_deployment
#
#     # Mocking the deployment returned by replace_namespaced_deployment to have 2 replicas
#     mock_updated_deployment = Mock(spec=client.V1Deployment)
#     mock_updated_deployment.spec.replicas = 2
#     mock_get_k8s_app_client.return_value.replace_namespaced_deployment.return_value = mock_updated_deployment
#
#     result = scale_replicas(Mock(), sample_module_name, sample_git_commit_hash, 2)
#     assert result.spec.replicas == 2
#
#
# @patch("dependencies.k8_wrapper.get_k8s_core_client")
# def test_get_logs_for_first_pod_in_deployment(mock_get_k8s_core_client):
#     mock_pod = Mock()
#     mock_pod.metadata.name = "pod1"
#     mock_get_k8s_core_client.return_value.list_namespaced_pod.return_value.items = [mock_pod]
#     mock_get_k8s_core_client.return_value.read_namespaced_pod_log.return_value = "Line1 Line2"
#     pod_name, logs = get_logs_for_first_pod_in_deployment(Mock(), sample_module_name, sample_git_commit_hash)
#     assert pod_name == "pod1"
#     assert logs == ["Line1 Line2"]
#
#
# @pytest.mark.parametrize(
#     "module_name, git_commit_hash, expected_deployment_name",
#     [
#         ("test_module", "1234567", "d-test-module-1234567-d"),
#         ("test.module", "7654321", "d-test-module-7654321-d"),
#         ("TEST_MODULE", "abcdefg", "d-test-module-abcdefg-d"),
#         ("test@module", "7654321", "d-test-module-7654321-d"),
#         ("test!module", "7654321", "d-test-module-7654321-d"),
#         ("test*module", "7654321", "d-test-module-7654321-d"),
#         ("test.module.with.many.dots", "7654321", "d-test-module-with-many-dots-7654321-d"),
#         ("a" * 64, "1234567", "d-" + "a" * (63 - len("d---d") - 7) + "-1234567-d"),
#         ("", "1234567", "d--1234567-d"),
#     ],
# )
# def test_sanitize_deployment_name(module_name, git_commit_hash, expected_deployment_name):
#     # When we sanitize the deployment name
#     deployment_name, _ = sanitize_deployment_name(module_name, git_commit_hash)
#     # Then the deployment name should match the expected format
#     assert deployment_name == expected_deployment_name
#     assert len(deployment_name) <= 63
