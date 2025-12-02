from PySide6.QtGui import QColor

from .base_token import BaseToken


class NPCToken(BaseToken):
    ttype = "npc"
    
    def __init__(self, x, y, name, number=None, scale=1):
        display_name = name if number == "None" else f"{name}#{number}"
        super().__init__(x, y, 35, QColor("#113f2e"), display_name, scale)
        self.name = name
        self.number = number
    
    def mime_data(self):
        return self.name, self.number
