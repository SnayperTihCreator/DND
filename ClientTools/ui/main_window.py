from typing import Callable, Optional
import uuid
from pathlib import Path

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMainWindow, QStackedWidget

from ClientTools.core.client import WebSocketClient
from ClientTools.core.client_data import ClientData
from ClientTools.core.image_receiver import ReceivedImage
from .login_widget import Loging
from .connector_widget import Connector
from ServerTools.ui.master_map_controller import MasterMapController
from ClientTools.ui.player_map_controller import PlayerMapController

from CommonTools.messages import *


class GameTable(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1000, 700)
        
        self._init_components()
        self._setup_ui()
        self._connect_signals()
        
        self.cache_folder = Path("./.cache")
        self.cache_folder.mkdir(parents=True, exist_ok=True)
        self.setWindowTitle("Виртуальный стол")
    
    def _init_components(self):
        """Инициализация компонентов приложения"""
        self.client = WebSocketClient(50 * 1024 * 1024)
        self.client_data = ClientData()
        self.players: dict[str, ClientData] = {}
        self.quen_image_load = {}
        self.triggers: dict[str, Callable] = {}
        
        self.stated = QStackedWidget()
        self.connector = Connector(self.client)
        self.loging = Loging(self.client, self.client_data)
        self.master_map: Optional[MasterMapController] = None
        self.player_map: Optional[PlayerMapController] = None
    
    def _setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.stated.addWidget(self.connector)
        self.stated.addWidget(self.loging)
        
        self.setCentralWidget(self.stated)
        self.stated.setCurrentWidget(self.connector)
    
    def _connect_signals(self):
        """Подключение сигналов и слотов"""
        self._setup_client_connections()
        self.connector.error.connect(self.show_error)
        self.loging.error.connect(self.show_error)
    
    def _setup_client_connections(self):
        """Настройка соединений с WebSocket клиентом"""
        connections = [
            (self.client.connected, self.on_client_connected),
            (self.client.disconnected, self.on_client_disconnected),
            (self.client.error_occurred, self.on_error_occurred),
            (self.client.message_received, self.on_msg_text),
            (self.client.image_received, self.on_image_received)
        ]
        
        for signal, slot in connections:
            signal.connect(slot)
    
    @Slot()
    def on_client_connected(self):
        """Обработка успешного подключения к серверу"""
        uid = uuid.uuid4().hex
        mode_trigger = self.active_master_mode if self.client_data.isMaster else self.active_player_mode
        self.register_trigger(uid, mode_trigger)
        self.statusBar().clearMessage()
    
    @Slot()
    def on_client_disconnected(self):
        """Обработка отключения от сервера"""
        self.stated.setCurrentWidget(self.connector)
        self.statusBar().showMessage("Сервер сдох")
        self.setWindowTitle("Виртуальный стол")
    
    @Slot(str, int)
    def on_progress(self, session_id, progress):
        """Обработка прогресса операции"""
        print(f"Session {session_id}: {progress}%")
    
    @Slot(str)
    def on_error_occurred(self, error_message):
        """Обработка ошибок соединения"""
        print(f"Connection error: {error_message}")
    
    @Slot(str)
    def on_msg_text(self, text):
        """Обработка текстовых сообщений"""
        self.handle_msg(BaseMessage.from_str(text))
    
    @Slot(ReceivedImage)
    def on_image_received(self, image_ref: ReceivedImage):
        """Обработка полученных изображений"""
        
        ci = self.client_data.image_load[image_ref.name] = self.cache_folder / f"{image_ref.name}.png"
        ci.write_bytes(image_ref.image_data)
        
        if image_ref.name in self.quen_image_load:
            match self.quen_image_load[image_ref.name]:
                case "background":
                    self._load_map_background(image_ref.name, ci)
                    self.statusBar().clearMessage()
                    del self.quen_image_load[image_ref.name]
    
    def active_master_mode(self):
        """Активация режима мастера"""
        self.master_map = MasterMapController(self.client, self.client_data)
        self.stated.addWidget(self.master_map)
        self.stated.setCurrentWidget(self.master_map)
        self.master_map.active = True
        self.setWindowTitle("Виртуальный стол: Мастер")
    
    def active_player_mode(self):
        """Активация режима игрока"""
        self.player_map = PlayerMapController(self.client, self.client_data)
        self.stated.addWidget(self.player_map)
        self.stated.setCurrentWidget(self.player_map)
        self.player_map.active = True
        self.setWindowTitle("Виртуальный стол: Игрок")
    
    def register_trigger(self, uid: str, callback: Callable):
        """Регистрация триггера обратного вызова"""
        self.triggers[uid] = callback
    
    def unregister_trigger(self, uid: str):
        del self.triggers[uid]
    
    def callback_trigger(self, uid: str):
        self.triggers[uid]()
        self.unregister_trigger(uid)
    
    def show_error(self, message: str):
        """Отображение ошибки в статусной строке"""
        self.statusBar().showMessage(message, 1000)
    
    # noinspection PyTypeChecker
    def handle_msg(self, msg: BaseMessage):
        """Обработка входящих сообщений"""
        match msg.type:
            case CommonActionType.IGNORE:
                self.unregister_trigger(msg.uid_callback)
            case CommonActionType.DONE_CALL:
                self.callback_trigger(msg.uid_callback)
            case ClientActionType.CONNECT:
                self._handle_client_connect(msg)
            case ClientActionType.START_PLAYER:
                self._handle_client_start_player(msg)
            case ClientActionType.START_MASTER:
                self._handle_client_start_master(msg)
            case ClientActionType.ADD_PLAYER:
                self._handle_client_add_data(msg)
            case CommonActionType.ERROR:
                self._handle_service_error(msg)
            case ClientActionType.REMOVE_PLAYER:
                self._handle_client_remove(msg)
            case MapActionType.LOAD_BACKGROUND:
                self._handle_map_background(msg)
            case ImageActionType.NAME_REQUEST:
                self._handle_request_image(msg)
            case _:
                print(f"Unhandled message type: {msg.type}")
    
    def _handle_connect_master(self):
        self.client.answer(MapGetBeginLoad(uid=self.client_data.uid))
        self.client.answer(MapGetAllTokens(uid=self.client_data.uid))
    
    def _handle_client_connect(self, msg: ClientConnect):
        """Обработка подключения клиента"""
        self.client_data.uid = msg.uid
        self.stated.setCurrentWidget(self.loging)
    
    def _handle_client_start_player(self, msg: ClientStartPlayer):
        """Обработка старта режима игрока"""
        if msg.name == self.client_data.name:
            self.active_player_mode()
        uid_callback = uuid.uuid4().hex
        self.register_trigger(uid_callback, self._handle_connect_master)
        self.client.answer(ClientMasterConnectHas(uid_callback=uid_callback))
    
    def _handle_client_start_master(self, msg: ClientStartMaster):
        """Обработка старта режима мастера"""
        self.active_master_mode()
    
    def _handle_client_add_data(self, msg: ClientAddPlayer):
        """Обработка добавления данных клиента"""
        if not msg.name:
            return
        player = ClientData(msg.uid, msg.name, msg.cls, False)
        self.players[player.uid] = player
        self.updateDataMap()
        
    def updateDataMap(self):
        if self.client_data.uid is None:
            return
        if self.master_map and self.master_map.active:
            self.master_map.update_players_list(self.players)
        if self.player_map and self.player_map.active:
            self.player_map.update_players_list(self.players)
    
    def _handle_service_error(self, msg: ErrorMessage):
        """Обработка ошибок сервиса"""
        self.show_error(msg.error)
    
    def _handle_client_remove(self, msg: ClientRemovePlayer):
        """Обработка удаления клиента"""
        if msg.uid in self.players:
            del self.players[msg.uid]
        self.updateDataMap()
    
    def _load_map_background(self, name, path):
        if self.client_data.uid is None:
            return
        self.player_map.load_map(name, path)
        
    
    
    def _handle_map_background(self, msg: MapLoadBackground):
        """Обработка данных фоновой карты"""
        if msg.name not in self.client_data.image_load:
            self.player_map.tabMaps.addMap(msg.name)
            self.client.answer(ImageNameRequest(name=msg.name))
            self.quen_image_load[msg.name] = "background"
        else:
            self._load_map_background(msg.name, self.client_data.image_load[msg.name])
        self.statusBar().showMessage("Внимание! Загружается карта")
    
    def _handle_request_image(self, msg: ImageNameRequest):
        image_path = self.client_data.image_load.get(msg.name)
        if image_path is None:
            self.client.answer(ErrorMessage(error="Не найдено было изображение"))
        self.client.send_image(image_path, msg.name)
