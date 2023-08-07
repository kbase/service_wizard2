import logging
from typing import Optional

from cacheout import LRUCache
from kubernetes import config
from kubernetes.client import CoreV1Api, AppsV1Api, NetworkingV1Api


class K8sClients:
    app_client: AppsV1Api
    core_client: CoreV1Api
    network_client: NetworkingV1Api
    service_status_cache: LRUCache
    all_service_status_cache: LRUCache

    def __init__(
        self,
        settings: "Settings",
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

        if sum(x is not None for x in [k8s_core_client, k8s_app_client, k8s_network_client]) > 1:
            raise ValueError("All k8s_clients should either be all None or all provided")

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
