from pydantic import BaseModel


class ServiceLogWebSocket(BaseModel):
    instance_id: str
    socket_url: str