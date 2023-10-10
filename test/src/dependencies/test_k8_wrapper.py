import time
from unittest.mock import call, patch, MagicMock

import pytest
from cacheout import LRUCache
from kubernetes import client
from kubernetes.client import (
    V1Ingress,
    V1HTTPIngressRuleValue,
    V1IngressRule,
    V1IngressSpec,
    V1IngressBackend,
    V1HTTPIngressPath,
    V1Service,
    V1ServiceSpec,
    V1ServicePort,
    ApiException,
    V1LabelSelector,
)

from configs.settings import get_settings
from dependencies.k8_wrapper import (
    get_pods_in_namespace,
    v1_volume_mount_factory,
    sanitize_deployment_name,
    create_clusterip_service,
    update_ingress_to_point_to_service,
    path_exists_in_ingress,
    create_and_launch_deployment,
    query_k8s_deployment_status,
    get_k8s_deployment_status_from_label,
    get_k8s_deployments,
    delete_deployment,
    scale_replicas,
)

# Import the necessary Kubernetes client classes if not already imported


# Reusable Sample Data
field_selector = "test-field_selector"
label_selector = "test-label-selector"

# Sample Data
sample_module_name = "test_module"
sample_git_commit_hash = "1234567"
sample_image = "test_image"
sample_labels = {"test_label": "label_value"}
sample_annotations = {"test_annotation": "annotation_value"}
sample_env = {"TEST_ENV": "value"}
sample_mounts_ro = ["/host/path:/container/path:ro"]
sample_mounts_rw = ["/host/path:/container/path:ro"]

# Sample Kubernetes Objects
sample_deployment = client.V1Deployment(
    metadata=client.V1ObjectMeta(name="mock_deployment_name"),
    spec=client.V1DeploymentSpec(
        replicas=1,  # initial replica count
        selector=client.V1LabelSelector(match_labels={"key": "value"}),  # example selector
        template=client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"key": "value"}), spec=client.V1PodSpec(containers=[client.V1Container(name="container-name", image="container-image")])
        ),
    ),
)


def test_get_pods_in_namespace(mock_request):
    namespace = mock_request.app.state.settings.namespace
    corev1api = mock_request.app.state.k8_clients.corev1api
    get_pods_in_namespace(corev1api, field_selector=field_selector, label_selector=label_selector)
    assert corev1api.list_namespaced_pod.call_args == call(namespace, field_selector="test-field_selector", label_selector="test-label-selector")


def test_v1_volume_mount_factory():
    for mount in sample_mounts_ro, sample_mounts_rw:
        volumes, volume_mounts = v1_volume_mount_factory(mount)
        expected_volumes = [client.V1Volume(name=f"volume-{0}", host_path=client.V1HostPathVolumeSource(path=mount[0].split(":")[0]))]
        expected_volume_mounts = [client.V1VolumeMount(name=f"volume-{0}", mount_path=mount[0].split(":")[1], read_only=mount[0].split(":")[2] == "ro")]
        assert volumes == expected_volumes
        assert volume_mounts == expected_volume_mounts

    # Test for empty or None mounts
    for bad_mount in [[""], [None]]:
        with pytest.raises(ValueError, match="Empty mount provided"):
            v1_volume_mount_factory(bad_mount)

    # Test for mounts without 3 parts
    bad_format_mount = ["path1:/container1"]
    with pytest.raises(ValueError, match="Invalid mount format"):
        v1_volume_mount_factory(bad_format_mount)

    # Test for invalid ro/rw values
    invalid_ro_rw = ["path1:/container1:invalid"]
    with pytest.raises(ValueError, match="Invalid permission in mount"):
        v1_volume_mount_factory(invalid_ro_rw)

    # Test for mount with more than 3 parts
    extra_parts_mount = ["path1:/container1:ro:extra"]
    with pytest.raises(ValueError, match="Invalid mount format"):
        v1_volume_mount_factory(extra_parts_mount)

    # Test for multiple valid mounts
    multiple_mounts = ["path1:/container1:ro", "path2:/container2:rw"]
    volumes, volume_mounts = v1_volume_mount_factory(multiple_mounts)
    expected_volumes = [client.V1Volume(name=f"volume-{i}", host_path=client.V1HostPathVolumeSource(path=mount.split(":")[0])) for i, mount in enumerate(multiple_mounts)]
    expected_volume_mounts = [
        client.V1VolumeMount(name=f"volume-{i}", mount_path=mount.split(":")[1], read_only=mount.split(":")[2] == "ro") for i, mount in enumerate(multiple_mounts)
    ]
    assert volumes == expected_volumes
    assert volume_mounts == expected_volume_mounts


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
        ("a" * 64, "1234567", "d-" + "a" * (63 - len("d---d") - 7) + "-1234567-d"),  # Testing truncation for really long module names
    ],
)
def test_sanitize_deployment_name(module_name, git_commit_hash, expected_deployment_name):
    # When we sanitize the deployment name
    deployment_name, _ = sanitize_deployment_name(module_name, git_commit_hash)
    # Then the deployment name should match the expected format
    assert deployment_name == expected_deployment_name
    assert len(deployment_name) <= 63


