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
                self._handle_create_map(msg)
            case MapActionType.MAP_DELETE:
                self._handle_delete_map(msg)
    
    def _handle_create_map(self, msg: MapCreateMap):
        self.tabMaps.addMap(msg.name, msg.visible)
    
    def _handle_delete_map(self, msg: MapDeleteMap):
        self.tabMaps.removeMap(msg.name)
