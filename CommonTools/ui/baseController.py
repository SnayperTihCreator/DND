from abc import ABCMeta, ABC, abstractmethod
from enum import Enum, auto

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import QObject, QPointF
from loguru import logger

logger = logger.bind(pack="BaseController")

from CommonTools.map_widget.tokens_dnd import BaseToken
from CommonTools.messages import *
from CommonTools.core import Socket, ClientData
from CommonTools.ui.tabs_map_controller import TabMapsWidget


class ViewFog(Enum):
    FULL = auto()
    DIFF = auto()


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
        self.activeMaps: set[str] = set()
        self.buffer_tokens: dict[tuple[str, str], tuple[QPointF, float]] = {}
        self.buffer_fog: dict[str, list[tuple[ViewFog, bool, list]]] = {}
        
        self.visible_tokens = {
            "players": True,
            "mobs": True,
            "npcs": True,
            "spawn_point": True
        }
    
    def clear_buffer(self, name_active):
        self.activeMaps.add(name_active)
        logger.success("Activate map: {name}", name=name_active)
        
        removed = []
        for (name_map, mime), (pos, scale) in self.buffer_tokens.items():
            if name_active == name_map:
                self.add_token_nw(name_map, mime, pos, scale)
                removed.append((name_map, mime))
        
        for uid in removed:
            del self.buffer_tokens[uid]
        
        fog_history = self.buffer_fog.pop(name_active)
        self.apply_fog_nw(name_active, fog_history)
    
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
    
    def update_players(self):
        if (map_main := self.tabMaps.getMap("main")) and map_main.token_spawn:
            current_ids = set(self.players_map.keys())
            new_ids = set(self.players.keys())
            
            for player_id in current_ids - new_ids:
                token = self.players_map.pop(player_id)
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
        if self.bufferActive and (msg.name not in self.activeMaps):
            self.buffer_fog.setdefault(msg.name, [])
            self.buffer_fog[msg.name].append((ViewFog.DIFF, msg.reveal, msg.data))
        else:
            self.apply_fog_nw(msg.name, [(ViewFog.DIFF, msg.reveal, msg.data)])
        return True
    
    def _handle_fog_full(self, msg: MapFogFull):
        if self.bufferActive and (msg.name not in self.activeMaps):
            self.buffer_fog[msg.name] = [(ViewFog.FULL, True, msg.data)]
        else:
            self.apply_fog_nw(msg.name, [(ViewFog.FULL, True, msg.data)])
        return True
    
    @abstractmethod
    def _handle_custom_message(self, msg: BaseMessage):
        pass
    
    def add_token(self, name, mime, pos, scale):
        if self.bufferActive and (name not in self.activeMaps):
            self.buffer_tokens[(name, mime)] = (pos, scale)
        else:
            self.add_token_nw(name, mime, pos, scale)
    
    def remove_token(self, name, mime):
        if self.bufferActive and (name not in self.activeMaps):
            self.buffer_tokens.pop((name, mime))
        else:
            self.remove_token_nw(name, mime)
    
    def move_token(self, name, mime, pos):
        if self.bufferActive and (name not in self.activeMaps):
            key = (name, mime)
            _, current_scale = self.buffer_tokens[key]
            self.buffer_tokens[key] = (pos, current_scale)
        else:
            self.move_token_nw(name, mime, pos)
    
    def add_token_nw(self, name, mime, pos, scale=1):
        token = self.tabMaps.create_token(name, mime, pos, scale)
        if token is not None:
            self._apply_visible_token(token)
        self.update_players()
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
