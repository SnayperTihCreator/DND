from pathlib import Path

from attrs import define, field

from network.mime import TokenMime


@define
class CreateData:
    mime: TokenMime
    scale: float
    description: str = field(default="")
    avatar: Path = field(factory=Path)
    extra: dict = field(factory=dict)