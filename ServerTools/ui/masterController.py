from PySide6.QtCore import QPoint

from CommonTools.core import Socket, ClientData
from CommonTools.messages import *
from CommonTools.ui.baseController import BaseController


class MasterController(BaseController):
    def __init__(self, socket: Socket):
        super().__init__(socket, ClientData("", "", "", None))
        
        self.tabMaps.set_token_movement(["players", "mobs", "npcs", "spawn_point"], True)
        self.tabMaps.call_all_method("setOffsetSize", QPoint(0, 0), 50)
        self.tabMaps.visible_always = True
    
    def _handle_custom_message(self, msg: BaseMessage):
        pass
    
    def addMap(self, name, visible):
        self.tabMaps.addMap(name, visible)
        self.socket.send_msg(MapCreateMap(name=name, visible=visible))
        
    def removeMap(self, name):
        self.tabMaps.removeMap(name)
        self.socket.send_msg(MapDeleteMap(name=name))
    
    def removeActiveMap(self):
        self.removeMap(self.tabMaps.getActiveNameMap())
