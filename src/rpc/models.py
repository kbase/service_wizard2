from typing import Optional, Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    message: str
    code: int
    name: str
    error: str = None


class JSONRPCResponse(BaseModel):
    version: str = "1.0"
    id: Optional[int | str]
    error: Optional[ErrorResponse]
    result: Any = None

    def dict(self, *args, **kwargs):
        response_dict = super().dict(*args, **kwargs)
        if self.result is None:
            response_dict.pop("result", None)

        if self.error is None:
            response_dict.pop("error", None)
            response_dict.pop("version", None)

        if self.id is None:
            response_dict.pop("id", None)

        return response_dict
