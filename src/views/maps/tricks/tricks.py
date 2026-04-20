from PySide6.QtGui import QColor

from .base import BaseTrick
from .configs import MobConfigTrick, PlayerConfigTrick, NPCConfigTrick, SpawnConfigTrick
from CommonTools.messages import TokenData


class NPCTrick(BaseTrick, type="npc"):
    @classmethod
    def create(cls, data: TokenData, *args, **kwargs):
        return cls(NPCConfigTrick(
            data.pos,
            QColor("#113f2e"),
            data.scale,
            35,
            data.kd
        ))


class MobTrick(BaseTrick, type="mob"):
    def __init__(self, config: MobConfigTrick):
        config.color = QColor("#df3b28")
        super().__init__(config)
        
    @classmethod
    def create(cls, data: TokenData, *args, **kwargs):
        return cls(MobConfigTrick(
            data.pos,
            QColor("#8833f1"),
            data.scale,
            35,
            data.kd
        ))


class PlayerTrick(BaseTrick, type="player"):
    config: PlayerConfigTrick
    
    @classmethod
    def create(cls, data: TokenData, *args, **kwargs):
        name, classe, uid, *_ = args
        return cls(PlayerConfigTrick(
            data.pos,
            QColor("#0883f1"),
            data.scale,
            40,
            100,
            name, classe, uid
        ))
    
    def isOwnTrick(self, uid):
        return self.config.uid == uid


class SpawnPlayerTrick(BaseTrick, type="spawn"):
    @classmethod
    def create(cls, data: TokenData, *args, **kwargs):
        return cls(SpawnConfigTrick(
            data.pos,
            QColor("#450549"),
            data.scale,
            40
        ))
