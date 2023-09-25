import logging
from typing import Optional

from cacheout import LRUCache
from fastapi.requests import Request
from kubernetes import config
from kubernetes.client import CoreV1Api, AppsV1Api, NetworkingV1Api, V1Deployment

from src.configs.settings import Settings


class K8sClients:
    app_client: AppsV1Api
    core_client: CoreV1Api
    network_client: NetworkingV1Api
    service_status_cache: LRUCache
    all_service_status_cache: LRUCache

    def __init__(
        self,
        settings: Settings,
        k8s_core_client: Optional[CoreV1Api] = None,
        k8s_app_client: Optional[AppsV1Api] = None,
        k8s_network_client: Optional[NetworkingV1Api] = None,
    ):
        """
        Setup Kubernetes clients.

        Parameters:
            settings (Settings): The settings object containing configuration details.
            k8s_core_client (Optional[client.CoreV1Api]): Optional preconfigured CoreV1Api client.
            k8s_app_client (Optional[client.AppsV1Api]): Optional preconfigured AppsV1Api client.
            k8s_network_client (Optional[client.NetworkingV1Api]): Optional preconfigured NetworkingV1Api client.

        Returns:
            Tuple[client.CoreV1Api, client.AppsV1Api, client.NetworkingV1Api]: The Kubernetes clients.

        Raises:
            ValueError: If more than one Kubernetes client is provided or if none are provided.
        """

        clients_and_types = [(k8s_core_client, CoreV1Api), (k8s_app_client, AppsV1Api), (k8s_network_client, NetworkingV1Api)]

        num_clients_provided = sum(x is not None for x in [k8s_core_client, k8s_app_client, k8s_network_client])
        if num_clients_provided not in [0, 3]:
            raise ValueError("All k8s_clients should either be all None or all provided")

        for client, expected_type in clients_and_types:
            if client is not None and not isinstance(client, expected_type):
                raise TypeError(f"Expected client of type {expected_type}, but got {type(client)}")

        if k8s_core_client is None:
            if settings.use_incluster_config is True:
                # Use a service account token if running in a k8s cluster
                logging.info("Loading in-cluster k8s config")
                config.load_incluster_config()
            else:
                # Use the kubeconfig file, useful for local development and testing
                logging.info(f"Loading k8s config from {settings.kubeconfig}")
                config.load_kube_config(config_file=settings.kubeconfig)
            k8s_core_client = CoreV1Api()
            k8s_app_client = AppsV1Api()
            k8s_network_client = NetworkingV1Api()

        self.app_client = k8s_app_client
        self.core_client = k8s_core_client
        self.network_client = k8s_network_client
        self.service_status_cache = LRUCache(ttl=10)
        self.all_service_status_cache = LRUCache(ttl=10)


def get_k8s_core_client(request: Request) -> CoreV1Api:
    return request.app.state.k8s_clients.core_client


def get_k8s_app_client(request: Request) -> AppsV1Api:
    return request.app.state.k8s_clients.app_client


def get_k8s_networking_client(request: Request) -> NetworkingV1Api:
    return request.app.state.k8s_clients.network_client


def get_k8s_service_status_cache(request: Request) -> LRUCache:
    return request.app.state.k8s_clients.service_status_cache


def get_k8s_all_service_status_cache(request: Request) -> LRUCache:
    return request.app.state.k8s_clients.all_service_status_cache


def check_service_status_cache(request: Request, label_selector_text) -> V1Deployment:
    cache = get_k8s_service_status_cache(request)
    return cache.get(label_selector_text, None)


def populate_service_status_cache(request: Request, label_selector_text, data: list):
    get_k8s_service_status_cache(request).set(label_selector_text, data)
