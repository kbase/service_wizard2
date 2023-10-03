from typing import Any, Optional, Union

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    message: str
    code: int
    name: str
    error: str = None




class JSONRPCResponse(BaseModel):
    version: str = "1.0"
    id: Optional[Union[int, str]] = 0
    error: Optional[ErrorResponse] = None
    result: Any = None

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
