from models import DynamicServiceStatus, ServiceStatus, ServiceHealth


def test_model_creation():
    data = {
        "git_commit_hash": "abcdef123456",
        "version": "1.0.0",
        "release_tags": ["beta", "latest"],
        "url": "http://example.com",
        "module_name": "TestModule",
        "deployment_name": "test-deployment",
        "replicas": 2,
        "available_replicas": 2,
    }

    model = DynamicServiceStatus(**data)

    assert model.git_commit_hash == "abcdef123456"
    assert model.version == "1.0.0"
    assert model.release_tags == ["beta", "latest"]
    assert model.url == "http://example.com"
    assert model.module_name == "TestModule"
    assert model.deployment_name == "test-deployment"
    assert model.replicas == 2
    assert model.available_replicas == 2
    assert model.up == 1
    assert model.status == ServiceStatus.RUNNING
    assert model.health == ServiceHealth.HEALTHY


def test_model_with_error_status():
    data = {
        "git_commit_hash": "abcdef123456",
        "version": "1.0.0",
        "release_tags": ["beta", "latest"],
        "url": "http://example.com",
        "module_name": "TestModule",
        "deployment_name": "test-deployment",
        "replicas": 3,
        "available_replicas": 2,  # This should trigger the ERROR status
    }

    model = DynamicServiceStatus(**data)

    assert model.status == ServiceStatus.ERROR


def test_calculate_up():
    assert DynamicServiceStatus.calculate_up(0, 0) == 0
    assert DynamicServiceStatus.calculate_up(2, 0) == 0
    assert DynamicServiceStatus.calculate_up(0, 2) == 0
    assert DynamicServiceStatus.calculate_up(2, 2) == 1


def test_calculate_status():
    assert DynamicServiceStatus.calculate_status(0, 0) == ServiceStatus.STOPPED
    assert DynamicServiceStatus.calculate_status(2, 0) == ServiceStatus.STARTING
    assert DynamicServiceStatus.calculate_status(0, 2) == ServiceStatus.STOPPED
    assert DynamicServiceStatus.calculate_status(2, 2) == ServiceStatus.RUNNING


def test_calculate_health():
    assert DynamicServiceStatus.calculate_health(0, 0) == ServiceHealth.UNHEALTHY
    assert DynamicServiceStatus.calculate_health(2, 0) == ServiceHealth.UNHEALTHY
    assert DynamicServiceStatus.calculate_health(0, 2) == ServiceHealth.UNHEALTHY
    assert DynamicServiceStatus.calculate_health(2, 2) == ServiceHealth.HEALTHY
    assert DynamicServiceStatus.calculate_health(3, 2) == ServiceHealth.DEGRADED
