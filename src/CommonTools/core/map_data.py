from typing import TYPE_CHECKING

from attrs import define


from network.mime import AssetsMime
if TYPE_CHECKING:
    from CommonTools.map_layout import MapWidget


@define
class MapData:
    name: str
    visible: bool
    mWidget: "MapWidget"
    
    @property
    def mime_s(self):
        return self.mime.to_str()
    
    @property
    def mime(self):
        return AssetsMime(category="map-fon", filename=self.name)
    
    @property
    def path(self):
        return self.mWidget.file_map
