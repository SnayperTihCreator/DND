from PySide6.QtGui import QColor

from .base_token import BaseToken


class MobToken(BaseToken):
    ttype = "mob"
    def __init__(self, x, y, name, number=1):
        super().__init__(x, y, 35, QColor("#df3b28"), f"{name}#{number}")
        self.name = name
        self.number = number
        
    def mime_data(self):
        return self.name, self.number