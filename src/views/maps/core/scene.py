from typing import ClassVar

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Signal, QPointF

# from .tooltip_token import ToolTipToken
from views.maps.tricks.base import BaseTrick


class Scene(QGraphicsScene):
    SPEED_TRICKS: ClassVar[int] = 250
    
    item_moved = Signal(object)
    item_added = Signal(object)
    item_removed = Signal(object)
    item_moved_map = Signal(object, str)
    
    contextMenuRequested = Signal(QPointF)
    
    def __init__(self):
        super().__init__()
        self._grid_factor = 1.0
        self._tricks: list[BaseTrick] = []
        self.global_tooltip = None #ToolTipToken()
        super().addItem(self.global_tooltip)
        self.hide_tooltip()
        
    @property
    def grid_factor(self):
        return self._grid_factor
    
    def update_grid(self, size: int):
        self._grid_factor = size/50
        for trick in self._tricks:
            trick.update_from_grid()
    
    def show_tooltip(self, text: str, pos: QPointF):
        if not text:
            return
        if not self.global_tooltip:
            return
        
        self.global_tooltip.setToolText(text)
        tt_w = self.global_tooltip.rect_w
        tt_h = self.global_tooltip.rect_h
        x = pos.x() - tt_w / 2
        y = pos.y() - tt_h - 10
        
        self.global_tooltip.setPos(x, y)
        self.global_tooltip.show()
    
    def hide_tooltip(self):
        if not self.global_tooltip:
            return
        self.global_tooltip.hide()
    
    def addItem(self, item):
        # if isinstance(item, ToolTipToken):
        #     return super().addItem(item)
        if isinstance(item, BaseTrick):
            self._tricks.append(item)
            
        super().addItem(item)
        return self.item_added.emit(item)
    
    def removeItem(self, item):
        if item is self.global_tooltip:
            return
        
        if isinstance(item, BaseTrick):
            self._tricks.remove(item)
        
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
