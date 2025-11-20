from PySide6.QtGui import QColor

from .base_token import BaseToken


class PlayerToken(BaseToken):
    ttype = "player"
    
    def __init__(self, x, y, name, cls, uid):
        super().__init__(x, y, 40, QColor("#0883f1"), f"{name}\n({cls})")
        self.name = name
        self.uid = uid
        self.cls = cls
    
    def isOwnToken(self, uid):
        return self.uid == uid
    
    def mime_data(self):
        return self.name, self.cls, self.uid
