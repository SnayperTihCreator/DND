from abc import ABCMeta, ABC, abstractmethod
import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout


logger = logging.getLogger("BaseController")

from CommonTools.map_layout.tokens_dnd import BaseToken
from CommonTools.messages import *
from CommonTools.core import ClientData, BufferManager, ViewFog
from CommonTools.ui.tabs_map_controller import TabMapsWidget
from CommonTools.utils import getImageMIME
from CommonTools.union import AsyncBridge


class MetaQABC(ABCMeta, type(QObject)):
    ...


class BaseController(QMainWindow, ABC, metaclass=MetaQABC):
    request_image = Signal(str, str)
    
    def __init__(self, socket: AsyncBridge, client: ClientData):
        super().__init__()
        self.socket = socket
        self.active = True
        
        self.players_map: dict[str, BaseToken] = {}
        self.players: dict[str, ClientData] = {}
        
        self.tabMaps = TabMapsWidget(client)
        self.cw = QWidget()
        self.main_box = QVBoxLayout(self.cw)
        self.setCentralWidget(self.cw)
        
        self.main_box.addWidget(self.tabMaps)
        
        self.buffer = BufferManager()
        self.tabMaps.token_image_registered.connect(self.register_image)
        self.tabMaps.request_image.connect(self.request_image)
        
        self.visible_tokens = {
            "players": True,
            "mobs": True,
            "npcs": True,
            "spawn_point": True
        }
    
    def clear_buffer(self, name_active):
        logger.info(f"Activate map: {name_active}")
        self.buffer.mark_active(name_active)
        
        for mime, pos, scale in self.buffer.popTokens(name_active):
            self.add_token_nw(name_active, mime, pos, scale)
        
        self.apply_fog_nw(name_active, self.buffer.popFog(name_active))
    
    def _apply_visible_token(self, token: BaseToken):
        visible = True
        match getattr(token, 'ttype', None):
            case "player":
                visible = self.visible_tokens['players']
            case "mob":
                visible = self.visible_tokens['mobs']
            case 'npc':
                visible = self.visible_tokens['npcs']
            case 'spawn':
                visible = self.visible_tokens['spawn_point']
        
        token.setVisible(visible)
    
    def set_visible_token(self, tokens, enable):
        for token in tokens:
            if token in self.visible_tokens:
                self.visible_tokens[token] = enable
    
    def update_player_list(self, players: dict[str, ClientData]):
        self.players = players.copy()
        self.update_players()
    
    def register_image(self, name: str, path: str):
        self.buffer.addImage(name, path)
        
        for mName, mdata in self.tabMaps.maps.items():
            for item in mdata.mWidget.items():
                if isinstance(item, BaseToken) and (getImageMIME(item.mime()) == name):
                    item.setPixmap(path)
                    
    def getImage(self, name: str):
        return self.buffer.getImage(name)
    
    def update_players(self):
        if (map_main := self.tabMaps.getMap("main")) and map_main.token_spawn:
            current_ids = set(self.players_map.keys())
            new_ids = set(self.players.keys())
            
            for player_id in current_ids - new_ids:
                token = self.players_map.pop(player_id)
                self.tabMaps.removeToken(token)
            
            for player_id in new_ids - current_ids:
                cd = self.players[player_id]
                token = self.players_map[player_id] = map_main.create_player(cd.name, cd.cls, player_id)
                img_name = getImageMIME(token.mime())
                
                if img := self.buffer.getImage(img_name):
                    token.setPixmap(img)
                else:
                    self.request_image.emit(img_name, token.mime())
    
    # noinspection PyTypeChecker
    def handle_message(self, msg: BaseMessage):
        if not self.active:
            return None
        match msg.type:
            case MapActionType.ADD_TOKEN:
                return self._handle_add_token(msg)
            case MapActionType.REMOVE_TOKEN:
                return self._handle_remove_token(msg)
            case MapActionType.MOVE_TOKEN:
                return self._handle_move_token(msg)
            case MapActionType.FOG_CHANGED:
                return self._handle_fog_change(msg)
            case MapActionType.FOG_FULL:
                return self._handle_fog_full(msg)
            case _:
                return self._handle_custom_message(msg)
    
    def _handle_add_token(self, msg: MapAddToken):
        self.add_token(msg.name, msg.mime, msg.pos, msg.scale)
        return True
    
    def _handle_remove_token(self, msg: MapRemoveToken):
        self.remove_token(msg.name, msg.mime)
        return True
    
    def _handle_move_token(self, msg: MapMoveToken):
        self.move_token(msg.name, msg.mime, msg.pos)
        return True
    
    def _handle_fog_change(self, msg: MapFogChanged):
        if self.buffer.should_buffer(msg.name):
            self.buffer.addFog(msg.name, ViewFog.DIFF, msg.reveal, msg.data)
        else:
            self.apply_fog_nw(msg.name, [(ViewFog.DIFF, msg.reveal, msg.data)])
        return True
    
    def _handle_fog_full(self, msg: MapFogFull):
        if self.buffer.should_buffer(msg.name):
            self.buffer.addFog(msg.name, ViewFog.FULL, True, msg.data)
        else:
            self.apply_fog_nw(msg.name, [(ViewFog.FULL, True, msg.data)])
        return True
    
    @abstractmethod
    def _handle_custom_message(self, msg: BaseMessage):
        pass
    
    def add_token(self, name, mime, pos, scale=1):
        if self.buffer.should_buffer(name):
            self.buffer.addToken(name, mime, pos, scale)
        else:
            self.add_token_nw(name, mime, pos, scale)
    
    def remove_token(self, name, mime):
        if self.buffer.should_buffer(name):
            self.buffer.removeToken(name, mime)
        else:
            self.remove_token_nw(name, mime)
    
    def move_token(self, name, mime, pos):
        if self.buffer.should_buffer(name):
            self.buffer.moveToken(name, mime, pos)
        else:
            self.move_token_nw(name, mime, pos)
    
    def add_token_nw(self, name, mime, pos, scale=1):
        token = self.tabMaps.create_token(name, mime, pos, scale)
        if token is None:
            return None
        
        self._apply_visible_token(token)
        imageName = getImageMIME(token.mime())
        
        if img := self.buffer.getImage(imageName):
            token.setPixmap(img)
        else:
            self.request_image.emit(imageName, token.mime())
        return token
    
    def remove_token_nw(self, name, mime):
        self.tabMaps.removeTokenByMime(name, mime)
    
    def move_token_nw(self, name, mime, pos):
        self.tabMaps.move_token(name, mime, pos)
    
    def apply_fog_nw(self, name, fogs: list[tuple[ViewFog, bool, list]]):
        if not (mWidget := self.tabMaps.getMap(name)):
            return
        for view, reveal, data in fogs:
            match view:
                case ViewFog.DIFF:
                    mWidget.setFogChange(reveal, data)
                case ViewFog.FULL:
                    mWidget.setFullFog(data)