@patch("dependencies.k8_wrapper.get_k8s_core_client")
def test_create_clusterip_service(mock_get_k8s_core_client, mock_request):
    mock_get_k8s_core_client.return_value.create_namespaced_service.return_value = "success"
    result = create_clusterip_service(mock_request, sample_module_name, sample_git_commit_hash, sample_labels)
    assert result == "success"

    # Also, let's assert that the mocked method was called with the expected parameters
    _, service_name = sanitize_deployment_name(sample_module_name, sample_git_commit_hash)
    mock_get_k8s_core_client.return_value.create_namespaced_service.assert_called_once_with(
        namespace=get_settings().namespace,
        body=V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=service_name, labels=sample_labels),
            spec=V1ServiceSpec(selector=sample_labels, ports=[V1ServicePort(port=5000, target_port=5000)], type="ClusterIP"),
        ),
    )


@patch("dependencies.k8_wrapper._ensure_ingress_exists")
def test_update_ingress_to_point_to_service(mock__ensure_ingress_exists, example_ingress, mock_request):
    # Good ingress, no exceptions
    mock__ensure_ingress_exists.return_value = example_ingress
    with patch("time.sleep"):
        update_ingress_to_point_to_service(mock_request, sample_module_name, sample_git_commit_hash)
        assert time.sleep.call_count == 0

    assert mock__ensure_ingress_exists.call_args == call(mock_request)

    # Ingress rules is None
    with patch("time.sleep"):
        # Force Initialize http attribute with an empty paths list if it is None
        example_ingress.spec.rules[0].http = None
        mock__ensure_ingress_exists.return_value = example_ingress
        update_ingress_to_point_to_service(mock_request, sample_module_name, sample_git_commit_hash)
        assert time.sleep.call_count == 0

    assert mock__ensure_ingress_exists.call_args == call(mock_request)

    # Unhandled exception
    api_exception = ApiException(408)
    mock__ensure_ingress_exists.side_effect = api_exception
    with pytest.raises(ApiException) as e:
        with patch("time.sleep"):
            update_ingress_to_point_to_service(mock_request, sample_module_name, sample_git_commit_hash)
        assert time.sleep.call_count == 0
    assert e.type == ApiException
    assert e.value == api_exception

    # Handled exception with a sleep to wait in case something else is changing ingress
    api_exception = ApiException(409)
    mock__ensure_ingress_exists.side_effect = api_exception
    with pytest.raises(ApiException) as e:
        with patch("time.sleep"):
            update_ingress_to_point_to_service(mock_request, sample_module_name, sample_git_commit_hash)
        assert time.sleep.call_count == 2
    assert e.type == ApiException
    assert e.value == api_exception


