from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QFrame
from PySide6.QtGui import QFont

from .base import Note


class NoteView(QWidget):
    def __init__(self, note: Note, parent=None):
        super().__init__(parent)
        self.note = note or Note()
        
        self.box = QVBoxLayout(self)
        self.box.setContentsMargins(30, 30, 30, 30)
        
        self.textBrowser = QTextBrowser()
        self.textBrowser.setFrameShape(QFrame.Shape.NoFrame)
        self.textBrowser.viewport().setAutoFillBackground(False)
        self.textBrowser.setStyleSheet("background: transparent;")
        self.box.addWidget(self.textBrowser)
        
        self.updateView()
    
    def updateView(self):
        font = QFont(self.note.font_family, self.note.font_size)
        self.textBrowser.setFont(font)
        self.textBrowser.setHtml(self.note.text)
        bg_style = f"""
                    QWidget {{
                        background-image: url(:/letters/{self.note.bg_index}.png);
                        background-position: center;
                        background-repeat: no-repeat;
                        background-color: #f5f5dc; /* Бежевый цвет, если картинки нет */
                        border-radius: 5px;
                    }}
                """
        self.setStyleSheet(bg_style)
        
    def setData(self, note: Note):
        self.note = note
        self.updateView()
        
