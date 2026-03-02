from pathlib import Path

from PySide6.QtCore import Signal, QSize, Qt
from PySide6.QtWidgets import (QWidget, QLineEdit, QPushButton, QMainWindow,
                               QComboBox, QFormLayout, QFileDialog)
from PySide6.QtGui import QIcon, QImage
from loguru import logger
from qasync import asyncSlot

from CommonTools.core import ClientData, classes
from ClientTools.core.client_socket import AsyncClientBridge
from CommonTools.utils import FORBIDDEN_CHARS
from CommonTools.messages import ClientStartPlayer


class Loging(QMainWindow):
    error_occurred = Signal(str)
    
    def __init__(self, socket: AsyncClientBridge, client_data: ClientData):
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
        self.selectAvToken.setToolTip("Изображение не больше 2048x2048px и ≤50МБ")
        self.selectAvToken.pressed.connect(self._on_select_avatar)
        self.box.addRow("Аватарка", self.selectAvToken)
        
        self.btn = QPushButton("Начать")
        self.box.addWidget(self.btn)
        self.btn.pressed.connect(self.on_press_button)
        
        self.setCentralWidget(self.cw)
        
        self.avatar_path = None
    
    def _on_select_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Аватарка токена", ".", "Image Files (*.png *.jpg *.jpeg)")
        if not path:
            return
        
        img = QImage(path)
        if img.isNull():
            self.error_occurred.emit("Не удалось прочитать изображение")
            return
        
        if img.sizeInBytes() >= 50 * 1024 ** 2:
            self.error_occurred.emit("Слишком большой вес изображения (макс. 50 МБ)")
            return
        
        if (img.width() > 2048) or (img.height() > 2048):
            self.error_occurred.emit("Слишком большой размер изображения (макс. 2048x2048)")
            return
        
        self.avatar_path = path
        self.selectAvToken.setText(Path(path).name)
    
    @asyncSlot()
    async def on_press_button(self):
        lineData = self.lineInputData.text().strip()
        if not lineData:
            self.error_occurred.emit("Введите имя персонажа")
            return
        
        if FORBIDDEN_CHARS.search(lineData):
            self.error_occurred.emit(f"Ник не должен содержать символы: {FORBIDDEN_CHARS.pattern[1:-1]}")
            return
        
        self.client_data.name = lineData
        self.client_data.cls = self.comboClass.currentText()
        
        avatar_url = None
        if self.avatar_path:
            self.btn.setDisabled(True)
            self.btn.setText("Загрузка аватара...")
            
            # Асинхронно загружаем файл на сервер
            uploaded_url = await self.socket.upload_file(Path(self.avatar_path))
            
            self.btn.setDisabled(False)
            self.btn.setText("Начать")
            
            if not uploaded_url:
                self.error_occurred.emit("Не удалось загрузить аватар")
                return
            
            avatar_url = uploaded_url
        
        self.socket.send_msg(ClientStartPlayer(
            name=self.client_data.name,
            cls=self.client_data.cls,
            iname=avatar_url
        ))
        
        logger.info(f"Запрос на запуск сессии: {self.client_data.name} ({self.client_data.cls})")
