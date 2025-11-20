from abc import ABC, abstractmethod, ABCMeta
from typing import Any

from PySide6.QtWidgets import QWidget, QGraphicsItem, QHBoxLayout, QVBoxLayout, QSizePolicy

from ClientTools.core.client import WebSocketClient
from ClientTools.core.client_data import ClientData
from CommonTools.map_widget import BaseToken, StopToken
from CommonTools.messages import *
from .tabs_map_controller import TabMapsWidget


class MetaQABC(ABCMeta, type(QWidget)):
    ...


class BaseMapController(QWidget, ABC, metaclass=MetaQABC):
    def __init__(self, socket: WebSocketClient, client: ClientData):
        super().__init__()
        self.socket = socket
        self.client = client
        self.socket.message_received.connect(self._on_message_received)
        self.active = False
        self.players_on_map: dict[str, BaseToken] = {}
        self.players: dict[str, ClientData] = {}
        
        self.defaultActive = False
        self.activeMaps: list[str] = []
        self.buffer_tokens: dict[str, Any] = {}
        
        self.moved_token = []
        
        self._init_map(client)
        self._setup_ui()
        self._connect_signals()
        
        self.visible_tokens = {
            'players': True,  # Игроки не перемещаются в режиме игрока
            'mobs': True,  # Мобы не перемещаются в режиме игрока
            'npcs': True,  # НПС не перемещаются в режиме игрока
            'spawn_point': True,  # Точка появления всегда перемещается только мастером
        }
        
    def event(self, event):
        if event.type() == StopToken.stopTypeEvent:
            self.socket.answer(ClientPlayerStop(uid=event.mime.split(":")[-1]))
        return super().event(event)
    
    def clear_buffer_token(self, name_active):
        self.activeMaps.append(name_active)
        removed = []
        
        for uid, pos in self.buffer_tokens.items():
            name, mime = uid.split("|")
            if name == name_active:
                self.add_token_no_wait(name, mime, pos)
                print(name, mime)
                removed.append(uid)
        
        for uid in removed:
            del self.buffer_tokens[uid]
    
    def set_token_movement_by_id(self, token_id: str, enabled: bool):
        """Включает/выключает перемещение для конкретного токена по ID"""
        for player_id, token in self.players_on_map.items():
            if hasattr(token, 'uid') and token.uid == token_id:
                token.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled)
                break
    
    def set_visible_token(self, tokens, enable):
        for token in tokens:
            if token in self.visible_tokens:
                self.visible_tokens[token] = enable
    
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
    
    def _init_map(self, client):
        """Инициализация карты - общая для всех контроллеров"""
        self.tabMaps = TabMapsWidget(client)
        self.tabMaps.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def _connect_signals(self):
        """Подключение общих сигналов"""
        self.socket.message_received.connect(self._on_message_received)
    
    def add_token(self, name, mime, pos):
        return self.tabMaps.create_token(name, mime, pos)
    
    # noinspection PyTypeChecker
    def _on_message_received(self, msg_raw: str):
        """Обработка общих сообщений"""
        if not self.active:
            return
        msg = BaseMessage.from_str(msg_raw)
        match msg.type:
            case MapActionType.MAP_CREATE:
                self.tabMaps.addMap(msg.name)
            case MapActionType.REMOVE_TOKEN:
                self._handle_remove_token(msg)
            case MapActionType.MOVE_TOKEN:
                self._handle_move_token(msg)
            case MapActionType.ADD_TOKEN:
                self._handle_add_token(msg)
            case _:
                self._handle_custom_message(msg)
    
    def _handle_add_token(self, msg: MapAddToken):
        if self.defaultActive and msg.name not in self.activeMaps:
            self.buffer_tokens[f"{msg.name}|{msg.mime}"] = msg.pos
        else:
            self.add_token_no_wait(msg.name, msg.mime, msg.pos)
    
    def _handle_remove_token(self, msg: MapRemoveToken):
        if self.defaultActive and msg.name not in self.activeMaps:
            del self.buffer_tokens[f"{msg.name}|{msg.mime}"]
        else:
            self.remove_token_no_wait(msg.name, msg.mime)
    
    def _handle_move_token(self, msg: MapMoveToken):
        self.moved_token.append(f"{msg.name}|{msg.mime}")
        if self.defaultActive and msg.name not in self.activeMaps:
            self.buffer_tokens[f"{msg.name}|{msg.mime}"] = msg.pos
        else:
            self.move_token_no_wait(msg.name, msg.mime, msg.pos)
    
    def update_players_list(self, players: dict[str, ClientData]):
        """Обновление списка игроков - общая логика"""
        self.players = players.copy()
        self.update_players()
    
    def update_players(self):
        if (map2 := self.tabMaps.getMap("main")) and map2.token_spawn:
            current_ids = set(self.players_on_map.keys())
            new_ids = set(self.players.keys())
            
            for player_id in current_ids - new_ids:
                token = self.players_on_map[player_id]
                self.tabMaps.removeToken(token)
            
            for player_id in new_ids - current_ids:
                cd = self.players[player_id]
                self.players_on_map[player_id] = map2.create_player(cd.name, cd.cls, player_id)
    
    @abstractmethod
    def _handle_custom_message(self, msg: BaseMessage):
        """Обработка специфичных сообщений - реализуется в потомках"""
        pass
    
    def _setup_ui(self):
        """Настройка UI - реализуется в потомках"""
        self.main_box = QHBoxLayout(self)
        self.box = QVBoxLayout()
        self.main_box.addLayout(self.box)
        
        self.box_button = QHBoxLayout()
        self.box.addWidget(self.tabMaps, 1)
        self.box.addLayout(self.box_button)
    
    def add_token_no_wait(self, name, mime, pos):
        token = self.tabMaps.create_token(name, mime, pos)
        if token is not None:
            self._apply_visible_token(token)
        self.update_players()
    
    def remove_token_no_wait(self, name, mime):
        self.tabMaps.remove_token(name, mime)
    
    def move_token_no_wait(self, name, mime, pos):
        self.tabMaps.move_token(name, mime, pos)
