from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QPixmap, QMovie, QColor, QImage
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem

if TYPE_CHECKING:
    from ..core.map import Map


class BaseMapView(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.path: Optional[Path] = None
        self.setZValue(-1000)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)
    
    def scene(self) -> Map:
        return super().scene()
    
    def load(self, path: Path | str):
        self.path = Path(path)
    
    def clear(self):
        self.path = None
        if scene := self.scene(): scene.update()
    
    def paint(self, painter, option, /, widget=...):
        pass


class MapImageView(BaseMapView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = QGraphicsPixmapItem(self)
    
    def load(self, path: Path | str):
        self.clear()
        super().load(path)
        if self.path.suffix not in (".png", ".jpg", ".jpeg"): return
        self._image.setPixmap(QPixmap(self.path))
    
    def clear(self):
        self._image.setPixmap(QPixmap())
        super().clear()
    
    def boundingRect(self):
        return self._image.boundingRect()


class MapGifView(BaseMapView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = QGraphicsPixmapItem(self)
        self._movie = QMovie()
        self._movie.frameChanged.connect(self._update_pixmap)
    
    def load(self, path: Path | str):
        self.clear()
        super().load(path)
        self._movie.setFileName(self.path.as_posix())
        if not self._movie.isValid(): return [self.clear(), None][1]
        self._movie.start()
        
        if frame := self._movie.currentPixmap():
            self._image.setPixmap(frame)
        return None
    
    def clear(self):
        self._image.setPixmap(QPixmap())
        self._movie.stop()
        self._movie.setFileName("")
        super().clear()
        if scene := self.scene():
            scene.update()
    
    def _update_pixmap(self, _):
        if not self._movie.isValid():
            return
        
        if (frame := self._movie.currentPixmap()).isNull():
            return
        
        self._image.setPixmap(frame)
        if scene := self.scene():
            scene.update()
    
    def boundingRect(self, /):
        return self._image.boundingRect()


class MapPainterView(BaseMapView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pen = QPen(QColor(255, 0, 0), 3, Qt.PenStyle.SolidLine)
        self._pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self._pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self._image = QGraphicsPixmapItem(self)
        self._canvas = QImage()
        
        self._last_point: Optional[QPointF] = None
        self._composition_mode = QPainter.CompositionMode.CompositionMode_SourceOver
        self._color = self._pen.color()
        self._drawing = False
    
    def load(self, path: Path | str):
        self.clear()
        super().load(path)
        w, h = map(int, self.path.stem.split("x"))
        w, h = min(w, 4096), min(h, 4096)
        self.path = Path(self.path.with_stem(f"{w}x{h}"))
        if self.path.exists():
            self._canvas = QImage(self.path.as_posix())
        else:
            self._canvas = QImage(w, h, QImage.Format.Format_ARGB32)
            self._canvas.fill(Qt.GlobalColor.transparent)
        self._update()
    
    def _update(self):
        self._image.setPixmap(QPixmap.fromImage(self._canvas))
    
    def start_stroke(self, pos: QPointF):
        self._last_point = self._image.mapFromScene(pos)
        self._drawing = True
    
    def continue_stroke(self, pos: QPointF):
        if self._last_point is None: return
        
        current_point = self._image.mapFromScene(pos)
        
        if (current_point - self._last_point).manhattanLength() < 1:
            return
        
        painter = QPainter(self._canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self._pen)
        
        painter.setCompositionMode(self._composition_mode)
        painter.drawLine(self._last_point, current_point)
        painter.end()
        
        self._last_point = current_point
        self._update()
    
    def stop_stroke(self):
        self._last_point = None
        self._drawing = False
        self.save()
        
    @property
    def isDrawing(self):
        return self._drawing
    
    def save(self):
        if self.path and not self._canvas.isNull():
            self._canvas.save(self.path.as_posix(), "PNG")
    
    def clear(self):
        if not self._canvas.isNull():
            self._canvas.fill(Qt.GlobalColor.transparent)
            self._update()
        super().clear()
    
    def set_eraser(self, enabled: bool):
        if enabled:
            self._color = self._pen.color()
            self._pen.setColor(Qt.GlobalColor.white)
            self._composition_mode = QPainter.CompositionMode.CompositionMode_DestinationOut
        else:
            self._pen.setColor(self._color)
            self._composition_mode = QPainter.CompositionMode.CompositionMode_SourceOver
    
    def set_color(self, color: QColor):
        if self._composition_mode != QPainter.CompositionMode.CompositionMode_DestinationOut:
            self._pen.setColor(color)
        self._color = color
        
    def set_width(self, width: int):
        self._pen.setWidth(width)
        
    def set_shape(self, shape: Qt.PenCapStyle):
        self._pen.setCapStyle(shape)
    
    def boundingRect(self, /):
        return self._image.boundingRect()


class MapCustomView(BaseMapView):
    def __init__(self, parent=None):
        super().__init__(parent)


__all__ = [
    "BaseMapView",
    "MapImageView", "MapGifView", "MapPainterView", "MapCustomView",
]
