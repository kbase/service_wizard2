from typing import Optional, List

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    message: str
    code: int
    name: str
    error: str = None


class JSONRPCResponse(BaseModel):
    version: str = "1.0"
    id: Optional[int]
    error: Optional[ErrorResponse]
    result: Optional[List[dict] | List[List[dict]]] = Field(default_factory=lambda: None)

    def dict(self, *args, **kwargs):
        # Remove 'result' from the dictionary if it's None
        response_dict = super().dict(*args, **kwargs)
        if self.result is None:
            response_dict.pop("result", None)

        if self.error is None:
            response_dict.pop("error", None)
            # TODO: Check this functionality
            response_dict.pop("version", None)

        if self.id is None:
            response_dict.pop("id", None)

        return response_dict
