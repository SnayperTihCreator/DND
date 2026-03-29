from typing import Any

from .core import BaseMessage, BaseActionType


class ProxyActionType(BaseActionType):
    CLIENT_CONNECT = "proxy", "client", "connect"
    CLIENT_DISCONNECT = "proxy", "client", "disconnect"
    
    TUNNEL_DATA = "proxy", "tunnel", "data"


class ProxyClientConnect(BaseMessage, type=ProxyActionType.CLIENT_CONNECT):
    uid: str


class ProxyClientDisconnect(BaseMessage, type=ProxyActionType.CLIENT_DISCONNECT):
    uid: str


class ProxyTunnel(BaseMessage, type=ProxyActionType.TUNNEL_DATA):
    uid: str
    msg: Any | BaseMessage


__all__ = [
    "ProxyActionType",
    "ProxyClientConnect", "ProxyClientDisconnect",
    "ProxyTunnel",
]
