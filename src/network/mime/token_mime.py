from typing import TypeAlias
from .core import BaseMime


class CacheMobMime(BaseMime, prefix="cache:mob"):
    name: str


class CacheNPCMime(BaseMime, prefix="cache:npc"):
    name: str
    

class CacheTokenMime(BaseMime, prefix="cache:token"):
    name: str
    unique: bool


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
CacheMime: TypeAlias = CacheMobMime | CacheNPCMime | CacheTokenMime
TokensMime: TypeAlias = TokenMime | CacheMime

__all__ = [
    "TokenMime", "CacheMime", "TokensMime",
    "SpawnMime",
    "PlayerMime", "MobMime", "NPCMime",
    "CacheMobMime", "CacheNPCMime", "CacheTokenMime"
]
