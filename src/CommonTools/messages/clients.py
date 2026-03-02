from typing import Optional
from .core import BaseMessage, BaseActionType


class ClientActionType(BaseActionType):
    CONNECT = "client", "connect", "data"
    
    START_PLAYER = "client", "start", "player"
    ADD_PLAYER = "client", "add", "player"
    REMOVE_PLAYER = "client", "remove", "player"
    
    NOTE_MSG = "client", "note", "msg"


class ClientNoteMsg(BaseMessage, type=ClientActionType.NOTE_MSG):
    title: str
    content: str
    idx_bg: int


class ClientConnect(BaseMessage, type=ClientActionType.CONNECT):
    uid: str


class ClientStartPlayer(BaseMessage, type=ClientActionType.START_PLAYER):
    name: str
    cls: str
    iname: Optional[str] = None


class ClientAddPlayer(BaseMessage, type=ClientActionType.ADD_PLAYER):
    uid: str
    name: str
    cls: str
    iname: Optional[str] = None


class ClientRemovePlayer(BaseMessage, type=ClientActionType.REMOVE_PLAYER):
    uid: str


__all__ = ["ClientActionType",
           "ClientConnect",
           "ClientStartPlayer", "ClientAddPlayer", "ClientRemovePlayer",
           
           "ClientNoteMsg",
           ]
