from abc import ABC, abstractmethod

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from attrs import define, field, validators

from CommonTools.mime import TokenMime, MobMime, NPCMime, SpawnMime, PlayerMime


def _tuple2qpoint(value):
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return QPointF(value[0], value[1])
    return value


def _str2qcolor(value):
    if isinstance(value, str):
        return QColor(value)
    return value


@define
class BaseConfigTrick(ABC):
    pos: QPointF = field(converter=_tuple2qpoint)
    color: QColor = field(converter=_str2qcolor, default=QColor("#000"))
    scale: float = field(validator=[validators.instance_of(float), validators.gt(0)], default=1.0)
    size: int = field(validator=[validators.instance_of(int), validators.gt(0)], default=40)
    
    @property
    @abstractmethod
    def title(self) -> str: ...
    
    @property
    @abstractmethod
    def mime(self) -> TokenMime: ...
    
    @property
    @abstractmethod
    def tooltip(self) -> str: ...


@define
class KdConfigTrick(BaseConfigTrick, ABC):
    kd: int = field(validator=[validators.instance_of(int), validators.gt(5)], default=5)


class NPCConfigTrick(KdConfigTrick):
    name: str = field(validator=validators.instance_of(str), default="")
    number: str = field(validator=validators.instance_of(str), default="0")
    unique: bool = field(validator=validators.instance_of(bool), default=False)
    hp: int = field(validator=validators.instance_of(int), default=0)
    description: str = field(validator=validators.instance_of(str), default="")
    size: int = field(validator=validators.instance_of(int), default=35)
    
    @property
    def title(self) -> str:
        return self.name if self.unique else f"{self.mime}#{self.number}"
    
    @property
    def mime(self) -> TokenMime:
        return NPCMime(name=self.name, number=self.number)
    
    @property
    def tooltip(self) -> str:
        return f"KD: {self.kd}<br>HP: {self.hp}<br>Описание:{self.description}"


@define
class MobConfigTrick(NPCConfigTrick):
    @property
    def mime(self) -> TokenMime:
        return MobMime(name=self.name, number=self.number)


@define
class PlayerConfigTrick(KdConfigTrick):
    name: str = field(validator=validators.instance_of(str), default="")
    cls: str = field(validator=validators.instance_of(str), default="")
    uid: str = field(validator=validators.instance_of(str), default="")
    
    @property
    def title(self) -> str:
        return f"{self.name}\n{self.cls}"
    
    @property
    def mime(self) -> TokenMime:
        return PlayerMime(name=self.name, cls=self.cls, uid=self.uid)
    
    @property
    def tooltip(self) -> str:
        return f"KD: {self.kd}"


@define
class SpawnConfigTrick(BaseConfigTrick):
    @property
    def title(self) -> str:
        return "Spawn"
    
    @property
    def mime(self) -> TokenMime:
        return SpawnMime()
    
    @property
    def tooltip(self) -> str:
        return ""


__all__ = [
    "BaseConfigTrick",
    "KdConfigTrick",
    
    "MobConfigTrick", "NPCConfigTrick",
    "PlayerConfigTrick", "SpawnConfigTrick",
]
