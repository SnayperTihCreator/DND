from PySide6.QtWidgets import QDialog, QFormLayout, QTextBrowser, QLineEdit, QCheckBox, QDialogButtonBox


class DialogCreateMap(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        
        self.box = QFormLayout(self)
        
        self.message_label = QTextBrowser()
        self.message_label.setPlainText(message)
        self.box.addRow(self.message_label)
        
        self.lineEditName = QLineEdit()
        self.lineEditName.setPlaceholderText("Имя")
        self.box.addRow("Имя", self.lineEditName)
        
        self.checkBoxVisible = QCheckBox()
        self.checkBoxVisible.setChecked(False)
        self.box.addRow("Видимый", self.checkBoxVisible)
        
        self.btnBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.box.addRow(self.btnBox)
        
        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)
    
    @classmethod
    def getNameAndVisible(cls, title, message):
        dialog = cls(title, message)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.lineEditName.text(), dialog.checkBoxVisible.isChecked()
        return None, None
