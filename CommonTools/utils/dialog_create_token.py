from abc import abstractmethod, ABCMeta, ABC
from typing import Optional
from functools import cache

from attrs import define

from PySide6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QTextBrowser, QLineEdit, QComboBox, QMessageBox, \
    QCheckBox, QWidget, QTextEdit, QSpinBox
from PySide6.QtCore import Qt

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
    
    @cache
    def cttype(self, ttype: str):
        return f"{ttype}:{self.name}"
    
    @cache
    def cttypeAndNumber(self, ttype: str, number: str):
        return f"{ttype}:{self.name}:{number}"


class BaseDialog(QDialog, ABC, metaclass=QMetaABC):
    def __init__(self, sndTitle, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создание токена")
        
        self.box = QFormLayout(self)
        self.description_text = QTextBrowser()
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
        self.box.addRow("Масштаб", self.boxScale)
        
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self._handle_request)
        self.buttonBox.rejected.connect(self.reject)
        self._preInit()
        self._postInit()
    
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
        self.description_text.adjustSize()
    
    @abstractmethod
    def getResult(self) -> DataDialog:
        ...
    
    @classmethod
    @abstractmethod
    def request(cls, sndTitle, parent=None):
        ...


class DialogCreateToken(BaseDialog):
    def _preInit(self):
        self.description_input = QTextEdit()
        self.box.addRow(self.description_input)
        
        self.spinBoxHp = QSpinBox(
            value=11,
            maximum=10 ** 6,
            minimum=0,
            singleStep=1,
            suffix="hp"
        )
        self.box.addRow("Здоровье", self.spinBoxHp)
        
        self.spinBoxKd = QSpinBox(
            value=5,
            minimum=5,
            maximum=100,
            singleStep=1,
            suffix="kd"
        )
        self.box.addRow("КД", self.spinBoxKd)
    
    def getResult(self) -> DataDialog:
        return DataDialog(
            self.lineEditName.text(),
            self.description_input.toPlainText(),
            self.spinBoxKd.value(),
            self.checkBox.isChecked(),
            self.spinBoxHp.value(),
            self.boxScale.itemData(self.boxScale.currentIndex(), Qt.ItemDataRole.UserRole)
        )
    
    @classmethod
    def request(cls, sndTitle, parent=None) -> Optional[DataDialog]:
        dialog = cls(sndTitle, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.getResult()
        return None
