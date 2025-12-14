from PySide6.QtCore import QPoint, Signal, QPointF
from PySide6.QtWidgets import QApplication

from CommonTools.core import Socket, ClientData
from ServerTools.core.server_socket import WebSocketServer
from CommonTools.messages import *
from CommonTools.ui.baseController import BaseController
from CommonTools.map_widget.tokens_dnd import BaseToken


class MasterController(BaseController):
    socket: WebSocketServer
    error = Signal(str)
    
    def __init__(self, socket: Socket):
        super().__init__(socket, ClientData("", "", "", None))
        
        self.tabMaps.set_token_movement(["players", "mobs", "npcs", "spawn_point"], True)
        self.tabMaps.call_all_method("setMasterView", True)
        self.tabMaps.call_all_method("setOffsetSize", QPoint(0, 0), 50)
        self.tabMaps.visible_always = True
        
        self.tabMaps.token_added.connect(self._ohandle_add_token)
        self.tabMaps.token_removed.connect(self._ohandle_remove_token)
        self.tabMaps.token_moved.connect(self._ohandle_move_token)
        self.tabMaps.token_moved_map.connect(self._ohandle_move_map)
        
        self.tabMaps.fog_changed.connect(self._ohandle_fog_change)
    
    def _handle_custom_message(self, msg: BaseMessage):
        return
    
    def _ohandle_fog_change(self, name, revealing, data):
        self.socket.send_msg(MapFogChanged(name=name, reveal=revealing, data=data))
    
    def _ohandle_add_token(self, name, token: BaseToken):
        if self.tabMaps.isEmpty():
            return
        self.socket.send_msg(MapAddToken(
            name=name,
            mime=token.mime(),
            pos=token.pos().toTuple(),
            scale=token.cfg.scale
        ))
        
        if token.ttype == "spawn":
            self.update_players()
        
    def sync_client_data(self, uid: str):
        offset, size = self.tabMaps.getOffsetSize()
        self.socket.answer(uid, MapGridData(offset=offset.toTuple(), size=size))
        for map_name in self.tabMaps.maps.keys():
            mdata, tokens = self.tabMaps.getMapData(map_name)
            
            self.socket.answer(uid, MapCreateMap(name=mdata.name, visible=mdata.visible))
            if mdata.mWidget.file_map:
                self.socket.answer(uid, MapLoadBackground(name=map_name))
            for item in mdata.mWidget.items():
                QApplication.processEvents()
                QApplication.processEvents()
                if isinstance(item, BaseToken):
                    self.socket.answer(uid, MapAddToken(name=map_name, mime=item.mime(), pos=item.pos().toTuple()))
            self.socket.answer(uid, MapFogFull(name=map_name, data=mdata.mWidget.getFullFog()))
    
    def _ohandle_remove_token(self, name, token: BaseToken):
        if self.tabMaps.isEmpty():
            return
        self.socket.send_msg(MapRemoveToken(name=name, mime=token.mime()))
    
    def _ohandle_move_token(self, name, token: BaseToken, pos: tuple[float, float]):
        if self.tabMaps.isEmpty():
            return
        self.socket.send_msg(MapMoveToken(name=name, mime=token.mime(), pos=pos))
    
    def _ohandle_move_map(self, from_map: str, token: BaseToken, to_map: str):
        mapTo = self.tabMaps.getMap(to_map)
        if mapTo is None:
            self.error.emit(f"Error: Не найдена карта с именем <{to_map}>")
            return
        if mapTo.file_map is None:
            self.error.emit(f"Error: карта не загружена, загрузите карту")
            return
        mapFrom = self.tabMaps.getMap(from_map)
        mapFrom.remove_token(token.mime())
        if mapTo.token_spawn is not None:
            spawn_pos = mapTo.token_spawn.pos()
        else:
            spawn_pos = QPointF(0, 0)
        mapTo.create_token(token.mime(), spawn_pos)
    
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
