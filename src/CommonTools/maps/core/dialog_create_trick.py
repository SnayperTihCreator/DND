from abc import ABCMeta, ABC, abstractmethod
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QSize, QPoint, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator, QImage
from PySide6.QtWidgets import QWidget, QTextBrowser, QDialog, QFormLayout, QLineEdit, QCheckBox, QComboBox, QPushButton, \
    QHBoxLayout, QWhatsThis, QDialogButtonBox, QMessageBox, QSpinBox, QFileDialog
from attrs import define, field

from CommonTools.components import AdvancedTextEdit


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


FORBIDDEN_PATTERN = QRegularExpression(r"[^|:@^\\n\\r\\t\"'`\\<>,%\\-]")


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
        validator = QRegularExpressionValidator(FORBIDDEN_PATTERN, self.lineEditName)
        self.lineEditName.setPlaceholderText("Имя токена")
        self.lineEditName.setValidator(validator)
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
        self.btnBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)
        self.__pre_init__()
        self.__post_init__()
    
    def setSubTitle(self, subtitle: str):
        self.subtitle.setPlainText(subtitle)
    
    def _whatThis(self):
        text = self.btnHelp.whatsThis()
        pos = self.btnHelp.mapToGlobal(QPoint(0, self.btnHelp.height()))
        QWhatsThis.showText(pos, text, self.btnHelp)
    
    def __post_init__(self):
        self.box.addRow(self.btnBox)
    
    def __pre_init__(self):
        pass
    
    @abstractmethod
    def get_result(self):
        ...
    
    @classmethod
    @abstractmethod
    def request(cls, subtitle: str, parent=None) -> Optional[ResultDialog]:
        ...


class DialogCreateTrick(BaseDialog):
    def __pre_init__(self):
        self.description = AdvancedTextEdit()
        self.box.addRow("Описание (HTML)", self.description)
        
        self.btnSelectAvatar = QPushButton("Выбрать аватар")
        self.btnSelectAvatar.pressed.connect(self._handle_select_avatar)
        self.box.addRow("Аватар", self.btnSelectAvatar)
        
        self.spinBoxHp = QSpinBox()
        self.spinBoxHp.setRange(0, 10 ** 6)
        self.spinBoxHp.setValue(11)
        self.box.addRow("Здоровье", self.spinBoxHp)
        
        self.spinBoxKd = QSpinBox()
        self.spinBoxKd.setRange(0, 100)
        self.spinBoxKd.setValue(10)
        self.box.addRow("КД", self.spinBoxKd)
        
        self._path: Optional[Path] = None
    
    def _handle_select_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Аватарка токена", ".", "Images (*.png *.jpg *.jpeg)")
        if not path: return
        
        img = QImage(path)
        if img.isNull():
            QMessageBox.critical(self, "Error", "Не удалось загрузить изображение!")
            return
        
        if img.sizeInBytes() >= 50 * 1024 ** 2:
            QMessageBox.critical(self, "Error", "Файл слишком тяжелый (>50MB)!")
            return
        
        self._path: Path = Path(path)
        self.btnSelectAvatar.setText(self._path.name)
    
    def get_result(self) -> ResultDialog:
        return ResultDialog(
            self.lineEditName.text().strip(),
            self.description.toHtml(),
            self.spinBoxKd.value(),
            self.checkBox.isChecked(),
            self.spinBoxHp.value(),
            float(self.boxScale.currentData()),
            Path(self._path)
        )
    
    @classmethod
    def request(cls, subtitle: str, parent=None) -> Optional[ResultDialog]:
        dialog = cls(subtitle, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_result()
        return None
