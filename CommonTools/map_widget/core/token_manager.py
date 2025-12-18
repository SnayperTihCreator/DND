import re
from typing import Optional

from PySide6.QtCore import QPointF, QObject, Signal
from PySide6.QtGui import QColor

from ..tokens_dnd import *
from ..utils import GridHelper
from CommonTools.utils.dialog_create_token import DataDialog, DialogCreateToken
from CommonTools.utils import MIME_RUNTIME_FORMAT, MIME_INPUT_FORMAT, getImageMIME
from CommonTools.core import PlayerTokenConfig, SpawnPlayerTokenConfig, ModNpcTokenConfig
from .graphicsScene import GraphicsScene


class TokenManager(QObject):
    image_registered = Signal(str, str)
    
    def __init__(self, scene: GraphicsScene):
        super().__init__()
        self.scene = scene
        self.grid_helper = GridHelper(scene)
        self.tokens: dict[str, BaseToken] = {}
        
        self._token_unique_cache: dict[str, int] = {}
    
    def create_token(self, mime: str, pos: QPointF, scale=1.0):
        
        mime_rf, result = self._normalize_mime(mime.strip())
        if mime_rf is None:
            return None
        
        if mime_rf in self.tokens:
            if mime_rf == "spawn:player:None":
                self.remove_token(mime_rf)
            else:
                mime_rf = self._reroll_id(mime_rf)
        
        aligned_pos = self.grid_helper.align_to_grid(pos)
        result = self._normalize_result(mime_rf, result, scale)
        token = self._create_token(mime_rf, aligned_pos, result)
        if token:
            self.tokens[token.mime()] = token
            token.setPPSize(self.grid_helper.get_grid_size())
        return token
    
    @staticmethod
    def _normalize_result(mime: str, result: DataDialog, scale: float):
        match = MIME_RUNTIME_FORMAT.match(mime)
        if not match:
            return None
        if result is None:
            result = DataDialog("None", "", 10, False, 10, scale)
        result.name = match.group(1)
        match list(match.groups()):
            case ["mob" | "npc", _, "None", None]:
                result.unique = True
                return result
            case _:
                return result
    
    def _normalize_mime(self, mime):
        if MIME_RUNTIME_FORMAT.match(mime) is not None:
            return mime, None
        
        if (match_input := MIME_INPUT_FORMAT.match(mime)) is None:
            return None, None
        
        match list(match_input.groups()):
            case ["mob", "request"]:
                result = DialogCreateToken.request("Моба")
                if result is None:
                    return None, None
                number = self._get_next_number(result.cttype("mob"), result.unique)
                mime_rf = result.cttypeAndNumber("mob", number)
                
                if result.image_path is not None:
                    name = getImageMIME(mime_rf)
                    self.image_registered.emit(name, result.image_path)
                    
                return mime_rf, result
            case ["npc", "request"]:
                result = DialogCreateToken.request("NPC")
                if result is None:
                    return None, None
                number = self._get_next_number(result.cttype("npc"), result.unique)
                mime_rf = result.cttypeAndNumber("npc", number)
                
                if result.image_path is not None:
                    name = getImageMIME(mime_rf)
                    self.image_registered.emit(name, result.image_path)
                
                return mime_rf, result
            case ["spawn", "player"]:
                return "spawn:player:None", None
            case _:
                return mime, None
    
    def _get_next_number(self, mime: str, unique: bool = False):
        if unique:
            return "None"
        
        uid = self._token_unique_cache.get(mime, 0) + 1
        self._token_unique_cache[mime] = uid
        return str(uid)
    
    def _reroll_id(self, mime):
        match_runtime = MIME_RUNTIME_FORMAT.match(mime)
        
        ttype, name, number, _ = match_runtime.groups()
        if ttype == "player":
            return mime
        if number == "None":
            return mime
        ext_number = self._token_unique_cache.get(f"{ttype}:{name}", 0)
        if int(number) < ext_number:
            number = self._get_next_number(f"{ttype}:{name}")
            mime = f"{ttype}:{name}:{number}"
        return mime
    
    def remove_token(self, mime):
        if mime in self.tokens:
            self.scene.removeItem(self.tokens[mime])
            self.tokens.pop(mime, None)
            return True
        return None
    
    def _create_token(self, mime: str, pos: QPointF, result: Optional[DataDialog]) -> Optional[BaseToken]:
        match_res = MIME_RUNTIME_FORMAT.match(mime)
        if not match_res:
            return None
        
        match list(match_res.groups()):
            case ["player", name, cls, uid]:
                return PlayerToken(PlayerTokenConfig(pos, QColor("#0883f1"), result.scale, 40, 100, name, cls, uid))
            case ["spawn", "player", "None", None]:
                return self._create_spawn(pos, result)
            case ["mob", name, number, None]:
                return MobToken(ModNpcTokenConfig(
                    pos, QColor("#0883f1"), result.scale, result.kd, name, number,
                    result.unique, result.hp, result.description, 35))
            case ["mob" | "npc" as ttype, name, number, None]:
                if number is None:
                    number = self._get_next_number(result.cttype(ttype), result.unique)
                
                color = QColor("#8833f1") if ttype == "mob" else QColor("#113f2e")
                
                config = ModNpcTokenConfig(
                    pos, color, result.scale, result.kd, name, number,
                    result.unique, result.hp, result.description, 35
                )
                
                if ttype == "mob":
                    return MobToken(config)
                else:
                    return NPCToken(config)
    
    def _create_spawn(self, pos, result):
        item = self.tokens.get("spawn:player:None", None)
        if item is not None:
            self.scene.removeItem(item)
            del self.tokens[item.mime]
        return SpawnPlayerToken(SpawnPlayerTokenConfig(pos, QColor("#450549"), result.scale, 40))
