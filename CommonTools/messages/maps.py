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


class MapsGroup(BaseMessage):
    name: str


class MapLoadBackground(MapsGroup, type=MapActionType.LOAD_BACKGROUND):
    uid: str = Field("")


class MapCreateMap(MapsGroup, type=MapActionType.MAP_CREATE):
    visible: bool


class MapDeleteMap(MapsGroup, type=MapActionType.MAP_DELETE):
    pass


class MapActiveMap(MapsGroup, type=MapActionType.MAP_ACTIVE):
    pass


class MapMessageToken(MapsGroup):
    mime: str


class MapFreezePlayer(BaseMessage, type=MapActionType.PLAYER_FREEZE):
    freeze: bool


class MapAddToken(MapMessageToken, type=MapActionType.ADD_TOKEN):
    pos: tuple[float, float]


class MapRemoveToken(MapMessageToken, type=MapActionType.REMOVE_TOKEN):
    pass


class MapMoveToken(MapMessageToken, type=MapActionType.MOVE_TOKEN):
    pos: tuple[float, float]


class MapGridData(BaseMessage, type=MapActionType.MAP_GRID_DATA):
    offset: tuple[float, float]
    size: int


class MapMovedMap(MapMessageToken, type=MapActionType.MAP_MOVE_MAP):
    name_target: str


__all__ = ["MapActionType",
           "MapFreezePlayer", "MapGridData",
           "MapLoadBackground",
           
           "MapCreateMap", "MapDeleteMap", "MapActiveMap",
           "MapMovedMap", "GetAllMaps",
           
           "MapAddToken", "MapRemoveToken", "MapMoveToken", "MapPlayerMoved"]
