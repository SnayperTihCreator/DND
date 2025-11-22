from .core import BaseMessage, BaseActionType


class ClientActionType(BaseActionType):
    CONNECT = "client", "connect", "data"
    
    START_PLAYER = "client", "start", "player"
    ADD_PLAYER = "client", "add", "player"
    REMOVE_PLAYER = "client", "remove", "player"


class ClientConnect(BaseMessage, type=ClientActionType.CONNECT):
    uid: str


class ClientStartPlayer(BaseMessage, type=ClientActionType.START_PLAYER):
    name: str
    cls: str


class ClientAddPlayer(BaseMessage, type=ClientActionType.ADD_PLAYER):
    uid: str
    name: str
    cls: str


class ClientRemovePlayer(BaseMessage, type=ClientActionType.REMOVE_PLAYER):
    uid: str


__all__ = ["ClientActionType",
           "ClientConnect",
           "ClientStartPlayer", "ClientAddPlayer", "ClientRemovePlayer"
           ]
