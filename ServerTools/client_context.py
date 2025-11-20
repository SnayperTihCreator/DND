import json5
import websockets
from attrs import define, field

from CommonTools.messages import BaseMessage


@define
class ClientContext:
    uid: str
    socket: websockets.ClientConnection = field(repr=False)
    
    name: str = field(default="", init=False)
    cls: str = field(default="", init=False)
    is_master: bool = field(default=False, init=False)
    is_player: bool = field(default=False, init=False)
    
    async def send_dict(self, data: dict):
        """Отправка данных в формате JSON"""
        await self.socket.send(json5.dumps(data, ensure_ascii=False))
    
    async def send_msg(self, msg: BaseMessage):
        """Отправка структурированного сообщения"""
        await self.send_dict(msg.to_dict())
