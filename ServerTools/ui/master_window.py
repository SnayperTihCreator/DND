from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QMainWindow, QToolBar, QSpinBox, QLabel, QCheckBox, QApplication, QFileDialog

from CommonTools.components import ColorButton, GuidePanel
from ServerTools.core.server_socket import WebSocketServer
from CommonTools.messages import *
from CommonTools.core import Image, ClientData
from ServerTools.components import TokensPanel, DialogCreateMap, PlayerPanel
from CommonTools.map_widget.tokens_dnd import BaseToken

from .masterController import MasterController


class MasterGameTable(QMainWindow):
    def __init__(self, login):
        super().__init__()
        self.setMinimumSize(1000, 700)
        self.setWindowTitle("Виртуальный стол: Мастер")
        
        self.images: dict[str, Any] = {}
        self.players: dict[str, ClientData] = {}
        self.server = WebSocketServer()
        self.server.client_connected.connect(self._handle_connect)
        self.server.client_disconnected.connect(self._handle_disconnect)
        self.server.message_received_uid.connect(self._handle_message_raw)
        self.server.image_received.connect(self._handle_image)
        
        self.server.start_server()
        
        self.cache_folder = Path("./.cache")
        self.cache_folder.mkdir(exist_ok=True, parents=True)
        
        self.controller = MasterController(self.server)
        self.setCentralWidget(self.controller)
        
        self.token_panel = TokensPanel()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.token_panel)
        
        self.guide_panel = GuidePanel("https://5e14.ttg.club/", "Справочник", f"Master{login}")
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.guide_panel)
        self.guide_panel.hide()
        
        self.player_panel = PlayerPanel()
        self.player_panel.active_change.connect(self._handle_change_freeze)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.player_panel)
        
        self.topToolBar = QToolBar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.topToolBar)
        
        self.create_map_action = self.topToolBar.addAction("Создать карту")
        self.create_map_action.triggered.connect(self._on_action_add_map)
        self.load_bg_action = self.topToolBar.addAction("Загрузить фон")
        self.load_bg_action.triggered.connect(self._on_action_load_bg)
        self.delete_map_action = self.topToolBar.addAction("Удалить карту")
        self.delete_map_action.triggered.connect(self._on_action_delete_map)
        self.save_map_action = self.topToolBar.addAction("Сохранить карту")
        self.active_map_action = self.topToolBar.addAction("Активировать карту")
        self.active_map_action.triggered.connect(self._on_action_active_map)
        
        self.bottomToolBar = QToolBar()
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.bottomToolBar)
        
        self.offset_grid_x = QSpinBox(value=0)
        self.offset_grid_x.valueChanged.connect(self._handle_offset_size_change)
        self.offset_grid_y = QSpinBox(value=0)
        self.offset_grid_y.valueChanged.connect(self._handle_offset_size_change)
        
        self.bottomToolBar.addWidget(QLabel("Отступ"))
        self.bottomToolBar.addWidget(self.offset_grid_x)
        self.bottomToolBar.addWidget(self.offset_grid_y)
        self.bottomToolBar.addWidget(QLabel("\t"))
        
        self.size_grid = QSpinBox(value=50)
        self.size_grid.valueChanged.connect(self._handle_offset_size_change)
        
        self.bottomToolBar.addWidget(QLabel("Размер сетки"))
        self.bottomToolBar.addWidget(self.size_grid)
        self.bottomToolBar.addWidget(QLabel("\t"))
        
        self.btnColorGrid = ColorButton(color="#4a4a4a")
        self.checkBoxVisibleGrid = QCheckBox("Сетка")
        
        self.bottomToolBar.addWidget(self.btnColorGrid)
        self.bottomToolBar.addWidget(self.checkBoxVisibleGrid)
        
        self.menu_panels = self.menuBar().addMenu("Панели")
        self.token_panel_action = self.menu_panels.addAction("Показать панель токенов")
        self.token_panel_action.triggered.connect(self.token_panel.show)
        
        self.guide_panel_action = self.menu_panels.addAction("Показать справочник")
        self.guide_panel_action.triggered.connect(self.guide_panel.show)
        
        self.player_panel_action = self.menu_panels.addAction("Показать панель игроков")
        self.player_panel_action.triggered.connect(self.player_panel.show)
    
    def _on_action_add_map(self):
        if self.controller.tabMaps.isEmpty():
            name, visible = "main", True
        else:
            name, visible = DialogCreateMap.getNameAndVisible(
                "Создать карту",
                "Дайте имя карте и будет ли видна карта игрокам")
        if name is not None:
            self.controller.addMap(name, visible)
    
    def _on_action_delete_map(self):
        if self.controller.tabMaps.isEmpty():
            return
        self.controller.removeActiveMap()
    
    def _on_action_load_bg(self):
        if name := self.controller.tabMaps.getActiveNameMap():
            path, _ = QFileDialog.getOpenFileName(self, "Выберете фон", ".", "Image(*.png *.jpg);;Animation(*.gif)")
            if path:
                self.images[name] = path
                self.controller.tabMaps.load_map(name, path)
                self.server.broadcast(MapLoadBackground(name=name))
    
    def _on_action_active_map(self):
        if name := self.controller.tabMaps.getActiveNameMap():
            self.controller.activeMap(name)
    
    def _handle_offset_size_change(self, *_):
        offset = QPoint(self.offset_grid_x.value(), self.offset_grid_y.value())
        size = self.size_grid.value()
        self.controller.tabMaps.call_all_method("setOffsetSize", offset, size)
        self.server.broadcast(MapGridData(offset=offset.toTuple(), size=size))
    
    def _handle_change_freeze(self, uid, state):
        print(uid, state)
    
    def _handle_connect(self, uid):
        print("Connect", uid)
    
    def _handle_disconnect(self, uid):
        print("Disconnect", uid)
        self.players.pop(uid)
        self.controller.update_player_list(self.players)
        self.player_panel.removePlayer(uid)
        self.server.broadcast(ClientRemovePlayer(uid=uid), uid)
    
    def _handle_message_raw(self, uid, msg_raw: str):
        msg = BaseMessage.from_str(msg_raw)
        self._handle_message(uid, msg)
    
    def _handle_message(self, uid, msg: BaseMessage):
        if self.controller.handle_message(msg):
            return
        match msg.type:
            case ClientActionType.START_PLAYER:
                self._action_add_player(uid, msg)
            case MapActionType.MAPS_ALL_DATA:
                self._handle_all_data_maps(uid, msg)
            case ImageActionType.NAME_REQUEST:
                self._handle_name_map(uid, msg)
            case _:
                print(f"unhadled {uid}:<{msg.type}>{msg}")
    
    def _handle_image(self, image: Image):
        cache_image = self.cache_folder / f"{image.name}{image.suffix}"
        cache_image.write_bytes(image.image_data)
        print(f"Get image {image.name}{image.suffix} as {image.strategy}")
    
    def _action_add_player(self, uid_answer: str, msg: ClientStartPlayer):
        self.server.answer(uid_answer, msg)
        self.server.broadcast(ClientAddPlayer(uid=uid_answer, name=msg.name, cls=msg.cls), uid_answer)
        for uid, client in self.server.clients.items():
            QApplication.processEvents()
            if client.is_playing and uid_answer != uid:
                self.server.answer(uid_answer, ClientAddPlayer(uid=uid, name=client.name, cls=client.cls))
        self.players[uid_answer] = self.server.clients[uid_answer]
        self.controller.update_player_list(self.players)
        self.player_panel.addPlayer(uid_answer, msg.name, msg.cls)
    
    def closeEvent(self, event):
        self.server.stop_server()
        return super().closeEvent(event)
    
    def _handle_all_data_maps(self, uid, _):
        offset: QPoint
        offset, size = self.controller.tabMaps.getOffsetSize()
        self.server.answer(uid, MapChangeGridOffset(offset=offset.toTuple(), size=size))
        for map_name in self.controller.tabMaps.maps.keys():
            QApplication.processEvents()
            mdata, tokens = self.controller.tabMaps.getMapData(map_name)
            
            self.server.answer(uid, MapCreateMap(name=mdata.name, visible=mdata.visible))
            if mdata.mWidget.file_map:
                self.server.answer(uid, MapLoadBackground(name=map_name))
            for item in mdata.mWidget.items():
                QApplication.processEvents()
                if isinstance(item, BaseToken):
                    self.server.answer(uid, MapAddToken(name=map_name, mime=item.mime(), pos=item.pos().toTuple()))
    
    def _handle_name_map(self, uid, msg: ImageNameRequest):
        if file_path := self.images.get(msg.name, None):
            self.server.answer(uid, DoneCallback(uid_callback=msg.uid))
            self.server.answer_image(uid, file_path, msg.name)
        else:
            self.server.answer(uid, IgnoreCallback(uid_callback=msg.uid))
