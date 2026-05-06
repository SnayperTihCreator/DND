from abc import ABC, abstractmethod

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from attrs import define, field

from network.mime import TokenMime, PlayerMime, MobMime, NPCMime, SpawnMime


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


@define
class PlayerConfig(BaseConfig):
    name: str = field(default="")
    cls: str = field(default="")
    uid: str = field(default="")
    
    @property
    def mime(self) -> TokenMime:
        return PlayerMime(name=self.name, cls=self.cls, uid=self.uid)


@define
class MobConfig(BaseConfig):
    name: str = field(default="")
    number: int = field(default=0)
    
    @property
    def mime(self) -> TokenMime:
        return MobMime(name=self.name, number=self.number)


@define
class NPCConfig(MobConfig):
    @property
    def mime(self) -> TokenMime:
        return NPCMime(name=self.name, number=self.number)


@define
class SpawnPlayerConfig(BaseConfig):
    @property
    def mime(self) -> TokenMime:
        return SpawnMime()


__all__ = ["PlayerConfig", "MobConfig", "NPCConfig", "SpawnPlayerConfig"]