def test_ensure_ingress_exists(mock_request, example_ingress):
    with patch("time.sleep"), patch("dependencies.k8_wrapper.get_k8s_networking_client") as mock_get_k8s_networking_client:
        mock_networking_v1_api = MagicMock()
        mock_get_k8s_networking_client.return_value = mock_networking_v1_api
        mock_networking_v1_api.read_namespaced_ingress.return_value = example_ingress

        update_ingress_to_point_to_service(mock_request, sample_module_name, sample_git_commit_hash)

        mock_networking_v1_api.read_namespaced_ingress.assert_called_once_with(name="dynamic-services", namespace=mock_request.app.state.settings.namespace)

        # Non 404 case
        with pytest.raises(ApiException) as e:
            mock_networking_v1_api.read_namespaced_ingress.side_effect = ApiException(409, "Conflict")
            update_ingress_to_point_to_service(mock_request, sample_module_name, sample_git_commit_hash)
        assert e.type == ApiException
        assert e.value.status == 409

        # 404 case

        mock_networking_v1_api.read_namespaced_ingress.side_effect = ApiException(404, "Not Found")
        update_ingress_to_point_to_service(mock_request, sample_module_name, sample_git_commit_hash)
        assert mock_networking_v1_api.create_namespaced_ingress.call_count == 1

        # The fixture has this field filled  out, so delete it!
        example_ingress.spec.rules[0].http = None

        mock_networking_v1_api.create_namespaced_ingress.assert_called_once_with(namespace=mock_request.app.state.settings.namespace, body=example_ingress)


def test_path_exists_in_ingress():
    # 1. Test when the path exists
    test_path1 = "/test-path"
    http_paths = [V1HTTPIngressPath(path=test_path1, path_type="Prefix", backend=V1IngressBackend(service=None, resource=None))]

    ingress_spec = V1IngressSpec(rules=[V1IngressRule(host="host", http=V1HTTPIngressRuleValue(paths=http_paths))])
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

    assert path_exists_in_ingress(ingress, test_path1) is True

    # 2. Test when the path doesn't exist
    test_path2 = "/nonexistent-path"
    assert path_exists_in_ingress(ingress, test_path2) is False

    # 3. Test when there are multiple paths
    test_path3 = "/another-path"
    ingress.spec.rules[0].http.paths.append(V1HTTPIngressPath(path=test_path3, path_type="Prefix", backend=V1IngressBackend(service=None, resource=None)))

    assert path_exists_in_ingress(ingress, test_path3) is True

    # 4. Test when there's no rule specified
    ingress_no_rule = V1Ingress(
        api_version="networking.k8s.io/v1",
        kind="Ingress",
        metadata=client.V1ObjectMeta(
            name="dynamic-services",
            annotations={
                "nginx.ingress.kubernetes.io/rewrite-target": "/$2",
            },
        ),
        spec=V1IngressSpec(),
    )

    assert path_exists_in_ingress(ingress_no_rule, test_path1) is False


@patch("dependencies.k8_wrapper.sanitize_deployment_name", return_value=("mock_deployment_name", "mock_service_name"))
@patch("dependencies.k8_wrapper.v1_volume_mount_factory", return_value=([], []))
def test_create_and_launch_deployment(mock_v1_volume_mount_factory, mock_sanitize_deployment_name, mock_request):
    selector = create_and_launch_deployment(
        request=mock_request,
        module_name=sample_module_name,
        module_git_commit_hash=sample_git_commit_hash,
        image=sample_image,
        labels=sample_labels,
        annotations=sample_annotations,
        env=sample_env,
        mounts=sample_mounts_ro,
    )
    expected_selector = V1LabelSelector(match_expressions=None, match_labels={"us.kbase.module.git_commit_hash": "1234567", "us.kbase.module.module_name": "test_module"})
    assert selector == expected_selector
    mock_sanitize_deployment_name.assert_called_once_with(sample_module_name, sample_git_commit_hash)
    mock_v1_volume_mount_factory.assert_called_once_with(sample_mounts_ro)

    args, kwargs = mock_request.app.state.k8s_clients.app_client.create_namespaced_deployment.call_args
    actual_deployment_body = kwargs["body"]

    # Validate the relevant parts of the deployment
    assert actual_deployment_body.metadata.name == "mock_deployment_name"
    assert actual_deployment_body.metadata.labels == sample_labels
    assert actual_deployment_body.metadata.annotations == sample_annotations
    assert actual_deployment_body.spec.template.spec.containers[0].image == sample_image


