from PySide6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QDialogButtonBox
from PySide6.QtCore import Qt


class RunDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.box = QVBoxLayout(self)
        
        self.setWindowTitle("Виртуальный стол")
        
        self.comboBox = QComboBox()
        self.comboBox.addItem("Игрок", userData="Player")
        self.comboBox.addItem("Мастер", userData="Master")
        self.comboBox.setCurrentIndex(0)
        self.box.addWidget(self.comboBox)
        
        self.btn_dialog = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.box.addWidget(self.btn_dialog)
        
        self.btn_dialog.accepted.connect(self.accept)
        self.btn_dialog.rejected.connect(self.reject)
        
        
    @classmethod
    def getWhatRunner(cls, callback):
        dialog = cls()
        match dialog.exec():
            case QDialog.DialogCode.Accepted:
                return dialog.comboBox.currentData(Qt.ItemDataRole.UserRole)
            case QDialog.DialogCode.Rejected:
                callback()
                return None
        
        
        