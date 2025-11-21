from PySide6.QtCore import QPoint

from CommonTools.core import Socket
from CommonTools.messages import *
from CommonTools.ui.baseController import BaseController


class PlayerController(BaseController):
    def __init__(self, socket: Socket):
        super().__init__(socket, socket.client)
        self.tabMaps.set_token_movement(["players", "mobs", "npcs", "spawn_point"], False)
        self.tabMaps.call_all_method("setOffsetSize", QPoint(0, 0), 50)
        self.tabMaps.call_all_method("setFreezeToken", True)
        
        self.set_visible_token(["spawn_point"], False)
        self.active = False
        self.bufferActive = True
    
    def _handle_custom_message(self, msg: BaseMessage):
        match msg.type:
            case MapActionType.MAP_CREATE:
                return self._handle_create_map(msg)
            case MapActionType.MAP_DELETE:
                return self._handle_delete_map(msg)
            case MapActionType.MAP_ACTIVE:
                return self._handle_active_map(msg)
            case MapActionType.MAP_GRID_DATA:
                return self._handle_grid_data(msg)
    
    def _handle_create_map(self, msg: MapCreateMap):
        return self.tabMaps.addMap(msg.name, msg.visible)
    
    def _handle_delete_map(self, msg: MapDeleteMap):
        return self.tabMaps.removeMap(msg.name)
        
    def _handle_active_map(self, msg: MapActiveMap):
        return self.tabMaps.activeMap(msg.name)
    
    def _handle_grid_data(self, msg: MapGridData):
        offset = QPoint(*msg.offset)
        self.tabMaps.call_all_method("setOffsetSize", offset, msg.size)
        return True
