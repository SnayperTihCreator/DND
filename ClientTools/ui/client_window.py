from pathlib import Path
from functools import partial

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QToolBar, QCheckBox, QGraphicsColorizeEffect
from PySide6.QtGui import QColor

from ClientTools.core.client_socket import WebSocketClient
from CommonTools.core import Image
from .connector_widget import Connector
from .login_widget import Loging
from .playerController import PlayerController
from CommonTools.components import GuidePanel, ColorButton, ImageManager, CallbackManager
from CommonTools.messages import *
from CommonTools.map_widget.tokens_dnd import MovedEvent


class PlayerGameTable(QMainWindow):
    def __init__(self, login):
        super().__init__()
        self.setMinimumSize(1000, 700)
        self.setWindowTitle("Виртуальный стол: Игрок")
        
        self.image_manager = ImageManager()
        self.callback_manager = CallbackManager()
        self.socket = WebSocketClient()
        self.client_data = self.socket.client
        self.socket.error_occurred.connect(self.showErrorMessage)
        self.socket.connected.connect(self._handle_connect)
        self.socket.disconnected.connect(self._handle_disconnect)
        self.socket.message_received.connect(self._handle_message_raw)
        self.socket.image_received.connect(self._handle_image)
        
        self.cache_folder = Path("./.cache")
        self.cache_folder.mkdir(exist_ok=True, parents=True)
        
        self.stacker = QStackedWidget()
        self.setCentralWidget(self.stacker)
        
        self.controller = PlayerController(self.socket)
        self.stacker.addWidget(self.controller)
        
        self.connector = Connector(self.socket)
        self.connector.error_occurred.connect(self.showErrorMessage)
        self.stacker.addWidget(self.connector)
        
        self.loging = Loging(self.socket, self.client_data)
        self.loging.error_occurred.connect(self.showErrorMessage)
        self.stacker.addWidget(self.loging)
        
        self.stacker.setCurrentWidget(self.connector)
        
        self.player_panel = GuidePanel("https://longstoryshort.app/characters/list/", "Лист персонажа", login)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.player_panel)
        self.player_panel.hide()
        
        self.menu_docker = self.menuBar().addMenu("Панели")
        self.player_panel_action = self.menu_docker.addAction("Открыть лист персонажа")
        self.player_panel_action.triggered.connect(self.player_panel.show)
        
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
        QTimer.singleShot(2000, self.resetEffect)
    
    def event(self, event):
        if event.type() == MovedEvent.MovedEventType:
            self.client_data.send_msg(MapPlayerMoved(
                uid=self.client_data.uid,
                pos=event.pos.toTuple()
            ))
            return True
        return super().event(event)
    
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
        print(f"Get image {image.name}{image.suffix} as {image.strategy}")
        self.image_manager.handle(image.name, cache_image)
    
    def _handle_message(self, msg: BaseMessage):
        if self.callback_manager.handle(msg):
            return
        
        if self.controller.handle_message(msg):
            return
        
        match msg.type:
            case ClientActionType.START_PLAYER:
                self.client_data.is_playing = True
                self.controller.active = True
                self.activate_controller()
                self.stacker.setCurrentWidget(self.controller)
                self.socket.send_msg(GetAllMaps())
            case MapActionType.LOAD_BACKGROUND if self.controller.active:
                self._handle_load_bg(msg)
            case _:
                print(f"unhandled <{msg.type}>{msg}")
    
    def _handle_load_bg(self, msg: MapLoadBackground):
        self.image_manager.register(msg.name, self._callback_load_bg)
        uid = self.callback_manager.register(True, ignore=partial(self.image_manager.unregister, msg.name))
        self.socket.send_msg(ImageNameRequest(name=msg.name, uid=uid))
    
    def _callback_load_bg(self, name, file_path):
        self.controller.tabMaps.load_map(name, file_path)
        self.controller.clear_buffer(name)
        
    def _handle_change_color(self, color):
        self.controller.tabMaps.call_all_method("setColorGrid", color)
        
    def _handle_change_vgrid(self, visible):
        self.controller.tabMaps.call_all_method("setVisibleGrid", visible)
