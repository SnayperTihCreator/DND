from abc import ABCMeta, ABC
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtWidgets import QWidget, QTextBrowser, QDialog, QFormLayout, QLineEdit, QCheckBox, QComboBox, QPushButton, \
    QHBoxLayout, QWhatsThis
from attrs import define, field


class QMetaABC(ABCMeta, type(QWidget)):
    pass


@define
class ResultDialog:
    name: str
    description: str = field(default="")
    kd: int = field(default=100)
    unique: bool = field(default=False)
    hp: int = field(default=1)
    scale: float = field(default=1.0)
    path: Path = field(factory=lambda: Path(""))
    
    
class AutoResizingTextBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.textChanged.connect(self.updateGeometry)
        
    def sizeHint(self):
        return QSize(self.width(), self.height())
    
    def fit_height(self):
        doc = self.document()
        doc.setTextWidth(self.viewport().width())
        height = doc.size().height()
        height += self.frameWidth() * 2
        return int(height + 5)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateGeometry()
        
        
class BaseDialog(QDialog, ABC, metaclass=QMetaABC):
    def __init__(self, subtitle: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создание токена")
        
        self.box = QFormLayout(self)
        self.subtitle = AutoResizingTextBrowser()
        self.subtitle.setReadOnly(True)
        self.setSubTitle(subtitle)
        self.box.addRow(self.subtitle)
        
        self.lineEditName = QLineEdit()
        self.lineEditName.setPlaceholderText("Имя токена")
        self.box.addRow("Имя", self.lineEditName)
        
        self.checkBox = QCheckBox()
        self.box.addRow("Уникальный", self.checkBox)
        
        self.boxScale = QComboBox()
        self.boxScale.addItem("Мелкий", 0.25)
        self.boxScale.addItem("Маленький", 0.75)
        self.boxScale.addItem("Обычный", 1.0)
        self.boxScale.addItem("Большой", 2.0)
        self.boxScale.addItem("Огромный", 3.0)
        self.boxScale.addItem("Гигантский", 4.0)
        self.boxScale.setCurrentText("Обычный")
        
        self.btnHelp = QPushButton("?")
        self.btnHelp.setWhatsThis("<img src=':/textures/help_size.png'>")
        self.btnHelp.pressed.connect(self._whatThis)
        
        scale_box = QHBoxLayout()
        scale_box.addWidget(self.boxScale)
        scale_box.addWidget(self.btnHelp)
        
        self.box.addRow("Масштаб", scale_box)
        
    def setSubTitle(self, subtitle: str):
        self.subtitle.setPlainText(subtitle)
    
    def _whatThis(self):
        text = self.btnHelp.whatsThis()
        pos = self.btnHelp.mapToGlobal(QPoint(0, self.btnHelp.height()))
        QWhatsThis.showText(pos, text, self.btnHelp)
        