from PySide6.QtCore import Qt, QPoint, QEvent
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView, QTabBar, QWidget, QVBoxLayout
from bidict import bidict

from .map import Map


from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QEvent
        

class Maps(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setInteractive(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.tabBar = QTabBar(self)
        self.tabBar.currentChanged.connect(self._update_current_map)
        self.tabBar.setProperty("margin_top", 10)
        self._maps: bidict[str, Map] = bidict()
        self._tabs: bidict[str, int] = bidict()
        
        self._is_panning = False
        self._last_mouse_pos: QPoint = None
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        hint = self.tabBar.sizeHint()
        x = (self.width() - hint.width()) // 2
        self.tabBar.setGeometry(x, self.tabBar.property("margin_top"), hint.width(), hint.height())
    
    def setMarginTabBar(self, value):
        self.tabBar.setProperty("margin_top", value)
        self.update()
    
    def addMap(self, name: str) -> Map:
        if name in self._maps:
            return self._maps[name]
        
        self._maps[name] = Map(self)
        self._tabs[name] = self.tabBar.addTab(name)
        
        if len(self._maps) == 1:
            self.setScene(self._maps[name])
        return self._maps[name]
    
    def _update_current_map(self, idx: int):
        name = self._tabs.inverse.get(idx)
        if not name: return
        scene = self._maps.get(name)
        if not scene: return
        self.scene().__prepare_view__(self)
        self.setScene(scene)
        self.centerOn(scene.provider)
        scene.__prepare_rect__()
    
    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            zoom_in_factor = 1.25
            zoom_out_factor = 1 / zoom_in_factor
            if event.angleDelta().y() > 0:
                self.scale(zoom_in_factor, zoom_in_factor)
            else:
                self.scale(zoom_out_factor, zoom_out_factor)
        else:
            super().wheelEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._is_panning = True
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self._is_panning:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()
            
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            
    def scene(self, /) -> Map:
        return super().scene()
