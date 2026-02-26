from typing import Optional

from attrs import define, field
import json5

from CommonTools.messages import BaseMessage

from .socket_adapter import AbstractAdapterSocket


@define
class ClientData:
    uid: str
    name: str = field(default="")
    cls: str = field(default="")
    
    socket: Optional[AbstractAdapterSocket] = field(repr=False, default=None)
    
    is_playing: bool = field(default=False, init=False)
    iname: Optional[str] = field(default=None, init=False)
    
    def send_msg(self, msg: BaseMessage):
        self.send_str(msg.to_dict())
    
    def send_str(self, msg: dict):
        self.socket.sendText(json5.dumps(msg, ensure_ascii=False))
    
    @property
    def mime(self):
        return f"player:{self.name}:{self.cls}:{self.uid}"
