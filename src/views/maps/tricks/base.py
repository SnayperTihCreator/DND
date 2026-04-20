from abc import ABCMeta, ABC, abstractmethod
from typing import ClassVar, Optional, TYPE_CHECKING

from PySide6.QtCore import QVariantAnimation, QRect, Qt, QPointF, QEasingCurve, QLineF, QRectF
from PySide6.QtGui import QPixmap, QPen, QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QMenu, QInputDialog

from .configs import BaseConfigTrick
from CommonTools.messages import TokenData

if TYPE_CHECKING:
    from ..core.scene import Scene


class QMetaAbc(ABCMeta, type(QGraphicsEllipseItem)): ...


class BaseTrick(ABC, QGraphicsEllipseItem, metaclass=QMetaAbc):
    TEXTURE_SIZE: ClassVar[int] = 512
    ttype: ClassVar[str]
    _default_border_ = None
    
    def __init__(self, config: BaseConfigTrick):
        super().__init__()
        self.config: BaseConfigTrick = config
        self._pixmap: Optional[QPixmap] = None
        
        if BaseTrick._default_border_ is None:
            BaseTrick._default_border_ = QPixmap(":/textures/border_token.png")
        self.border_pixmap = BaseTrick._default_border_
        
        r = config.size / 2
        self.setRect(-r, -r, config.size, config.size)
        x, y = self.config.pos.toTuple()
        self._trick_scale = 1.0
        super().setPos(x, y)
        
        self._old_pos = self.pos()
        self._animation = QVariantAnimation()
        self._animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._animation.valueChanged.connect(self._on_animation_update)
        self._animation.finished.connect(self._on_animation_finished)
        self._block_animation_stop = False
        self._is_running_anim = False
        
        self.setBrush(self.config.color)
        self.setPen(QPen(QColor("#000"), 2))
        self._cache_text_color = Qt.GlobalColor.black
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)
        self.update_from_grid()
    
    def __init_subclass__(cls, **kwargs):
        cls.ttype = kwargs.get("type", "service")
    
    def scene(self) -> "Scene":
        return super().scene()
    
    def itemChange(self, change, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemPositionChange:
                if self._is_running_anim and not self._block_animation_stop:
                    self.stopMoved()
                
                scene = self.scene()
                if scene:
                    if self._old_pos != value:
                        scene.item_moved.emit(self)
                        self._old_pos = value
        
        return super().itemChange(change, value)
    
    def setPixmap(self, pixmap: QPixmap | str | bytes):
        original = QPixmap()
        if isinstance(pixmap, str):
            original.load(pixmap)
        elif isinstance(pixmap, bytes):
            original.loadFromData(pixmap)
        elif isinstance(pixmap, QPixmap):
            original = pixmap
        else:
            raise TypeError()
        
        if original.isNull():
            return
        
        size = min(original.width(), original.height())
        x = (original.width() - size) // 2
        y = (original.height() - size) // 2
        cropped = original.copy(QRect(x, y, size, size))
        self._pixmap = cropped.scaled(
            self.TEXTURE_SIZE, self.TEXTURE_SIZE,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        self._cache_text_color = self._calculate_text_color()
        self.setPen(QPen(self.config.color, 1.5))
        self.update()
    
    def _calculate_text_color(self):
        if self._pixmap and not self._pixmap.isNull():
            color = self._pixmap.toImage().scaled(
                1, 1, Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation
            ).pixelColor(0, 0)
            brightness = color.lightness()
        else:
            brightness = self.brush().color().lightness()
        return Qt.GlobalColor.black if brightness > 128 else Qt.GlobalColor.white
    
    @property
    def textColor(self):
        return QColor(self._cache_text_color)
    
    @property
    def isSideClient(self):
        return not (self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
    
    def set_trick_scale(self, factor: float):
        self._trick_scale = factor
        self.update_from_grid()
    
    def update_from_grid(self):
        scene = self.scene()
        if scene is None: return
        
        self._update_trick_scale(scene.grid_factor)
    
    def _update_trick_scale(self, factor_grid: float):
        final = (factor_grid * self._trick_scale) + 0.25
        self.prepareGeometryChange()
        super().setScale(final)
    
    def _on_animation_finished(self):
        self._is_running_anim = False
    
    def _on_animation_update(self, value):
        self._block_animation_stop = True
        self.setPos(value)
        self._block_animation_stop = False
        self.scene().update()
    
    def move_to(self, pos: QPointF):
        grid_factor = self.scene().grid_factor
        line = QLineF(self.pos(), pos)
        dist_px = line.length()
        if dist_px < 1.0:
            self.setPos(pos)
            return
        
        distance = dist_px / (self.config.scale * grid_factor)
        duration = int(distance * self.scene().SPEED_TRICKS)
        duration = max(100, min(duration, 2000))
        
        self._animation.stop()
        self._is_running_anim = True
        
        self._animation.setStartValue(self.pos())
        self._animation.setEndValue(pos)
        self._animation.setDuration(duration)
        self._animation.start()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_running_anim:
                self._animation.stop()
                self._old_pos = self.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self.scene():
            self.scene().update()
    
    def hoverEnterEvent(self, event):
        if self.isSideClient or not self.config.tooltip:
            return
        
        local_top_center = QPointF(0, self.rect().top())
        scene_pos = self.mapToScene(local_top_center)
        if self.scene():
            self.scene().show_tooltip(self.config.tooltip, scene_pos)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        if self.scene():
            self.scene().hide_tooltip()
        super().hoverLeaveEvent(event)
    
    def stopMoved(self):
        self._animation.stop()
        self._is_running_anim = False
    
    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        rect = self.rect()
        
        if self._pixmap and not self._pixmap.isNull():
            painter.save()
            path = QPainterPath()
            path.addEllipse(rect)
            painter.setClipPath(path)
            
            painter.drawPixmap(rect, self._pixmap, QRectF(self._pixmap.rect()))
            painter.restore()
            
            painter.setPen(self.pen())
            painter.drawEllipse(rect)
        else:
            super().paint(painter, option, widget)
        
        if not self.border_pixmap.isNull():
            BORDER_SCALE = 1.5
            m_w = rect.width() * (BORDER_SCALE - 1) / 2
            m_h = rect.height() * (BORDER_SCALE - 1) / 2
            border_rect = rect.adjusted(-m_w, -m_h, m_w, m_h)
            painter.drawPixmap(border_rect, self.border_pixmap, QRectF(self.border_pixmap.rect()))
        self._draw_text(painter)
    
    def _draw_text(self, painter):
        text = self._get_text()
        painter.setPen(QPen(self.textColor))
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        rect = self.rect()
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, text)
    
    def _get_text(self):
        return text if len(text := self.config.title) <= 15 else text[:15]
    
    def contextMenuEvent(self, event):
        if self.isSideClient:
            return
        
        menu = QMenu()
        
        delete_action = menu.addAction("Удалить")
        delete_action.triggered.connect(self._handle_delete_action)
        
        moveMap = menu.addAction("Перенести")
        moveMap.triggered.connect(self._handle_move_map)
        
        menu.exec(event.screenPos())
    
    @classmethod
    @abstractmethod
    def create(cls, data: TokenData, *args, **kwargs):
        ...
    
    def _handle_delete_action(self):
        self.scene().removeItem(self)
    
    def _handle_move_map(self):
        text, ok = QInputDialog.getText(self.scene().views()[0], "Переместить", "UID карты")
        if ok and self.scene():
            self.scene().item_moved_map.emit(self, text)
    
    @property
    def mime(self):
        return self.config.mime
