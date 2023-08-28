import logging
import re
from unittest.mock import Mock, patch

import pytest
from fastapi import Request, HTTPException
from kubernetes.client import ApiException

from src.clients.CachedCatalogClient import CachedCatalogClient
from src.configs.settings import get_settings
from src.dependencies import lifecycle
from test.src.dependencies import test_lifecycle_helpers as tlh


def _get_mock_request():
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
    return request


@pytest.fixture
def mock_request():
    return _get_mock_request()


def test_simple_get_volume_mounts(mock_request):
    mock_request.app.state.catalog_client.list_service_volume_mounts.return_value = [
        {"host_dir": "host1", "container_dir": "container1", "read_only": 1},
        {"host_dir": "host2", "container_dir": "container2", "read_only": 0},
    ]
    result = lifecycle.get_volume_mounts(mock_request, None, None)
    expected_result = ["host1:container1:ro", "host2:container2:rw"]
    assert result == expected_result


def test_simple_setup_metadata():
    module_name = "test_module"
    requested_module_version = "1.0"
    git_commit_hash = "hash123"
    version = "1.0"
    git_url = "https://github.com/test/repo"

    labels, annotations = lifecycle._setup_metadata(module_name, requested_module_version, git_commit_hash, version, git_url)
    assert labels == {
        "us.kbase.dynamicservice": "true",
        "us.kbase.module.git_commit_hash": git_commit_hash,
        "us.kbase.module.module_name": module_name.lower(),
    }
    assert annotations == {
        "git_commit_hash": git_commit_hash,
        "module_name": module_name,
        "module_version_from_request": requested_module_version,
        "us.kbase.catalog.moduleversion": version,
        "description": re.sub(r"^(https?://)", "", git_url),
        "k8s_deployment_name": "to_be_overwritten",
        "k8s_service_name": "to_be_overwritten",
    }


def test_simple_get_env(mock_request):
    envs = lifecycle.get_env(request=mock_request, module_name=None, module_version=None)
    s = get_settings()

    expected_environ_map = {
        "KBASE_ENDPOINT": s.kbase_services_endpoint,
        "AUTH_SERVICE_URL": s.auth_legacy_url,
        "AUTH_SERVICE_URL_ALLOW_INSECURE": "false",
        "KBASE_SECURE_CONFIG_PARAM_test_secure_param_name": "test_secure_param_value",
    }
    for item in expected_environ_map:
        assert expected_environ_map[item] == envs[item]


@patch("src.dependencies.lifecycle.scale_replicas")
@patch("src.dependencies.lifecycle.get_service_status_with_retries")
@patch("src.dependencies.lifecycle._create_cluster_ip_service_helper")
@patch("src.dependencies.lifecycle._update_ingress_for_service_helper")
@patch("src.dependencies.lifecycle._setup_metadata")
@patch("src.dependencies.lifecycle._create_and_launch_deployment_helper")
def test_start_deployment(
    _create_and_launch_deployment_helper_mock,
    _setup_metadata_mock,
    _update_ingress_for_service_helper_mock,
    _create_cluster_ip_service_helper_mock,
    get_service_status_with_retries_mock,
    scale_replicas_mock,
):
    # Test Deployment Does Not Already exist, no need to scale replicas
    _create_and_launch_deployment_helper_mock.return_value = False
    _setup_metadata_mock.return_value = {}, {}
    get_service_status_with_retries_mock.return_value = tlh.get_stopped_deployment("tester")
    mock_request = _get_mock_request()
    rv = lifecycle.start_deployment(request=mock_request, module_name="test_module", module_version="dev")
    scale_replicas_mock.assert_not_called()
    assert rv == tlh.get_stopped_deployment("tester")

    # Test Deployment Already Exists, need to scale instead of recreate
    _create_and_launch_deployment_helper_mock.return_value = True
    lifecycle.start_deployment(request=mock_request, module_name="test_module", module_version="dev")
    scale_replicas_mock.assert_called_once()  #


@patch("src.dependencies.lifecycle.create_and_launch_deployment")
def test__create_and_launch_deployment_helper(mock_create_and_launch, mock_request):
    # Test truthiness based on api exception
    module_name = "test_module"
    git_commit_hash = "hash123"
    image = "test_image"
    labels = {}
    annotations = {}
    env = {}
    mounts = []

    mock_exception = ApiException(status=409)
    mock_create_and_launch.side_effect = mock_exception

    # Act
    result = lifecycle._create_and_launch_deployment_helper(
        annotations=annotations, env=env, image=image, labels=labels, module_git_commit_hash=git_commit_hash, module_name=module_name, mounts=mounts, request=mock_request
    )

    # Assert
    assert result is True

    mock_create_and_launch.side_effect = None
    result = lifecycle._create_and_launch_deployment_helper(
        annotations=annotations, env=env, image=image, labels=labels, module_git_commit_hash=git_commit_hash, module_name=module_name, mounts=mounts, request=mock_request
    )
    assert result is False

    with pytest.raises(HTTPException) as e:
        mock_create_and_launch.side_effect = ApiException(status=500)
        lifecycle._create_and_launch_deployment_helper(
            annotations=annotations, env=env, image=image, labels=labels, module_git_commit_hash=git_commit_hash, module_name=module_name, mounts=mounts, request=mock_request
        )
    assert e.value.status_code == 500


