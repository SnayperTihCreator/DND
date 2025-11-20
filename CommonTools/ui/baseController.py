from abc import ABCMeta, ABC, abstractmethod
from typing import Any

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import QObject

from CommonTools.map_widget.tokens_dnd import BaseToken
from CommonTools.messages import *
from CommonTools.core import Socket, ClientData
from CommonTools.ui.tabs_map_controller import TabMapsWidget


class MetaQABC(ABCMeta, type(QObject)):
    ...


class BaseController(QMainWindow, ABC, metaclass=MetaQABC):
    def __init__(self, socket: Socket, client: ClientData):
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
        
        self.bufferActive = False
        self.activeMaps: list[str] = []
        self.buffer_tokens: dict[str, Any] = {}
        
        self.visible_tokens = {
            "players": True,
            "mobs": True,
            "npcs": True,
            "spawn_point": True
        }
    
    def clear_buffer(self, name_active):
        self.activeMaps.append(name_active)
        removed = []
        for uid, pos in self.buffer_tokens.copy().items():
            name, mime = uid.split("|")
            if name_active == name:
                self.add_token_nw(name, mime, pos)
                removed.append(uid)
        
        for uid in removed:
            del self.buffer_tokens[uid]
    
    def _apply_visible_token(self, token: BaseToken):
        match getattr(token, 'ttype', None):
            case "player":
                visible = self.visible_tokens['players']
            case "mob":
                visible = self.visible_tokens['mobs']
            case 'npc':
                visible = self.visible_tokens['npcs']
            case 'spawn':
                visible = self.visible_tokens['spawn_point']
            case _:
                visible = True  # Остальные токены не перемещаются по умолчанию
        
        token.setVisible(visible)
    
    def set_visible_token(self, tokens, enable):
        for token in tokens:
            if token in self.visible_tokens:
                self.visible_tokens[token] = enable
    
    def update_player_list(self, players: dict[str, ClientData]):
        self.players = players.copy()
        self.update_players()
    
    def update_players(self):
        if (map_main := self.tabMaps.getMap("main")) and map_main.token_spawn:
            current_ids = set(self.players_map.keys())
            new_ids = set(self.players.keys())
            
            for player_id in current_ids - new_ids:
                token = self.players_map[player_id]
                self.tabMaps.removeToken(token)
            
            for player_id in new_ids - current_ids:
                cd = self.players[player_id]
                self.players_map[player_id] = map_main.create_player(cd.name, cd.cls, player_id)
    
    # noinspection PyTypeChecker
    def handle_message(self, msg: BaseMessage):
        if not self.active:
            return
        match msg.type:
            case MapActionType.ADD_TOKEN:
                return self._handle_add_token(msg)
            case MapActionType.REMOVE_TOKEN:
                return self._handle_remove_token(msg)
            case MapActionType.MOVE_TOKEN:
                return self._handle_move_token(msg)
            case _:
                return self._handle_custom_message(msg)
    
    def _handle_add_token(self, msg: MapAddToken):
        self.add_token(msg.name, msg.mime, msg.pos)
        return True
    
    def _handle_remove_token(self, msg: MapRemoveToken):
        self.remove_token(msg.name, msg.mime)
        return True
    
    def _handle_move_token(self, msg: MapMoveToken):
        self.move_token(msg.name, msg.mime, msg.pos)
        return True
    
    @abstractmethod
    def _handle_custom_message(self, msg: BaseMessage):
        pass
    
    def add_token(self, name, mime, pos):
        if self.bufferActive and name not in self.activeMaps:
            self.buffer_tokens[f"{name}|{mime}"] = pos
        else:
            self.add_token_nw(name, mime, pos)
    
    def remove_token(self, name, mime):
        if self.bufferActive and name not in self.activeMaps:
            del self.buffer_tokens[f"{name}|{mime}"]
        else:
            self.remove_token_nw(name, mime)
    
    def move_token(self, name, mime, pos):
        if self.bufferActive and name not in self.activeMaps:
            self.buffer_tokens[f"{name}|{mime}"] = pos
        else:
            self.move_token_nw(name, mime, pos)
    
    def add_token_nw(self, name, mime, pos):
        token = self.tabMaps.create_token(name, mime, pos)
        if token is not None:
            self._apply_visible_token(token)
        self.update_players()
    
    def remove_token_nw(self, name, mime):
        self.tabMaps.removeTokenByMime(name, mime)
    
    def move_token_nw(self, name, mime, pos):
        self.tabMaps.move_token(name, mime, pos)
