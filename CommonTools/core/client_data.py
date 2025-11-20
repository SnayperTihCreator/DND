from typing import Optional

from PySide6.QtWebSockets import QWebSocket
from attrs import define, field
import json5

from CommonTools.messages import BaseMessage


@define
class ClientData:
    uid: str
    name: str
    cls: str
    
    socket: Optional[QWebSocket] = field(repr=False)
    
    is_playing: bool = field(default=False, init=False)
    
    def send_msg(self, msg: BaseMessage):
        self.send_str(msg.to_dict())
    
    def send_str(self, msg: dict):
        self.socket.sendTextMessage(json5.dumps(msg, ensure_ascii=False))
