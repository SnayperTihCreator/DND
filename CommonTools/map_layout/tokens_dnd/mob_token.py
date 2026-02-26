from PySide6.QtGui import QColor

from .base_token import BaseToken
from CommonTools.core import ModNpcTokenConfig


class MobToken(BaseToken):
    ttype = "mob"
    
    def __init__(self, config: ModNpcTokenConfig):
        config.color = QColor("#df3b28")
        super().__init__(config)
