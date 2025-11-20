from PySide6.QtGui import QColor

from .base_token import BaseToken


class SpawnPlayerToken(BaseToken):
    ttype = "spawn"
    
    def __init__(self, x, y):
        super().__init__(x, y, 40, QColor("#450549"), "Спавн")
        
    def mime_data(self):
        return "player",
