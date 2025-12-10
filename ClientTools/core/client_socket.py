from PySide6.QtCore import Signal, QUrl
from PySide6.QtWebSockets import QWebSocket
from loguru import logger
from CommonTools.core import Socket
from CommonTools.messages import BaseMessage, ClientActionType

logger = logger.bind(pack="SocketClient")


class WebSocketClient(Socket):
    connected = Signal()
    disconnected = Signal()
    
    def __init__(self, max_size=10485760):
        super().__init__(QWebSocket())
        self.socket.setMaxAllowedIncomingMessageSize(max_size)
        self.socket.connected.connect(self.connected.emit)
        self.socket.disconnected.connect(self.disconnected.emit)
        self.socket.textMessageReceived.connect(self._on_message)
        self.socket.errorOccurred.connect(self._on_error)
        self.image_sender.client = self.client
    
    def connect_server(self, ip):
        self.socket.open(QUrl(f"ws://{ip}:8765"))
    
    def _on_message(self, message):
        msg = BaseMessage.from_str(message)
        if self.image_receiver.handle_message(msg):
            return
        
        match msg.type:
            case ClientActionType.CONNECT:
                self.client.uid = msg.uid
                logger.success(f"Connected: {msg.uid}")
            case _:
                self.message_received.emit(message)
    
    def _on_error(self, _):
        self.error_occurred.emit(f"Connection error: {self.socket.errorString()}")
