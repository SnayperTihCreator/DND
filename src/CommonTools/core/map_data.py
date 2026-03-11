from attrs import define

from CommonTools.map_layout import MapWidget
from CommonTools.mime import AssetsMime


@define
class MapData:
    name: str
    visible: bool
    mWidget: MapWidget
    
    @property
    def mime_s(self):
        return self.mime.to_str()
    
    @property
    def mime(self):
        return AssetsMime(category="map-fon", filename=self.name)
    
    @property
    def path(self):
        return self.mWidget.file_map
