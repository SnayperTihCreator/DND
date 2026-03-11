import asyncio
from typing import Any, Protocol
from abc import ABC, abstractmethod

from websockets import ServerConnection

from attrs import define, field

from CommonTools.messages import BaseMessage


class SocketProtocol(Protocol):
    def send(self, msg: BaseMessage): ...
    
    def answer(self, uid: str, msg: BaseMessage): ...
    
    def broadcast(self, msg: BaseMessage): ...
    
    def get_me(self): ...


@define
class AbstractAdapterSocket(ABC):
    _ws: Any = field(repr=False)
    
    @abstractmethod
    def close(self): ...


@define
class TextAdapterSocket(AbstractAdapterSocket):
    @abstractmethod
    def sendText(self, text: str): ...


@define
class SocketAdapter(TextAdapterSocket):
    _ws: ServerConnection = field(repr=False)
    
    def sendText(self, text: str):
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._ws.send(text))
        except RuntimeError:
            pass
    
    async def _send(self, text):
        try:
            await self._ws.send(text)
        except Exception:
            pass
    
    def close(self):
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._ws.close())
        except RuntimeError:
            pass


__all__ = [
    "AbstractAdapterSocket", "TextAdapterSocket",
    "SocketAdapter",
]
