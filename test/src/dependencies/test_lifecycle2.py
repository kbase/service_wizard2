#
# from unittest.mock import patch
#
# import pytest
#
# from src.dependencies.lifecycle import get_env, get_volume_mounts, _setup_metadata, _create_and_launch_deployment_helper, \
#     _create_cluster_ip_service_helper, _update_ingress_for_service_helper, start_deployment, stop_deployment
#
#

#
# def test_get_volume_mounts_success():
#     # Mocking the response from the KBase Catalog to simulate valid volume mount data
#     mock_response = [
#         {
#             'volume_name': 'test_volume',
#             'mount_path': '/test/path',
#             'read_only': False
#         }
#     ]
#     with patch('src.dependencies.lifecycle.get_catalog_volume_mounts', return_value=mock_response):
#         mounts = get_volume_mounts('test_module')
#         assert len(mounts) == 1
#         assert mounts[0].name == 'test_volume'
#         assert mounts[0].mount_path == '/test/path'
#         assert mounts[0].read_only == False
#
# def test_get_volume_mounts_invalid_data():
#     # Mocking an invalid response from the KBase Catalog
#     mock_response = [
#         {
#             'invalid_key': 'test_volume',
#             'mount_path': '/test/path'
#         }
#     ]
#     with patch('src.dependencies.lifecycle.get_catalog_volume_mounts', return_value=mock_response):
#         with pytest.raises(Exception, match="Invalid data from KBase Catalog"):
#             get_volume_mounts('test_module')
#
#
#
# def test_setup_metadata_success():
#     labels, annotations = _setup_metadata('test_module', 'test_version', 'test_commit')
#     assert labels['module-name'] == 'test_module'
#     assert labels['module-version'] == 'test_version'
#     assert labels['module-git-commit'] == 'test_commit'
#     assert annotations['module-name'] == 'test_module'
#     assert annotations['module-version'] == 'test_version'
#     assert annotations['module-git-commit'] == 'test_commit'
#
# def test_setup_metadata_missing_params():
#     labels, annotations = _setup_metadata('test_module', None, None)
#     assert labels['module-name'] == 'test_module'
#     assert 'module-version' not in labels
#     assert 'module-git-commit' not in labels
#     assert annotations['module-name'] == 'test_module'
#     assert 'module-version' not in annotations
#     assert 'module-git-commit' not in annotations
#
#
#
# def test_create_and_launch_deployment_helper_success():
#     # Mocking the necessary Kubernetes interactions
#     with patch('src.dependencies.lifecycle.some_k8s_function', return_value=True):
#         result = _create_and_launch_deployment_helper('test_params')
#         assert result is True
#
# def test_create_cluster_ip_service_helper_success():
#     # Mocking the necessary Kubernetes interactions
#     with patch('src.dependencies.lifecycle.some_k8s_function', return_value=True):
#         result = _create_cluster_ip_service_helper('test_params')
#         assert result is True
#
# def test_update_ingress_for_service_helper_success():
#     # Mocking the necessary Kubernetes interactions
#     with patch('src.dependencies.lifecycle.some_k8s_function', return_value=True):
#         result = _update_ingress_for_service_helper('test_params')
#         assert result is True
#
# # Additional tests can be added for failure scenarios, exceptions, etc.
#
#
#
# def test_start_deployment_success():
#     # Mocking the necessary functions and interactions for a successful deployment start
#     with patch('src.dependencies.lifecycle.some_k8s_function', return_value=True),          patch('src.dependencies.lifecycle.some_other_function', return_value=True):
#         result = start_deployment('test_module', 'test_version', 1)
#         # Assertions to check successful deployment start
#
# def test_start_deployment_service_exists():
#     # Mocking the scenario where the service already exists
#     with patch('src.dependencies.lifecycle.some_k8s_function', return_value=True):
#         with pytest.raises(Exception, match="Service already exists"):
#             start_deployment('test_module', 'test_version', 1)
#
# def test_stop_deployment_success():
#     # Mocking the necessary functions and interactions for a successful deployment stop
#     with patch('src.dependencies.lifecycle.some_k8s_function', return_value=True),          patch('src.dependencies.lifecycle.some_other_function', return_value=True):
#         result = stop_deployment('test_module', 'test_version')
#         # Assertions to check successful deployment stop
#
# def test_stop_deployment_no_rights():
#     # Mocking the scenario where the user doesn't have the necessary rights
#     with patch('src.dependencies.lifecycle.some_k8s_function', return_value=False):
#         with pytest.raises(Exception, match="User does not have rights"):
#             stop_deployment('test_module', 'test_version')
#
# # Additional tests can be added for other scenarios, exceptions, etc.
