import asyncio
import logging
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QToolBar, QCheckBox,
    QGraphicsColorizeEffect, QMessageBox, QGraphicsEffect
)
from psygnal import set_async_backend

from ClientTools.core import AsyncClientBridge

from CommonTools.notes import Note
from CommonTools.updater_manager import UpdateManager
from CommonTools.core import classes
from CommonTools.components import GuidePanel, ColorButton, RouterDescriptor
from CommonTools.map_layout.tokens_dnd import MovedEvent
from CommonTools.messages import *
from CommonTools.utils import restart_app

from .login_widget import Loging
from .player_controller import PlayerController
from .note_book import NoteBookDock

logger = logging.getLogger(__name__)


class PlayerGameTable(QMainWindow):
    router = RouterDescriptor()
    
    def __init__(self, login, server_ip=None, server_port=None):
        super().__init__()
        logger.info("Initializing PlayerGameTable window...")
        
        self.server_ip = server_ip
        self.server_port = server_port
        
        self.setMinimumSize(1000, 700)
        self.setWindowIcon(QIcon(":/icons/main.png"))
        self.setWindowTitle("Виртуальный стол: Игрок")
        
        self.cache_folder = Path("./.cache/client")
        self.cache_folder.mkdir(exist_ok=True, parents=True)
        
        self.updater = UpdateManager(self)
        
        self.socket = AsyncClientBridge()
        self.client_data = self.socket.me
        
        self.socket.error_occurred.connect(self.showErrorMessage)
        self.socket.connected.connect(self._handle_connect)
        self.socket.disconnected.connect(self._handle_disconnect)
        self.socket.downloader.file_downloaded.connect(self._on_file_downloaded)
        self.socket.downloader.download_progress.connect(self._on_download_progress)
        
        self.stacker = QStackedWidget()
        self.setCentralWidget(self.stacker)
        
        self.controller = PlayerController(self.socket)
        self.stacker.addWidget(self.controller)
        
        self.loging = Loging(self.socket, self.client_data)
        self.loging.error_occurred.connect(self.showErrorMessage)
        self.stacker.addWidget(self.loging)
        
        self.player_panel = GuidePanel("...", "Лист персонажа", login)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.player_panel)
        self.player_panel.hide()
        
        self.player_cls_panel = GuidePanel("...", "Лист класса", f"{login}-cls")
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.player_cls_panel)
        self.player_cls_panel.hide()
        
        self.note_archive = NoteBookDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.note_archive)
        self.note_archive.hide()
        
        self.menu_docker = self.menuBar().addMenu("Панели")
        self.player_panel_action = self.menu_docker.addAction("Открыть лист персонажа")
        self.player_panel_action.triggered.connect(self.player_panel.show)
        self.player_cls_panel_action = self.menu_docker.addAction("Открыть лист класса")
        self.player_cls_panel_action.triggered.connect(self._on_action_show_player_cls)
        self.note_archive_action = self.menu_docker.addAction("Показать архив заметок")
        self.note_archive_action.triggered.connect(self.note_archive.show)
        
        self.menu_updater = self.menuBar().addMenu("Обновления")
        self.check_update_action = self.menu_updater.addAction("Проверить наличие обновлений")
        self.check_update_action.triggered.connect(self._on_action_check_update)
        
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
    
    def start_services(self):
        logger.info("Starting asynchronous services...")
        asyncio.create_task(self._start())
    
    async def _start(self):
        backend = set_async_backend("asyncio")
        await backend.running.wait()
        
        self.socket.message_received.connect(self._handle_message_raw)
        
        if self.server_ip and self.server_port:
            logger.info("Attempting to connect to server %s:%s", self.server_ip, self.server_port)
            self.socket.connect_server(self.server_ip, self.server_port)
        else:
            self.showErrorMessage("Could not determine server address.")
    
    def _on_file_downloaded(self, file_id: str, local_path: Path):
        logger.info("File '%s' downloaded. Applying...", file_id)
        map_name = Path(file_id).stem
        self.controller.register_image(file_id, local_path.as_posix())
        if self.controller.tabMaps.getMap(map_name):
            self.controller.tabMaps.load_map(map_name, local_path.as_posix())
            self.controller.clear_buffer(map_name)
    
    def _on_download_progress(self, file_id: str, percent: int):
        self.statusBar().showMessage(f"Downloading {file_id}: {percent}%")
        if percent == 100:
            QTimer.singleShot(1000, self.statusBar().clearMessage)
    
    def _on_action_check_update(self):
        logger.info("User initiated update check.")
        self.updater.check_for_updates(False)
    
    def _on_action_show_player_cls(self):
        if self.client_data.cls:
            url = f"https://5e14.ttg.club/classes/{classes.get(self.client_data.cls, '')}"
            self.player_cls_panel.handle_load_url(url)
            self.player_cls_panel.show()
        else:
            self.showErrorMessage("You have not selected a class yet")
    
    def deactivate_controller(self):
        self.bottomToolBar.hide()
    
    def activate_controller(self):
        self.bottomToolBar.show()
    
    def applyErrorEffect(self):
        colorize = QGraphicsColorizeEffect(self)
        colorize.setColor(QColor("#f00"))
        self.statusBar().setGraphicsEffect(colorize)
    
    def resetEffect(self):
        self.statusBar().setGraphicsEffect(QGraphicsEffect())
    
    def showErrorMessage(self, msg: str):
        self.applyErrorEffect()
        self.statusBar().showMessage(msg, 2000)
        logger.error("Error message shown to user: '%s'", msg)
        QTimer.singleShot(2000, self.resetEffect)
    
    def customEvent(self, event: MovedEvent):
        if event.type() == MovedEvent.MovedEventType:
            logger.debug("Sending token movement to position: %s", event.pos_target.toTuple())
            self.socket.send_msg(MapPlayerMoved(pos=event.pos_target.toTuple()))
            event.accept()
        super().customEvent(event)
    
    def _handle_connect(self):
        logger.info("Successfully connected to server. Switching to login screen.")
        self.statusBar().clearMessage()
        self.stacker.setCurrentWidget(self.loging)
    
    def _handle_disconnect(self):
        logger.critical("Connection to server lost! Initiating restart.")
        self.showErrorMessage("Server is dead")
        self.note_archive.save_backup()
        self.deactivate_controller()
        QMessageBox.critical(self, "Connection Lost",
                             "Connection to the server has been lost.\n"
                             "The application will now restart.")
        restart_app()
    
    async def _handle_message_raw(self, msg_raw: str):
        logger.debug("Received raw message: %s", msg_raw)
        msg = BaseMessage.from_str(msg_raw)
        await self._handle_message(msg)
    
    async def _handle_message(self, msg: BaseMessage):
        if self.controller.handle_message(msg):
            return
        if await self.router(self.client_data, msg):
            return
        logger.warning("Unprocessed message: type=%s, content=%s", msg.type, msg)
    
    @router.handler(ClientActionType.NOTE_MSG)
    def _handle_note_message(self, _uid, msg: ClientNoteMsg):
        logger.info("Received new note: '%s'", msg.title)
        note = Note(msg.content, msg.title, msg.idx_bg)
        self.note_archive.add_note(note)
    
    @router.handler(ClientActionType.START_PLAYER)
    def _handle_start_player(self, _uid, msg: ClientStartPlayer):
        logger.info("Received command to start player session.")
        self.client_data.is_playing = True
        self.controller.active = True
        self.activate_controller()
        self.stacker.setCurrentWidget(self.controller)
        self.socket.send_msg(GetAllMaps())
        
        if msg.iname:
            self.socket.send_msg(ImageNameRequest(name=msg.iname, uid=""))
    
    @router.handler(MapActionType.LOAD_BACKGROUND)
    def _handle_load_background(self, _uid, msg: MapLoadBackground):
        if not self.controller.active: return
        logger.info("Received command to load background for map '%s'", msg.name)
    
    @router.handler(ClientActionType.ADD_PLAYER)
    def _handle_add_player(self, _uid, msg: ClientAddPlayer):
        logger.info("Adding player token '%s' to map '%s'", msg.name, msg.map_name)
        self.controller.add_token(msg.map_name, msg.mime, msg.pos)
    
    def _handle_change_color(self, color):
        logger.debug("User changed grid color to %s", color)
        self.controller.tabMaps.call_all_method("setColorGrid", color)
    
    def _handle_change_vgrid(self, visible):
        logger.debug("User changed grid visibility to %s", visible)
        self.controller.tabMaps.call_all_method("setVisibleGrid", visible)
    
    def closeEvent(self, event):
        logger.info("Player window is closing.")
        self.updater.stop_download_thread()
        super().closeEvent(event)
