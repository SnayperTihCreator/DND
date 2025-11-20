from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve, QPointF, QEvent
from PySide6.QtGui import QPen, QPainter, QColor
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QMenu, QApplication, QInputDialog


class MovedEvent(QEvent):
    MovedEventType = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self, pos: QPointF):
        self.pos_target = pos
        super().__init__(self.MovedEventType)


class BaseToken(QGraphicsEllipseItem):
    ttype = "service"
    
    def __init__(self, x, y, size=40, color=QColor("#fff"), text=""):
        super().__init__(0, 0, size, size)
        self.text = text
        self.size = size
        
        self.old_pos = self.pos()
        self.animation = QVariantAnimation()
        self.animation.valueChanged.connect(self.on_animation_update)
        self.animation.finished.connect(self.on_animation_finished)
        self.old_anim_pos = self.pos()
        self.is_running_anim = False
        
        self._setup_token(x, y, size, color)
    
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
    
    def _setup_token(self, x, y, size, color):
        """Настройка базовых параметров токена"""
        self.setPos(x - size / 2, y - size / 2)  # Центрируем
        self.setBrush(color)
        self.setPen(QPen(QColor("#000"), 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
    
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
        super().mousePressEvent(event)
    
    def stopMoved(self):
        self.animation.stop()
        self.is_running_anim = False
    
    def paint(self, painter, option, widget=None):
        """Отрисовка токена с текстом"""
        super().paint(painter, option, widget)
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
        return self.text if len(self.text) <= 10 else f"{self.text[:10]}..."
    
    def _get_text_color(self):
        """Определяет цвет текста на основе фона"""
        bg_color = self.brush().color()
        brightness = (bg_color.red() * 0.299 +
                      bg_color.green() * 0.587 +
                      bg_color.blue() * 0.114)
        return Qt.black if brightness > 186 else Qt.white
    
    def mouseMoveEvent(self, event):
        """Обновление сцены при перемещении"""
        super().mouseMoveEvent(event)
        if self.scene():
            self.scene().update()
    
    def contextMenuEvent(self, event):
        if not (self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable):
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
    
    def mime_data(self):
        return []
    
    def mime(self):
        return f"{self.ttype}:{':'.join(map(str, self.mime_data()))}"
