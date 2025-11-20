from PySide6.QtCore import Signal, QUrl
from PySide6.QtWebSockets import QWebSocket

from CommonTools.core import Socket
from CommonTools.messages import *


class WebSocketClient(Socket):
    connected = Signal()
    disconnected = Signal()
    
    def __init__(self, max_size=10 * 1024 ** 2):
        super().__init__(QWebSocket())
        self.socket.setMaxAllowedIncomingMessageSize(max_size)
        
        self.socket.connected.connect(self.connected.emit)
        self.socket.disconnected.connect(self.disconnected.emit)
        self.socket.textMessageReceived.connect(self._handle_message)
        self.socket.errorOccurred.connect(self._handle_error)
        
        self.image_sender.client = self.client
    
    def connect_server(self, ip):
        self.socket.open(QUrl(f"ws://{ip}:8765"))
    
    def _handle_message(self, message):
        msg = BaseMessage.from_str(message)
        if not self.image_receiver.handle_message(msg):
            match msg.type:
                case ClientActionType.CONNECT:
                    self.client.uid = msg.uid
                    print(self.client.uid)
                case _:
                    self.message_received.emit(message)
    
    def _handle_error(self, error):
        msg_error = f"Error: {error}"
        self.error_occurred.emit(msg_error)
