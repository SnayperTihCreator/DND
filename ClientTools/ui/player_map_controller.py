from PySide6.QtCore import QPointF, QPoint
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QCheckBox

from CommonTools.core.client_data import ClientData
from CommonTools.ui.base_map_controller import BaseMapController
from CommonTools.map_widget import BaseToken

from CommonTools.messages import *
from CommonTools.components.colorButton import ColorButton


class PlayerMapController(BaseMapController):
    def __init__(self, client: ClientData):
        self._init_actions()
        super().__init__(client)
        self._setup_player_specifics()
        
        self.tabMaps.set_token_movement(["players", "mobs", "npcs", "spawn_point"], False)
        self.tabMaps.calls_saved("setFreezeToken", False)
        self.tabMaps.calls_saved("setOffsetSize", QPoint(0, 0), 50)
        
        self.tabMaps.set_freeze(True)
        self.set_visible_token(["spawn_point"], False)
        
        self.defaultActive = True
    
    def _setup_ui(self):
        """Настройка UI игрока"""
        super()._setup_ui()
        
        self.btnColorGrid = ColorButton(color="#4a4a4a")
        self.btnColorGrid.color_changed.connect(self._handle_change_color)
        self.box_button.addWidget(self.btnColorGrid)
        
        self.checkBoxVisibleGrid = QCheckBox("Сетка")
        self.checkBoxVisibleGrid.setChecked(True)
        self.checkBoxVisibleGrid.toggled.connect(self._handle_visible_grid_change)
        self.box_button.addWidget(self.checkBoxVisibleGrid)
        
        # =====================ButtonPanel=============================
    
    def _handle_change_color(self, color):
        self.tabMaps.call_all_method("setColorGrid", color)
    
    def _handle_visible_grid_change(self, state):
        self.tabMaps.call_all_method("setVisibleGrid", state)
    
    def _setup_player_specifics(self):
        """Специфичные для игрока настройки"""
        self.tabMaps.token_moved.connect(self._on_token_moved)
    
    def _on_token_moved(self, name: str, token: BaseToken, pos: tuple[float, float]):
        uid = f"{name}|{token.mime()}"
        if uid not in self.moved_token:
            self.socket.answer(MapMoveToken(mime=token.mime(), pos=pos, name=name))
        else:
            self.moved_token.remove(uid)
    
    def _init_actions(self):
        self.switch_visible_list_action = QAction("Переключить видимость листа персонажа")
        self.switch_visible_list_action.triggered.connect(self._on_switch_visible_list)
    
    def _on_switch_visible_list(self):
        self.guide_panel.setVisible(not self.guide_panel.isVisible())
    
    def load_map(self, name: str, file_path: str):
        """Загрузка карты из файла"""
        if file_path:
            self.tabMaps.load_map(name, file_path)
            self.clear_buffer_token(name)
    
    def update_players(self):
        super().update_players()
        if (map2 := self.tabMaps.getMap("main")) and map2.token_spawn and not self.player_token:
            self.player_token = map2.create_player(self.client.name, self.client.cls, self.client.uid)
    
    def _handle_custom_message(self, msg: BaseMessage):
        """Обработка специфичных для игрока сообщений"""
        match msg.type:
            case MapActionType.MAP_CHANGE_GRID_OFFSET:
                self._handle_change_grid_offset(msg)
            case MapActionType.PLAYER_FREEZE:
                self.tabMaps.set_freeze(msg.freeze)
            case MapActionType.MAP_GRID_DATA:
                self._handle_grid_data(msg)
            case ClientActionType.PLAYER_STOP:
                self._handle_player_stop(msg)
            case MapActionType.MAP_MOVE_MAP:
                self._handle_token_move(msg)
                
    def _handle_player_stop(self, msg: ClientPlayerStop):
        self.player_token.stopMoved()
    
    def _handle_change_grid_offset(self, msg: MapChangeGridOffset):
        pos = QPointF(*msg.offset)
        self.tabMaps.call_all_method("setOffsetSize", pos, msg.size)
        
    def _handle_grid_data(self, msg: MapGridData):
        pos = QPointF(*msg.offset)
        self.tabMaps.call_all_method("setOffsetSize", pos, msg.size)

    def _handle_token_move(self, msg: MapMovedMap):
        map1 = self.tabMaps.getMap(msg.name)
        map2 = self.tabMaps.getMap(msg.name_target)
        
        map1.remove_token(msg.mime)
        map2.create_token(msg.mime, QPointF(0, 0))