from .core import BaseMessage, BaseActionType


class ClientActionType(BaseActionType):
    CONNECT = "client", "connect", "data"
    PLAYER_STOP = "client", "player", "stop"
    
    START_PLAYER = "client", "start", "player"
    START_MASTER = "client", "start", "master"
    
    ADD_PLAYER = "client", "add", "player"
    REMOVE_PLAYER = "client", "remove", "player"
    
    MASTER_CONNECT_HAS = "client", "master", "connect_has"


class ClientPlayerStop(BaseMessage, type=ClientActionType.PLAYER_STOP):
    uid: str


class ClientConnect(BaseMessage, type=ClientActionType.CONNECT):
    uid: str


class ClientStartPlayer(BaseMessage, type=ClientActionType.START_PLAYER):
    name: str
    cls: str


class ClientStartMaster(BaseMessage, type=ClientActionType.START_MASTER):
    tag: str


class ClientAddPlayer(BaseMessage, type=ClientActionType.ADD_PLAYER):
    uid: str
    name: str
    cls: str


class ClientRemovePlayer(BaseMessage, type=ClientActionType.REMOVE_PLAYER):
    uid: str


class ClientMasterConnectHas(BaseMessage, type=ClientActionType.MASTER_CONNECT_HAS):
    uid_callback: str


__all__ = ["ClientConnect", "ClientStartPlayer", "ClientStartMaster",
           "ClientAddPlayer", "ClientRemovePlayer", "ClientMasterConnectHas",
           
           "ClientActionType", "ClientPlayerStop"]
