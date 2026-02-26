from typing import Optional

from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve, QPointF, QEvent, QRect, QRectF
from PySide6.QtGui import QPen, QPainter, QColor, QPixmap, QPainterPath
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QMenu, QInputDialog

from CommonTools.core import TokenConfig


class MovedEvent(QEvent):
    MovedEventType = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self, pos: QPointF):
        self.pos_target = pos
        super().__init__(self.MovedEventType)


class BaseToken(QGraphicsEllipseItem):
    ttype = "service"
    _default_border = None
    
    def __init__(self, config: TokenConfig):
        super().__init__(0, 0, config.size, config.size)
        self.cfg = config
        
        self._pixmap: Optional[QPixmap] = None
        if BaseToken._default_border is None:
            BaseToken._default_border = QPixmap(":/textures/border_token.png")
        self.border_pixmap = BaseToken._default_border
        
        self.old_pos = self.pos()
        self.animation = QVariantAnimation()
        self.animation.valueChanged.connect(self.on_animation_update)
        self.animation.finished.connect(self.on_animation_finished)
        self.old_anim_pos = self.pos()
        self.is_running_anim = False
        
        x, y = self.cfg.pos.toTuple()
        size = self.cfg.size
        self.setPos(x - size / 2, y - size / 2)  # Центрируем
        self.setBrush(self.cfg.color)
        self.setPen(QPen(QColor("#000"), 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)
    
    def setPixmap(self, pixmap: str | bytes | QPixmap):
        original = QPixmap()
        if isinstance(pixmap, str):
            original.load(pixmap)
        elif isinstance(pixmap, bytes):
            original.loadFromData(pixmap)
        elif isinstance(pixmap, QPixmap):
            original = pixmap.copy()
        
        if original.isNull():
            return
        
        size = min(original.width(), original.height())
        x = (original.width() - size) // 2
        y = (original.height() - size) // 2
        cropped = original.copy(QRect(x, y, size, size))
        
        TEXTURE_SIZE = 512
        self._pixmap = cropped.scaled(
            TEXTURE_SIZE, TEXTURE_SIZE,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPen(QPen(self.cfg.color, 1.5))
        
        self.update()
    
    @property
    def isSideClient(self):
        return not (self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
    
    def setScale(self, scale):
        return super().setScale(scale * self.cfg.scale + 0.25)
    
    def setPPSize(self, size):
        aspect = size / 50
        self.setScale(aspect)
    
    def on_animation_update(self, value):
        self.old_anim_pos = value
        self.setPos(value)
        self.scene().update()
    
    def on_animation_finished(self):
        self.is_running_anim = False
    
    def setPos(self, pos, y=None):
        if y is not None:
            pos = QPointF(pos, y)
        if self.is_running_anim and pos != self.old_anim_pos:
            self.stopMoved()
        if not (self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable) and self.is_running_anim:
            self.stopMoved()
        super().setPos(pos)
    
    def move_to(self, target_pos: QPointF):
        self.is_running_anim = True
        self.old_anim_pos = self.pos()
        
        distance = ((target_pos - self.pos()).x() ** 2 + (target_pos - self.pos()).y() ** 2) ** 0.5
        
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(target_pos)
        self.animation.setDuration(distance / 5 * 1000)
        self.animation.setEasingCurve(QEasingCurve.Type.Linear)
        self.animation.start()
    
    def itemChange(self, change, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemPositionChange:
                if self.old_pos != value:
                    self.scene().item_moved.emit(self)
                    self.old_pos = self.pos()
        return super().itemChange(change, value)
    
    def mouseReleaseEvent(self, event):
        """Привязка к сетке при отпускании"""
        super().mouseReleaseEvent(event)
    
    def mousePressEvent(self, event):
        self.animation.stop()
        self.is_running_anim = False
        self.old_anim_pos = self.pos()
        super().mousePressEvent(event)
    
    def hoverEnterEvent(self, event):
        if self.isSideClient or not self.cfg.tooltip:
            return
        scene_pos = self.mapToScene(self.rect().width() / 2, 0)
        self.scene().show_tooltip(self.cfg.tooltip, scene_pos)
        
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.scene().hide_tooltip()
        super().hoverLeaveEvent(event)
    
    def stopMoved(self):
        self.animation.stop()
        self.is_running_anim = False
    
    def paint(self, painter, option, widget=None):
        """Отрисовка токена с текстом"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self._pixmap:
            path = QPainterPath()
            path.addEllipse(self.rect())
            painter.save()
            painter.setClipPath(path)
            painter.drawPixmap(self.rect().toRect(), self._pixmap)
            painter.restore()
        else:
            super().paint(painter, option, widget)
        
        BORDER_SCALE = 1.5
        w = self.rect().width() * BORDER_SCALE + 1
        h = self.rect().height() * BORDER_SCALE + 1
        x = self.rect().center().x() - (w / 2)
        y = self.rect().center().y() - (h / 2)
        painter.drawPixmap(QRectF(x, y, w, h).toRect(), self.border_pixmap)
        if self._pixmap:
            painter.setPen(self.pen())
            painter.drawEllipse(self.rect())
        self._draw_text(painter)
    
    def _draw_text(self, painter: QPainter):
        """Отрисовка текста на токене"""
        display_text = self._get_display_text()
        text_color = self._get_text_color()
        
        painter.setPen(QPen(text_color))
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        font_metrics = painter.fontMetrics()
        text_rect = font_metrics.boundingRect(display_text)
        text_rect.setHeight(font_metrics.height() * (display_text.count("\n") + 1))
        text_rect.moveCenter(self.rect().center().toPoint())
        
        painter.drawText(text_rect, display_text, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap)
    
    def _get_display_text(self):
        """Возвращает текст для отображения (обрезанный при необходимости)"""
        return text if len(text := self.cfg.text) <= 10 else f"{text[:10]}..."
    
    def _get_text_color(self):
        """Определяет цвет текста на основе фона"""
        if self._pixmap and not self._pixmap.isNull():
            img = self._pixmap.toImage()
            avg_color = img.scaled(1, 1,
                                   Qt.AspectRatioMode.IgnoreAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation).pixelColor(0, 0)
            brightness = avg_color.lightness()
        else:
            brightness = self.brush().color().lightness()
        return Qt.GlobalColor.black if brightness > 128 else Qt.GlobalColor.white
    
    def mouseMoveEvent(self, event):
        """Обновление сцены при перемещении"""
        super().mouseMoveEvent(event)
        if self.scene():
            self.scene().update()
    
    def contextMenuEvent(self, event):
        if self.isSideClient:
            return
        menu = QMenu()
        
        delete_action = menu.addAction("Удалить")
        delete_action.triggered.connect(self._handle_delete_action)
        
        moveMap = menu.addAction("Перенести")
        moveMap.triggered.connect(self._handle_move_map)
        
        menu.exec(event.screenPos())
    
    def _handle_delete_action(self):
        self.scene().removeItem(self)
    
    def _handle_move_map(self):
        text, ok = QInputDialog.getText(self.scene().views()[0], "Переместить", "UID карты")
        if ok:
            self.scene().item_moved2.emit(self, text)
    
    def mime(self):
        return self.cfg.mime(self.ttype)
