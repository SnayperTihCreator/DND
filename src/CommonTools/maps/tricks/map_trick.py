from pathlib import Path
from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import QPoint
from PySide6.QtGui import QPixmap, QMovie, QColor, QPen
from PySide6.QtWidgets import QGraphicsPixmapItem

if TYPE_CHECKING:
    from CommonTools.maps.core.scene import Scene


class MapFon1(QGraphicsPixmapItem):
    def __init__(self):
        super().__init__(QPixmap())
        self.path: Optional[Path] = None
        self._movie = QMovie()
        self._movie.frameChanged.connect(self._updateFrame)
        
        self._grid_size = 50
        self._grid_visible = True
        self._offset_grid = QPoint(0, 0)
        self._grid_color = QColor("#4a4a4a")
    
    def scene(self) -> "Scene":
        return super().scene()
    
    def load(self, path: Path):
        self.path = Path(path)
        match self.path.suffix.lower():
            case ".png" | ".jpg":
                self._loadStatic()
            case ".gif":
                self._loadDynamic()
    
    def _loadStatic(self):
        self.clear()
        self.setPixmap(QPixmap(self.path))
    
    def _loadDynamic(self):
        self.clear()
        self._movie.setFileName(self.path.as_posix())
        
        if not self._movie.isValid():
            self._loadStatic()
        self._movie.start()
        
        if frame := self._movie.currentPixmap():
            self.setPixmap(frame)
    
    def clear(self):
        self.setPixmap(QPixmap())
        self._movie.stop()
        self._movie.setFileName("")
        
        if self.scene():
            self.scene().update()
    
    def _updateFrame(self, _):
        if not self._movie.isValid():
            return
        
        frame = self._movie.currentPixmap()
        if frame.isNull():
            return
        self.setPixmap(frame)
        if self.scene():
            self.scene().update()
    
    def setOffsetSize(self, offset: QPoint, size: int):
        self._offset_grid = QPoint(offset)
        self._grid_size = size
        if self.scene():
            self.scene().update_grid(size)
        self.update()
    
    def setColorGrid(self, color: str):
        self._grid_color = QColor(color)
        self.update()
    
    def paint(self, painter, option, widget, /):
        super().paint(painter, option, widget)
        if self._grid_visible:
            self._draw_grid(painter)
    
    def _draw_grid(self, painter):
        painter.setPen(QPen(self._grid_color, 2))
        rect = self.boundingRect()
        
        self._draw_vertical_lines(painter, rect)
        self._draw_horizontal_lines(painter, rect)
    
    def _draw_vertical_lines(self, painter, rect):
        x = self._offset_grid.x()
        while x <= rect.width():
            painter.drawLine(x, 0, x, rect.height())
            x += self._grid_size
    
    def _draw_horizontal_lines(self, painter, rect):
        y = self._offset_grid.y()
        while y <= rect.height():
            painter.drawLine(0, y, rect.width(), y)
            y += self._grid_size
