from typing import Optional

from PySide6.QtCore import QPointF, Signal, QObject

from ..tokens_dnd import *
from ..utils import GridHelper
from ClientTools.utils.twoInputDialog import TwoInputDialog
from .graphicsScene import GraphicsScene


class TokenManager(QObject):
    token_added = Signal(str, QPointF)  # данные токена
    token_removed = Signal(str)  # ID токена
    token_moved = Signal(str, dict)  # ID токена и позиция
    
    def __init__(self, scene: GraphicsScene):
        super().__init__()
        self.scene = scene
        self.grid_helper = GridHelper(scene)
        
        self.tokens: dict[str, BaseToken] = {}
        self.base_size: int = 50
    
    def create_token(self, mime: str, pos: QPointF):
        if mime in self.tokens:
            return
        aligned_pos = self.grid_helper.align_to_grid(pos)
        token = self._create_token(mime, aligned_pos)
        if token is not None:
            self.token_added.emit(token.mime(), pos)
            self.tokens[token.mime()] = token
            token.setPPSize(self.base_size)
        return token
    
    def remove_token(self, mime):
        if mime in self.tokens:
            self.scene.removeItem(self.tokens[mime])
            del self.tokens[mime]
    
    def _create_token(self, mime: str, pos: QPointF) -> Optional[BaseToken]:
        match mime.split(":"):
            case ["player", name, cls, uid]:
                return self._create_player(pos, name, cls, uid)
            case ["spawn", "player"]:
                return self._create_spawn(pos)
            case ["player", uid]:
                return self._create_player(pos, "<unknown>", "", uid)
            case ["mob", name, number]:
                return self._create_mob(pos, name, number)
            case ["mob", "request"]:
                name, number = TwoInputDialog.request("Какое имя и номер у моба?", "Имя", "Номер")
                return self._create_mob(pos, name, number)
            case ["mob", name]:
                return self._create_mob(pos, name)
            case ["npc", name, function]:
                return self._create_npc(pos, name, function)
            case ["npc", "request"]:
                name, function = TwoInputDialog.request("Какое название и функция у NPC", "Название", "Функция")
                return self._create_npc(pos, name, function)
            case ["npc", name]:
                return self._create_npc(pos, name, "")
    
    def _create_player(self, pos, name, cls, uid):
        return PlayerToken(pos.x(), pos.y(), name, cls, uid)
    
    def _create_spawn(self, pos):
        for item in self.scene.items():
            if isinstance(item, SpawnPlayerToken):
                self.scene.removeItem(item)
        return SpawnPlayerToken(pos.x(), pos.y())
    
    def _create_mob(self, pos, name, number="#"):
        if name is None:
            return None
        return MobToken(pos.x(), pos.y(), name, number)
    
    def _create_npc(self, pos, name, function):
        if name is None:
            return None
        return NPCToken(pos.x(), pos.y(), name, function)
