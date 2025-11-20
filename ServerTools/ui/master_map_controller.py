from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar, QFileDialog, QInputDialog, QSpinBox, QLabel, QCheckBox

from ClientTools.components import TokensPanel, PlayerPanel
from ClientTools.core.client import WebSocketClient
from ClientTools.core.client_data import ClientData
from CommonTools.map_widget import BaseToken
from CommonTools.messages import *
from CommonTools.ui.base_map_controller import BaseMapController
from CommonTools.components.guide_panel import GuidePanel
from CommonTools.components.colorButton import ColorButton


class MasterMapController(BaseMapController):
    def __init__(self, socket: WebSocketClient, client_data: ClientData):
        self._init_actions()
        super().__init__(socket, client_data)
        self._setup_master_specifics()
        
        self.tabMaps.call_all_method("set_token_movement", ["players", "mobs", "npcs", "spawn_point"], True)
    
    def _setup_ui(self):
        """Настройка UI мастера"""
        super()._setup_ui()
        
        self.offset_grid_x = QSpinBox(value=0)
        self.offset_grid_x.valueChanged.connect(self._handle_change_offset_grid)
        self.offset_grid_y = QSpinBox(value=0)
        self.offset_grid_y.valueChanged.connect(self._handle_change_offset_grid)
        
        self.box_button.addWidget(QLabel("Отступ"))
        self.box_button.addWidget(self.offset_grid_x)
        self.box_button.addWidget(self.offset_grid_y)
        
        self.box_button.addSpacing(10)
        
        self.size_grid = QSpinBox(value=50)
        self.size_grid.valueChanged.connect(self._handle_change_offset_grid)
        
        self.box_button.addWidget(QLabel("Размер сетки"))
        self.box_button.addWidget(self.size_grid)
        
        self.btnColorGrid = ColorButton(color="#4a4a4a")
        self.btnColorGrid.color_changed.connect(self._handle_change_color)
        self.box_button.addWidget(self.btnColorGrid)
        
        self.checkBoxVisibleGrid = QCheckBox("Сетка")
        self.checkBoxVisibleGrid.setChecked(True)
        self.checkBoxVisibleGrid.toggled.connect(self._handle_visible_grid_change)
        self.box_button.addWidget(self.checkBoxVisibleGrid)
        
        # ======================ButtonPanel========================
        
        self.token_panel = TokensPanel()
        self.guide_panel = GuidePanel("https://5e14.ttg.club/")
        self.player_panel = PlayerPanel()
        self.player_panel.active_change.connect(self._handle_change_freeze_player)
        
        self.main_box.addWidget(self.token_panel)
        self.main_box.addWidget(self.guide_panel)
        self.main_box.insertWidget(0, self.player_panel)
        self.guide_panel.hide()
        
        self._init_toolbar()
        self.deactive_panels()
    
    def _handle_change_freeze_player(self, uid, active):
        self.socket.answer(MapFreezePlayer(uid=uid, freeze=not active))
    
    def _handle_change_offset_grid(self, _value):
        offset = QPoint(self.offset_grid_x.value(), self.offset_grid_y.value())
        self.tabMaps.setOffsetSize(offset, self.size_grid.value())
        self.socket.answer(MapChangeGridOffset(offset=offset.toTuple(), size=self.size_grid.value()))
    
    def _handle_change_color(self, color):
        self.tabMaps.call_all_method("setColorGrid", color)
    
    def _handle_visible_grid_change(self, state):
        self.tabMaps.call_all_method("setVisibleGrid", state)
    
    def _init_toolbar(self):
        """Создаем toolbar и добавляем его в layout"""
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.addAction(self.create_map_action)
        self.toolbar.addAction(self.load_background_action)
        self.toolbar.addAction(self.load_map_action)
        self.toolbar.addAction(self.switch_guide_action)
        
        # Добавляем toolbar в layout
        self.box.insertWidget(0, self.toolbar)
    
    def _setup_master_specifics(self):
        """Специфичные для мастера настройки"""
        self.tabMaps.token_added.connect(self._on_token_added)
        self.tabMaps.token_removed.connect(self._on_token_removed)
        self.tabMaps.token_moved.connect(self._on_token_moved)
        self.tabMaps.token_moved_map.connect(self._on_token_moved_map)
    
    def _init_actions(self):
        self.load_map_action = QAction("Загрузить карту")
        self.load_map_action.triggered.connect(self.on_load_map)
        
        self.create_map_action = QAction("Создать карту")
        self.create_map_action.triggered.connect(self._on_create_map)
        
        self.load_background_action = QAction("Загрузить фон")
        self.load_background_action.triggered.connect(self._on_load_background)
        
        self.switch_guide_action = QAction("Переключить видимость гайда")
        self.switch_guide_action.triggered.connect(self._on_switch_visible)
    
    def deactive_panels(self):
        self.token_panel.setDisabled(True)
    
    def active_panels(self):
        self.token_panel.setDisabled(False)
    
    def update_players_list(self, players: dict[str, ClientData]):
        super().update_players_list(players)
        
        self.player_panel.clear()
        for uid, player in players.items():
            self.player_panel.addPlayer(uid, player.name, player.cls)
    
    def _on_token_added(self, name: str, token: BaseToken):
        """Отправка данных о добавленном токене"""
        if token.ttype != "player":
            self.update_players()
            self.socket.answer(MapAddToken(mime=token.mime(), pos=token.pos().toTuple(), name=name))
    
    def _on_token_removed(self, name: str, token: BaseToken):
        self.socket.answer(MapRemoveToken(mime=token.mime(), name=name))
        
    def _on_token_moved_map(self, name: str, token: BaseToken, name_target: str):
        if self.tabMaps.getMap(name_target) is None:
            return
        map1 = self.tabMaps.getMap(name)
        map2 = self.tabMaps.getMap(name_target)
        
        map1.remove_token(token.mime())
        map2.create_token(token.mime(), token.pos())
        
        self.socket.answer(MapMovedMap(name=name, mime=token.mime(), name_target=name_target))
    
    def _on_token_moved(self, name: str, token: BaseToken, pos: tuple[float, float]):
        uid = f"{name}|{token.mime()}"
        if uid not in self.moved_token:
            self.socket.answer(MapMoveToken(mime=token.mime(), pos=pos, name=name))
        else:
            self.moved_token.remove(uid)
    
    def _on_create_map(self):
        if self.tabMaps.isEmpty():
            name = "main"
        else:
            name, ok = QInputDialog.getText(self, "Имя карты", "Как называется данное место?")
            if not ok:
                return
        self.tabMaps.addMap(name)
        self.socket.answer(MapCreateMap(name=name))
    
    def _on_load_background(self):
        
        name = self.tabMaps.getActiveNameMap()
        if name is None:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть карту", "../../ClientTools/ui", "Image Files (*.png; *.jpg)"
        )
        if file_path:
            self.tabMaps.load_map(name, file_path)
            self.active_panels()
            self.client.image_load[name] = file_path
            self.socket.answer(MapLoadBackground(name=name))
    
    def on_load_map(self):
        pass
    
    def _on_switch_visible(self):
        self.guide_panel.setVisible(not self.guide_panel.isVisible())
    
    def _handle_custom_message(self, msg: BaseMessage):
        """Обработка специфичных для мастера сообщений"""
        match msg.type:
            case MapActionType.GET_BEGIN_LOAD:
                self._handle_load_map_begin(msg)
            case MapActionType.GET_ALL_TOKEN:
                self._handle_get_all_token(msg)
    
    def _handle_load_map_begin(self, msg: MapGetBeginLoad):
        if self.tabMaps.getMap("main") is not None:
            self.socket.answer(MapLoadBackground(name="main", uid=msg.uid))
    
    def _handle_get_all_token(self, msg: MapGetAllTokens):
        if self.tabMaps.isEmpty():
            return
        for name, token in self.tabMaps.items():
            self.socket.answer(MapAddToken2(name=name, mime=token.mime(), pos=token.pos().toTuple(), uid=msg.uid))
        self.socket.answer(MapGridData(offset=self.tabMaps.offset.toTuple(), size=self.tabMaps.size))
