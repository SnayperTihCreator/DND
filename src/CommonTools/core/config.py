from abc import ABC, abstractmethod

from PySide6.QtGui import QColor
from PySide6.QtCore import QPointF
from attrs import define, field, validators


def _to_qpoint(value):
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return QPointF(value[0], value[1])
    return value


def _to_qcolor(value):
    if isinstance(value, str):
        return QColor(value)
    return value


@define
class TokenConfig(ABC):
    pos: QPointF = field(converter=_to_qpoint)
    color: QColor = field(converter=_to_qcolor, default=QColor("#fff"))
    scale: float = field(validator=[validators.instance_of(float), validators.gt(0)], default=1.0)
    size: int = field(validator=validators.instance_of(int), default=40)
    
    @property
    @abstractmethod
    def text(self): return ""
    
    @abstractmethod
    def mime(self, ttype): ...
    
    @property
    @abstractmethod
    def tooltip(self): ...


@define
class KdTokenConfig(TokenConfig, ABC):
    kd: int = field(validator=[validators.instance_of(int), validators.ge(5)], default=5)


@define
class ModNpcTokenConfig(KdTokenConfig):
    name: str = field(validator=validators.instance_of(str), default="")
    number: str = field(validator=validators.instance_of(str), default="None")
    unique: bool = field(validator=validators.instance_of(bool), default=False)
    hp: int = field(validator=validators.instance_of(int), default=0)
    description: str = field(validator=validators.instance_of(str), default="")
    size: int = field(validator=validators.instance_of(int), default=35)
    
    @property
    def text(self):
        return self.name if self.unique else f"{self.name}#{self.number}"
    
    def mime(self, ttype):
        return f"{ttype}:{self.name}:{self.number}"
    
    @property
    def tooltip(self):
        # <img src='icon_hp' width='64' height='icon_kd'>
        return f"KD: {self.kd}<br>HP: {self.hp}<br>Описание:{self.description}"


@define
class PlayerTokenConfig(KdTokenConfig):
    name: str = field(validator=validators.instance_of(str), default="")
    cls: str = field(validator=validators.instance_of(str), default="")
    uid: str = field(validator=validators.instance_of(str), default="")
    
    @property
    def text(self):
        return f"{self.name}\n({self.cls})"
    
    def mime(self, ttype):
        return f"{ttype}:{self.name}:{self.cls}:{self.uid}"
    
    @property
    def tooltip(self):
        return f"KD: {self.kd}"


@define
class SpawnPlayerTokenConfig(TokenConfig):
    @property
    def text(self):
        return "Спавн"
    
    def mime(self, ttype):
        return f"{ttype}:player:None"
    
    @property
    def tooltip(self):
        return ""


__all__ = ["PlayerTokenConfig", "SpawnPlayerTokenConfig", "ModNpcTokenConfig", "TokenConfig"]
