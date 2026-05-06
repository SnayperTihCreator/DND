import zlib
from typing import Optional

from PySide6.QtCore import QRectF, Qt, QRect, QSize, QPointF
from PySide6.QtGui import QImage, QPixmap, QColor, QPainter, QBrush, QPen, QBitmap, QRegion
from PySide6.QtWidgets import QGraphicsItem
from icecream import ic


class FogView(QGraphicsItem):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setZValue(1000)
        self._mask = QImage()
        self._texture = QPixmap(":/textures/fog.png")
        
        self._pen = QPen(Qt.GlobalColor.white, 20, Qt.PenStyle.SolidLine)
        self._pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self._pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self._last_point: Optional[QPointF] = None
        self._drawing = False
        
        if self._texture.isNull():
            self._texture = QPixmap(256, 256)
            self._texture.fill(QColor(30, 30, 35))
    
    def init(self, size: QSize):
        self.prepareGeometryChange()
        self._mask = QImage(size.width(), size.height(), QImage.Format.Format_Grayscale8)
        self.fill()
    
    @property
    def isDrawing(self):
        return self._drawing
    
    def clear(self):
        if self._mask.isNull(): return QRect(), b""
        self._mask.fill(Qt.GlobalColor.white)
        self.update()
        return self.mask()
    
    def fill(self):
        if self._mask.isNull(): return QRect(), b""
        self._mask.fill(Qt.GlobalColor.black)
        self.update()
        return self.mask()
    
    def mask(self, rect: Optional[QRect] = None) -> tuple[QRect, bytes]:
        if self._mask.isNull(): return QRect(), b""
        
        target = rect if rect else self._mask.rect()
        target = target.intersected(self._mask.rect())
        if target.isEmpty(): return QRect(), b""
        
        patch = self._mask.copy(target)
        rdata = patch.constBits().tobytes()
        data = zlib.compress(rdata, level=9)
        return QRect(target), data
    
    def set_eraser(self, enabled: bool):
        self._pen.setColor(Qt.GlobalColor.black if not enabled else Qt.GlobalColor.white)
    
    def set_width(self, size):
        self._pen.setWidth(size)
    
    def start_stroke(self, pos: QPointF):
        self._last_point = self.mapFromScene(pos)
        self._drawing = True
    
    def continue_stroke(self, pos: QPointF):
        if self._mask.isNull() or self._last_point is None:
            return QRect(), b""
        
        current_point = self.mapFromScene(pos)
        
        if (current_point - self._last_point).manhattanLength() < 2:
            return QRect(), b""
        
        painter = QPainter(self._mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self._pen)
        painter.drawLine(self._last_point, current_point)
        painter.end()
        
        dirty_rect = QRectF(self._last_point, current_point).normalized().toRect()
        r = self._pen.width() + 2
        dirty_rect.adjust(-r, -r, r, r)
        
        self.update(QRectF(dirty_rect))
        self._last_point = current_point
        
        return self.mask(dirty_rect)
    
    def stop_stroke(self):
        self._last_point = None
        self._drawing = False
    
    def updateMask(self, rect: QRect, data: bytes):
        rdata = zlib.decompress(data)
        patch = QImage(rdata, rect.width(), rect.height(), QImage.Format.Format_Alpha8).copy()
        painter = QPainter(self._mask)
        painter.drawImage(rect.topLeft(), patch)
        painter.end()
        self.update(rect)
    
    def boundingRect(self, /):
        if self._mask.isNull():
            return QRectF()
        return self._mask.rect().toRectF()
    
    def paint(self, painter, option, /, widget=...):
        if self._mask.isNull():
            return
        
        painter.save()
        
        # painter.drawTiledPixmap(self._mask.rect(), self._texture)
        # # painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        # painter.drawImage(0, 0, self._mask)
        
        bitmap = QBitmap.fromImage(self._mask)
        painter.setClipRegion(QRegion(bitmap))
        painter.drawTiledPixmap(self._mask.rect(), self._texture)
        
        painter.restore()
