from PySide6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QTextBrowser, QLineEdit, QComboBox, QMessageBox
from PySide6.QtCore import Qt

from .name_utils import FORBIDDEN_CHARS


class BaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создание токена")
        
        self.box = QFormLayout(self)
        self.description_text = QTextBrowser()
        self.description_text.setReadOnly(True)
        self.box.addRow(self.description_text)
        
        self.lineEditName = QLineEdit()
        self.lineEditName.setPlaceholderText("Имя токена")
        self.box.addRow("Имя:", self.lineEditName)
        
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self._handle_request)
        self.buttonBox.rejected.connect(self.reject)
    
    def _handle_request(self):
        if self._handle_forbidden():
            QMessageBox.warning(self, "Не разрешенные символы!",
                                f"Найдены запрещенные символы: {FORBIDDEN_CHARS.pattern[1:-1]}")
        else:
            self.accept()
    
    def _handle_forbidden(self):
        return FORBIDDEN_CHARS.match(self.lineEditName.text()) is None
    
    def initBtnDialog(self):
        self.box.addRow(self.buttonBox)
    
    def setDescription(self, text):
        self.description_text.setPlainText(text)
        self.description_text.adjustSize()


class DialogCreateToken(BaseDialog):
    def __init__(self, sndTitle, parent=None):
        super().__init__(parent)
        self.setDescription("Ввидите имя и номер моба")
        
        self.lineEditFn = QLineEdit()
        self.box.addRow(sndTitle, self.lineEditFn)
        
        self.boxScale = QComboBox()
        self.boxScale.addItem("Мелкий", 0.25)
        self.boxScale.addItem("Маленький", 0.75)
        self.boxScale.addItem("Обычный", 1)
        self.boxScale.addItem("Большой", 2)
        self.boxScale.addItem("Огромный", 3)
        self.boxScale.addItem("Гиганский", 4)
        self.boxScale.setCurrentText("Обычный")
        self.box.addRow("Масштаб", self.boxScale)
        
        self.initBtnDialog()
    
    def _handle_forbidden(self):
        return super()._handle_forbidden() or (FORBIDDEN_CHARS.search(self.lineEditFn.text()) is None)
    
    @classmethod
    def request(cls, sndTitle, parent=None):
        dialog = cls(sndTitle, parent)
        if dialog.exec_() == QDialog.DialogCode.Accepted:
            return dialog.lineEditName.text(), dialog.lineEditFn.text(), dialog.boxScale.itemData(
                dialog.boxScale.currentIndex(), Qt.ItemDataRole.UserRole)
        return None, None, None
