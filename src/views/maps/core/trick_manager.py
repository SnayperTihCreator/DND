from pathlib import Path
from typing import Optional

from PySide6.QtCore import QPointF

from CommonTools.mime import *
from CommonTools.messages import TokenData

from .dialog_create_trick import DialogCreateTrick, ResultDialog
from .scene import Scene
from ..tricks.base import BaseTrick
from ..tricks.tricks import NPCTrick, MobTrick, PlayerTrick, SpawnPlayerTrick


class TricksManager:
    def __init__(self, scene: Scene):
        self.scene = scene
        self._tricks: dict[BaseMime, BaseTrick] = {}
        self._tricks_cache: dict[BaseMime, int] = {}
    
    def create_trick(self, data: TokenData):
        token: Optional[BaseTrick] = None
        
        data.align(self.align_to_grid)
        match data.mime:
            case NPCMime():
                token = NPCTrick.create(data)
            case MobMime():
                token = MobTrick.create(data)
            case PlayerMime(name=name, cls=cls, uid=uid):
                token = PlayerTrick.create(data, name, cls, uid)
            case SpawnMime():
                token = self._create_spawn(data)
        
        if token:
            self._tricks[data.mime] = token
            token.update_from_grid()
        return token
    
    def create_trick_input(self, imime: InputMime, pos: QPointF) -> tuple[BaseTrick, Path]:
        mime, result = self._dialog_create_trick(imime)
        data = TokenData(mime=mime, kd=result.kd, scale=result.scale, pos=pos, image=result.path)
        return self.create_trick(data), data.image
    
    def _dialog_create_trick(self, imime: InputMime) -> tuple[Optional[TokenMime], Optional[ResultDialog]]:
        match imime:
            case InputMime(name="mob"):
                result = DialogCreateTrick.request("Моба")
                if result is None:
                    return None, None
                cmime = CacheMobMime(name=result.name)
                mime = MobMime(name=cmime.name, number=self._get_next_number(cmime, result.unique))
                return mime, result
            case InputMime(name="npc"):
                result = DialogCreateTrick.request("NPC")
                if result is None:
                    return None, None
                cmime = CacheNPCMime(name=result.name)
                mime = NPCMime(name=cmime.name, number=self._get_next_number(cmime, result.unique))
                return mime, result
            case InputMime(name="spawn-player"):
                return SpawnMime(), None
            case _:
                return None, None
    
    def _get_next_number(self, mime: CacheMime, unique: bool = False):
        if unique:
            return "0"
        
        uid = self._tricks_cache.get(mime, 0) + 1
        self._tricks_cache[mime] = uid
        return str(uid)
    
    def remove_trick(self, data: TokenMime):
        if data.mime in self._tricks:
            self.scene.removeItem(self._tricks[data.mime])
            self._tricks.pop(data.mime, None)
            return True
        return None
    
    def align_to_grid(self, pos: QPointF):
        if self.scene is None:
            grid_factor = 1.0
        else:
            grid_factor = self.scene.grid_factor
        
        cell_center_x = (round(pos.x() / grid_factor) * grid_factor) + (grid_factor / 2)
        cell_center_y = (round(pos.y() / grid_factor) * grid_factor) + (grid_factor / 2)
        
        return QPointF(cell_center_x, cell_center_y)
    
    def _create_spawn(self, data: TokenData):
        trick = self._tricks.pop(data.mime, None)
        if trick is not None:
            self.scene.removeItem(trick)
        return SpawnPlayerTrick.create(data)
