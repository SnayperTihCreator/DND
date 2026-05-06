from typing import Self

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

from .base import BaseToken
from .configs import *
from ..utils.data import CreateData


class PlayerToken(BaseToken):
    ttype = "player"
    
    def __init__(self, config: PlayerConfig):
        super().__init__(config)
        
    @classmethod
    def create(cls, data: CreateData, *args, **kwargs) -> Self:
        return cls(PlayerConfig(
            40, QPointF(0, 0), QColor("#0883f1"), data.scale, data.description,
            data.mime.name, data.mime.cls, data.mime.uid
        ))
    
    
class MobToken(BaseToken):
    ttype = "mob"
    
    def __init__(self, config: MobConfig):
        super().__init__(config)
        
    @classmethod
    def create(cls, data: CreateData, *args, **kwargs) -> Self:
        return cls(MobConfig(
            40, QPointF(0, 0), QColor("#8833f1"), data.scale, data.description,
            data.mime.name, data.mime.number
        ))
    
    
class NPCToken(BaseToken):
    ttype = "npc"
    def __init__(self, config: NPCConfig):
        super().__init__(config)
        
    @classmethod
    def create(cls, data: CreateData, *args, **kwargs) -> Self:
        return cls(NPCConfig(
            40, QPointF(0, 0), QColor("#113f2e"), data.scale, data.description,
            data.mime.name, data.mime.number
        ))
    

class SpawnPlayerToken(BaseToken):
    ttype = "spawnplayer"
    
    def __init__(self, config: SpawnPlayerConfig):
        super().__init__(config)
        
    @classmethod
    def create(cls, data: CreateData, *args, **kwargs) -> Self:
        return cls(SpawnPlayerConfig(
            40, QPointF(0, 0), QColor("#450549"), data.scale, data.description,
        ))
    