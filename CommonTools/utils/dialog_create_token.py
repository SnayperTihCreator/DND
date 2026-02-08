from abc import abstractmethod, ABCMeta, ABC
from typing import Optional
from functools import cache

from attrs import define

from PySide6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QTextBrowser, QLineEdit, QComboBox, QMessageBox, \
    QCheckBox, QWidget, QTextEdit, QSpinBox, QPushButton, QWhatsThis, QHBoxLayout, QLabel, QFileDialog
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QImage

from CommonTools.components import AdvancedTextEdit
from .name_utils import FORBIDDEN_CHARS


class QMetaABC(ABCMeta, type(QWidget)):
    ...


@define(hash=True)
class DataDialog:
    name: str
    description: str
    kd: Optional[int]
    unique: Optional[bool]
    hp: int
    scale: float
    image_path: Optional[str] = None
    
    @cache
    def cttype(self, ttype: str):
        return f"{ttype}:{self.name}"
    
    @cache
    def cttypeAndNumber(self, ttype: str, number: str):
        return f"{ttype}:{self.name}:{number}"


class AutoResizingTextBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.textChanged.connect(self.updateGeometry)
    
    def sizeHint(self):
        return QSize(self.width(), self.fit_height())
    
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
    def __init__(self, sndTitle, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создание токена")
        
        self.box = QFormLayout(self)
        self.description_text = AutoResizingTextBrowser()
        self.description_text.setReadOnly(True)
        self.setDescription(f"Ввидите имя {sndTitle}")
        self.box.addRow(self.description_text)
        
        self.lineEditName = QLineEdit()
        self.lineEditName.setPlaceholderText("Имя токена")
        self.box.addRow("Имя:", self.lineEditName)
        
        self.checkBox = QCheckBox()
        self.box.addRow("Уникальный", self.checkBox)
        
        self.boxScale = QComboBox()
        self.boxScale.addItem("Мелкий", 0.25)
        self.boxScale.addItem("Маленький", 0.75)
        self.boxScale.addItem("Обычный", 1.0)
        self.boxScale.addItem("Большой", 2.0)
        self.boxScale.addItem("Огромный", 3.0)
        self.boxScale.addItem("Гиганский", 4.0)
        self.boxScale.setCurrentText("Обычный")
        
        self.btnHelp = QPushButton("?")
        self.btnHelp.setWhatsThis("<img src=':/textures/help_size.png'>")
        self.btnHelp.pressed.connect(self._whatThis)
        
        scale_box = QHBoxLayout()
        scale_box.addWidget(QLabel("Масштаб"))
        scale_box.addWidget(self.boxScale)
        scale_box.addWidget(self.btnHelp)
        
        self.box.addRow(scale_box)
        
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self._handle_request)
        self.buttonBox.rejected.connect(self.reject)
        self._preInit()
        self._postInit()
    
    def _whatThis(self):
        text = self.btnHelp.whatsThis()
        pos = self.btnHelp.mapToGlobal(QPoint(0, self.btnHelp.height()))
        
        QWhatsThis.showText(pos, text, self.btnHelp)
    
    def _handle_request(self):
        if self._handle_forbidden():
            QMessageBox.critical(self, "ОШИБКА БЛЯТЬ!!!",
                                 f"ТЫ ВИДИШЬ ЭТИ БУКВЫ: {FORBIDDEN_CHARS.pattern[1:-1]}\nИХ НЕЛЬЗЯ ИСПОЛЬЗОВАТЬ!!\nДОЛБОЯЩЕР!!")
        else:
            self.accept()
    
    def _handle_forbidden(self):
        return FORBIDDEN_CHARS.match(self.lineEditName.text()) is not None
    
    def _preInit(self):
        pass
    
    def _postInit(self):
        self.box.addRow(self.buttonBox)
    
    def setDescription(self, text):
        self.description_text.setPlainText(text)
        
    def showError(self, text):
        QMessageBox.critical(self, "Ошибка", text)
    
    @abstractmethod
    def getResult(self) -> DataDialog:
        ...
    
    @classmethod
    @abstractmethod
    def request(cls, sndTitle, parent=None):
        ...


class DialogCreateToken(BaseDialog):
    def _preInit(self):
        self.description_input = AdvancedTextEdit()
        self.box.addRow(self.description_input)
        
        self.btnSelectAvatar = QPushButton("Выбрать аватар")
        self.btnSelectAvatar.pressed.connect(self._handle_select_avatar)
        self.box.addRow("Аватар", self.btnSelectAvatar)
        
        self.spinBoxHp = QSpinBox(
            value=11,
            maximum=10 ** 6,
            minimum=0,
            singleStep=1,
        )
        self.box.addRow("Здоровье", self.spinBoxHp)
        
        self.spinBoxKd = QSpinBox(
            value=5,
            minimum=5,
            maximum=100,
            singleStep=1,
        )
        self.box.addRow("КД", self.spinBoxKd)
        
        self.path_avatar = None
        
    def _handle_select_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Аватарка токена", ".", "Image Files (*.png *.jpg *.jpeg)")
        if path:
            
            img = QImage(path)
            if img.isNull():
                self.showError("Не найдено изображение")
                return
            
            if img.sizeInBytes() >= 50 * 1024 ** 2:
                self.showError("Слишком большой вес изображения")
                return
            
            if (img.width() > 2048) or (img.height() > 2048):
                self.showError("Слишком большой размер изображения")
                return
            
            self.path_avatar = path
            self.btnSelectAvatar.setText("Выбрато")
    
    def getResult(self) -> DataDialog:
        return DataDialog(
            self.lineEditName.text(),
            self.description_input.toHtml(),
            self.spinBoxKd.value(),
            self.checkBox.isChecked(),
            self.spinBoxHp.value(),
            self.boxScale.itemData(self.boxScale.currentIndex(), Qt.ItemDataRole.UserRole),
            self.path_avatar
        )
    
    @classmethod
    def request(cls, sndTitle, parent=None) -> Optional[DataDialog]:
        dialog = cls(sndTitle, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.getResult()
        return None
