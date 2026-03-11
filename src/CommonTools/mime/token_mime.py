from .core import BaseMime


class MobNPCMime(BaseMime, prefix="token"):
    ttype: str
    name: str
    number: str


class PlayerMime(BaseMime, prefix="token"):
    ttype: str
    name: str
    cls: str
    uid: str


class SpawnMime(BaseMime, prefix="token:spawn"):
    pass


__all__ = [
    "SpawnMime",
    "PlayerMime", "MobNPCMime"
]
