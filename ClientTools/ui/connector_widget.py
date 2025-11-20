from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton

from ClientTools.core.client_socket import WebSocketClient


class Connector(QWidget):
    error_occurred = Signal(str)
    
    def __init__(self, socket: WebSocketClient):
        super().__init__()
        self.socket = socket
        
        self.box = QVBoxLayout(self)
        
        self.lineInputIp = QLineEdit()
        self.lineInputIp.setPlaceholderText("xxx.xxx.xxx.xxx")
        self.lineInputIp.setText("127.0.0.1")
        self.box.addWidget(self.lineInputIp)
        
        self.btn = QPushButton("Connect")
        self.box.addWidget(self.btn)
        self.btn.pressed.connect(self.on_press_button)
    
    def on_press_button(self):
        ip = self.lineInputIp.text().strip()
        if ip:
            self.socket.connect_server(ip)
        else:
            self.error_occurred.emit("Пустой IP")