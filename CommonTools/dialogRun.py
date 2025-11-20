from PySide6.QtWidgets import QDialog, QFormLayout, QComboBox, QDialogButtonBox, QLineEdit, QMessageBox
from PySide6.QtCore import Qt


class RunDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.box = QFormLayout(self)
        
        self.setWindowTitle("Виртуальный стол")
        
        self.lineLogin = QLineEdit()
        self.lineLogin.setPlaceholderText("Логин")
        self.lineLogin.setText("DndGame")
        
        self.box.addRow("Логин", self.lineLogin)
        
        self.comboBox = QComboBox()
        self.comboBox.addItem("Игрок", userData="Player")
        self.comboBox.addItem("Мастер", userData="Master")
        self.comboBox.setCurrentIndex(0)
        self.box.addRow("Роль", self.comboBox)
        
        self.btn_dialog = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.box.addRow(self.btn_dialog)
        
        self.btn_dialog.accepted.connect(self._handle_accepted)
        self.btn_dialog.rejected.connect(self.reject)
        
    def _handle_accepted(self):
        if self.lineLogin.text().strip():
            self.accept()
        else:
            QMessageBox.warning(self, "Пустое поле ввода логина",
                                "Было определено пустое поле ввода логина.\n"
                                "Логин нужен для работы браузеров.")
        
        
    @classmethod
    def getWhatRunner(cls, callback):
        dialog = cls()
        match dialog.exec():
            case QDialog.DialogCode.Accepted:
                return dialog.comboBox.currentData(Qt.ItemDataRole.UserRole), dialog.lineLogin.text().strip()
            case QDialog.DialogCode.Rejected:
                callback()
                return None, None
        
        
        