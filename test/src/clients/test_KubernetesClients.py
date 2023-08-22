from unittest.mock import patch, Mock

import kubernetes
import pytest
from kubernetes.client import CoreV1Api, AppsV1Api, NetworkingV1Api

from src.clients.KubernetesClients import K8sClients
from src.configs.settings import get_settings


@pytest.fixture
def settings():
    settings = get_settings()
    return settings


def test_k8s_clients_all_none(settings):
    with patch("kubernetes.config.load_kube_config"):
        with patch("kubernetes.client.CoreV1Api", return_value=Mock(spec=CoreV1Api)):
            with patch("kubernetes.client.AppsV1Api", return_value=Mock(spec=AppsV1Api)):
                with patch("kubernetes.client.NetworkingV1Api", return_value=Mock(spec=NetworkingV1Api)):
                    client = K8sClients(settings=settings)
                    assert isinstance(client.core_client, CoreV1Api)
                    assert isinstance(client.app_client, AppsV1Api)
                    assert isinstance(client.network_client, NetworkingV1Api)


def test_k8s_clients_all_provided(settings):
    core_client_mock = Mock(spec=CoreV1Api)
    app_client_mock = Mock(spec=AppsV1Api)
    network_client_mock = Mock(spec=NetworkingV1Api)
    client = K8sClients(settings, k8s_core_client=core_client_mock, k8s_app_client=app_client_mock, k8s_network_client=network_client_mock)
    assert client.core_client == core_client_mock
    assert client.app_client == app_client_mock
    assert client.network_client == network_client_mock


def test_k8s_clients_mixed_clients(settings):
    with pytest.raises(ValueError, match="All k8s_clients should either be all None or all provided"):
        K8sClients(settings, k8s_core_client=Mock(spec=CoreV1Api))

    with pytest.raises(ValueError, match="All k8s_clients should either be all None or all provided"):
        K8sClients(settings, k8s_core_client=Mock(spec=CoreV1Api), k8s_app_client=Mock(spec=AppsV1Api))

    with pytest.raises(ValueError, match="All k8s_clients should either be all None or all provided"):
        K8sClients(settings, k8s_core_client=Mock(spec=CoreV1Api), k8s_app_client=Mock(spec=AppsV1Api), k8s_network_client=None)


def test_k8s_clients_incluster_config(settings):
    with patch("kubernetes.config.load_incluster_config"):
        with patch("kubernetes.client.CoreV1Api", return_value=Mock(spec=CoreV1Api)):
            with patch("kubernetes.client.AppsV1Api", return_value=Mock(spec=AppsV1Api)):
                with patch("kubernetes.client.NetworkingV1Api", return_value=Mock(spec=NetworkingV1Api)):
                    client = K8sClients(settings)
                    assert isinstance(client.core_client, CoreV1Api)
                    assert isinstance(client.app_client, AppsV1Api)
                    assert isinstance(client.network_client, NetworkingV1Api)


def test_k8s_clients_invalid_client_types(settings):
    invalid_client = "invalid_client"
    valid_core_client = Mock(spec=CoreV1Api)
    valid_app_client = Mock(spec=AppsV1Api)
    valid_network_client = Mock(spec=NetworkingV1Api)

    client_combinations = {
        CoreV1Api: (invalid_client, valid_app_client, valid_network_client),
        AppsV1Api: (valid_core_client, invalid_client, valid_network_client),
        NetworkingV1Api: (valid_core_client, valid_app_client, invalid_client),
    }

    for expected_type, (core, app, net) in client_combinations.items():
        with pytest.raises(TypeError, match=f"Expected client of type {expected_type}, but got"):
            K8sClients(settings, k8s_core_client=core, k8s_app_client=app, k8s_network_client=net)


def test_k8s_clients_config_load_errors(settings):
    with pytest.raises(kubernetes.config.config_exception.ConfigException, match="Invalid kube-config file. No configuration found."):
        settings.use_incluster_config = False
        settings.kubeconfig = "/invalid_path/to/kubeconfig"
        K8sClients(settings)

    with pytest.raises(kubernetes.config.config_exception.ConfigException, match="Service host/port is not set."):
        settings.use_incluster_config = True
        K8sClients(settings)
