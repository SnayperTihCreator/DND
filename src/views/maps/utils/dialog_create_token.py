from pathlib import Path
from typing import Optional

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator, QImage
from PySide6.QtWidgets import QDialog, QMessageBox, QFileDialog
from network.mime import *
from network.mime.token_mime import CacheTokenMime
from .data import CreateData
from uic.dialog_create_token_ui import Ui_CreateToken

forbidden_chars = r'|:@\n\r\t\'\"`\\<>,%-'


class DialogCreateToken(QDialog, Ui_CreateToken):
    def __init__(self, subtitle, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.btnBox.accepted.connect(self._handle_accept)
        self.btnBox.rejected.connect(self.reject)
        self.btnSelectAvatar.clicked.connect(self._handle_select_avatar)
        self.label.setText(self.label.text().format(subtitle))
        regex = QRegularExpression(f"[^{forbidden_chars}]")
        self.validator = QRegularExpressionValidator(regex)
        self.lineEditName.setValidator(self.validator)
        self._avatar: Optional[Path] = None
        self._scales = (0.25, 0.75, 1.0, 2.0, 3.0, 4.0)
        
    def _handle_accept(self):
        name = self.lineEditName.text().strip()
        
        if not name:
            QMessageBox.critical(self, "Error", "Please enter a name.")
            
        self.accept()
        
    def _handle_select_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Avatar", None, "Images(*.png *.jpg *.jpeg)")
        if path:
            img = QImage(path)
            if img.isNull():
                QMessageBox.critical(self, "Error", "Не удалось загрузить изображение!")
                return
            if img.sizeInBytes() >= 50 * 1024 ** 2:
                QMessageBox.critical(self, "Error", "Файл слишком тяжелый (>50MB)!")
                return
            self._avatar = Path(path)
            self.btnSelectAvatar.setText(f"Avatar: {self._avatar.name}")
            
    @property
    def avatar(self):
        return Path(self._avatar)
    
    @property
    def mime(self) -> TokensMime:
        return CacheTokenMime(
            name=self.lineEditName.text().strip(),
            unique=self.checkBoxUnique.isChecked()
        )
    
    @property
    def scale(self):
        return self._scales[self.comboBoxScale.currentIndex()]
            
    @classmethod
    def request(cls, subtitle, parent=None) -> Optional[CreateData]:
        dialog = cls(subtitle, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return CreateData(
                dialog.mime, dialog.scale, dialog.textEditDescription.toHtml(),
                dialog.avatar
            )
        return None
        
        
    
            
        
        