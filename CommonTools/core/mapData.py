from pathlib import Path
from typing import Optional

from attrs import define, field

from CommonTools.map_widget import MapWidget


@define
class MapData:
    name: str
    visible: bool
    mWidget: MapWidget
