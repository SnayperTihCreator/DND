from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING

from PySide6.QtGui import QPainter, QPen, QPixmap, QMovie
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
        
    def load(self, path: Path | str):
        self.clear()
        super().load(path)
        w, h = self.path.stem.split("x")


class MapCustomView(BaseMapView):
    def __init__(self, parent=None):
        super().__init__(parent)


__all__ = [
    "BaseMapView",
    "MapImageView", "MapGifView", "MapPainterView", "MapCustomView",
]
