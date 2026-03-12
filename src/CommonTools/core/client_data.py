from typing import Optional

from attrs import define, field
import json5

from CommonTools.messages import BaseMessage

from .socket_adapter import TextAdapterSocket
from ..mime import PlayerMime


@define
class ClientData:
    uid: str
    name: str = field(default="")
    cls: str = field(default="")
    
    socket: Optional[TextAdapterSocket] = field(repr=False, default=None)
    
    is_playing: bool = field(default=False, init=False)
    iname: Optional[str] = field(default=None, init=False)
    
    def send(self, msg: BaseMessage):
        self.socket.sendText(msg.to_str())
    
    @property
    def mime(self):
        return f"player:{self.name}:{self.cls}:{self.uid}"
    
    @property
    def mime2(self):
        return PlayerMime(name=self.name, cls=self.cls, uid=self.uid)