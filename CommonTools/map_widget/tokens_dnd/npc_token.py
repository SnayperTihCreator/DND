from PySide6.QtGui import QColor

from .base_token import BaseToken


class NPCToken(BaseToken):
    ttype = "npc"
    
    def __init__(self, x, y, name, function):
        super().__init__(x, y, 35, QColor("#113f2e"), name)
        self.name = name
        self.function = function
    
    def mime_data(self):
        return self.name, self.function
