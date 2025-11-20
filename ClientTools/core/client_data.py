from attrs import define, field
from pathlib import Path
from typing import Optional


@define
class ClientData:
    uid: str = field(default=None)
    name: str = field(default=None)
    cls: str = field(default=None)
    isMaster: bool = field(default=False)
    
    image_load: dict[str, str] = field(factory=dict)
    current_map: Optional[str] = field(default=None)
