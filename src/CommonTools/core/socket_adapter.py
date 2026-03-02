import asyncio
from typing import Any
from abc import ABC, abstractmethod

from websockets import ServerConnection

from attrs import define, field


@define
class AbstractAdapterSocket(ABC):
    _ws: Any = field(repr=False)
    
    @abstractmethod
    def sendText(self, text: str): ...
    
    @abstractmethod
    def close(self): ...


@define
class SocketAdapter(AbstractAdapterSocket):
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


__all__ = ['AbstractAdapterSocket', "SocketAdapter"]
