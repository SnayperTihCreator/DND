from .core import BaseMessage, BaseActionType

from pydantic import Field


class MapActionType(BaseActionType):
    MAPS_ALL_DATA = "map", "maps", "data"
    MAP_DATA = "map", "map", "data"
    MAP_CHANGE_GRID_OFFSET = "map", "grid", "data"
    PLAYER_FREEZE = "map", "player", "freeze"
    PLAYER_MOVED = "map", "player", "move"
    
    LOAD_BACKGROUND = "map", "background", "data"
    GET_CURRENT_LOAD = "map", "load", "current"
    GET_BEGIN_LOAD = "map", "load", "begin"
    
    MAP_CREATE = "map", "create", "map"
    MAP_DELETE = "map", "delete", "map"
    MAP_ACTIVE = "map", "active", "map"
    MAP_GRID_DATA = "map", "grid", "data"
    MAP_MOVE_MAP = "map", "move", "map"
    
    ADD_TOKEN = "map", "add", "token"
    ADD_TOKEN2 = "map", "add", "token2"
    REMOVE_TOKEN = "map", "remove", "token"
    MOVE_TOKEN = "map", "move", "token"
    GET_ALL_TOKEN = "map", "token", "all"


class GetAllMaps(BaseMessage, type=MapActionType.MAPS_ALL_DATA):
    pass


class MapData(BaseMessage, type=MapActionType.MAP_DATA):
    name: str
    tokens: dict[str, tuple[float, float]]
    active: bool
    
    
class MapPlayerMoved(BaseMessage, type=MapActionType.PLAYER_MOVED):
    uid: str
    pos: tuple[float, float]


class MapChangeGridOffset(BaseMessage, type=MapActionType.MAP_CHANGE_GRID_OFFSET):
    offset: tuple[float, float]
    size: int


class MapLoadBackground(BaseMessage, type=MapActionType.LOAD_BACKGROUND):
    name: str
    uid: str = Field("")


class MapGetCurrentLoad(BaseMessage, type=MapActionType.GET_CURRENT_LOAD):
    uid: str


class MapGetBeginLoad(BaseMessage, type=MapActionType.GET_BEGIN_LOAD):
    uid: str


class MapCreateMap(BaseMessage, type=MapActionType.MAP_CREATE):
    name: str
    visible: bool
    
class MapDeleteMap(BaseMessage, type=MapActionType.MAP_DELETE):
    name: str
    
    
class MapActiveMap(BaseMessage, type=MapActionType.MAP_ACTIVE):
    name: str


class MapMessageToken(BaseMessage):
    name: str
    mime: str


class MapAddToken(MapMessageToken, type=MapActionType.ADD_TOKEN):
    pos: tuple[float, float]


class MapAddToken2(MapMessageToken, type=MapActionType.ADD_TOKEN2):
    pos: tuple[float, float]
    uid: str


class MapFreezePlayer(BaseMessage, type=MapActionType.PLAYER_FREEZE):
    uid: str
    freeze: bool


class MapRemoveToken(MapMessageToken, type=MapActionType.REMOVE_TOKEN):
    pass


class MapMoveToken(MapMessageToken, type=MapActionType.MOVE_TOKEN):
    pos: tuple[float, float]


class MapGetAllTokens(BaseMessage, type=MapActionType.GET_ALL_TOKEN):
    uid: str


class MapGridData(BaseMessage, type=MapActionType.MAP_GRID_DATA):
    offset: tuple[float, float]
    size: int


class MapMovedMap(BaseMessage, type=MapActionType.MAP_MOVE_MAP):
    name: str
    mime: str
    name_target: str


__all__ = ["MapActionType", "MapAddToken2", "MapFreezePlayer", "MapGridData",
           "MapLoadBackground", "MapGetCurrentLoad", "MapGetBeginLoad",
           
           "MapCreateMap", "MapChangeGridOffset", "MapMovedMap", "MapDeleteMap", "MapActiveMap",
           
           "MapAddToken", "MapRemoveToken", "MapMoveToken", "MapGetAllTokens",
           "MapData", "GetAllMaps", "MapPlayerMoved"]
