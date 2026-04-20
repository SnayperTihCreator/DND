from typing import Any

from .core import BaseMessage, BaseActionType


class ProxyActionType(BaseActionType):
    CLIENT_CONNECT = "proxy", "client", "connect"
    CLIENT_DISCONNECT = "proxy", "client", "disconnect"
    
    TUNNEL_DATA = "proxy", "tunnel", "data"
    TABLE_SWITCH = "proxy", "table", "switch"


class ProxyClientConnect(BaseMessage, type=ProxyActionType.CLIENT_CONNECT):
    uid: str


class ProxyClientDisconnect(BaseMessage, type=ProxyActionType.CLIENT_DISCONNECT):
    uid: str


class ProxyTunnel(BaseMessage, type=ProxyActionType.TUNNEL_DATA):
    uid: str
    msg: Any | BaseMessage


class ProxyOpenTable(BaseMessage, type=ProxyActionType.TABLE_SWITCH):
    open: bool


__all__ = [
    "ProxyActionType",
    "ProxyClientConnect", "ProxyClientDisconnect",
    "ProxyTunnel", "ProxyOpenTable",
]
