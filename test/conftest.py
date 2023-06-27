import os

import pytest
from dotenv import load_dotenv


@pytest.fixture(autouse=True)
def load_environment():
    # Ensure that the environment variables are loaded before running the tests
    load_dotenv()


@pytest.fixture(autouse=True)
def generate_kubeconfig():
    # Generate a kubeconfig file for testing
    os.environ['KUBECONFIG'] = "test_kubeconfig_file"
    kubeconfig_path = os.environ['KUBECONFIG']

    kubeconfig_content = """\
apiVersion: v1
kind: Config
current-context: test-context
clusters:
- name: test-cluster
  cluster:
    server: https://test-api-server
    insecure-skip-tls-verify: true
contexts:
- name: test-context
  context:
    cluster: test-cluster
    user: test-user
users:
- name: test-user
  user:
    exec:
      command: echo
      apiVersion: client.authentication.k8s.io/v1alpha1
      args:
      - "access_token"
"""

    with open(kubeconfig_path, "w") as kubeconfig_file:
        kubeconfig_file.write(kubeconfig_content.strip())

    yield

    # Clean up the generated kubeconfig file after the tests
    os.remove(kubeconfig_path)
