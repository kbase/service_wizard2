# import traceback
# from unittest.mock import patch
#
# import pytest
# from fastapi import HTTPException
#
# import clients.baseclient
# from dependencies.k8_wrapper import DuplicateLabelsException
# from dependencies.status import (
#     lookup_module_info,
#     get_service_status_without_retries,
#     get_service_status_with_retries,
#     get_dynamic_service_status_helper,
#     get_status,
#     get_version,
#     get_all_dynamic_service_statuses,
# )
# from models import CatalogModuleInfo
# from test.src.dependencies.test_helpers import assert_exception_correct, get_running_deployment_status, sample_catalog_module_info, create_sample_deployment
#
# sample_module_name = "test_module"
# sample_git_commit = "test_hash"
#
#
# def test_lookup_module_info(mock_request):
#     # Good request
#     lookup_module_info(mock_request, sample_module_name, sample_git_commit)
#     mock_request.app.state.catalog_client.get_combined_module_info.assert_called_once_with(sample_module_name, sample_git_commit)
#
#     # Catalog is down
#     mock_request.app.state.catalog_client.get_combined_module_info.side_effect = clients.baseclient.ServerError(name="test", code=0, message=0)
#     with pytest.raises(HTTPException):
#         lookup_module_info(mock_request, sample_module_name, sample_git_commit)
#
#     # Something unexpected happens
#     mock_request.app.state.catalog_client.get_combined_module_info.side_effect = Exception()
#     evr = CatalogModuleInfo(
#         url="No Valid URL Found, or possible programming error ",
#         version=sample_git_commit,
#         module_name=sample_module_name,
#         release_tags=[],
#         git_commit_hash="test_hash",
#         owners=["Unknown"],
#     )
#
#     assert lookup_module_info(mock_request, sample_module_name, sample_git_commit) == evr
#
#
# @patch("dependencies.status.get_service_status_with_retries")
# def test_get_service_status_without_retries(mock_get_service_status_with_retries, mock_request):
#     get_service_status_without_retries(mock_request, sample_module_name, sample_git_commit)
#     mock_get_service_status_with_retries.assert_called_once_with(mock_request, sample_module_name, sample_git_commit, retries=0)
#
#
# @patch("time.sleep")
# @patch("dependencies.status.get_dynamic_service_status_helper")
# @patch("dependencies.status.lookup_module_info")
# def test_get_service_status_with_retries(
#     mock_lookup_module_info, mock_get_dynamic_service_status_helper, mock_sleep, mock_request, example_dynamic_service_status_up, example_dynamic_service_status_down
# ):
#     # Test ServerError
#     mock_get_dynamic_service_status_helper.side_effect = clients.baseclient.ServerError(name="test", code=0, message="Server Error!")
#     with pytest.raises(HTTPException) as exc_info:
#         get_service_status_with_retries(mock_request, sample_module_name, sample_git_commit, retries=1)
#     expected_exception = HTTPException(status_code=500, detail="test: 0. Server Error!\n")
#     assert_exception_correct(got=exc_info.value, expected=expected_exception)
#
#     # Test DuplicateLabelsException
#     mock_get_dynamic_service_status_helper.side_effect = DuplicateLabelsException()
#     with pytest.raises(HTTPException) as exc_info:
#         get_service_status_with_retries(mock_request, sample_module_name, sample_git_commit, retries=1)
#     expected_exception = HTTPException(status_code=500, detail="Duplicate labels found in deployment, an admin screwed something up!")
#     assert_exception_correct(got=exc_info.value, expected=expected_exception)
#
#     # Test General Exception
#     mock_get_dynamic_service_status_helper.side_effect = Exception("Some unexpected error!")
#     with pytest.raises(Exception) as exc_info:  # Catch the exception
#         get_service_status_with_retries(mock_request, sample_module_name, sample_git_commit, retries=1)
#     expected_exception = Exception("Failed to get service status after maximum retries")
#     assert_exception_correct(got=exc_info.value, expected=expected_exception)
#
#     # Reset the side effect for the next tests
#     mock_get_dynamic_service_status_helper.side_effect = None
#
#     with pytest.raises(Exception) as e:
#         get_service_status_with_retries(mock_request, sample_module_name, sample_git_commit, retries=10)
#     assert_exception_correct(got=e.value, expected=Exception("Failed to get service status after maximum retries"))
#
#     # Deployment is up
#     mock_get_dynamic_service_status_helper.return_value = example_dynamic_service_status_up
#     rv = get_service_status_with_retries(mock_request, sample_module_name, sample_git_commit, retries=10)
#     assert rv.up
#
#     # Deployment is down
#     mock_get_dynamic_service_status_helper.return_value = example_dynamic_service_status_down
#     rv = get_service_status_with_retries(mock_request, sample_module_name, sample_git_commit, retries=10)
#     assert not rv.up
#     assert rv.replicas == 0
#
#
# @patch("dependencies.status.lookup_module_info")
# @patch("dependencies.status.query_k8s_deployment_status")
# def test_get_dynamic_service_status_helper(mock_query_k8s_deployment_status, mock_lookup_module_info, mock_request):
#     # Found it!
#     mock_lookup_module_info.return_value = sample_catalog_module_info()
#     mock_query_k8s_deployment_status.return_value = create_sample_deployment("test", 1, 1, 1, 0)
#     rv = get_dynamic_service_status_helper(mock_request, sample_module_name, sample_git_commit)
#     expected_dss = get_running_deployment_status("test")
#     assert rv == expected_dss
#
#     # Test the case where no dynamic service is found
#     mock_query_k8s_deployment_status.return_value = None
#     with pytest.raises(HTTPException) as e:
#         get_dynamic_service_status_helper(mock_request, sample_module_name, sample_git_commit)
#     expected_exception = HTTPException(status_code=404, detail=f"No dynamic service found with module_name={sample_module_name} and version={sample_git_commit}")
#     assert e.value.status_code == 404
#     assert e.value.detail == expected_exception.detail
#     assert_exception_correct(e.value, expected_exception)
#
#
# @patch("dependencies.status.get_k8s_deployments")
# def test_get_all_dynamic_service_statuses(mock_get_k8s_deployments, mock_request):
#     # No Deployments found
#     mock_get_k8s_deployments.return_value = []
#     with pytest.raises(HTTPException) as e:
#         get_all_dynamic_service_statuses(mock_request, sample_module_name, sample_git_commit)
#     # No kubernetes found!
#     expected_exception = HTTPException(
#         status_code=404,
#         detail=f"No deployments found in kubernetes cluster with namespace=" f"{mock_request.app.state.settings.namespace} and labels=dynamic-service=true!",
#     )
#     assert e.value.status_code == 404
#     assert e.value.detail == expected_exception.detail
#     assert_exception_correct(e.value, expected_exception)
#
#     # Get running deployment
#     mock_get_k8s_deployments.return_value = [create_sample_deployment("test", 1, 1, 1, 0)]
#     rv = get_all_dynamic_service_statuses(mock_request, sample_module_name, sample_git_commit)
#     expected_dss = get_running_deployment_status("test")
#     assert rv == [expected_dss]
#
#     # Inject a bad key
#     mock_get_k8s_deployments.return_value = [create_sample_deployment("test", 1, 1, 1, 0)]
#     mock_get_k8s_deployments.return_value[0].metadata.annotations["module_name"] = None
#     mock_get_k8s_deployments.return_value[0].metadata.annotations["git_commit_hash"] = None
#     with pytest.raises(HTTPException) as e:
#         get_all_dynamic_service_statuses(mock_request, sample_module_name, sample_git_commit)
#
#     expected_exception = HTTPException(
#         status_code=404,
#         detail=f"No dynamic services found in kubernetes cluster with namespace={mock_request.app.state.settings.namespace} and "
#         f"labels=dynamic-service=true! Or "
#         f"they were found and they were missing the module_name and git_commit_hash annotations!",
#     )
#     assert e.value.status_code == expected_exception.status_code
#     assert e.value.detail == expected_exception.detail
#     assert_exception_correct(e.value, expected_exception)
#
#     # NO dynamic services found in the catalog
#     mock_request.app.state.catalog_client.get_hash_to_name_mappings.return_value = None
#     with pytest.raises(HTTPException) as e:
#         get_all_dynamic_service_statuses(mock_request, sample_module_name, sample_git_commit)
#     expected_exception = HTTPException(status_code=404, detail="No dynamic services found in catalog!")
#     assert e.value.status_code == 404
#     assert e.value.detail == expected_exception.detail
#     assert_exception_correct(e.value, expected_exception)
#
#
# def test_get_status(mock_request):
#     mock_request.app.state.settings.vcs_ref = "1.2.3"
#     result = get_status(mock_request)
#     expected = {
#         "git_commit_hash": "1.2.3",
#         "state": "OK",
#         "version": "1.2.3",
#         "message": "",
#         "git_url": "https://github.com/kbase/service_wizard2",
#     }
#     assert result == expected
#
#     result_with_params = get_status(mock_request, module_name="some_module", version="some_version")
#     assert result_with_params == expected
#
#
# def test_get_version(mock_request):
#     mock_request.app.state.settings.vcs_ref = "1.2.3"
#     result = get_version(mock_request)
#     expected = ["1.2.3"]
#     assert result == expected
#
#     result_with_params = get_version(mock_request, module_name="some_module", version="some_version")
#     assert result_with_params == expected
