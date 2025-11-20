from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QMainWindow

from CommonTools.core import ClientData, Socket

from CommonTools.messages import *


class Loging(QMainWindow):
    error_occurred = Signal(str)
    
    def __init__(self, socket: Socket, client_data: ClientData):
        super().__init__()
        self.socket = socket
        self.client_data = client_data
        
        self.cw = QWidget()
        self.box = QVBoxLayout(self.cw)
        
        self.lineInputData = QLineEdit()
        self.lineInputData.setPlaceholderText("Имя персонажа")
        self.box.addWidget(self.lineInputData)
        
        self.lineInputClass = QLineEdit()
        self.lineInputClass.setPlaceholderText("Класс")
        self.box.addWidget(self.lineInputClass)
        
        self.btn = QPushButton("Начать")
        self.box.addWidget(self.btn)
        self.btn.pressed.connect(self.on_press_button)
        
        self.setCentralWidget(self.cw)
    
    def on_press_button(self):
        lineData = self.lineInputData.text()
        if not lineData:
            self.error_occurred.emit("Пустое поле")
            return
        
        if (":" in lineData) or ("|" in lineData):
            self.error_occurred.emit("Ник не должен содержать ':' или '|'")
            return
        self.client_data.name = lineData
        self.client_data.cls = self.lineInputClass.text()
        print(f"start {lineData}")
        self.socket.send_msg(ClientStartPlayer(name=lineData, cls=self.client_data.cls))
