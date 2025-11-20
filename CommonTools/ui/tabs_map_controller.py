from functools import partial
from typing import Any
from copy import copy

from PySide6.QtWidgets import QTabWidget
from PySide6.QtCore import Signal, QPointF

from CommonTools.map_widget import MapWidget
from CommonTools.core.client_data import ClientData
from CommonTools.core.mapData import MapData
from CommonTools.map_widget.tokens_dnd import BaseToken


class TabMapsWidget(QTabWidget):
    token_added = Signal(str, object)
    token_removed = Signal(str, object)
    token_moved = Signal(str, object, tuple)
    
    token_moved_map = Signal(str, object, str)
    
    def __init__(self, client):
        super().__init__()
        self.client: ClientData = client
        self.maps: dict[str, MapData] = {}
        
        self.movement_settings = {
            'players': True,
            'mobs': True,
            'npcs': True,
            'spawn_point': True,
        }
        
        self.calls_saved: dict[str, tuple[Any, ...]] = {}
        self.visible_always = False
    
    def addMap(self, name, visible=True):
        if self.maps.get(name, None) is None:
            mWidget = MapWidget(self.client)
            mWidget.set_token_movement([k for k, v in self.movement_settings.items() if v], True)
            mWidget.set_token_movement([k for k, v in self.movement_settings.items() if not v], False)
            mWidget.token_added.connect(partial(self.token_added.emit, name))
            mWidget.token_removed.connect(partial(self.token_removed.emit, name))
            mWidget.token_moved.connect(partial(self.token_moved.emit, name))
            mWidget.token_moved_map.connect(partial(self.token_moved_map.emit, name))
            
            for fname, args in self.calls_saved.items():
                impl = getattr(mWidget, fname, None)
                if impl is None:
                    continue
                impl(*args)
            idx = self.addTab(mWidget, name)
            self.setTabVisible(idx, visible or self.visible_always)
            self.maps[name] = MapData(name, visible, mWidget)
    
    def removeMap(self, name):
        if mWidget := self.getMap(name):
            self.removeTab(self.indexOf(mWidget))
            del self.maps[name]
    
    def getMapData(self, name) -> tuple[MapData, list[BaseToken]]:
        mdata = self.maps[name]
        return mdata, [item for item in mdata.mWidget.items() if isinstance(item, BaseToken)]
    
    def getOffsetSize(self):
        return copy(self.calls_saved["setOffsetSize"])
    
    def load_map(self, name, file_path):
        self.maps[name].mWidget.load_map(file_path)
    
    def getActiveNameMap(self):
        if not self.maps:
            return None
        return list(self.maps.keys())[self.currentIndex()]
    
    def getMap(self, name) -> MapWidget:
        mdata = self.maps.get(name, None)
        if mdata:
            return mdata.mWidget
    
    def isEmpty(self):
        return not bool(self.maps)
    
    # noinspection PyArgumentList
    def create_token(self, name: str, mime: str, pos: tuple[float, float]):
        point = QPointF(*pos)
        mWidget = self.getMap(name)
        if mWidget is None:
            return
        token = mWidget.create_token(mime, point)
        return token
    
    def removeTokenByMime(self, name: str, mime: str):
        mWidget = self.getMap(name)
        if mWidget is None:
            return
        mWidget.remove_token(mime)
    
    def removeToken(self, token: BaseToken):
        for mdata in self.maps.values():
            if token in mdata.mWidget.items():
                mdata.mWidget.remove_token(token.mime())
    
    def move_token(self, name, mime, pos):
        mWidget = self.getMap(name)
        if mWidget is None:
            return
        mWidget.setTokenMimePos(mime, pos)
    
    def call_all_method(self, name, *args):
        self.calls_saved[name] = args
        for mdata in self.maps.values():
            mWidget = mdata.mWidget
            impl = getattr(mWidget, name, None)
            if impl is None:
                print(f"Function for {mWidget} not find {name}")
                continue
            impl(*args)
    
    def set_token_movement(self, tokens, enabled):
        for token_type in tokens:
            if token_type in self.movement_settings:
                self.movement_settings[token_type] = enabled
        
        for mdata in self.maps.values():
            mdata.mWidget.set_token_movement([k for k, v in self.movement_settings.items() if v], True)
            mdata.mWidget.set_token_movement([k for k, v in self.movement_settings.items() if not v], False)
    
    def items(self, fname=None):
        for name, mdata in self.maps.items():
            for item in mdata.mWidget.items():
                if isinstance(item, BaseToken):
                    yield name, item
            if fname and (fname == name):
                return
