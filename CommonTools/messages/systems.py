from .core import BaseSystemMessage, BaseActionType


class SystemActionType(BaseActionType):
    INFO = "system", "server", "info"


class SystemServerInfo(BaseSystemMessage, type=SystemActionType.INFO):
    http_port: int
    table_name: str


__all__ = ["SystemActionType",
           "SystemServerInfo"]
