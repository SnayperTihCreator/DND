import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal, QSize, Qt
from PySide6.QtWidgets import (QWidget, QLineEdit, QPushButton, QMainWindow,
                               QComboBox, QFormLayout, QFileDialog)
from PySide6.QtGui import QIcon, QImage
from qasync import asyncSlot

from CommonTools.core import ClientData, classes
from ClientTools.core.client_socket import AsyncClientBridge
from CommonTools.utils import FORBIDDEN_CHARS
from network.messages import ClientStartPlayer

logger = logging.getLogger(__name__)


class Loging(QMainWindow):
    error_occurred = Signal(str)
    
    def __init__(self, socket: AsyncClientBridge, client_data: ClientData):
        super().__init__()
        logger.info("Login widget initialized.")
        self.socket = socket
        self.cd = client_data
        
        self.cw = QWidget()
        self.box = QFormLayout(self.cw)
        self.box.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        self.lineInputData = QLineEdit()
        self.lineInputData.setPlaceholderText("Character Name")
        self.lineInputData.returnPressed.connect(self.on_press_button)
        self.box.addRow("Name", self.lineInputData)
        
        self.comboClass = QComboBox()
        self.comboClass.setIconSize(QSize(1, 1) * 32)
        for cls, icon in classes.items():
            self.comboClass.addItem(QIcon(f":/icons/cls/{icon}.png"), cls)
        self.box.addRow("Class", self.comboClass)
        
        self.selectAvToken = QPushButton("Select")
        self.selectAvToken.setToolTip("Image up to 2048x2048px and ≤50MB")
        self.selectAvToken.pressed.connect(self._on_select_avatar)
        self.box.addRow("Avatar", self.selectAvToken)
        
        self.btn = QPushButton("Start")
        self.box.addWidget(self.btn)
        self.btn.pressed.connect(self.on_press_button)
        
        self.setCentralWidget(self.cw)
        
        self.avatar_path: Optional[Path] = None
    
    def _on_select_avatar(self):
        logger.debug("Avatar selection dialog opened.")
        path, _ = QFileDialog.getOpenFileName(self, "Token Avatar", ".", "Image Files (*.png *.jpg *.jpeg)")
        if not path:
            logger.debug("Avatar selection cancelled.")
            return
        
        img = QImage(path)
        if img.isNull():
            logger.warning("Failed to read selected image file: %s", path)
            self.error_occurred.emit("Could not read the image file")
            return
        
        if img.sizeInBytes() >= 50 * 1024 ** 2:
            logger.warning("Selected avatar is too large: %s bytes", img.sizeInBytes())
            self.error_occurred.emit("Image file size is too large (max. 50MB)")
            return
        
        if (img.width() > 2048) or (img.height() > 2048):
            logger.warning("Selected avatar dimensions are too large: %sx%s", img.width(), img.height())
            self.error_occurred.emit("Image dimensions are too large (max. 2048x2048)")
            return
        
        logger.info("Avatar selected successfully: %s", path)
        _, self.avatar_path = self.socket.loadTo(path)
        self.selectAvToken.setText(Path(path).name)
    
    @asyncSlot()
    async def on_press_button(self):
        logger.info("'Start' button pressed.")
        
        lineData = self.lineInputData.text().strip()
        if not lineData:
            logger.warning("Attempted to start with an empty character name.")
            self.error_occurred.emit("Please enter a character name")
            return
        
        if FORBIDDEN_CHARS.search(lineData):
            logger.warning("Attempted to use a name with forbidden characters: %s", lineData)
            self.error_occurred.emit(f"Name must not contain: {FORBIDDEN_CHARS.pattern[1:-1]}")
            return
        
        self.cd.name = lineData
        self.cd.cls = self.comboClass.currentText()
        
        self.socket.send(ClientStartPlayer(name=self.cd.name, cls=self.cd.cls))
        
        logger.info("Session start requested for: %s (%s)", self.cd.name, self.cd.cls)
