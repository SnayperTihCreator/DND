from pathlib import Path
from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QGraphicsItem

from .map_view import *

if TYPE_CHECKING:
    from .map import Map


class MapProvider(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self._view: Optional[BaseMapView] = None
        
    def scene(self, /) -> "Map": return super().scene()
    
    def _draw_vertical_lines(self, painter, rect):
        if not (scene := self.scene()): return
        if scene.grid.size <= 10: return
        if scene.grid.size > 200: return
        
        x = scene.grid.offset.x()
        while x <= rect.width():
            painter.drawLine(x, 0, x, rect.height())
            x += scene.grid.size
    
    def _draw_horizontal_lines(self, painter, rect):
        if not (scene := self.scene()): return
        if scene.grid.size <= 10: return
        if scene.grid.size > 200: return
        
        y = scene.grid.offset.y()
        while y <= rect.height():
            painter.drawLine(0, y, rect.width(), y)
            y += scene.grid.size
    
    def _draw_grid(self, painter: QPainter):
        if not (scene := self.scene()): return
        painter.save()
        painter.setPen(QPen(scene.grid.color, 0))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        rect = self.boundingRect()
        
        self._draw_vertical_lines(painter, rect)
        self._draw_horizontal_lines(painter, rect)
        painter.restore()
    
    def loadStatic(self, path: Path | str):
        if not isinstance(self._view, MapImageView) and self._view:
            self.removeItem(self._view)
            self._view = None
        if self._view is None:
            self._view = MapImageView(self)
        self._view.load(path)
        
    def loadAnimation(self, path: Path | str):
        if not isinstance(self._view, MapGifView) and self._view:
            self.removeItem(self._view)
            self._view = None
        if self._view is None:
            self._view = MapGifView(self)
        self._view.load(path)
        
    def loadPainter(self, path: str):
        if not isinstance(self._view, MapPainterView) and self._view:
            self.removeItem(self._view)
            self._view = None
        if self._view is None:
            self._view = MapGifView(self)
        self._view.load(path)
        
    @property
    def view_painter(self) -> Optional[MapPainterView]:
        if isinstance(self._view, MapPainterView):
            return self._view
        return None
    
    def boundingRect(self):
        return self.childrenBoundingRect()
    
    def removeItem(self, item: QGraphicsItem):
        if scene := self.scene(): scene.removeItem(item)
    
    def paint(self, painter, option, /, widget=...):
        if not (scene := self.scene()): return
        if scene.grid.visible:
            self._draw_grid(painter)
