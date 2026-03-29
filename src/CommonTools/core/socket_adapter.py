import asyncio
from typing import Any, Protocol, Optional
from abc import ABC, abstractmethod

from websockets import ServerConnection

from attrs import define, field

from CommonTools.messages import BaseMessage


class SocketProtocol(Protocol):
    def send(self, msg: BaseMessage): ...
    
    def answer(self, uid: str, msg: BaseMessage): ...
    
    def broadcast(self, msg: BaseMessage): ...
    
    def get_me(self): ...


class ProxyServer(Protocol):
    async def proxy_send(self, msg: BaseMessage, uid: str): ...


@define
class AbstractAdapterSocket(ABC):
    _ws: Any = field(repr=False)
    
    @abstractmethod
    def close(self): ...


@define
class SenderAdapterSocket(AbstractAdapterSocket):
    @abstractmethod
    def send(self, msg: BaseMessage): ...


@define
class ProxyAdapterSocket(SenderAdapterSocket):
    uid: str
    bridge: ProxyServer
    
    def send(self, msg: BaseMessage):
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self.bridge.proxy_send(msg, self.uid))
        except RuntimeError:
            pass
    
    def close(self):
        pass


@define
class SocketAdapter(SenderAdapterSocket):
    _ws: ServerConnection = field(repr=False)
    
    def send(self, msg: BaseMessage):
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._ws.send(msg.to_str()))
        except RuntimeError:
            pass
    
    def close(self):
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._ws.close())
        except RuntimeError:
            pass


__all__ = [
    "AbstractAdapterSocket", "SenderAdapterSocket",
    "ProxyAdapterSocket",
    "SocketAdapter",
]
