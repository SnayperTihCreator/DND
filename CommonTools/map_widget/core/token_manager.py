import re
from typing import Optional

from PySide6.QtCore import QPointF, Signal, QObject

from ..tokens_dnd import *
from ..utils import GridHelper
from CommonTools.utils.dialog_create_token import DialogCreateToken
from CommonTools.utils import MIME_RUNTIME_FORMAT, MIME_INPUT_FORMAT
from .graphicsScene import GraphicsScene


class TokenManager(QObject):
    def __init__(self, scene: GraphicsScene):
        super().__init__()
        self.scene = scene
        self.grid_helper = GridHelper(scene)
        self.tokens: dict[str, BaseToken] = {}
        
        self._token_unique_cache: dict[str, int] = {}
    
    def create_token(self, mime: str, pos: QPointF, scale=1.0):
        
        mime_rf, scale = self._normalize_mime(mime.strip(), scale)
        if mime_rf is None:
            return None
        
        if mime_rf in self.tokens:
            if mime_rf == "spawn:player:None":
                self.remove_token(mime_rf)
            else:
                mime_rf = self._reroll_id(mime_rf)
                
        if mime_rf is None:
            return None
        aligned_pos = self.grid_helper.align_to_grid(pos)
        token = self._create_token(MIME_RUNTIME_FORMAT.match(mime_rf), aligned_pos, scale)
        if token:
            self.tokens[token.mime()] = token
            token.setPPSize(self.grid_helper.get_grid_size())
        return token
    
    def _normalize_mime(self, mime, scale):
        if MIME_RUNTIME_FORMAT.match(mime) is not None:
            return mime, scale
        
        if (match_input := MIME_INPUT_FORMAT.match(mime)) is None:
            return None, None
        
        match list(match_input.groups()):
            case ["mob", "request"]:
                name, scale = DialogCreateToken.request("Моба")
                number = self._get_next_number(f"mob:{name}")
                return f"mob:{name.replace('%', '')}:{number}", scale
            case ["mob", name]:
                number = self._get_next_number(mime)
                return f"mob:{name.replace('%', '')}:{number}", scale
            case ["npc", name]:
                number = self._get_next_number(mime)
                return f"npc:{name.replace('%', '')}:{number}", scale
            case ["npc", "request"]:
                name, scale = DialogCreateToken.request("NPC")
                number = self._get_next_number(f"npc:{name}")
                return f"npc:{name.replace('%', '')}:{number}", scale
            case ["spawn", "player"]:
                return "spawn:player:None", scale
            case _:
                return mime, scale
    
    def _get_next_number(self, mime: str):
        if "%" in mime:
            return "None"
        
        uid = self._token_unique_cache.get(mime, 0) + 1
        self._token_unique_cache[mime] = uid
        return str(uid)
    
    def _reroll_id(self, mime):
        match_runtime = MIME_RUNTIME_FORMAT.match(mime)
        
        ttype, name, number, _ = match_runtime.groups()
        if ttype == "player":
            return None
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
    
    def _create_token(self, mime: re.Match[str], pos: QPointF, scale: float) -> Optional[BaseToken]:
        match list(mime.groups()):
            case ["player", name, cls, uid]:
                return self._create_player(pos, name, cls, uid)
            case ["spawn", "player", "None", None]:
                return self._create_spawn(pos)
            case ["mob", name, number, None]:
                return self._create_mob(pos, name, number, scale)
            case ["mob", name, None, None]:
                number = self._get_next_number(f"mob:{name}")
                return self._create_mob(pos, name, number, scale)
            case ["npc", name, number, None]:
                return self._create_npc(pos, name, number, scale)
            case ["npc", name, None, None]:
                number = self._get_next_number(f"npc:{name}")
                return self._create_npc(pos, name, number, scale)
    
    @staticmethod
    def _create_player(pos, name, cls, uid):
        return PlayerToken(pos.x(), pos.y(), name, cls, uid)
    
    def _create_spawn(self, pos):
        for item in self.scene.items():
            if isinstance(item, SpawnPlayerToken):
                self.scene.removeItem(item)
                del self.tokens[item.mime]
        return SpawnPlayerToken(pos.x(), pos.y())
    
    @staticmethod
    def _create_mob(pos, name, number, scale=1):
        if (name is None) or (name == "%"):
            return None
        return MobToken(pos.x(), pos.y(), name, number, scale)
    
    @staticmethod
    def _create_npc(pos, name, number, scale=1):
        if (name is None) or (name == "%"):
            return None
        return NPCToken(pos.x(), pos.y(), name, number, scale)
