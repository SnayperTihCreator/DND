from typing import Optional
from pathlib import Path

from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QPen, QPixmap, QMovie
from PySide6.QtWidgets import QGraphicsPixmapItem


class MapWithGridItem(QGraphicsPixmapItem):
    def __init__(self):
        super().__init__(QPixmap())
        
        self.file_path: Optional[Path] = None
        self.movie = QMovie()
        self.movie.frameChanged.connect(self._updateFrame)
        
        self.grid_size = 50
        self.grid_visible = True
        self.offset_grid = QPoint(0, 0)
        self.grid_color = QColor("#4a4a4a")
    
    def load(self, file_path):
        self.file_path = Path(file_path)
        match self.file_path.suffix.lower():
            case ".png" | ".jpg":
                self._loadStatic()
            case ".gif":
                self._loadDynamic()
    
    def _loadStatic(self):
        self.setPixmap(QPixmap(self.file_path))
    
    def _loadDynamic(self):
        self.movie.setFileName(self.file_path.as_posix())
        if not self.movie.isValid():
            self._loadStatic()
            return
        self.movie.start()
        
        if frame := self.movie.currentPixmap():
            self.setPixmap(frame)
    
    def clear(self):
        self.setPixmap(QPixmap())
        self.movie.stop()
        self.movie.setFileName("")
        self.scene().update()
    
    def _updateFrame(self, _):
        if not self.movie.isValid():
            return
        frame = self.movie.currentPixmap()
        if frame.isNull():
            return
        self.setPixmap(frame)
        if self.scene():
            self.scene().update()
    
    def setOffsetSize(self, offset: QPoint, size: int):
        self.offset_grid.setX(offset.x())
        self.offset_grid.setY(offset.y())
        self.grid_size = size
        self.update()
    
    def setColorGrid(self, color: str):
        self.grid_color = QColor(color)
        self.update()
    
    def paint(self, painter, option, widget=None):
        """Отрисовка карты и сетки"""
        super().paint(painter, option, widget)
        if self.grid_visible:
            self._draw_grid(painter)
    
    def _draw_grid(self, painter):
        """Отрисовка сетки поверх карты"""
        painter.setPen(QPen(self.grid_color, 2))
        rect = self.boundingRect()
        
        self._draw_vertical_lines(painter, rect)
        self._draw_horizontal_lines(painter, rect)
    
    def _draw_vertical_lines(self, painter, rect):
        """Отрисовка вертикальных линий сетки"""
        x = self.offset_grid.x()
        while x <= rect.width():
            painter.drawLine(x, 0, x, rect.height())
            x += self.grid_size
    
    def _draw_horizontal_lines(self, painter, rect):
        """Отрисовка горизонтальных линий сетки"""
        y = self.offset_grid.y()
        while y <= rect.height():
            painter.drawLine(0, y, rect.width(), y)
            y += self.grid_size
