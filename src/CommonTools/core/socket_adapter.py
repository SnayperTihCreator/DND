import asyncio
from abc import ABC, abstractmethod
from typing import Any

from attrs import define, field
from websockets import ServerConnection, State

from network.messages import BaseMessage
from protocols.network import ServerProxyProtocol


@define
class AbstractAdapterSocket(ABC):
    _ws: Any = field(repr=False)
    
    @abstractmethod
    def close(self): ...
    
    @abstractmethod
    def is_alive(self): ...


@define
class SenderAdapterSocket(AbstractAdapterSocket):
    @abstractmethod
    def send(self, msg: BaseMessage): ...


@define
class ProxyAdapterSocket(SenderAdapterSocket):
    uid: str
    bridge: ServerProxyProtocol
    
    def send(self, msg: BaseMessage):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.bridge.proxy_send(msg, self.uid))
        except RuntimeError:
            pass
    
    def is_alive(self):
        return bool(self.bridge)
    
    def close(self):
        pass


@define
class SocketAdapter(SenderAdapterSocket):
    _ws: ServerConnection = field(repr=False)
    
    def send(self, msg: BaseMessage):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._ws.send(msg.to_str()))
        except RuntimeError:
            pass
    
    def is_alive(self):
        return self._ws and self._ws.state == State.OPEN
    
    def close(self):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._ws.close())
        except RuntimeError:
            pass


__all__ = [
    "AbstractAdapterSocket", "SenderAdapterSocket",
    "ProxyAdapterSocket",
    "SocketAdapter",
]
