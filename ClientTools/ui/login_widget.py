from PySide6.QtCore import Signal, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QMainWindow, QComboBox
from PySide6.QtGui import QIcon
from loguru import logger

from CommonTools.core import ClientData, Socket, classes
from CommonTools.utils import FORBIDDEN_CHARS

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
        self.lineInputData.returnPressed.connect(self.on_press_button)
        self.box.addWidget(self.lineInputData)
        
        self.comboClass = QComboBox()
        self.comboClass.setIconSize(QSize(1, 1)*32)
        for cls, icon in classes.items():
            self.comboClass.addItem(QIcon(f":/icons/cls/{icon}.png"), cls)
        self.box.addWidget(self.comboClass)
        self.btn = QPushButton("Начать")
        self.box.addWidget(self.btn)
        self.btn.pressed.connect(self.on_press_button)
        self.setCentralWidget(self.cw)
    
    def on_press_button(self):
        lineData = self.lineInputData.text()
        if not lineData:
            self.error_occurred.emit("Пустое поле")
            return
        
        if FORBIDDEN_CHARS.search(lineData):
            self.error_occurred.emit(f"Ник не должен содержать {FORBIDDEN_CHARS.pattern[1:-1]}")
            return
        self.client_data.name = lineData
        self.client_data.cls = self.comboClass.currentText()
        self.socket.send_msg(ClientStartPlayer(
            name=self.client_data.name, cls=self.client_data.cls))
        logger.info("Запрос запуска сессии под: {name}|{clas}", name=self.client_data.name, clas=self.client_data.cls)
