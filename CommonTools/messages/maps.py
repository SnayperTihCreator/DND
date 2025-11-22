from .core import BaseMessage, BaseActionType

from pydantic import Field


class MapActionType(BaseActionType):
    MAPS_ALL_DATA = "map", "maps", "data"
    PLAYER_FREEZE = "map", "player", "freeze"
    PLAYER_MOVED = "map", "player", "move"
    
    LOAD_BACKGROUND = "map", "background", "data"
    
    MAP_CREATE = "map", "create", "map"
    MAP_DELETE = "map", "delete", "map"
    MAP_ACTIVE = "map", "active", "map"
    MAP_GRID_DATA = "map", "grid", "data"
    MAP_MOVE_MAP = "map", "move", "map"
    
    ADD_TOKEN = "map", "add", "token"
    REMOVE_TOKEN = "map", "remove", "token"
    MOVE_TOKEN = "map", "move", "token"


class GetAllMaps(BaseMessage, type=MapActionType.MAPS_ALL_DATA):
    pass


class MapPlayerMoved(BaseMessage, type=MapActionType.PLAYER_MOVED):
    uid: str
    pos: tuple[float, float]


class MapLoadBackground(BaseMessage, type=MapActionType.LOAD_BACKGROUND):
    name: str
    uid: str = Field("")


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


class MapFreezePlayer(BaseMessage, type=MapActionType.PLAYER_FREEZE):
    uid: str
    freeze: bool


class MapRemoveToken(MapMessageToken, type=MapActionType.REMOVE_TOKEN):
    pass


class MapMoveToken(MapMessageToken, type=MapActionType.MOVE_TOKEN):
    pos: tuple[float, float]


class MapGridData(BaseMessage, type=MapActionType.MAP_GRID_DATA):
    offset: tuple[float, float]
    size: int


class MapMovedMap(BaseMessage, type=MapActionType.MAP_MOVE_MAP):
    name: str
    mime: str
    name_target: str


__all__ = ["MapActionType",
           "MapFreezePlayer", "MapGridData",
           "MapLoadBackground",
           
           "MapCreateMap", "MapDeleteMap", "MapActiveMap",
           "MapMovedMap",  "GetAllMaps",
           
           "MapAddToken", "MapRemoveToken", "MapMoveToken",  "MapPlayerMoved"]
