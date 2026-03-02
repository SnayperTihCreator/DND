from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton

from ClientTools.core.client_socket import AsyncClientBridge


class Connector(QWidget):
    error_occurred = Signal(str)
    
    def __init__(self, socket: AsyncClientBridge):
        super().__init__()
        self.socket = socket
        
        self.box = QVBoxLayout(self)
        
        self.lineInputIp = QLineEdit()
        self.lineInputIp.setPlaceholderText("IP адрес мастера")
        self.lineInputIp.setText("127.0.0.1")
        self.lineInputIp.returnPressed.connect(self.on_press_button)
        self.box.addWidget(self.lineInputIp)
        
        # --- ИЗМЕНЕНИЕ 3: ДОБАВЛЯЕМ ПОЛЕ ДЛЯ ПОРТА ---
        self.lineInputPort = QLineEdit()
        self.lineInputPort.setPlaceholderText("Порт (по умолчанию 8765)")
        self.lineInputPort.setText("8765")
        self.lineInputPort.returnPressed.connect(self.on_press_button)
        self.box.addWidget(self.lineInputPort)
        
        self.btn = QPushButton("Подключиться")
        self.box.addWidget(self.btn)
        self.btn.pressed.connect(self.on_press_button)
    
    def on_press_button(self):
        ip = self.lineInputIp.text().strip()
        port_str = self.lineInputPort.text().strip()
        
        if not ip:
            self.error_occurred.emit("Введите IP адрес")
            return
        
        if not port_str:
            self.error_occurred.emit("Введите порт")
            return
        
        try:
            port = int(port_str)
            self.socket.connect_server(ip, port)
        except ValueError:
            self.error_occurred.emit("Порт должен быть числом")
