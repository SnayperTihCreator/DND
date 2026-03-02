from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Signal, QPointF

from .tooltip_token import ToolTipToken


class GraphicsScene(QGraphicsScene):
    item_moved = Signal(object)
    item_added = Signal(object)
    item_removed = Signal(object)
    
    item_moved2 = Signal(object, str)
    contextMenuRequested = Signal(QPointF)
    
    def __init__(self):
        super().__init__()
        self.global_tooltip = ToolTipToken()
        super().addItem(self.global_tooltip)
        self.global_tooltip.hide()
    
    def show_tooltip(self, text: str, pos: QPointF):
        if not text:
            return
        
        self.global_tooltip.setToolText(text)
        tt_w = self.global_tooltip.rect_w
        tt_h = self.global_tooltip.rect_h
        x = pos.x() - tt_w / 2
        y = pos.y() - tt_h - 10
        
        self.global_tooltip.setPos(x, y)
        self.global_tooltip.show()
    
    def hide_tooltip(self):
        self.global_tooltip.hide()
    
    def addItem(self, item):
        if isinstance(item, ToolTipToken):
            return super().addItem(item)
        
        super().addItem(item)
        return self.item_added.emit(item)
    
    def removeItem(self, item):
        if item is self.global_tooltip:
            return
        
        self.item_removed.emit(item)
        super().removeItem(item)
    
    def clear(self):
        items = self.items().copy()
        for item in items:
            if item is self.global_tooltip:
                continue
            self.removeItem(item)
        
        self.global_tooltip.hide()
    
    def contextMenuEvent(self, event):
        self.contextMenuRequested.emit(event.scenePos())
        super().contextMenuEvent(event)
    
    def _handle_delete_item(self, item):
        self.item_removed.emit(item)
