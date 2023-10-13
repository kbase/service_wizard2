from unittest.mock import patch, Mock

import pytest

from clients.baseclient import ServerError
from dependencies.logs import get_service_log_web_socket, get_service_log
from models import CatalogModuleInfo

# Sample test data
mock_module_info = Mock(spec=CatalogModuleInfo)
mock_module_info.release_tags = []
mock_module_info.owners = ["owner1"]


@patch("dependencies.logs.get_logs_for_first_pod_in_deployment", return_value=("pod1", "sample_logs"))
@patch("dependencies.status.lookup_module_info", return_value=mock_module_info)
def test_get_service_log(mock_lookup_module_info, mock_get_logs_for_first_pod_in_deployment, mock_request):
    # Test for owner trying to access logs of a dev service
    mock_request.app.state.user_auth_roles.is_admin_or_owner.return_value = True
    logs = get_service_log(mock_request, "test_module", "test_version")
    assert logs == [{"instance_id": "pod1", "log": "sample_logs"}]

    # Test for non-admin, non-owner user trying to access logs of a non-dev service
    mock_request.state.user_auth_roles.is_admin_or_owner.return_value = False
    with pytest.raises(ServerError):
        get_service_log(mock_request, "test_module", "test_version")


# Test for the not implemented function
def test_get_service_log_web_socket():
    mock_request = Mock()

    with pytest.raises(NotImplementedError):
        get_service_log_web_socket(mock_request, "test_module", "test_version")
