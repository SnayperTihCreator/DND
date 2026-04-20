from .core import BaseSystemMessage, BaseActionType


class SystemActionType(BaseActionType):
    INFO = "system", "server", "info"
    RESOURCE_AVAILABLE = "system", "resource", "available"


class SystemServerInfo(BaseSystemMessage, type=SystemActionType.INFO):
    http_port: int
    table_name: str
    uid: str


class SystemResourceAvailable(BaseSystemMessage, type=SystemActionType.RESOURCE_AVAILABLE):
    filename: str


__all__ = ["SystemActionType",
           "SystemServerInfo", "SystemResourceAvailable"]