@patch("dependencies.k8_wrapper._get_deployment_status")
def test_query_k8s_deployment_status(mock_get_deployment_status, mock_request):
    query_k8s_deployment_status(mock_request, sample_module_name, sample_git_commit_hash)
    expected_label_selector = "us.kbase.module.module_name=test_module,us.kbase.module.git_commit_hash=1234567"
    mock_get_deployment_status.assert_called_once_with(mock_request, expected_label_selector)


@patch("dependencies.k8_wrapper._get_deployment_status")
def test_get_k8s_deployment_status_from_label(mock_get_deployment_status, mock_request):
    label_selector = client.V1LabelSelector(match_labels={"key1": "value1", "key2": "value2"})

    # Call the function
    get_k8s_deployment_status_from_label(mock_request, label_selector)

    # Validate that _get_deployment_status was called with the correct label selector
    expected_label_selector = "key1=value1,key2=value2"
    mock_get_deployment_status.assert_called_once_with(mock_request, expected_label_selector)


@patch("dependencies.k8_wrapper.get_k8s_all_service_status_cache")
def test_get_k8s_deployments(mock_get_k8s_all_service_status_cache, mock_request):
    all_service_status_cache = MagicMock(spec=LRUCache)
    mock_request.app.state.k8s_clients.all_service_status_cache = all_service_status_cache
    mock_get_k8s_all_service_status_cache.return_value = all_service_status_cache

    # Scenario 1: Deployments are in the cache
    example_deployments = ["deployment1", "deployment2"]
    all_service_status_cache.get.return_value = example_deployments

    assert get_k8s_deployments(mock_request) == example_deployments
    assert all_service_status_cache.get.called_with(label_selector, None)
    assert all_service_status_cache.set.call_count == 0

    # Scenario 2: Deployments not in cache, fetch from K8s with no deployments matching label
    all_service_status_cache.get.return_value = None
    get_k8s_deployments(mock_request)
    assert mock_request.app.state.k8s_clients.app_client.list_namespaced_deployment.called_with(
        mock_request.app.state.settings.namespace, label_selector="us.kbase.dynamicservice=true"
    )
    assert all_service_status_cache.set.called_with(label_selector, None)

    # Scenario 3: Deployments not in cache, fetch from K8s with one or more deployments matching label
    all_service_status_cache.get.return_value = None
    mock_request.app.state.k8s_clients.app_client.list_namespaced_deployment.return_value.items = example_deployments
    get_k8s_deployments(mock_request)
    assert get_k8s_deployments(mock_request) == example_deployments
    all_service_status_cache.set.assert_called_with("us.kbase.dynamicservice=true", example_deployments)


@patch("dependencies.k8_wrapper.sanitize_deployment_name", return_value=("mock_deployment_name", "mock_service_name"))
def test_delete_deployment(mock_sanitize_deployment_name, mock_request):
    result = delete_deployment(mock_request, sample_module_name, sample_git_commit_hash)
    mock_sanitize_deployment_name.assert_called_once_with(sample_module_name, sample_git_commit_hash)
    mock_request.app.state.k8s_clients.app_client.delete_namespaced_deployment.assert_called_once_with(
        name="mock_deployment_name", namespace=mock_request.app.state.settings.namespace
    )
    assert result == "mock_deployment_name"


@patch("dependencies.k8_wrapper.query_k8s_deployment_status")
def test_scale_replicas(mock_query_deployment_status, mock_request):
    desired_replicas = 3
    mock_query_deployment_status.return_value = sample_deployment
    scale_replicas(mock_request, sample_module_name, sample_git_commit_hash, desired_replicas)
    mock_query_deployment_status.assert_called_once_with(mock_request, sample_module_name, sample_git_commit_hash)
    mock_request.app.state.k8s_clients.app_client.replace_namespaced_deployment.assert_called_once_with(
        name="mock_deployment_name", namespace=mock_request.app.state.settings.namespace, body=sample_deployment
    )
