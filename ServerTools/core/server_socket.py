import uuid
from functools import partial
from contextlib import contextmanager

from PySide6.QtCore import Signal
from PySide6.QtWebSockets import QWebSocketServer
from PySide6.QtNetwork import QHostAddress
from PySide6.QtWidgets import QApplication

from CommonTools.core import Socket, ClientData, ImageSender
from CommonTools.messages import *


class WebSocketServer(Socket):
    message_received_uid = Signal(str, str)
    client_connected = Signal(str)
    client_disconnected = Signal(str)
    
    def __init__(self, max_size=10 * 1024 ** 2):
        super().__init__(None)
        self.clients: dict[str, ClientData] = {}
        self.server = QWebSocketServer("DndRunner", QWebSocketServer.SslMode.NonSecureMode)
        self.max_size_msg = max_size
    
    def start_server(self):
        if self.server.listen(QHostAddress("0.0.0.0"), 8765):
            self.server.newConnection.connect(self.on_new_connection)
            return True
        else:
            return False
    
    @contextmanager
    def bind_client(self, uid):
        try:
            self.client = self.clients[uid]
            self.socket = self.client.socket
            yield
        finally:
            self.client = None
            self.socket = None
    
    def on_new_connection(self):
        socket = self.server.nextPendingConnection()
        socket.setMaxAllowedIncomingMessageSize(self.max_size_msg)
        if socket:
            uid = uuid.uuid4().hex
            self.clients[uid] = ClientData(uid, "", "", socket)
            
            socket.textMessageReceived.connect(partial(self._handle_message, uid))
            socket.disconnected.connect(partial(self._handle_disconnect, uid))
            self.client_connected.emit(uid)
            self.answer(uid, ClientConnect(uid=uid))
    
    def send_msg(self, msg: BaseMessage):
        for uid, client in self.clients.items():
            QApplication.processEvents()
            client.send_msg(msg)
    
    def send_image(self, path, name):
        for uid, client in self.clients.items():
            self.image_sender.send_image_socket(path, name, client)
    
    def answer(self, uid: str, msg: BaseMessage):
        with self.bind_client(uid):
            self.clients[uid].send_msg(msg)
    
    def answer_image(self, uid: str, path, name):
        client = self.clients[uid]
        self.image_sender.send_image_socket(path, name, client)
    
    def broadcast(self, msg: BaseMessage, uid_answer=None):
        for uid, client in self.clients.items():
            QApplication.processEvents()
            if uid_answer and (uid == uid_answer):
                continue
            client.send_msg(msg)
    
    def _handle_message(self, uid: str, message: str):
        msg = BaseMessage.from_str(message)
        if not self.image_receiver.handle_message(msg):
            match msg.type:
                case ClientActionType.START_PLAYER:
                    self.clients[uid].name = msg.name
                    self.clients[uid].cls = msg.cls
                    self.clients[uid].is_playing = True
            self.message_received_uid.emit(uid, message)
            self.message_received.emit(message)
    
    def _handle_disconnect(self, uid: str):
        if uid in self.clients:
            self.clients[uid].socket.deleteLater()
            del self.clients[uid]
        self.client_disconnected.emit(uid)
    
    def stop_server(self):
        for client in self.clients.values():
            client.socket.close()
        self.server.close()
