from functools import partial
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QToolBar, QCheckBox,
    QGraphicsColorizeEffect
)
from loguru import logger

from ClientTools.core.client_socket import WebSocketClient
from CommonTools.core import Image, classes
from CommonTools.components import GuidePanel, ColorButton, AsyncRequestManager, ImageContext, MessageRouter
from CommonTools.map_widget.tokens_dnd import MovedEvent
from CommonTools.messages import (
    BaseMessage, ClientActionType, MapActionType, MapPlayerMoved,
    GetAllMaps, MapLoadBackground, ImageNameRequest, ClientStartPlayer, ClientAddPlayer
)
from CommonTools.utils import getImageMIME
from .connector_widget import Connector
from .login_widget import Loging
from .playerController import PlayerController

logger = logger.bind(pack="ClientWindow")

router = MessageRouter()


class PlayerGameTable(QMainWindow):
    def __init__(self, login):
        super().__init__()
        self.setMinimumSize(1000, 700)
        self.setWindowIcon(QIcon(":/icons/main.png"))
        self.setWindowTitle("Виртуальный стол: Игрок")
        
        self.cache_folder = Path("./.cache")
        self.cache_folder.mkdir(exist_ok=True, parents=True)
        
        # Managers
        self.async_manager = AsyncRequestManager()
        
        # Socket setup
        self.socket = WebSocketClient()
        self.client_data = self.socket.client
        
        self.socket.error_occurred.connect(self.showErrorMessage)
        self.socket.connected.connect(self._handle_connect)
        self.socket.disconnected.connect(self._handle_disconnect)
        self.socket.message_received.connect(self._handle_message_raw)
        self.socket.image_received.connect(self._handle_image)
        
        # UI Setup
        self.stacker = QStackedWidget()
        self.setCentralWidget(self.stacker)
        
        # Pages
        self.controller = PlayerController(self.socket)
        self.stacker.addWidget(self.controller)
        self.controller.request_image.connect(self._on_request_image)
        
        self.connector = Connector(self.socket)
        self.connector.error_occurred.connect(self.showErrorMessage)
        self.stacker.addWidget(self.connector)
        
        self.loging = Loging(self.socket, self.client_data)
        self.loging.error_occurred.connect(self.showErrorMessage)
        self.stacker.addWidget(self.loging)
        
        self.stacker.setCurrentWidget(self.connector)
        
        # Docks
        self.player_panel = GuidePanel(
            "https://longstoryshort.app/characters/list/",
            "Лист персонажа",
            login
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.player_panel)
        self.player_panel.hide()
        
        self.player_cls_panel = GuidePanel(
            "https://5e14.ttg.club/classes",
            "Лист класса",
            f"{login}-cls"
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.player_cls_panel)
        self.player_cls_panel.hide()
        
        # Menu
        self.menu_docker = self.menuBar().addMenu("Панели")
        
        self.player_panel_action = self.menu_docker.addAction("Открыть лист персонажа")
        self.player_panel_action.triggered.connect(self.player_panel.show)
        
        self.player_cls_panel_action = self.menu_docker.addAction("Открыть лист класса")
        self.player_cls_panel_action.triggered.connect(self._on_action_show_player_cls)
        
        # Toolbar
        self.bottomToolBar = QToolBar()
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.bottomToolBar)
        
        self.btnColorGrid = ColorButton(color="#4a4a4a")
        self.btnColorGrid.color_changed.connect(self._handle_change_color)
        
        self.checkBoxVisibleGrid = QCheckBox("Сетка")
        self.checkBoxVisibleGrid.setChecked(True)
        self.checkBoxVisibleGrid.toggled.connect(self._handle_change_vgrid)
        
        self.bottomToolBar.addWidget(self.btnColorGrid)
        self.bottomToolBar.addWidget(self.checkBoxVisibleGrid)
        
        self.deactivate_controller()
    
    def _on_action_show_player_cls(self):
        if self.client_data.cls:
            url = f"https://5e14.ttg.club/classes/{classes.get(self.client_data.cls, '')}"
            self.player_cls_panel.handle_load_url(url)
            self.player_cls_panel.show()
        else:
            self.showErrorMessage("Вы еще не выбрали класс")
    
    def deactivate_controller(self):
        self.bottomToolBar.hide()
    
    def activate_controller(self):
        self.bottomToolBar.show()
    
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
    
    def customEvent(self, event: MovedEvent):
        if event.type() == MovedEvent.MovedEventType:
            self.client_data.send_msg(MapPlayerMoved(pos=event.pos_target.toTuple()))
            event.accept()
        super().customEvent(event)
    
    def _handle_connect(self):
        self.statusBar().clearMessage()
        self.stacker.setCurrentWidget(self.loging)
    
    def _handle_disconnect(self):
        self.showErrorMessage("Сервер сдох")
        self.deactivate_controller()
        self.stacker.setCurrentWidget(self.connector)
        self.controller.tabMaps.clearMaps()
    
    def _handle_message_raw(self, msg_raw: str):
        msg = BaseMessage.from_str(msg_raw)
        self._handle_message(msg)
    
    def _handle_image(self, image: Image):
        cache_image = self.cache_folder / f"{image.name}{image.suffix}"
        cache_image.write_bytes(image.image_data)
        
        logger.debug("Получено изображение {iname}{isuffix} через {istrategy}",
                     iname=image.name, isuffix=image.suffix, istrategy=image.strategy)
        self.async_manager.handle_resource("images", image.name, cache_image.as_posix())
    
    def _handle_message(self, msg: BaseMessage):
        if self.async_manager.handle_message(msg):
            return
        if self.controller.handle_message(msg):
            return
        if router.dispatch(self, self.client_data, msg):
            return
        logger.info("Не обработанное сообщение: {mtype} - {msg}", mtype=msg.type, msg=msg)
    
    @router.handler(ClientActionType.START_PLAYER)
    def _handle_start_player(self, _uid, msg: ClientStartPlayer):
        self.client_data.is_playing = True
        self.controller.active = True
        self.activate_controller()
        self.stacker.setCurrentWidget(self.controller)
        self.socket.send_msg(GetAllMaps())
        
        if msg.iname:
            ctx = ImageContext(None, self._callback_my_avatar, msg.iname)
            self.async_manager.register(ctx)
            self.socket.send_msg(ImageNameRequest(name=msg.iname, uid=ctx.uid))
        logger.info("Запуск сессии")
    
    def _callback_my_avatar(self, ctx: ImageContext, file_name: str):
        self.controller.register_image(ctx.name, file_name)
    
    @router.handler(MapActionType.LOAD_BACKGROUND)
    def _handle_load_bg(self, _uid, msg: MapLoadBackground):
        if not self.controller.active: return
        ctx = ImageContext(None, self._callback_load_bg, msg.name)
        self.async_manager.register(ctx)
        self.socket.send_msg(ImageNameRequest(name=ctx.name, uid=ctx.uid))
    
    def _callback_load_bg(self, ctx: ImageContext, file_path):
        logger.info("Загрузка фона")
        self.statusBar().showMessage("Загрузка фона", 2000)
        self.controller.tabMaps.load_map(ctx.name, file_path)
        self.controller.clear_buffer(ctx.name)
    
    @router.handler(ClientActionType.ADD_PLAYER)
    def _handle_add_player(self, _uid, msg: ClientAddPlayer):
        ctx = ImageContext(None, self._callback_add_player, msg.iname)
        self.async_manager.register(ctx)
        self.socket.send_msg(ImageNameRequest(name=ctx.name, uid=ctx.uid))
    
    def _callback_add_player(self, ctx: ImageContext, file_path):
        self.controller.register_image(ctx.name, file_path)
    
    def _on_request_image(self, name, _mime: str):
        ctx = ImageContext(None, self._callback_image_downloaded, name)
        self.async_manager.register(ctx)
        self.socket.send_msg(ImageNameRequest(name=name, uid=ctx.uid))
    
    def _callback_image_downloaded(self, ctx: ImageContext, file_path):
        self.controller.register_image(ctx.name, file_path)
    
    def _handle_change_color(self, color):
        self.controller.tabMaps.call_all_method("setColorGrid", color)
    
    def _handle_change_vgrid(self, visible):
        self.controller.tabMaps.call_all_method("setVisibleGrid", visible)
