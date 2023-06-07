from pydantic import BaseModel
from functools import cached_property


from src.configs.settings import get_settings


class ServiceLogWebSocket(BaseModel):
    instance_id: str
    socket_url: str



class UserAuthRoles:
    def __init__(self, username: str, roles: list[str]):
        self.username = username
        self.roles = roles

    @cached_property
    def is_admin(self) -> bool:
        settings = get_settings()
        return any(role in settings.admin_roles for role in self.roles)