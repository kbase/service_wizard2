from typing import Any, Union

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    message: str
    code: int
    name: str
    error: str | None = None


class JSONRPCResponse(BaseModel):
    version: str = "1.0"
    id: Union[int, str] | None = 0
    error: ErrorResponse | None = None
    result: Any | None = None

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        # Default behavior for the serialization
        serialized_data = super().model_dump(*args, **kwargs)

        # Custom logic to exclude fields based on their values
        if serialized_data.get("result") is None:
            serialized_data.pop("result", None)

        if serialized_data.get("error") is None:
            serialized_data.pop("error", None)
            serialized_data.pop("version", None)

        if serialized_data.get("id") is None:
            serialized_data.pop("id", None)

        return serialized_data
