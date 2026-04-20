from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Signal, QPointF, QPoint
from PySide6.QtGui import QColor, QTransform
from PySide6.QtWidgets import QGraphicsScene
from attrs import define, field

from .manager import Manager
from .map_provider import MapProvider
from ..tokens import BaseToken
from ..utils.automatic import properties

if TYPE_CHECKING:
    from .maps import Maps


@define
class GridData:
    scene: "Map"
    visible: bool = field(default=True)
    offset: QPoint = field(factory=lambda: QPoint(0, 0))
    color: QColor = field(factory=lambda: QColor("#4a4a4a"))
    
    @property
    def size(self) -> int:
        return self.scene.grid_factor * 50


@define
class View:
    transform: QTransform = field(factory=QTransform)
    center: QPointF = field(factory=lambda: QPointF(0, 0))
    _loaded: bool = field(default=False, init=False, repr=False)
    
    def load(self):
        self._loaded = True
    
    def isLoaded(self) -> bool:
        return self._loaded


class Map(QGraphicsScene):
    name: str = properties("name")
    speed_trick: int = properties("speed")
    grid_factor: float = properties("grid_factor")
    isSideClient: bool = properties("isClient")
    
    token_moved = Signal(object)
    token_added = Signal(object)
    token_removed = Signal(object)
    token_moved_map = Signal(object, str)
    
    contextMenuRequested = Signal(QPointF)
    
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.setProperty("name", name)
        self.setProperty("speed", 250)
        self.setProperty("grid_factor", 1.0)
        self.setProperty("isClient", False)
        
        self.margin = 250
        
        self.view_data = View()
        self.manager = Manager(self)
        self.provider = MapProvider()
        self.grid = GridData(self)
        
        self.addItem(self.provider)
    
    def update_grid(self, size: int):
        self.setProperty("grid_factor", size / 50)
        self.manager.update_size_tokens()
    
    def contextMenuEvent(self, event):
        self.contextMenuRequested.emit(event.scenePos())
        super().contextMenuEvent(event)
    
    def addToken(self, pos: QPointF, token: BaseToken):
        return self.manager.addToken(pos, token)
    
    def removeToken(self, token: BaseToken):
        return self.manager.removeToken(token)
    
    def moveToken(self, pos: QPointF, token: BaseToken):
        return self.manager.moveToken(pos, token)
    
    def currentView(self) -> Optional["Maps"]:
        try:
            return self.views()[0]
        except IndexError:
            return None
        
    def painter(self):
        return self.provider.view_painter
    
    def __prepare_view__(self, view: "Maps"):
        if not view: return
        self.view_data.load()
        self.view_data.transform = view.transform()
        self.view_data.center = view.mapToScene(view.viewport().rect().center())
    
    def __prepare_rect__(self, init=False):
        if not (view := self.currentView()): return
        rect = self.itemsBoundingRect().adjusted(-self.margin, -self.margin, self.margin, self.margin)
        view.setSceneRect(rect)
        
        if init or (not self.view_data.isLoaded()):
            view.fitInView(self.provider)
            self.__prepare_view__(view)
        else:
            view.setTransform(self.view_data.transform)
            view.centerOn(self.view_data.center)
    
    def load(self, path: str):
        path = Path(path)
        match path.suffix:
            case ".png" | ".jpeg" | ".jpg":
                self.provider.loadStatic(path)
            case ".gif":
                self.provider.loadAnimation(path)
            case ".paint":
                self.provider.loadPainter(path)
        self.__prepare_rect__(True)
        
