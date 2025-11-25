from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QFormLayout, QComboBox, QDialogButtonBox, QLineEdit, QMessageBox, QPushButton
from PySide6.QtCore import Qt


class RunDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.box = QFormLayout(self)
        self.setWindowIcon(QIcon(":/icons/main.png"))
        self.setWindowTitle("Виртуальный стол")
        
        self.lineLogin = QLineEdit()
        self.lineLogin.setPlaceholderText("Логин")
        self.lineLogin.setText("DndGame")
        
        self.active_mode = None
        
        self.box.addRow("Логин", self.lineLogin)
        
        btnPlayer = QPushButton("Игрок")
        btnPlayer.pressed.connect(self._handle_pressed)
        btnPlayer.setProperty("udata", "player")
        
        btnMaster = QPushButton("Мастер")
        btnMaster.pressed.connect(self._handle_pressed)
        btnMaster.setProperty("udata", "master")
        
        self.btn_dialog1 = QDialogButtonBox()
        self.btn_dialog1.addButton(btnPlayer, QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_dialog1.addButton(btnMaster, QDialogButtonBox.ButtonRole.AcceptRole)
        self.box.addRow(self.btn_dialog1)
        
        self.btn_dialog2 = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel,
            centerButtons=True
        )
        self.box.addRow(self.btn_dialog2)
        
        self.btn_dialog1.accepted.connect(self._handle_accepted)
        self.btn_dialog2.rejected.connect(self.reject)
    
    def _handle_pressed(self):
        btn = self.sender()
        self.active_mode = btn.property("udata")
    
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
                return dialog.active_mode, dialog.lineLogin.text().strip()
            case QDialog.DialogCode.Rejected:
                callback()
                return None, None
