from abc import ABC, abstractmethod

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from attrs import define, field

from network.mime import TokenMime


@define
class BaseConfig(ABC):
    size: int = field(default=50)
    pos: QPointF = field(factory=lambda: QPointF(0, 0))
    color: QColor = field(factory=lambda: QColor(0, 0, 0))
    scale: float = field(default=1)
    title: str = field(default="")
    
    @property
    @abstractmethod
    def mime(self) -> TokenMime: ...