from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QKeyEvent, QWheelEvent
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene

from ..tokens_dnd import MapWithGridItem


class ViewController:
    def __init__(self, view: QGraphicsView):
        self.view = view
        self.scene: QGraphicsScene = view.scene()
        
        self.offset = QPoint(0, 0)
        self.grid_size = 50
        self.color_grid = "#4a4a4a"
        self.grid_visible = True
        
        self.map_item: MapWithGridItem = MapWithGridItem()
        self.zoom_level = 1.0
        
        # Настройки масштабирования
        self.zoom_factor = 1.15
        self.zoom_min = 0.1
        self.zoom_max = 10.0
    
    def clear(self):
        self.map_item.clear()
    
    def load_map(self, file_path):
        self.scene.clear()
        
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            self.map_item.load(file_path)
            self.scene.addItem(self.map_item)
            self.scene.setSceneRect(self.map_item.boundingRect())
            self.updateGridRender()
            self.fit_to_view()
            return True
        return False
    
    def updateGridRender(self):
        if self.map_item is None:
            return
        self.map_item.setOffsetSize(self.offset, self.grid_size)
        self.map_item.setColorGrid(self.color_grid)
        self.map_item.grid_visible = self.grid_visible
        self.scene.update()
    
    def setVisibleGrid(self, visible):
        self.grid_visible = visible
        self.updateGridRender()
    
    def setOffsetSize(self, offset: QPoint, size: int):
        self.offset = QPoint(offset.x(), offset.y())
        self.grid_size = size
        self.updateGridRender()
    
    def setColorGrid(self, color: str):
        self.color_grid = color
        self.updateGridRender()
    
    def fit_to_view(self):
        """Подгоняет изображение под размер виджета"""
        if self.map_item:
            self.view.fitInView(self.map_item, Qt.KeepAspectRatio)
            self.zoom_level = self.view.transform().m11()
    
    def zoom_in(self):
        """Увеличивает масштаб"""
        self.zoom_level = min(self.zoom_level * self.zoom_factor, self.zoom_max)
        self._apply_zoom()
    
    def zoom_out(self):
        """Уменьшает масштаб"""
        self.zoom_level = max(self.zoom_level / self.zoom_factor, self.zoom_min)
        self._apply_zoom()
    
    def reset_zoom(self):
        """Сбрасывает масштаб к 100%"""
        self.zoom_level = 1.0
        self._apply_zoom()
    
    def _apply_zoom(self):
        """Применяет текущий уровень масштабирования"""
        self.view.resetTransform()
        self.view.scale(self.zoom_level, self.zoom_level)
    
    def wheelEvent(self, event: QWheelEvent):
        """Обработка колесика мыши для масштабирования"""
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # Передаем событие родительскому виджету
            QGraphicsView.wheelEvent(self.view, event)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Обработка клавиш"""
        key_actions = {
            Qt.Key_Plus: self.zoom_in,
            Qt.Key_Equal: self.zoom_in,
            Qt.Key_Minus: self.zoom_out,
            Qt.Key_0: self.reset_zoom,
            Qt.Key_1: self.fit_to_view,
        }
        
        if action := key_actions.get(event.key()):
            action()
        else:
            QGraphicsView.keyPressEvent(self.view, event)
    
    def toggle_fullscreen(self):
        """Переключает полноэкранный режим"""
        window = self.view.window()
        if window.isFullScreen():
            window.showNormal()
        else:
            window.showFullScreen()
