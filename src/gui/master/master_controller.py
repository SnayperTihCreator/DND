import logging
from pathlib import Path

from PySide6.QtCore import QPoint, Signal, QPointF

from CommonTools.core import ClientData
from CommonTools.map_layout import BaseToken
from CommonTools.ui.base_controller import BaseController
from ServerTools.core import AsyncServerBridge
from network.messages import *
from network.mime import TokenMime

logger = logging.getLogger(__name__)


class MasterController(BaseController):
    socket: AsyncServerBridge
    error = Signal(str)
    
    def __init__(self, socket: AsyncServerBridge):
        super().__init__(socket, ClientData(""))
        
        self.tabMaps.set_token_movement(["players", "mobs", "npcs", "spawn_point"], True)
        self.tabMaps.call_all_method("setMasterView", True)
        self.tabMaps.call_all_method("setOffsetSize", QPoint(0, 0), 50)
        self.tabMaps.visible_always = True
        
        self.tabMaps.token_added.connect(self._ohandle_add_token)
        self.tabMaps.token_removed.connect(self._ohandle_remove_token)
        self.tabMaps.token_moved.connect(self._ohandle_move_token)
        self.tabMaps.token_moved_map.connect(self._ohandle_move_map)
        
        self.tabMaps.fog_changed.connect(self._ohandle_fog_change)
        self.tabMaps.request_image.connect(self.applyAvatar)
    
    def applyAvatar(self, avatar, mime):
        print(avatar, mime)
        if not (img := self.buffer.getImage(avatar)): return
        
        for mName, mdata in self.tabMaps.maps.items():
            if not (token := mdata.mWidget.token_manager.tokens.get(mime)): continue
            
            token.setPixmap(img)
    
    async def _handle_custom_message(self, msg: BaseMessage):
        return
    
    def _ohandle_fog_change(self, name, revealing, data):
        self.socket.send(MapFogChanged(name=name, reveal=revealing, data=data))
    
    def _ohandle_add_token(self, name, token: BaseToken):
        if self.tabMaps.isEmpty():
            return
        self.socket.send(MapAddToken(
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
            
            if mdata.path:
                filename = self.socket.loadTo(mdata.path)
                self.socket.answer(uid, SystemResourceAvailable(filename=filename))
                self.socket.answer(uid, MapLoadBackground(mime=mdata.mime, filename=filename))
            
            for item in mdata.mWidget.items():
                if isinstance(item, BaseToken):
                    self.socket.answer(uid, MapAddToken(name=map_name, mime=item.mime(), pos=item.pos().toTuple()))
            
            self.socket.answer(uid, MapFogFull(name=map_name, data=mdata.mWidget.getFullFog()))
    
    def _ohandle_remove_token(self, name, token: BaseToken):
        if self.tabMaps.isEmpty():
            return
        self.socket.send(MapRemoveToken(name=name, mime=token.mime()))
    
    def _ohandle_move_token(self, name, token: BaseToken, pos: tuple[float, float]):
        if self.tabMaps.isEmpty():
            return
        self.socket.send(MapMoveToken(name=name, mime=token.mime(), pos=pos))
    
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
        self.socket.send(MapCreateMap(name=name, visible=visible))
    
    def removeMap(self, name):
        self.tabMaps.removeMap(name)
        self.socket.send(MapDeleteMap(name=name))
    
    def removeActiveMap(self):
        self.removeMap(self.tabMaps.getActiveNameMap())
    
    def activeMap(self, name):
        if self.tabMaps.getMap(name):
            self.tabMaps.activeMap(name)
            self.socket.send(MapActiveMap(name=name))
    
    def _load_image(self, filename: Path, mime: TokenMime):
        self.register_image(mime.to_str().removeprefix("token:"), filename)
    
    @BaseController.router.handler(ClientActionType.LOAD_AVATAR)
    def _handle_load_avatar(self, _: str, msg: ClientLoadAvatar):
        logger.info("Loading avatar: %s", msg.mime)
        self.socket.manager.add_task(msg.filename, self._load_image, args=(msg.mime,))
        return True
