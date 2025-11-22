from PySide6.QtWidgets import (QFormLayout, QDialog, QVBoxLayout, QLineEdit,
                               QDialogButtonBox, QTextBrowser)


class TwoInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ввод двух значений")
        self.resize(300, 150)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.requestText = QTextBrowser()
        layout.addWidget(self.requestText)
        
        box = QFormLayout()
        layout.addLayout(box)
        
        self.input1 = QLineEdit()
        box.addRow("Первое значение:", self.input1)
        
        self.input2 = QLineEdit()
        box.addRow("Второе значение:", self.input2)
        
        # Кнопки
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
    
    def get_values(self):
        return self.input1.text(), self.input2.text()
    
    def setPlaceholders(self, ph1, ph2, q):
        self.input1.setPlaceholderText(ph1)
        self.input2.setPlaceholderText(ph2)
        self.requestText.setPlainText(q)
    
    @classmethod
    def request(cls, qu, ph1="", ph2=""):
        dialog = cls()
        dialog.setPlaceholders(ph1, ph2, qu)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_values()
        return None, None
