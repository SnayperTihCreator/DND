from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QPushButton, QColorDialog


class ColorButton(QPushButton):
    color_changed = Signal(QColor)
    
    def __init__(self, parent=None, color=QColor(255, 255, 255)):
        super().__init__(parent)
        self.color = QColor(color)
        self.setMinimumHeight(40)
        self.setMaximumWidth(150)
        self.setMinimumWidth(100)
        self.pressed.connect(self._handle_pressed)
    
    def _handle_pressed(self):
        color = QColorDialog.getColor(self.color)
        if color.isValid():
            self.setColor(color)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        color_rect = self.rect().adjusted(10, 10, -10, -10)
        painter.fillRect(color_rect, self.color)
        painter.drawRect(color_rect)
        painter.setPen(Qt.GlobalColor.black if self.color.lightness() > 128 else Qt.GlobalColor.white)
        painter.drawText(self.rect().toRectF(), "Выбрать цвет", Qt.AlignmentFlag.AlignCenter)
        painter.end()
        
    
    def setColor(self, color):
        self.color = color
        self.color_changed.emit(color)
        self.update()
    
    def getColor(self):
        return self.color
