from PySide6.QtGui import QColor

from .base_token import BaseToken
from CommonTools.core import PlayerTokenConfig


class PlayerToken(BaseToken):
    cfg: PlayerTokenConfig
    ttype = "player"
    
    def isOwnToken(self, uid):
        return self.cfg.uid == uid
    
