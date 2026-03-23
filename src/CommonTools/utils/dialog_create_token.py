from abc import abstractmethod, ABCMeta, ABC
from functools import cache
from typing import Optional

from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QImage
from PySide6.QtWidgets import (QDialog, QFormLayout, QDialogButtonBox, QTextBrowser, QLineEdit,
                               QComboBox, QMessageBox, QCheckBox, QWidget, QSpinBox,
                               QPushButton, QWhatsThis, QHBoxLayout, QLabel, QFileDialog)
from attrs import define, field, validators

from CommonTools.components import AdvancedTextEdit
from .name_utils import FORBIDDEN_CHARS


# Исправленный метакласс для работы ABC с QWidget
class QMetaABC(ABCMeta, type(QWidget)):
    pass


@define(hash=True)
class DataDialog:
    name: str = field(validator=validators.instance_of(str))
    description: str = field(default="")
    kd: Optional[int] = field(default=None, validator=validators.optional(validators.ge(0)))
    unique: bool = field(default=False)
    hp: int = field(default=1, validator=validators.ge(0))
    # Валидация масштаба: от мелкого (0.1) до гигантского (10.0)
    scale: float = field(default=1.0, validator=validators.and_(
        validators.instance_of((int, float)),
        validators.ge(0.1),
        validators.le(10.0)
    ))
    image_path: Optional[str] = field(default=None)
    
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
        self.setDescription(f"Введите параметры для {sndTitle}")
        self.box.addRow(self.description_text)
        
        self.lineEditName = QLineEdit()
        self.lineEditName.setPlaceholderText("Имя токена")
        self.box.addRow("Имя:", self.lineEditName)
        
        self.checkBox = QCheckBox()
        self.box.addRow("Уникальный", self.checkBox)
        
        self.boxScale = QComboBox()
        # Данные храним в UserRole как float
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
        name = self.lineEditName.text().strip()
        
        if not name:
            self.showError("Имя не может быть пустым, долбоящер!")
            return
        
        if self._handle_forbidden():
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("ОШИБКА БЛЯТЬ!!!")
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setText(f"ТЫ ВИДИШЬ ЭТИ БУКВЫ: <b>{FORBIDDEN_CHARS.pattern[1:-1]}</b><br>"
                        f"ИХ НЕЛЬЗЯ ИСПОЛЬЗОВАТЬ!!<br><b>ДОЛБОЯЩЕР!!</b>")
            msg.exec()
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
        self.box.addRow("Описание (HTML):", self.description_input)
        
        self.btnSelectAvatar = QPushButton("Выбрать аватар")
        self.btnSelectAvatar.pressed.connect(self._handle_select_avatar)
        self.box.addRow("Аватар:", self.btnSelectAvatar)
        
        self.spinBoxHp = QSpinBox()
        self.spinBoxHp.setRange(0, 10 ** 6)
        self.spinBoxHp.setValue(11)
        self.box.addRow("Здоровье:", self.spinBoxHp)
        
        self.spinBoxKd = QSpinBox()
        self.spinBoxKd.setRange(0, 100)
        self.spinBoxKd.setValue(10)
        self.box.addRow("КД:", self.spinBoxKd)
        
        self.path_avatar = None
    
    def _handle_select_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Аватарка токена", ".", "Images (*.png *.jpg *.jpeg)")
        if path:
            img = QImage(path)
            if img.isNull():
                self.showError("Не удалось загрузить изображение!")
                return
            if img.sizeInBytes() >= 50 * 1024 ** 2:
                self.showError("Файл слишком тяжелый (>50MB)!")
                return
            
            self.path_avatar = path
            self.btnSelectAvatar.setText("Аватар выбран")
    
    def getResult(self) -> DataDialog:
        return DataDialog(
            name=self.lineEditName.text().strip(),
            description=self.description_input.toHtml(),
            kd=self.spinBoxKd.value(),
            unique=self.checkBox.isChecked(),
            hp=self.spinBoxHp.value(),
            scale=float(self.boxScale.currentData()),
            image_path=self.path_avatar
        )
    
    @classmethod
    def request(cls, sndTitle, parent=None) -> Optional[DataDialog]:
        dialog = cls(sndTitle, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.getResult()
        return None