@patch("src.dependencies.lifecycle.create_clusterip_service")
@patch.object(logging, "warning")
def test__create_cluster_ip_service_helper(mock_logging_warning, mock_create_clusterip_service, mock_request):
    # Test truthiness based on api exception
    module_name = "test_module"
    git_commit_hash = "hash123"
    labels = {}

    mock_create_clusterip_service.side_effect = None
    lifecycle._create_cluster_ip_service_helper(request=mock_request, module_name=module_name, catalog_git_commit_hash=git_commit_hash, labels=labels)
    assert mock_create_clusterip_service.call_count == 1
    assert mock_logging_warning.call_count == 0

    mock_create_clusterip_service.side_effect = ApiException(status=409)
    lifecycle._create_cluster_ip_service_helper(request=mock_request, module_name=module_name, catalog_git_commit_hash=git_commit_hash, labels=labels)
    mock_logging_warning.assert_called_once_with("Service already exists, skipping creation")
    assert mock_logging_warning.call_count == 1
    assert mock_create_clusterip_service.call_count == 2

    with pytest.raises(HTTPException) as e:
        mock_create_clusterip_service.side_effect = ApiException(status=500)
        lifecycle._create_cluster_ip_service_helper(request=mock_request, module_name=module_name, catalog_git_commit_hash=git_commit_hash, labels=labels)
    assert e.value.status_code == 500
    assert mock_logging_warning.call_count == 1
    assert mock_create_clusterip_service.call_count == 3


@patch("src.dependencies.lifecycle.update_ingress_to_point_to_service")
@patch.object(logging, "warning")
def test_create_and_launch_deployment_helper(mock_logging_warning, mock_update_ingress_to_point_to_service, mock_request):
    # Test truthiness based on api exception
    module_name = "test_module"
    git_commit_hash = "hash123"

    mock_update_ingress_to_point_to_service.side_effect = None
    lifecycle._update_ingress_for_service_helper(request=mock_request, module_name=module_name, git_commit_hash=git_commit_hash)
    assert mock_update_ingress_to_point_to_service.call_count == 1
    assert mock_logging_warning.call_count == 0

    mock_update_ingress_to_point_to_service.side_effect = ApiException(status=409)
    lifecycle._update_ingress_for_service_helper(request=mock_request, module_name=module_name, git_commit_hash=git_commit_hash)
    assert mock_update_ingress_to_point_to_service.call_count == 2
    assert mock_logging_warning.call_count == 1
    mock_logging_warning.assert_called_once_with("Ingress already exists, skipping creation")

    with pytest.raises(HTTPException) as e:
        mock_update_ingress_to_point_to_service.side_effect = ApiException(status=500)
        lifecycle._update_ingress_for_service_helper(request=mock_request, module_name=module_name, git_commit_hash=git_commit_hash)
    assert e.value.status_code == 500
    assert mock_update_ingress_to_point_to_service.call_count == 3
    assert mock_logging_warning.call_count == 1


#
# @patch("src.dependencies.lifecycle.get_service_status_with_retries")
# @patch("src.dependencies.lifecycle._update_ingress_for_service_helper")
# @patch("src.dependencies.lifecycle._create_cluster_ip_service_helper")
# @patch("src.dependencies.lifecycle._create_and_launch_deployment_helper")
# @patch("src.dependencies.lifecycle.get_env")
# @patch("src.dependencies.lifecycle.get_volume_mounts")
# @patch("src.dependencies.lifecycle._setup_metadata")
# def test_start_deployment_existing(
#         mock_setup_metadata, mock_get_volume_mounts, mock_get_env,
#         mock_create_and_launch, mock_create_cluster_ip, mock_update_ingress,
#         mock_get_status, mock_request):
#     # Arrange
#     module_name = "test_module"
#     module_version = "1.0"
#
#     mock_setup_metadata.return_value = ({}, {})
#     mock_get_volume_mounts.return_value = []
#     mock_get_env.return_value = {}
#     mock_create_and_launch.return_value = False
#     mock_create_cluster_ip.return_value = None
#     mock_update_ingress.return_value = None
#     mock_get_status.return_value = tlh.get_running_deployment(deployment_name="test_existing_deployment")
#
#     # Act
#     result = start_deployment(mock_request, module_name, module_version)
#
#     # Assert
#     assert isinstance(result, DynamicServiceStatus)
#
#
#
#
#
#
