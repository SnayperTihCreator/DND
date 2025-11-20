from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Signal, QPointF


class GraphicsScene(QGraphicsScene):
    item_moved = Signal(object)
    item_added = Signal(object)
    item_removed = Signal(object)
    
    item_moved2 = Signal(object, str)
    contextMenuRequested = Signal(QPointF)
    
    def __init__(self):
        super().__init__()
    
    def addItem(self, item):
        super().addItem(item)
        
        self.item_added.emit(item)
    
    def removeItem(self, item):
        self.item_removed.emit(item)
        super().removeItem(item)
    
    def clear(self):
        items = self.items().copy()
        for item in items:
            self.item_removed.emit(item)
        super().clear()
        
    def contextMenuEvent(self, event):
        self.contextMenuRequested.emit(event.scenePos())
        super().contextMenuEvent(event)
    
    def _handle_delete_item(self, item):
        self.item_removed.emit(item)
