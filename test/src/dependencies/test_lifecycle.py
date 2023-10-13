import logging
import re
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from kubernetes.client import ApiException

from clients.baseclient import ServerError
from dependencies import lifecycle
from models import ServiceStatus, DynamicServiceStatus
from test.src.dependencies import test_helpers as tlh


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
    s = mock_request.app.state.settings

    expected_environ_map = {
        "KBASE_ENDPOINT": s.kbase_services_endpoint,
        "AUTH_SERVICE_URL": s.auth_legacy_url,
        "AUTH_SERVICE_URL_ALLOW_INSECURE": "false",
        "KBASE_SECURE_CONFIG_PARAM_test_secure_param_name": "test_secure_param_value",
    }
    for item in expected_environ_map:
        assert expected_environ_map[item] == envs[item]


@patch("dependencies.lifecycle.scale_replicas")
@patch("dependencies.lifecycle.get_service_status_with_retries")
@patch("dependencies.lifecycle._create_cluster_ip_service_helper")
@patch("dependencies.lifecycle._update_ingress_for_service_helper")
@patch("dependencies.lifecycle._setup_metadata")
@patch("dependencies.lifecycle._create_and_launch_deployment_helper")
def test_start_deployment(
    _create_and_launch_deployment_helper_mock,
    _setup_metadata_mock,
    _update_ingress_for_service_helper_mock,
    _create_cluster_ip_service_helper_mock,
    get_service_status_with_retries_mock,
    scale_replicas_mock,
    mock_request,
):
    # Test Deployment Does Not Already exist, no need to scale replicas
    _create_and_launch_deployment_helper_mock.return_value = False
    _setup_metadata_mock.return_value = {}, {}
    get_service_status_with_retries_mock.return_value = tlh.get_stopped_deployment_status("tester")

    rv = lifecycle.start_deployment(request=mock_request, module_name="test_module", module_version="dev")
    scale_replicas_mock.assert_not_called()
    assert rv == tlh.get_stopped_deployment_status("tester")

    # Test Deployment Already Exists, need to scale instead of recreate
    _create_and_launch_deployment_helper_mock.return_value = True
    lifecycle.start_deployment(request=mock_request, module_name="test_module", module_version="dev")
    scale_replicas_mock.assert_called_once()  #


@patch("dependencies.lifecycle.create_and_launch_deployment")
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


@patch("dependencies.lifecycle.create_clusterip_service")
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


@patch("dependencies.lifecycle.update_ingress_to_point_to_service")
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


@patch("dependencies.lifecycle.scale_replicas")
def test_stop_deployment(mock_scale_replicas, mock_request):
    mock_request.state.user_auth_roles.is_admin_or_owner.return_value = False
    with pytest.raises(ServerError) as e:
        lifecycle.stop_deployment(request=mock_request, module_name="test_module", module_version="test_version")
    assert mock_request.state.user_auth_roles.is_admin_or_owner.call_count == 1
    assert e.value.code == -32000
    assert e.value.message == "Only admins or module owners can stop dynamic services"

    mock_request.state.user_auth_roles.is_admin_or_owner.return_value = True

    deployment = tlh.create_sample_deployment(deployment_name="test_deployment_name", replicas=0, ready_replicas=0, available_replicas=0, unavailable_replicas=0)

    mock_scale_replicas.return_value = deployment

    rv = lifecycle.stop_deployment(request=mock_request, module_name="test_module", module_version="test_version")

    dds = DynamicServiceStatus(
        git_commit_hash="test_hash",
        status=ServiceStatus.STOPPED,
        version="test_version",
        hash="test_hash",
        release_tags=["test_tag"],
        url="https://ci.kbase.us/dynamic_services/test_module.test_hash",
        module_name="test_module",
        health=ServiceStatus.STOPPED,
        up=0,
        deployment_name="test_deployment_name",
        replicas=0,
        updated_replicas=0,
        ready_replicas=0,
        available_replicas=0,
        unavailable_replicas=0,
    )
    assert rv == dds
