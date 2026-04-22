from __future__ import annotations
from pathlib import Path
from typing import runtime_checkable, Protocol, TYPE_CHECKING

from psygnal import Signal



if TYPE_CHECKING:
    from CommonTools.core import ClientData, NetworkConfig
    from network.messages import *
    from ServerTools.core.proxy import MasterProxyHandler


@runtime_checkable
class ServerSocketProtocol(Protocol):
    clients: dict[str, ClientData]
    assets: Path
    config: NetworkConfig
    file_loaded: Signal
    
    def answer(self, uid: str, msg: BaseMessage): ...
    
    def set_access(self, allow: bool): ...
    
    async def handle_websocket(self, websocket): ...


class ServerProxyProtocol(ServerSocketProtocol):
    proxy_handler: MasterProxyHandler
    
    async def __prepare_message__(self, uid: str, msg: BaseMessage): ...
    
    async def proxy_send(self, msg: BaseMessage, uid: str): ...
