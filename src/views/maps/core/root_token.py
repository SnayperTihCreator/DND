from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QGraphicsItem


class RootToken(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paint(self, painter, option, /, widget = ...):
        pass
    
    def boundingRect(self, /):
        return QRectF()