from typing import Optional

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

from CommonTools.mime import BaseMime, NPCMime, MobMime, PlayerMime, SpawnMime
from CommonTools.messages import TokenData

from .scene import Scene
from ..tricks.base import BaseTrick
from ..tricks.tricks import NPCTrick, MobTrick, PlayerTrick, SpawnPlayerTrick
from ..tricks.configs import NPCConfigTrick, MobConfigTrick, PlayerConfigTrick, SpawnConfigTrick


class TrickFactory:
    @staticmethod
    def create_npc_trick(data: TokenData):
        config = NPCConfigTrick(
            data.pos,
            QColor("#113f2e"),
            data.scale,
            35,
            data.kd
        )
        return NPCTrick(config)
    
    @staticmethod
    def create_mob_trick(data: TokenData):
        config = MobConfigTrick(
            data.pos,
            QColor("#8833f1"),
            data.scale,
            35,
            data.kd
        )
        return MobTrick(config)
    
    @staticmethod
    def create_player_trick(data: TokenData, name, cls, uid):
        config = PlayerConfigTrick(
            data.pos,
            QColor("#0883f1"),
            data.scale,
            40,
            100,
            name, cls, uid
        )
        return PlayerTrick(config)
    
    @staticmethod
    def create_spawn_player_trick(data: TokenData):
        config = SpawnConfigTrick(
            data.pos,
            QColor("#450549"),
            data.scale,
            40
        )
        return SpawnPlayerTrick(config)


class TricksManager:
    def __init__(self, scene: Scene):
        self.scene = scene
        self._tricks = dict[BaseMime, BaseTrick] = {}
    
    def create_trick(self, data: TokenData):
        token: Optional[BaseTrick] = None
        
        data.pos = self.align_to_grid(data.pos)
        match data.mime:
            case NPCMime():
                token = TrickFactory.create_npc_trick(data)
            case MobMime():
                token = TrickFactory.create_mob_trick(data)
            case PlayerMime(name=name, cls=cls, uid=uid):
                token = TrickFactory.create_player_trick(data, name, cls, uid)
            case SpawnMime():
                token = TrickFactory.create_spawn_player_trick(data)
        
        if token:
            self._tricks[data.mime] = token
            token.update_from_grid()
        return token
    
    def align_to_grid(self, pos: QPointF):
        if self.scene is None:
            grid_factor = 1.0
        else:
            grid_factor = self.scene.grid_factor
        
        cell_center_x = (round(pos.x() / grid_factor) * grid_factor) + (grid_factor / 2)
        cell_center_y = (round(pos.y() / grid_factor) * grid_factor) + (grid_factor / 2)
        
        return QPointF(cell_center_x, cell_center_y)
