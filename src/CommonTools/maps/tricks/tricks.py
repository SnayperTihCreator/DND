from PySide6.QtGui import QColor

from .base import BaseTrick
from .configs import MobConfigTrick, PlayerConfigTrick


class NPCTrick(BaseTrick, type="npc"):
    pass


class MobTrick(BaseTrick, type="mob"):
    def __init__(self, config: MobConfigTrick):
        config.color = QColor("#df3b28")
        super().__init__(config)


class PlayerTrick(BaseTrick, type="player"):
    config: PlayerConfigTrick
    
    def isOwnTrick(self, uid):
        return self.config.uid == uid


class SpawnPlayerTrick(BaseTrick, type="spawn"):
    pass
