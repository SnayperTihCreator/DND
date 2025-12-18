from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QPoint, QPointF, QTimer
from PySide6.QtWidgets import QMainWindow, QToolBar, QSpinBox, QLabel, QCheckBox, QApplication, QFileDialog, \
    QGraphicsColorizeEffect, QMessageBox
from PySide6.QtGui import QIcon, QColor
from loguru import logger

from CommonTools.map_widget import MapWidget

logger = logger.bind(pack="ServerWindow")

from CommonTools.components import ColorButton, GuidePanel, MessageRouter
from ServerTools.core.server_socket import WebSocketServer
from CommonTools.messages import *
from CommonTools.core import Image, ClientData
from ServerTools.components import TokensPanel, DialogCreateMap, PlayerPanel
from CommonTools.utils import validate_and_resize_image, getImageMIME

from .masterController import MasterController

router = MessageRouter()


class MasterGameTable(QMainWindow):
    def __init__(self, login):
        super().__init__()
        self.setMinimumSize(1000, 700)
        self.setWindowTitle("Виртуальный стол: Мастер")
        self.setWindowIcon(QIcon(":/icons/main.png"))
        
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
        self.controller.error.connect(self.showErrorMessage)
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
        self.btnColorGrid.color_changed.connect(self._handle_change_color)
        self.checkBoxVisibleGrid = QCheckBox("Сетка")
        self.checkBoxVisibleGrid.setChecked(True)
        self.checkBoxVisibleGrid.toggled.connect(self._handle_change_vgrid)
        
        self.bottomToolBar.addWidget(self.btnColorGrid)
        self.bottomToolBar.addWidget(self.checkBoxVisibleGrid)
        
        self.topPaintBar = QToolBar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.topPaintBar)
        
        self.changeDragPaint = self.topPaintBar.addAction("Редактировать туман")
        self.changeDragPaint.triggered.connect(self._on_action_change_drag_paint)
        self.changeDrawErase = self.topPaintBar.addAction("Стирать")
        self.changeDrawErase.triggered.connect(self._on_action_change_erase)
        self.brushSize = QSpinBox(value=50, minimum=1, maximum=10 ** 6, singleStep=1)
        self.topPaintBar.addWidget(self.brushSize)
        self.brushSize.valueChanged.connect(self._on_action_change_size_brush)
        
        self.actionClearFog = self.topPaintBar.addAction("Очистить туман")
        self.actionClearFog.triggered.connect(self._on_action_clear_fog)
        
        self.actionResetFog = self.topPaintBar.addAction("Восстановить туман")
        self.actionResetFog.triggered.connect(self._on_action_reset_fog)
        
        self.controller.tabMaps.currentMapChanged.connect(self._handle_current_map)
        
        self.menu_panels = self.menuBar().addMenu("Панели")
        self.token_panel_action = self.menu_panels.addAction("Показать панель токенов")
        self.token_panel_action.triggered.connect(self.token_panel.show)
        
        self.guide_panel_action = self.menu_panels.addAction("Показать справочник")
        self.guide_panel_action.triggered.connect(self.guide_panel.show)
        
        self.player_panel_action = self.menu_panels.addAction("Показать панель игроков")
        self.player_panel_action.triggered.connect(self.player_panel.show)
        
        self._deactivate_control()
    
    def applyErrorEffect(self):
        colorize = QGraphicsColorizeEffect(self)
        colorize.setColor(QColor("#f00"))
        
        self.statusBar().setGraphicsEffect(colorize)
    
    def resetEffect(self):
        self.statusBar().setGraphicsEffect(None)
    
    def showErrorMessage(self, msg: str):
        self.applyErrorEffect()
        self.statusBar().showMessage(msg, 2000)
        logger.error(msg)
        QTimer.singleShot(2000, self.resetEffect)
    
    def _on_action_add_map(self):
        if self.controller.tabMaps.isEmpty():
            name, visible = "main", True
        else:
            name, visible = DialogCreateMap.getNameAndVisible(
                "Создать карту",
                "Дайте имя карте и будет ли видна карта игрокам")
        if name is not None:
            self.controller.addMap(name, visible)
        self._handle_current_map(name)
    
    def _on_action_delete_map(self):
        if self.controller.tabMaps.isEmpty():
            return
        self.controller.removeActiveMap()
    
    def _on_action_load_bg(self):
        if not (name := self.controller.tabMaps.getActiveNameMap()):
            return
        path, _ = QFileDialog.getOpenFileName(self, "Выберете фон", ".", "Image(*.png *.jpg);;Animation(*.gif)")
        
        if not path:
            return
        
        path2 = validate_and_resize_image(path, self.cache_folder, max_size=4096)
        
        if path2 is None:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить изображение (слишком большое или битое)["
                                                 "4000*4000 макс пикселей].")
            return
        
        self.controller.register_image(name, path2)
        self.controller.tabMaps.load_map(name, path2)
        self.server.broadcast(MapLoadBackground(name=name))
        self._handle_current_map(name)
    
    def _on_action_active_map(self):
        if name := self.controller.tabMaps.getActiveNameMap():
            self.controller.activeMap(name)
    
    def _on_action_change_drag_paint(self):
        if name := self.controller.tabMaps.getActiveNameMap():
            mWidget = self.controller.tabMaps.getMap(name)
            mWidget.setFogMode(not mWidget.isActiveFogMode(), mWidget.isRevealFogMode())
            self._handle_change_state_fog(mWidget)
    
    def _on_action_change_erase(self):
        if name := self.controller.tabMaps.getActiveNameMap():
            mWidget = self.controller.tabMaps.getMap(name)
            mWidget.setFogMode(mWidget.isActiveFogMode(), not mWidget.isRevealFogMode())
            self._handle_change_state_fog(mWidget)
    
    def _on_action_change_size_brush(self, value):
        self.controller.tabMaps.call_all_method("setFogBrushSize", value)
    
    def _on_action_clear_fog(self):
        if name := self.controller.tabMaps.getActiveNameMap():
            mWidget = self.controller.tabMaps.getMap(name)
            mWidget.clearFog()
    
    def _on_action_reset_fog(self):
        if name := self.controller.tabMaps.getActiveNameMap():
            mWidget = self.controller.tabMaps.getMap(name)
            mWidget.resetFog()
    
    def _handle_change_state_fog(self, mWidget: MapWidget):
        if mWidget.isActiveFogMode():
            self.changeDragPaint.setText("Перемещение токенов")
            self.changeDrawErase.setDisabled(False)
            self.brushSize.setDisabled(False)
        else:
            self.changeDragPaint.setText("Редактирование тумана")
            self.changeDrawErase.setDisabled(True)
            self.brushSize.setDisabled(True)
        
        if mWidget.isRevealFogMode():
            self.changeDrawErase.setText("Стирать")
        else:
            self.changeDrawErase.setText("Рисовать")
    
    def _handle_offset_size_change(self, *_):
        offset = QPoint(self.offset_grid_x.value(), self.offset_grid_y.value())
        size = self.size_grid.value()
        self.controller.tabMaps.call_all_method("setOffsetSize", offset, size)
        self.server.broadcast(MapGridData(offset=offset.toTuple(), size=size))
    
    def _handle_change_freeze(self, uid, state):
        logger.info("Изменения состояния заморозки у {uid}:{state}", uid=uid, state=state)
        self.server.answer(uid, MapFreezePlayer(freeze=state))
    
    def _handle_connect(self, uid):
        logger.success("Клиент подключен с uid: {uid}", uid=uid)
    
    def _handle_change_color(self, color):
        self.controller.tabMaps.call_all_method("setColorGrid", color)
    
    def _handle_change_vgrid(self, visible):
        self.controller.tabMaps.call_all_method("setVisibleGrid", visible)
    
    def _handle_disconnect(self, uid):
        self.players.pop(uid, None)
        self.controller.update_player_list(self.players)
        self.player_panel.removePlayer(uid)
        self.server.broadcast(ClientRemovePlayer(uid=uid), uid)
        logger.success("Клиент отключен с uid: {uid}", uid=uid)
    
    def _handle_message_raw(self, uid, msg_raw: str):
        msg = BaseMessage.from_str(msg_raw)
        self._handle_message(uid, msg)
    
    def _handle_message(self, uid, msg: BaseMessage):
        if self.controller.handle_message(msg):
            return
        
        if router.dispatch(self, uid, msg):
            return
        
        logger.info("Не обработанное сообщение: {mtype} - {msg}", mtype=msg.type, msg=msg)
    
    def _handle_image(self, image: Image):
        cache_image = self.cache_folder / f"{image.name}{image.suffix}"
        cache_image.write_bytes(image.image_data)
        
        self.controller.register_image(image.name, cache_image.as_posix())
        logger.debug("Получено изображение {iname}{isuffix} через {istrategy}", iname=image.name,
                     isuffix=image.suffix, istrategy=image.strategy)
    
    @router.handler(ClientActionType.START_PLAYER)
    def _action_add_player(self, uid_answer: str, msg: ClientStartPlayer):
        self.server.answer(uid_answer, msg)
        self.server.clients[uid_answer].iname = msg.iname
        self.server.broadcast(ClientAddPlayer(uid=uid_answer, name=msg.name, cls=msg.cls, iname=msg.iname), uid_answer)
        for uid, client in self.server.clients.items():
            QApplication.processEvents()
            if client.is_playing and uid_answer != uid:
                self.server.answer(uid_answer, ClientAddPlayer(
                    uid=uid, name=client.name, cls=client.cls, iname=client.iname
                ))
        self.players[uid_answer] = self.server.clients[uid_answer]
        self.controller.update_player_list(self.players)
        if msg.iname and (img := self.controller.getImage(msg.iname)):
            imageName = getImageMIME(f"player:{msg.name}:{msg.cls}:{uid_answer}")
            self.controller.register_image(imageName, img)
        self.player_panel.addPlayer(uid_answer, msg.name, msg.cls)
    
    @router.handler(MapActionType.MAPS_ALL_DATA)
    def _action_get_all_data(self, uid, _: GetAllMaps):
        self.controller.sync_client_data(uid)
    
    @router.handler(MapActionType.PLAYER_MOVED)
    def _handle_player_moved(self, uid, msg: MapPlayerMoved):
        token = self.controller.players_map[uid]
        token.move_to(QPointF(msg.pos[0], msg.pos[1]))
    
    def closeEvent(self, event):
        self.server.stop_server()
        return super().closeEvent(event)
    
    @router.handler(ImageActionType.NAME_REQUEST)
    def _handle_name_map(self, uid, msg: ImageNameRequest):
        if file_path := self.controller.getImage(msg.name):
            self.server.answer(uid, DoneCallback(uid_callback=msg.uid))
            self.server.answer_image(uid, file_path, msg.name)
        else:
            self.server.answer(uid, IgnoreCallback(uid_callback=msg.uid))
    
    def _handle_current_map(self, name: Optional[str]):
        if name is None:
            return
        self._deactivate_control()
        self.load_bg_action.setDisabled(False)
        self.active_map_action.setDisabled(False)
        self.delete_map_action.setDisabled(False)
        name_map = self.controller.tabMaps.getActiveNameMap()
        mWidget = self.controller.tabMaps.getMap(name_map)
        if mWidget and mWidget.file_map:
            self.bottomToolBar.setDisabled(False)
            self.topPaintBar.setDisabled(False)
            self._handle_change_state_fog(mWidget)
    
    def _deactivate_control(self):
        self.topPaintBar.setDisabled(True)
        self.bottomToolBar.setDisabled(True)
        self.topPaintBar.setDisabled(True)
        self.load_bg_action.setDisabled(True)
        self.delete_map_action.setDisabled(True)
        self.save_map_action.setDisabled(True)
        self.active_map_action.setDisabled(True)
