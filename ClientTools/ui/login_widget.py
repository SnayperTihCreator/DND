from PySide6.QtCore import Signal, QSize, Qt
from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QMainWindow, QComboBox, QFormLayout, QFileDialog
from PySide6.QtGui import QIcon, QImage
from loguru import logger

from CommonTools.core import ClientData, Socket, classes
from CommonTools.utils import FORBIDDEN_CHARS, getImageMIME

from CommonTools.messages import *


class Loging(QMainWindow):
    error_occurred = Signal(str)
    
    def __init__(self, socket: Socket, client_data: ClientData):
        super().__init__()
        self.socket = socket
        self.client_data = client_data
        
        self.cw = QWidget()
        self.box = QFormLayout(self.cw)
        self.box.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        self.lineInputData = QLineEdit()
        self.lineInputData.setPlaceholderText("Имя персонажа")
        self.lineInputData.returnPressed.connect(self.on_press_button)
        self.box.addRow("Имя", self.lineInputData)
        
        self.comboClass = QComboBox()
        self.comboClass.setIconSize(QSize(1, 1) * 32)
        for cls, icon in classes.items():
            self.comboClass.addItem(QIcon(f":/icons/cls/{icon}.png"), cls)
        self.box.addRow("Класс", self.comboClass)
        
        self.selectAvToken = QPushButton("Выбрать")
        self.selectAvToken.setToolTip("Изображение не больше 2048*2048px и ≤50МБ")
        self.selectAvToken.pressed.connect(self._on_select_avatar)
        self.box.addRow("Аватарка", self.selectAvToken)
        
        self.btn = QPushButton("Начать")
        self.box.addWidget(self.btn)
        self.btn.pressed.connect(self.on_press_button)
        
        self.setCentralWidget(self.cw)
        
        self.avatar_path = None
    
    def _on_select_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Аватарка токена", ".", "Image Files (*.png *.jpg *.jpeg)")
        if path:
            img = QImage(path)
            if img.isNull():
                self.error_occurred.emit("Не найдено изображение")
                return
            
            if img.sizeInBytes() >= 50 * 1024 ** 2:
                self.error_occurred.emit("Слишком большой вес изображения")
                return
            
            if (img.width() > 2048) or (img.height() > 2048):
                self.error_occurred.emit("Слишком большой размер изображения")
                return
            
            self.avatar_path = path
            self.selectAvToken.setText("Выбрано")
    
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
        
        if self.avatar_path:
            iname = getImageMIME(self.client_data.mime)
            self.socket.send_image(self.avatar_path, iname)
        else:
            iname = None
        
        self.socket.send_msg(ClientStartPlayer(
            name=self.client_data.name,
            cls=self.client_data.cls,
            iname=iname
        ))
        logger.info("Запрос запуска сессии под: {name}|{clas}", name=self.client_data.name, clas=self.client_data.cls)
