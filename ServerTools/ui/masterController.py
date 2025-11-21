from PySide6.QtCore import QPoint

from CommonTools.core import Socket, ClientData
from CommonTools.messages import *
from CommonTools.ui.baseController import BaseController
from CommonTools.map_widget.tokens_dnd import BaseToken


class MasterController(BaseController):
    def __init__(self, socket: Socket):
        super().__init__(socket, ClientData("", "", "", None))
        
        self.tabMaps.set_token_movement(["players", "mobs", "npcs", "spawn_point"], True)
        self.tabMaps.call_all_method("setOffsetSize", QPoint(0, 0), 50)
        self.tabMaps.visible_always = True
        
        self.tabMaps.token_added.connect(self._ohandle_add_token)
        self.tabMaps.token_removed.connect(self._ohandle_remove_token)
        self.tabMaps.token_moved.connect(self._ohandle_move_token)
        self.tabMaps.token_moved_map.connect(self._ohandle_move_map)
    
    def _handle_custom_message(self, msg: BaseMessage):
        return
    
    def _ohandle_add_token(self, name, token: BaseToken):
        if self.tabMaps.isEmpty():
            return
        self.socket.send_msg(MapAddToken(name=name, mime=token.mime(), pos=token.pos().toTuple()))
        self.update_players()
            
    def _ohandle_remove_token(self, name, token: BaseToken):
        if self.tabMaps.isEmpty():
            return
        self.socket.send_msg(MapRemoveToken(name=name, mime=token.mime()))
        
    def _ohandle_move_token(self, name, token: BaseToken, pos: tuple[float, float]):
        if self.tabMaps.isEmpty():
            return
        self.socket.send_msg(MapMoveToken(name=name, mime=token.mime(), pos=pos))
        
    def _ohandle_move_map(self, from_map, token, to_map):
        pass
    
    def addMap(self, name, visible):
        self.tabMaps.addMap(name, visible)
        self.socket.send_msg(MapCreateMap(name=name, visible=visible))
        
    def removeMap(self, name):
        self.tabMaps.removeMap(name)
        self.socket.send_msg(MapDeleteMap(name=name))
    
    def removeActiveMap(self):
        self.removeMap(self.tabMaps.getActiveNameMap())
        
    def activeMap(self, name):
        if self.tabMaps.getMap(name):
            self.tabMaps.activeMap(name)
            self.socket.send_msg(MapActiveMap(name=name))
