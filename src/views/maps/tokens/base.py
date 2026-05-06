from __future__ import annotations

from abc import ABCMeta, ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, ClassVar, Self

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPixmap, QPen, QColor, QBrush, QTransform
from PySide6.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsPixmapItem, QGraphicsTextItem

if TYPE_CHECKING:
    from ..core.map import Map

from .configs import BaseConfig
from ..utils.data import CreateData


class BaseToken(QGraphicsEllipseItem):
    TEXTURE_SIZE: ClassVar[int] = 512
    BORDER_SCALE: ClassVar[float] = 1.5
    __default_border__: ClassVar[Optional[QPixmap]] = None
    ttype: ClassVar[str]
    
    def __init__(self, config: BaseConfig):
        self._cache_text_color = Qt.GlobalColor.black
        r = config.size / 2
        super().__init__(-r, -r, config.size, config.size)
        self.config = config
        self._token_scale = config.scale
        self.setPos(self.config.pos)
        
        self.setBrush(self.config.color)
        pen = QPen(QColor("#000000"), 1.5)
        pen.setCosmetic(True)
        self.setPen(pen)
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)
        
        self.avatar = QGraphicsEllipseItem(self.rect(), self)
        self.avatar.setPen(Qt.PenStyle.NoPen)
        
        self.border = QGraphicsPixmapItem(self)
        if BaseToken.__default_border__ is None:
            BaseToken.__default_border__ = QPixmap(":/textures/border_token.png")
        self.border.setPixmap(BaseToken.__default_border__)
        target_width = self.rect().width() * self.BORDER_SCALE
        self.border.setScale(target_width / BaseToken.__default_border__.width())
        bb_rect = self.border.boundingRect()
        self.border.setPos(-bb_rect.width() * self.border.scale() / 2,
                           -bb_rect.height() * self.border.scale() / 2)
        
        self.label = QGraphicsTextItem("", self)
        self.label.setDefaultTextColor(Qt.GlobalColor.black)
        self.label.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.label.setTextWidth(self.rect().width() + 10)
        option_label = self.label.document().defaultTextOption()
        option_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.document().setDefaultTextOption(option_label)
        self.setText(self.config.title)
        self.update_grid()
    
    def setText(self, text: str):
        self.label.setPlainText(text)
        rect = self.label.boundingRect()
        self.label.setPos(-rect.width() / 2, -rect.height() / 2)
    
    def setPos(self, pos, /):
        self.config.pos = pos
        return super().setPos(pos)
    
    def scene(self) -> Map:
        return super().scene()
    
    def update_grid(self):
        if not (scene := self.scene()): return
        self._update_token_scale(scene.grid_factor)
    
    def _update_token_scale(self, factor: float):
        final = (factor * self._token_scale) + 0.25
        self.prepareGeometryChange()
        self.setScale(final)
    
    def setPixmap(self, pixmap: QPixmap | str | bytes):
        original = QPixmap()
        if isinstance(pixmap, str):
            original.load(pixmap)
        elif isinstance(pixmap, bytes):
            original.loadFromData(pixmap)
        elif isinstance(pixmap, QPixmap):
            original = pixmap.copy()
        else:
            raise TypeError(f"Unsupported type {type(pixmap)}")
        
        if original.isNull():
            return
        
        size = min(original.width(), original.height())
        x = (original.width() - size) / 2
        y = (original.height() - size) / 2
        cropped = original.copy(QRect(int(x), int(y), size, size))
        
        final_pixmap = cropped.scaled(
            self.TEXTURE_SIZE, self.TEXTURE_SIZE,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        
        brush = QBrush(final_pixmap)
        token_rect = self.rect()  # Это (-r, -r, width, height)
        scale = token_rect.width() / self.TEXTURE_SIZE
        tr = QTransform()
        tr.scale(scale, scale)
        tr.translate(token_rect.x() / scale, token_rect.y() / scale)
        
        brush.setTransform(tr)
        self.avatar.setBrush(brush)
        self._cache_text_color = self._calculate_text_color()
        self.label.setDefaultTextColor(self._cache_text_color)
    
    def _calculate_text_color(self) -> QColor:
        pixmap = self.avatar.brush().textureImage()
        
        if pixmap and not pixmap.isNull():
            color = pixmap.scaled(
                1, 1, Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation
            ).pixelColor(0, 0)
            brightness = color.lightness()
        else:
            brightness = self.brush().color().lightness()
        return QColor(Qt.GlobalColor.black if brightness > 128 else Qt.GlobalColor.white)
    
    @classmethod
    def create(cls, data: CreateData, *args, **kwargs) -> Self:
        ...
    
    @property
    def isSideClient(self):
        if scene := self.scene(): return scene.isSideClient
        return False
    
    def setTokenScale(self, factor: float):
        self._token_scale = factor
        self.update_grid()
    
    def boundingRect(self):
        return super().boundingRect().adjusted(-20, -20, 20, 20)
    
    @property
    def mime(self):
        return self.config.mime
