from functools import partial

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView, QTabBar
from bidict import bidict
from pydantic import ValidationError
from psygnal import Signal

from network.mime import InputMime
from .map import Map


class Maps(QGraphicsView):
    requestImage = Signal(str, object, str)  # Signal[<name-map>, <Mime> <path>]
    token_added = Signal(str, object)  # Signal[<name-map>, <token>]
    token_removed = Signal(str, object)  # Signal[<name-map>, <mime>]
    token_moved = Signal(str, object, object)  # Signal[<name-map>, <mime>, <point>]
    token_moved_map = Signal(str, object, str)  # Signal[<name-map>, <token>, <point>]
    fog_changed = Signal(str, object, bytes)  # Signal[<name-map>, <rect>, <bytes>]
    map_fon_changed = Signal(str, str)  # Signal[<name-map>, <path>]
    
    #  TODO исправить храние и изменить храниние на UID
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
        self.setAcceptDrops(True)
        
        self.tabBar = QTabBar(self)
        self.tabBar.currentChanged.connect(self._update_current_map)
        self.tabBar.setProperty("margin_top", 10)
        self._maps: bidict[str, Map] = bidict()
        self._tabs: bidict[str, int] = bidict()
        
        self._is_panning = False
        self._last_mouse_pos: QPoint = None
    
    def dragEnterEvent(self, event, /):
        try:
            InputMime.model_validate(event.mimeData().text())
            event.acceptProposedAction()
        except ValidationError:
            pass
    
    def dragMoveEvent(self, event, /):
        event.acceptProposedAction()
    
    def dropEvent(self, event, /):
        mime = InputMime.model_validate(event.mimeData().text())
        pos = self.mapToScene(event.pos())
        if scene := self.scene():
            token, avatar = scene.manager.createTokenFromInput(mime)
            self.requestImage.emit(scene.name, token.mime, avatar.as_posix())
            scene.addToken(pos, token)
        event.acceptProposedAction()
    
    def scene(self, /) -> Map:
        return super().scene()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        hint = self.tabBar.sizeHint()
        x = (self.width() - hint.width()) // 2
        self.tabBar.setGeometry(x, self.tabBar.property("margin_top"), hint.width(), hint.height())
    
    def setMarginTabBar(self, value):
        self.tabBar.setProperty("margin_top", value)
        self.update()
    
    # TODO исправить добавление
    def addMap(self, name: str, is_active: bool = True) -> Map:
        if name in self._maps:
            return self._maps[name]
        
        m = self._maps[name] = Map(self, is_active)
        m.token_added.connect(partial(self.token_added.emit, name))
        m.token_moved.connect(partial(self.token_moved.emit, name))
        m.token_removed.connect(partial(self.token_removed.emit, name))
        m.token_moved_map.connect(partial(self.token_moved_map.emit, name))
        m.fogChanged.connect(partial(self.fog_changed.emit, name))
        m.mapFonChanged.connect(partial(self.map_fon_changed, name))
        idx = self._tabs[name] = self.tabBar.addTab(name)
        
        if not is_active:
            self.tabBar.setTabVisible(idx, False)
        
        if len(self._maps) == 1:
            self.setScene(self._maps[name])
        return self._maps[name]
    
    # TODO Исправить удаление
    def removeMap(self, name: str):
        self._maps.pop(name)
        self._tabs.pop(name)
    
    def activateMap(self, name: str):
        idx = self._tabs.get(name)
        if idx is None: return
        self.tabBar.setTabVisible(idx, True)
        self.scene().active = True
    
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
            return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self._is_panning:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()
            
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
