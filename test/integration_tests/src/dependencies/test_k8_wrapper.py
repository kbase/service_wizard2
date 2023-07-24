import json
import os
from unittest.mock import create_autospec

import pytest
import requests
from cacheout import LRUCache
from fastapi.testclient import TestClient
from kubernetes import config, client
from pykube import Pod
from pytest_kind import KindCluster
from requests.adapters import HTTPAdapter
import requests_mock

from src.clients.CatalogClient import Catalog
from src.configs.settings import get_settings
from src.factory import create_app
from dependencies.authentication import authenticated_user

from dotenv import load_dotenv


@pytest.fixture(autouse=True)
def load_environment():
    # Ensure that the environment variables are loaded before running the tests
    load_dotenv("/Users/bsadkhin/modules/kbase/service_wizard2/.env")


@pytest.fixture(scope="session")
def kind_cluster():
    # Will need to load_env to run this function
    cluster = KindCluster("service-wizard")
    # For race conditions:
    try:
        cluster.delete()
    except Exception as e:
        print(e)
    print("Creating cluster")
    cluster.create()
    # Create a namespace
    try:
        cluster.kubectl("create", "namespace", get_settings().namespace)
    except Exception as e:
        print(e)

    yield cluster
    cluster.delete()


@pytest.fixture
def k8_api_client(kind_cluster):
    kubeconfig_path = str(kind_cluster.kubeconfig_path)
    config.load_kube_config(config_file=kubeconfig_path)
    api_client = client.ApiClient()
    yield api_client


@pytest.fixture
def mock_catalog_client():
    cc = create_autospec(Catalog)

    """
     from biokbase.catalog.Client import Catalog
     cc = Catalog(url="https://ci.kbase.us/services/catalog")
     cc.version()
     cc.get_module_version({"module_name": "NarrativeService", "version": "8a9bb32f9e2ec5169815b984de8e8df550699630"})
     """
    cc_result = {
        "module_name": "NarrativeService",
        "released": 1,
        "released_timestamp": None,
        "notes": "",
        "timestamp": 1651522838549,
        "registration_id": "1651522838549_531b1651-c528-4112-bf69-20d78a479020",
        "version": "0.5.2",
        "git_commit_hash": "8a9bb32f9e2ec5169815b984de8e8df550699630",
        "git_commit_message": "Merge pull request #92 from kbaseapps/fix_get_narrative_doc_worksheets\n\nFix get narrative doc worksheets",
        "narrative_methods": [],
        "local_functions": [],
        "docker_img_name": "dockerhub-ci.kbase.us/kbase:narrativeservice.8a9bb32f9e2ec5169815b984de8e8df550699630",
        "dynamic_service": 1,
        "release_timestamp": 1651522963611,
        "git_url": "https://github.com/kbaseapps/NarrativeService",
        "release_tags": ["release", "beta", "dev"],
    }
    cc.get_module_version.return_value = cc_result
    cc.get_secure_config_params.return_value = [
        {
            "module_name": "NarrativeService",
            "version": "",
            "param_name": "service_token",
            "param_value": "<REDACTED_FOR_YOUR_SAFETY_AND_PLEASURE>",
            "is_password": 1,
        },
        {
            "module_name": "NarrativeService",
            "version": "",
            "param_name": "ws_admin_token",
            "param_value": "<REDACTED_FOR_YOUR_SAFETY_AND_PLEASURE>",
            "is_password": 1,
        },
    ]
    cc.list_volume_mounts.return_value = [
        {
            "module_name": "NarrativeService",
            "function_name": "service",
            "client_group": "service",
            "volume_mounts": [{"host_dir": "/data/static_narratives", "container_dir": "/kb/module/work/nginx", "read_only": 0}],
        }
    ]

    yield cc


@pytest.fixture
def k8_api_client(kind_cluster):
    kubeconfig_path = str(kind_cluster.kubeconfig_path)
    config.load_kube_config(config_file=kubeconfig_path)

    api_client = client.ApiClient()
    yield api_client


@pytest.fixture
def v1_core_client(k8_api_client):
    v1_core = client.CoreV1Api(k8_api_client)
    yield v1_core


@pytest.fixture
def apps_v1_client(k8_api_client):
    apps_v1 = client.AppsV1Api(k8_api_client)
    yield apps_v1


@pytest.fixture
def app(kind_cluster, mock_catalog_client, v1_core_client, apps_v1_client):
    token_cache = LRUCache(maxsize=100, ttl=300)
    catalog_cache = LRUCache(maxsize=100, ttl=300)
    app = create_app(
        token_cache=token_cache,
        catalog_cache=catalog_cache,
        catalog_client=mock_catalog_client,
        k8s_app_client=apps_v1_client,
        k8s_core_client=v1_core_client,
    )
    app.dependency_overrides[authenticated_user] = lambda: ...
    return app


# def test_kubernetes_version(kind_cluster):
#     assert kind_cluster.api.version == ("1", "25")
#
#
# def test_namespace_and_pods(k8_api_client):
#     v1_core = client.CoreV1Api(k8_api_client)
#     namespace_name = get_settings().namespace
#     namespace_exists = False
#     try:
#         v1_core.read_namespace(name=namespace_name)
#         namespace_exists = True
#     except client.ApiException as e:
#         if e.status != 404:
#             raise
#     assert namespace_exists
#     # Check if there are no pods in the namespace
#     pods = v1_core.list_namespaced_pod(namespace=namespace_name).items
#     assert len(pods) == 0


@pytest.fixture
def client_with_authorization(app):
    def _get_client_with_authorization(authorization_value="faketoken", cookies=None):
        client = TestClient(app)
        client.headers["Authorization"] = f"{authorization_value}"
        if cookies:
            client.cookies["kbase_session"] = f"{authorization_value}"
        return client

    return _get_client_with_authorization


#
# def test_get_start(client_with_authorization):
#     with client_with_authorization() as client:
#         response = client.get("/start/?module_name=StaticNarrative&version=beta")
#
#         assert response.json() != []
#         assert response.json() == [123]
#         assert response.status_code == 200


def test_get_status_nonexistent(client_with_authorization):
    with client_with_authorization() as client:
        response = client.get("/get_service_status?module_name=StaticNarrative&version=beta")
        assert response.json() != []
        assert response.json() == [123]
        assert response.status_code == 200


def test_get_good_status(client_with_authorization):
    {
        "git_commit_hash": "8a9bb32f9e2ec5169815b984de8e8df550699630",
        "status": "active",
        "version": "0.5.2",
        "hash": "8a9bb32f9e2ec5169815b984de8e8df550699630",
        "release_tags": ["release", "beta", "dev"],
        "url": "https://ci.kbase.us:443/dynserv/8a9bb32f9e2ec5169815b984de8e8df550699630.NarrativeService",
        "module_name": "NarrativeService",
        "health": "healthy",
        "up": 1,
    }

    with client_with_authorization() as client:
        response = client.get("/get_service_status?module_name=NarrativeService&version=beta")
        assert response.json() != []
        assert response.json() == [123]
        assert response.status_code == 200
