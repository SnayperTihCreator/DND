from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsPixmapItem


class MapWithGridItem(QGraphicsPixmapItem):
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self._setup_grid()
    
    def _setup_grid(self):
        """Настройка параметров сетки"""
        self.grid_size = 50
        self.offset_grid = QPoint(0, 0)
        self.grid_visible = True
        self.grid_color = QColor("#4a4a4a")
    
    def setOffsetSize(self, offset: QPoint, size: int):
        self.offset_grid.setX(offset.x())
        self.offset_grid.setY(offset.y())
        self.grid_size = size
    
    def setColorGrid(self, color: str):
        self.grid_color = QColor(color)
    
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
