from enum import auto, Enum
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QGraphicsItem
from views.maps.core.fog_view import FogView

from .map_view import *
from .root_token import RootToken
from .view_box import ViewBox

if TYPE_CHECKING:
    from .map import Map


class ModeMap(Enum):
    MOVE_TOKEN = auto()
    PAINTER_MAP = auto()
    FOG_MAP = auto()


class MapProvider(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self._view: Optional[BaseMapView] = None
        self._root = RootToken(self)
        self._fog = FogView(self)
        self._view_box = ViewBox(self)
        
        self._mode = ModeMap.MOVE_TOKEN
    
    def scene(self, /) -> "Map":
        return super().scene()
    
    @property
    def fog(self) -> FogView:
        return self._fog
    
    @property
    def rtoken(self):
        return self._root
    
    @property
    def mode(self) -> ModeMap:
        return self._mode
    
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
        self.fog.init(self._view.boundingRect().toRect().size())
    
    def loadAnimation(self, path: Path | str):
        if not isinstance(self._view, MapGifView) and self._view:
            self.removeItem(self._view)
            self._view = None
        if self._view is None:
            self._view = MapGifView(self)
        self._view.load(path)
        self.fog.init(self._view.boundingRect().toRect().size())
    
    def loadPainter(self, path: str):
        if not isinstance(self._view, MapPainterView) and self._view:
            self.removeItem(self._view)
            self._view = None
        if self._view is None:
            self._view = MapPainterView(self)
        self._view.load(path)
        self.fog.init(self._view.boundingRect().toRect().size())
    
    @property
    def painter(self) -> Optional[MapPainterView]:
        if isinstance(self._view, MapPainterView):
            return self._view
        return None
    
    def mousePressEvent(self, event, /):
        if (self._mode == ModeMap.PAINTER_MAP) and (painter := self.painter):
            painter.start_stroke(event.scenePos())
            event.accept()
            return
        if self._mode == ModeMap.FOG_MAP:
            self._fog.start_stroke(event.scenePos())
            event.accept()
            return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event, /):
        if (painter := self.painter) and painter.isDrawing:
            if painter.continue_stroke(event.scenePos()):
                self.scene().mapFonChanged.emit(painter.path.as_posix())
            event.accept()
            return
        if self.fog.isDrawing:
            rect, data = self._fog.continue_stroke(event.scenePos())
            if not rect.isEmpty():
                self.scene().fogChanged.emit(rect, data)
            event.accept()
            return
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event, /):
        if (painter := self.painter) and painter.isDrawing:
            painter.stop_stroke()
            event.accept()
            return
        if self.fog.isDrawing:
            self.fog.stop_stroke()
            event.accept()
            return
        super().mouseReleaseEvent(event)
    
    def setMode(self, mode: ModeMap):
        self._mode = mode
    
    def boundingRect(self):
        return self.childrenBoundingRect()
    
    def removeItem(self, item: QGraphicsItem):
        if scene := self.scene(): scene.removeItem(item)
    
    def paint(self, painter, option, /, widget=...):
        if not (scene := self.scene()): return
        if scene.grid.visible:
            self._draw_grid(painter)
