from typing import TypeAlias
from .core import BaseMime


class MobMime(BaseMime, prefix="token:mob"):
    name: str
    number: str


class NPCMime(BaseMime, prefix="token:npc"):
    name: str
    number: str


class PlayerMime(BaseMime, prefix="token:player"):
    name: str
    cls: str
    uid: str


class SpawnMime(BaseMime, prefix="token:spawn"):
    pass


TokenMime: TypeAlias = MobMime | NPCMime | PlayerMime | SpawnMime

__all__ = [
    "TokenMime",
    "SpawnMime",
    "PlayerMime", "MobMime", "NPCMime",
]
