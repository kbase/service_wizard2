import pytest
from pydantic import ValidationError

from rpc.models import ErrorResponse, JSONRPCResponse


# 1. Test that the models can be instantiated with valid data.


def test_error_response_creation():
    data = {
        "message": "An error occurred",
        "code": 400,
        "name": "BadRequest",
    }
    response = ErrorResponse(**data)
    assert response.message == data["message"]
    assert response.code == data["code"]
    assert response.name == data["name"]
    assert response.error is None


def test_jsonrpc_response_creation():
    data = {
        "result": "Success",
    }
    response = JSONRPCResponse(**data)
    assert response.version == "1.0"
    assert response.id == 0
    assert response.result == data["result"]
    assert response.error is None


# 2. Test that the models raise validation errors for invalid data.


def test_invalid_error_response_creation():
    data = {
        "message": "An error occurred",
    }
    with pytest.raises(ValidationError):
        ErrorResponse(**data)


def test_invalid_jsonrpc_response_creation():
    data = {
        "version": 2,
    }
    with pytest.raises(ValidationError):
        JSONRPCResponse(**data)


# 3. Test the custom logic in the model_dump method.


def test_model_dump():
    data = {
        "result": "Success",
    }
    response = JSONRPCResponse(**data)
    serialized_data = response.model_dump()

    assert "result" in serialized_data
    assert "error" not in serialized_data
    assert "version" not in serialized_data
    assert serialized_data["result"] == "Success"

    error_data = {
        "message": "An error occurred",
        "code": 400,
        "name": "BadRequest",
    }
    response_with_error = JSONRPCResponse(error=ErrorResponse(**error_data))
    serialized_data_with_error = response_with_error.model_dump()

    assert "error" in serialized_data_with_error
    assert "version" in serialized_data_with_error
    assert "result" not in serialized_data_with_error
    assert serialized_data_with_error["error"]["message"] == "An error occurred"


# Tests for ErrorResponse


def test_full_error_response_creation():
    data = {"message": "An error occurred", "code": 500, "name": "InternalServerError", "error": "Some error string"}
    response = ErrorResponse(**data)
    assert response.message == data["message"]
    assert response.code == data["code"]
    assert response.name == data["name"]
    assert response.error == data["error"]


# Tests for JSONRPCResponse


def test_full_jsonrpc_response_creation():
    data = {"version": "1.0", "id": "some-id", "result": "Success", "error": None}
    response = JSONRPCResponse(**data)
    assert response.version == data["version"]
    assert response.id == data["id"]
    assert response.result == data["result"]
    assert response.error == data["error"]


def test_jsonrpc_model_dump_with_both_fields():
    data = {
        "result": "Success",
        "error": {
            "message": "An error occurred",
            "code": 400,
            "name": "BadRequest",
        },
    }
    response = JSONRPCResponse(**data)
    serialized_data = response.model_dump()
    assert "error" in serialized_data
    assert "result" in serialized_data


def test_jsonrpc_model_dump_with_id():
    data = {"id": "some-id", "result": "Success"}
    response = JSONRPCResponse(**data)
    serialized_data = response.model_dump()
    assert serialized_data["id"] == "some-id"


def test_jsonrpc_model_dump_without_id():
    data = {"id": None, "result": "Success"}
    response = JSONRPCResponse(**data)
    serialized_data = response.model_dump()
    assert "id" not in serialized_data
