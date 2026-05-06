from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QGraphicsItem

from ..tokens import BaseToken


class RootToken(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def addToken(self, token: BaseToken):
        token.setParentItem(self)
    
    def removeToken(self, token: BaseToken):
        token.setParentItem(None)
        if scene := self.scene(): scene.removeItem(token)
    
    def paint(self, painter, option, /, widget=...):
        pass
    
    def boundingRect(self, /):
        return QRectF()
